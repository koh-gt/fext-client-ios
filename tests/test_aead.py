#!/usr/bin/env python3
"""Proof that the pure-Python AEAD fallback in app/main.py is correct and
wire-compatible with the `cryptography` library.

Runs anywhere (no Kivy, no native crypto needed) — the known-answer vectors
always execute; the differential fuzz against `cryptography` only runs when
that library is importable (i.e. on desktop/CI, never on the iOS device where
the pure tier is what actually ships).

    python3 tests/test_aead.py            # quick: KAT + 200 fuzz cases
    FEXT_FUZZ=10000 python3 tests/test_aead.py   # thorough differential run

Exit code is non-zero on any failure, so CI can gate on it.
"""
import importlib.util
import os
import sys
import tempfile
import types

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "app", "main.py")


# --- import app/main.py with Kivy stubbed (the UI is never touched here) ------
def _install_kivy_stubs():
    def cls(name):
        return type(name, (object,), {"__init__": lambda self, *a, **k: None})

    def mod(name, **attrs):
        m = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(m, k, v)
        sys.modules[name] = m

    ns = types.SimpleNamespace
    mod("kivy")
    mod("kivy.app", App=cls("App"))
    mod("kivy.clock", Clock=ns(schedule_once=lambda *a, **k: None,
                               schedule_interval=lambda *a, **k: None))
    mod("kivy.core")
    mod("kivy.core.clipboard", Clipboard=ns(copy=lambda *a: None))
    mod("kivy.core.image", Image=cls("CoreImage"))
    mod("kivy.core.window", Window=ns(bind=lambda *a, **k: None, size=(0, 0),
                                      softinput_mode="", clearcolor=None))
    mod("kivy.graphics", Color=cls("Color"), Ellipse=cls("Ellipse"),
        Line=cls("Line"), RoundedRectangle=cls("RR"), Triangle=cls("Tri"))
    mod("kivy.metrics", dp=lambda v: v, sp=lambda v: v)
    mod("kivy.uix")
    for path, names in {
        "anchorlayout": ["AnchorLayout"], "behaviors": ["ButtonBehavior"],
        "boxlayout": ["BoxLayout"], "filechooser": ["FileChooserListView"],
        "image": ["Image"], "label": ["Label"], "modalview": ["ModalView"],
        "scrollview": ["ScrollView"], "textinput": ["TextInput"],
        "widget": ["Widget"],
    }.items():
        mod(f"kivy.uix.{path}", **{n: cls(n) for n in names})
    mod("kivy.uix.screenmanager", NoTransition=cls("NoTransition"),
        Screen=cls("Screen"), ScreenManager=cls("ScreenManager"),
        SlideTransition=cls("SlideTransition"))
    mod("kivy.utils", get_color_from_hex=lambda h: (0, 0, 0, 1),
        platform="linux")
    mod("qrcode", QRCode=cls("QRCode"))
    if importlib.util.find_spec("requests") is None:
        mod("requests", Session=cls("Session"), RequestException=Exception,
            Response=cls("Response"), exceptions=ns())


def load_main():
    _install_kivy_stubs()
    os.environ["HOME"] = tempfile.mkdtemp()      # keys land in a throwaway dir
    spec = importlib.util.spec_from_file_location("fext_main", MAIN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


FAILS = 0


def check(name, cond):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + name)
    if not cond:
        FAILS += 1


# --- known-answer tests (no dependencies) ------------------------------------
def test_kat(m):
    # FIPS-197 Appendix C.3 AES-256 block
    key = bytes.fromhex("000102030405060708090a0b0c0d0e0f"
                        "101112131415161718191a1b1c1d1e1f")
    got = m._AES256(key).encrypt_block(bytes.fromhex(
        "00112233445566778899aabbccddeeff"))
    check("FIPS-197 AES-256 block", got.hex() == "8ea2b7ca516745bfeafc4990"
          "4b496089")

    # NIST GCM-256: empty key/iv/pt -> tag only
    ct = m.AESGCMPure(bytes(32)).encrypt(bytes(12), b"", None)
    check("NIST GCM-256 empty", ct.hex() ==
          "530f8afbc74536b9a963b4f1c4cb738b")
    # NIST GCM-256: one zero block
    ct = m.AESGCMPure(bytes(32)).encrypt(bytes(12), bytes(16), None)
    check("NIST GCM-256 one block", ct.hex() ==
          "cea7403d4d606b6e074ec5d3baf39d18d0d1c8a799996bf0265b98b5d48ab919")

    # RFC 5869 HKDF-SHA256 test case 1
    okm = m._hkdf_sha256_pure(bytes.fromhex("0b" * 22), 42,
                              bytes.fromhex("000102030405060708090a0b0c"),
                              bytes.fromhex("f0f1f2f3f4f5f6f7f8f9"))
    check("RFC5869 HKDF case 1", okm.hex() ==
          "3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf"
          "34007208d5b887185865")


# --- differential fuzz vs cryptography (only when it is importable) -----------
def test_differential(m):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM as Ref
        from cryptography.hazmat.primitives.hashes import SHA256
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:     # absent OR broken (e.g. pyo3 PanicException)
        print("  skip differential fuzz (cryptography not importable here)")
        return
    n = int(os.environ.get("FEXT_FUZZ", "200"))
    ok = True
    for _ in range(n):
        key, nonce = os.urandom(32), os.urandom(12)
        pt = os.urandom(int.from_bytes(os.urandom(2), "big") % 600)
        aad = os.urandom(int.from_bytes(os.urandom(1), "big") % 64)
        mine = m.AESGCMPure(key).encrypt(nonce, pt, aad)
        if mine != Ref(key).encrypt(nonce, pt, aad):
            ok = False
            break
        if Ref(key).decrypt(nonce, mine, aad) != pt:
            ok = False
            break
        if m.AESGCMPure(key).decrypt(nonce, Ref(key).encrypt(nonce, pt, aad),
                                     aad) != pt:
            ok = False
            break
    check(f"{n} differential GCM cases vs cryptography", ok)

    ok = True
    for _ in range(min(n, 500)):
        ikm = os.urandom(int.from_bytes(os.urandom(1), "big") % 64 + 1)
        length = int.from_bytes(os.urandom(1), "big") % 128 + 1
        info = os.urandom(int.from_bytes(os.urandom(1), "big") % 40)
        if m._hkdf_sha256_pure(ikm, length, None, info) != HKDF(
                algorithm=SHA256(), length=length, salt=None,
                info=info).derive(ikm):
            ok = False
            break
    check("differential HKDF vs cryptography", ok)


# --- end-to-end envelope through the real CryptoEngine, both tiers ------------
def test_envelope_interop(m):
    def identity(label):
        priv, _pub, addr, _n = m.mine_identity()
        km = m.IdentityManager()
        km.add_identity(priv, label)
        km.set_username(label.lower())
        return km, addr

    a_keys, a_addr = identity("Alice")
    b_keys, _b_addr = identity("Bob")
    a, b = m.CryptoEngine(a_keys), m.CryptoEngine(b_keys)
    body = "hearthside ✓✓✓ — 0123456789 the quick brown fox"
    native = m.HAVE_NATIVE_AEAD

    tiers = [(False, False, "pure->pure")]
    if native:
        tiers += [(True, True, "native->native"),
                  (True, False, "native->pure (iOS interop)"),
                  (False, True, "pure->native (iOS interop)")]
    for send, recv, note in tiers:
        m.HAVE_NATIVE_AEAD = send
        env, _ = a.build_envelope(body, b_keys.public_key_hex)
        m.HAVE_NATIVE_AEAD = recv
        payload = b.open_envelope(env, a_addr)
        check(f"{note}: round-trips", payload["body"] == body and
              payload["sender"]["address"] == a_addr)
        ct = bytearray(m.b64d(env["ciphertext"]))
        ct[0] ^= 1
        env["ciphertext"] = m.b64e(bytes(ct))
        try:
            b.open_envelope(env, a_addr)
            check(f"{note}: tamper rejected", False)
        except m.CryptoEngine.EnvelopeError:
            check(f"{note}: tamper rejected", True)
    m.HAVE_NATIVE_AEAD = native


if __name__ == "__main__":
    mod = load_main()
    print(f"app/main.py loaded — AEAD backend here: {mod.AEAD_BACKEND}")
    test_kat(mod)
    test_differential(mod)
    test_envelope_interop(mod)
    print()
    print("RESULT:", "ALL PASSED" if FAILS == 0 else f"{FAILS} FAILURE(S)")
    sys.exit(1 if FAILS else 0)
