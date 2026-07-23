<p align="center">
  <img src="ios/icon-preview-1024.png" alt="FEXT" width="160" height="160">
</p>

<h1 align="center">FEXT for iOS</h1>

<p align="center">
  A production iOS package of the FEXT end-to-end-encrypted messenger —
  the single-file Kivy client, built for the iPhone with <a
  href="https://github.com/kivy/kivy-ios">kivy-ios</a>.
</p>

---

FEXT is an open-source, end-to-end-encrypted messenger. Every message is signed
and sealed **on the device** before it leaves; the relay only ever handles
opaque ciphertext and a public `username → address` directory. Identities are
Bitcoin-compatible secp256k1 keys whose addresses carry a `Fec` proof-of-work
prefix. The whole client is one auditable file — [`app/main.py`](app/main.py) —
so the single promise the system rests on can be verified line by line:

> **No plaintext ever leaves the process.**

This repository turns that client into a shippable iOS app: the entry point,
the build pipeline, the app icons and launch screen, the `Info.plist`
configuration, a proof suite for the crypto, and CI.

## Repository layout

| Path | What it is |
|------|------------|
| `app/main.py` | The complete FEXT client — the kivy-ios app entry point. |
| `tests/test_aead.py` | Proof the pure-Python AES-GCM/HKDF matches `cryptography` + NIST/RFC vectors, and that envelopes round-trip through the real `CryptoEngine`. |
| `scripts/build_ios.sh` | One-command, reproducible kivy-ios build → Xcode project. |
| `scripts/export_ipa.sh` | Turns the built project into an installable `.ipa` (unsigned for sideloading, or signed — manual signing for CI). |
| `scripts/publish_release.sh` | Attaches the built `.ipa`(s) to a GitHub Release (full release when signed, pre-release when unsigned). |
| `scripts/patch_xcode.py` | Injects `Info.plist` keys, icons and the launch screen into the generated project. |
| `scripts/make_assets.py` | Regenerates the app-icon set from the brand palette. |
| `ios/AppIcon.appiconset/` | The generated, App-Store-safe icon set (opaque, no alpha). |
| `ios/LaunchScreen.storyboard` | Branded launch screen. |
| `ios/info_additions.plist` | ATS, orientation and status-bar keys merged at build time. |
| `requirements.txt` / `requirements-ios.txt` | Desktop dev deps / the pure-Python deps kivy-ios installs. |
| `.github/workflows/ios.yml` | CI: fast crypto proof on every push; full macOS build on demand. |

## The one interesting build decision: crypto without `cryptography`

The FEXT crypto core (secp256k1, ECDSA, ECDH, Base58Check, RIPEMD-160) is
already **pure Python** with an optional native fast-path (`coincurve`). The
only hard native dependency used to be the [`cryptography`](https://pypi.org/project/cryptography/)
library, for AES-256-GCM and HKDF-SHA256.

`cryptography`'s modern releases bind to a Rust extension that **does not
cross-compile through kivy-ios** — it is the single most common Kivy-on-iOS
build failure (`ImportError: … PyInit_cryptography_hazmat_bindings__rust`).

So this build adds an **AEAD layer** to `app/main.py` that uses the exact same
two-tier strategy the secp256k1 code already uses:

```
Tier 1  cryptography (AES-NI / libcrypto)  — used when installed (desktop/CI)
Tier 2  a self-contained pure-Python        — used when it is not (iOS)
        AES-256-GCM + HKDF-SHA256
```

The pure tier has **zero native dependencies**, so the iOS build needs no
OpenSSL/Rust recipe at all. It is not a reinterpretation of the standard — it
is verified **byte-identical** to `cryptography`:

- FIPS-197 AES-256 known-answer test
- NIST AES-256-GCM vectors
- RFC 5869 HKDF-SHA256 vectors
- 10,000+ randomized differential cases (both encrypt directions,
  cross-decryption, tamper rejection)
- the exact FEXT envelope shape, round-tripped through the real `CryptoEngine`
  in **all four** tier combinations (so a message sealed on desktop opens on
  iOS and vice versa)

The wire format, keys, addresses, signatures and envelope layout are
**unchanged** — desktop, Android and iOS all interoperate. Re-run the proof:

```bash
pip install cryptography           # the reference to diff against
FEXT_FUZZ=10000 python3 tests/test_aead.py
```

(The vectors run even without `cryptography` installed — the differential part
simply skips, which is exactly the situation on the phone.)

## Prerequisites (build machine)

iOS binaries can only be produced on **macOS**. You need:

- macOS with **Xcode** + Command Line Tools (`xcode-select --install`)
- **Homebrew** (`build_ios.sh` uses it for `autoconf automake libtool pkg-config`)
- Python 3.9+
- An **Apple Developer account** for signing (only needed to run on a device or
  submit — the build itself does not need it)

## Build

```bash
# from the repo root, on macOS:
APP_TITLE=FEXT \
BUNDLE_ID=com.yourorg.fext \
PROJECT_VERSION=3.1.0 \
BUILD_NUMBER=1 \
scripts/build_ios.sh
```

The first run compiles CPython, Kivy, the SDL2 stack and Pillow for iOS and
takes **20–60 minutes**. Subsequent runs reuse the compiled frameworks; pass
`SKIP_TOOLCHAIN_BUILD=1` to skip the recipe step explicitly.

What the script does:

1. builds the kivy-ios recipes: `python3 kivy pillow` (note: **not**
   `cryptography`);
2. installs the pure-Python deps from `requirements-ios.txt`
   (`requests`, `qrcode`, `websocket-client`);
3. runs `toolchain create` to generate `build-ios/FEXT-ios/`;
4. runs `scripts/patch_xcode.py` to set the bundle id / version and install the
   FEXT `Info.plist` keys, icons and launch screen.

## Install on your iPhone (getting a `.ipa`)

> A `.ipa` can only be built on **macOS**, and iOS will not install an *unsigned*
> app — "directly on an iPhone" always means *something* signs it (Xcode,
> AltStore/Sideloadly, or your developer certificate). No `.ipa` can be produced
> on Linux. Pick the path that matches what you have:

### A — You have a Mac (easiest)

Run straight from Xcode; it signs with your Apple ID (a **free** ID gives a
7-day install, a **paid** one lasts a year):

```bash
scripts/build_ios.sh
open build-ios/FEXT-ios/FEXT.xcodeproj   # Signing & Capabilities → your Team → ▶ Run
```

Prefer a `.ipa` file? After `build_ios.sh`:

```bash
METHOD=ad-hoc TEAM_ID=YOURTEAMID scripts/export_ipa.sh   # → build-ios/ipa/export/FEXT.ipa
```

### B — No Mac, free Apple ID → build in CI, sideload (no paid account)

1. Push this repo (or apply the bundle) so GitHub Actions can run.
2. **Actions → iOS → Run workflow** — the `ios-build` job runs on a macOS runner.
3. Grab **`FEXT-unsigned.ipa`** either from the run's **`fext-ios-ipa`** artifact
   or, more conveniently, from the **GitHub Release** the run publishes (see
   *"CI publishes a Release"* below).
4. Install it with **[AltStore](https://altstore.io)** or
   **[Sideloadly](https://sideloadly.io)** — they re-sign it with your Apple ID
   and push it to the device over USB/Wi-Fi. Re-sign every 7 days on a free ID.

### C — Signed `.ipa` from CI (paid Apple Developer account)

With a paid membership the `ios-build` job also emits a **signed**,
directly-installable `.ipa`. It signs **manually** in CI (the reliable path —
automatic signing needs an interactive Xcode), so a **profile name is required**.

**Secrets** (Settings → Secrets and variables → Actions → *Secrets*):

| Secret | How to produce it |
|--------|-------------------|
| `APPLE_CERT_P12_BASE64` | Export your **Apple Distribution** cert + key from Keychain Access as `cert.p12`, then `base64 -i cert.p12 \| pbcopy`. |
| `APPLE_CERT_PASSWORD` | The password you set on that `.p12`. |
| `APPLE_PROVISIONING_PROFILE_BASE64` | An **ad-hoc** profile (`.mobileprovision`) for your bundle id, whose device list includes each target iPhone's **UDID**; `base64 -i profile.mobileprovision \| pbcopy`. |

**Variables** (same page → *Variables*):

| Variable | Value |
|----------|-------|
| `APPLE_TEAM_ID` | Your 10-char Team ID. |
| `APPLE_PROFILE_NAME` | The profile's **exact name** (as shown in the Developer portal). **Required** — this selects manual signing. |
| `IPA_METHOD` | `ad-hoc` (direct device install, default) or `app-store` (TestFlight). |
| `APPLE_SIGN_IDENTITY` | *Optional* override; defaults to `Apple Distribution` (or `Apple Development` for the `development` method). |

The bundle id you build with (`BUNDLE_ID`, default `com.example.fext`) **must
match the provisioning profile**. Install the resulting **ad-hoc** `.ipa` via
Apple Configurator, Finder (drag it onto the device), or Xcode ▸ Devices &
Simulators — it runs only on the UDIDs baked into the profile.

### CI publishes a Release

Every manual **Run workflow** (unless you untick **Publish the built .ipa as a
GitHub Release**) attaches the built `.ipa` to a GitHub Release tagged
`v<version>-b<build>`:

- a **signed** build → a **full release** (one-click download, install directly);
- an **unsigned-only** build → a **pre-release** (re-sign to install).

So the newest `.ipa` is always one click away under the repo's **Releases**,
and it doesn't expire after 90 days the way the Actions artifact does.

### D — TestFlight / App Store

```bash
METHOD=app-store TEAM_ID=YOURTEAMID scripts/export_ipa.sh
xcrun altool --upload-app -t ios -f build-ios/ipa/export/FEXT.ipa \
  --apiKey <KEY_ID> --apiIssuer <ISSUER_ID>      # or drag into Transporter.app
```

See **App Store notes** below before any public submission.

## App Store notes (read before submitting publicly)

- **Cleartext transport (ATS).** The client is pinned to a relay reached over
  **cleartext HTTP/WebSocket at a bare IP** (`http://118.189.201.104:50607`).
  `ios/info_additions.plist` therefore sets `NSAllowsArbitraryLoads` (ATS can't
  scope an exception to an IP literal). This is fine for TestFlight / internal
  distribution, and the app's own traffic is already end-to-end ciphertext over
  Python sockets. **For public App Store review, stand the relay up on HTTPS/WSS
  behind a real domain, update `SERVER_URL` in `app/main.py`, and delete the
  `NSAppTransportSecurity` key.** Apple scrutinizes arbitrary-loads, and
  cleartext-to-an-IP is a likely rejection.
- **Export compliance.** The app uses non-exempt encryption. We deliberately do
  **not** set `ITSAppUsesNonExemptEncryption` — it is a legal declaration for
  the publisher to make. Open-source apps using standard cryptography often
  qualify for an exemption (BIS License Exception TSU), but confirm your
  classification. Answer the prompt in App Store Connect, or add the key once
  you have decided.
- **Icons & launch screen** are already wired by the build. **Bundle id,
  version and team** are yours to set.

## Testing

```bash
# fast: known-answer vectors + a quick differential + envelope interop
pip install cryptography
python3 tests/test_aead.py

# thorough differential run
FEXT_FUZZ=10000 python3 tests/test_aead.py
```

CI (`.github/workflows/ios.yml`) runs the compile + crypto proof on every push,
and a full unsigned macOS build on manual **workflow_dispatch**.

## Regenerating the app icon

```bash
pip install pillow
python3 scripts/make_assets.py     # rewrites ios/AppIcon.appiconset/*
```

## Desktop development

The same file runs on the desktop (with the fast native crypto path):

```bash
pip install -r requirements.txt
python3 app/main.py
```

## Known follow-ups (not blockers)

- **Safe-area / notch.** kivy-ios renders full-screen, so on notched devices
  the top app bar sits partly under the status bar. Reading the safe-area
  insets in the Kivy layout would polish this; it's a UI change beyond
  packaging and left untouched here.
- **Relay HTTPS** — see App Store notes above.

## License

See [LICENSE](LICENSE). The client is published in full so anyone can audit it.
