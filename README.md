<p align="center">
  <img src="ios/icon-preview-1024.png" alt="FEXT" width="160" height="160">
</p>

<h1 align="center">FEXT for iOS</h1>

<p align="center">
  A production iOS package of the FEXT end-to-end-encrypted messenger —
  the single-file Kivy client, built for the iPhone with <a
  href="https://github.com/kivy/kivy-ios">kivy-ios</a>.
</p>

<p align="center">
  <b><a href="#-install-on-your-iphone-in-10-minutes">📲 Install on your iPhone in 10 minutes →</a></b>
</p>

---

FEXT is an open-source, end-to-end-encrypted messenger. Every message is signed
and sealed **on the device** before it leaves; the relay only ever handles
opaque ciphertext and a public `username → address` directory. This repository
packages the client — one auditable file, [`app/main.py`](app/main.py) — into a
shippable iOS app.

> **This is the v7 client.** It talks to the relay over **HTTPS/WSS**, draws
> its message ticks as vector strokes, follows the conversation smoothly with a
> jump-to-bottom pill, recovers cleanly when the relay doesn't recognise you,
> and lets you remove an identity from the device. The cryptography is
> byte-identical to v6, so v6 and v7 users interoperate.

---

# 📲 Install on your iPhone in 10 minutes

**No Mac, no jailbreak, no App Store, no paid Apple Developer account.** You
sideload the app: download the ready-made `.ipa` from this repo's Releases, then
use a free tool to sign it with your own Apple ID and install it. Here's the
whole thing, start to finish, for someone who has never done this before.

### What you need

| | |
|---|---|
| An iPhone | iOS 15 or newer |
| An Apple ID | A **free** one is fine (any normal Apple account) |
| A computer, **once** | Windows or Mac, to set up the sideloading app |
| ~10 minutes | Most of it is a one-time setup you never repeat |

> **Why a computer if this is "on-device"?** Apple requires the very first
> install of a sideloading app to be authorised from a trusted computer. After
> that, the app lives on your phone and re-signs FEXT for you. A **free** Apple
> ID keeps apps working for **7 days** at a time (they refresh automatically);
> a paid Developer account lasts a year.

---

### Step 1 — Download the FEXT `.ipa`

Open this on the device (or your computer) and grab the app file:

> ### ⬇︎ **[Download the latest FEXT `.ipa` from Releases](https://github.com/koh-gt/fext-client-ios/releases/latest)**

On the Releases page, under **Assets**, tap **`FEXT-unsigned.ipa`**. It's
"unsigned" on purpose — the sideloading app in Step 2 signs it with *your* Apple
ID during install. That's what makes it free and tied to your account only.

*(No `.ipa` on the Releases page yet? See [Building the `.ipa`
yourself](#getting-the-ipa-yourself-building) — a maintainer runs one CI button
and the Release appears.)*

---

### Step 2 — Get a sideloading app (pick one)

You only do this once. Any of these three works — **AltStore is the most
beginner-friendly**, so start there unless you have a reason not to.

<table>
<tr>
<th>Tool</th><th>Best for</th><th>How it works</th>
</tr>
<tr>
<td><b><a href="https://altstore.io">AltStore</a></b><br>(recommended)</td>
<td>Beginners who own a computer they can leave on Wi-Fi at home.</td>
<td>Install <b>AltServer</b> on your computer, plug the iPhone in once, and it
puts an <b>AltStore</b> app on your phone. AltStore then re-signs your apps
automatically whenever the phone and computer are on the same Wi-Fi.</td>
</tr>
<tr>
<td><b><a href="https://sidestore.io">SideStore</a></b></td>
<td>People who want to refresh apps <b>without</b> a computer afterward.</td>
<td>A fork of AltStore. The one-time setup (a "pairing file") is a little more
involved, but after that it renews apps entirely on the phone.</td>
</tr>
<tr>
<td><b><a href="https://sideloadly.io">Sideloadly</a></b></td>
<td>A single quick install, cable in hand, no app-store-style UI.</td>
<td>A desktop app. Drag the <code>.ipa</code> in, type your Apple ID, click
<b>Start</b>. Simplest for a one-off; you re-run it to refresh.</td>
</tr>
</table>

Follow the official install page for whichever you picked (linked above) until
you can see **AltStore / SideStore on your iPhone's Home Screen** — or, for
Sideloadly, until the app is open on your computer with your iPhone plugged in.
That's the end of the one-time part.

> **Apple ID tip:** signing in asks for your Apple ID password. If you use
> two-factor authentication (most people do), generate an **app-specific
> password** at [account.apple.com](https://account.apple.com) → *Sign-In &
> Security* → *App-Specific Passwords*, and use that instead. Your credentials
> go to **Apple**, not to FEXT or these tools' authors.

---

### Step 3 — Install FEXT

**Using AltStore or SideStore (on the iPhone):**

1. Open **AltStore / SideStore** → **My Apps** tab.
2. Tap the **`+`** in the top-left corner.
3. Pick **`FEXT-unsigned.ipa`** (it's in *Downloads* if you saved it in Step 1).
4. Enter your Apple ID if asked, and wait for the progress bar. FEXT appears on
   your Home Screen. 🎉

**Using Sideloadly (on the computer):**

1. Plug in the iPhone, open **Sideloadly**.
2. Drag **`FEXT-unsigned.ipa`** onto the window, enter your Apple ID, click
   **Start**. FEXT installs to the phone.

---

### Step 4 — First launch (two quick iOS settings)

The very first time you tap the FEXT icon, iOS blocks it until you approve the
certificate — this is normal for every sideloaded app:

1. **Trust the certificate.** *Settings → General → VPN & Device Management →*
   tap your Apple ID under *Developer App →* **Trust**.
2. **Enable Developer Mode** *(iOS 16 and newer only).* *Settings → Privacy &
   Security → Developer Mode →* turn **on**, then let the phone restart.

Now open FEXT, pick a username, and you're messaging. It connects to the relay
over HTTPS automatically — nothing to configure.

---

### Keeping it installed

A free Apple ID signs apps for **7 days**. You don't reinstall — you *refresh*:

- **AltStore / SideStore:** refreshes on its own. Keep AltServer running on your
  computer on the same Wi-Fi (AltStore), or just open SideStore now and then. If
  a badge says an app is expiring, open the app and tap **Refresh**.
- **Sideloadly:** re-run the same drag-and-drop before the 7 days are up.
- **A paid Apple Developer account** stretches this to a full year.

> Refreshing re-signs the **same** install — your identities, messages and
> settings stay put. You only lose them if you *delete* the app.

---

### Troubleshooting

| Symptom | Fix |
|---|---|
| "Unable to Install" / "Maximum number of apps" | A free Apple ID allows **3** sideloaded apps at once. Remove one, or use a paid account. |
| FEXT icon is greyed out or "Untrusted Developer" | You skipped **Step 4.1** — trust the certificate in *VPN & Device Management*. |
| App opens then closes instantly (iOS 16+) | You skipped **Step 4.2** — enable **Developer Mode** and restart. |
| App "expired" after a week | Refresh it (see above). Normal on a free Apple ID. |
| Status bar says *Offline — retrying…* | Tap the status ribbon to reconnect now; check the phone has internet. The relay is HTTPS and reached automatically. |

---

## What FEXT is (and why it's one file)

Identities are Bitcoin-compatible secp256k1 keys whose addresses carry a `Fec`
proof-of-work prefix. The whole client is one auditable file —
[`app/main.py`](app/main.py) — so the single promise the system rests on can be
verified line by line:

> **No plaintext ever leaves the process.**

This repository turns that client into a shippable iOS app: the entry point,
the build pipeline, the app icons and launch screen, the `Info.plist`
configuration, a proof suite for the crypto, and CI.

## Repository layout

| Path | What it is |
|------|------------|
| `app/main.py` | The complete FEXT **v7** client — the kivy-ios app entry point. |
| `tests/test_aead.py` | Proof the pure-Python AES-GCM/HKDF matches `cryptography` + NIST/RFC vectors, and that envelopes round-trip through the real `CryptoEngine`. |
| `scripts/build_ios.sh` | One-command, reproducible kivy-ios build → Xcode project. |
| `scripts/export_ipa.sh` | Turns the built project into an installable `.ipa` (unsigned for sideloading, or signed). |
| `scripts/publish_release.sh` | Attaches the built `.ipa`(s) to a GitHub Release (runs in CI). |
| `scripts/patch_xcode.py` | Injects `Info.plist` keys, icons and the launch screen into the generated project. |
| `scripts/make_assets.py` | Regenerates the app-icon set from the brand palette. |
| `ios/AppIcon.appiconset/` | The generated, App-Store-safe icon set (opaque, no alpha). |
| `ios/LaunchScreen.storyboard` | Branded launch screen. |
| `ios/info_additions.plist` | ATS, orientation and status-bar keys merged at build time. |
| `requirements.txt` / `requirements-ios.txt` | Desktop dev deps / the pure-Python deps kivy-ios installs. |
| `.github/workflows/ios.yml` | CI: fast crypto proof on every push; full macOS build + Release on demand. |

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
**unchanged** — desktop, Android and iOS all interoperate, and v6 talks to v7.
Re-run the proof:

```bash
pip install cryptography           # the reference to diff against
FEXT_FUZZ=10000 python3 tests/test_aead.py
```

(The vectors run even without `cryptography` installed — the differential part
simply skips, which is exactly the situation on the phone.)

### v7 transport note

v7 moved the relay to **HTTPS/WSS**. `requests` verifies TLS against the
`certifi` bundle shipped inside the app; `websocket-client` is now pinned to the
**same** bundle (`_ws_ssl_options()` in `app/main.py`). Without that pin the
WebSocket verifies against the OS trust store, which frequently does not resolve
on a python-for-android/kivy-ios build — HTTPS would succeed while realtime push
silently degraded to slow HTTP polling. `certifi` is therefore a required
dependency (see `requirements-ios.txt`). Verification is never disabled.

## Getting the `.ipa` yourself (building)

Most people should just [download it from Releases](#step-1--download-the-fext-ipa).
This section is for maintainers and contributors who want to build it.

> A `.ipa` can only be built on **macOS**, and iOS will not install an *unsigned*
> app — "directly on an iPhone" always means *something* signs it (Xcode,
> AltStore/SideStore/Sideloadly, or your developer certificate). No `.ipa` can be
> produced on Linux. Pick the path that matches what you have:

### CI (no Mac needed) → a downloadable Release

1. **Actions → iOS → Run workflow.** The `ios-build` job runs on a macOS runner
   and, with **Publish the built .ipa as a GitHub Release** left ticked,
   publishes **`FEXT-unsigned.ipa`** to a Release (tagged `vX.Y.Z-bN`) and as a
   run artifact.
2. Everyone else just downloads it from
   [Releases](https://github.com/koh-gt/fext-client-ios/releases) and follows the
   [10-minute install](#-install-on-your-iphone-in-10-minutes) above.
3. Configure the optional signing secrets/vars (below) and the same job also
   emits a **signed** `.ipa` and promotes the Release from pre-release to full.

### On a Mac (easiest for a developer)

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

The first `build_ios.sh` run compiles CPython, Kivy, the SDL2 stack and Pillow
for iOS and takes **20–60 minutes**. Subsequent runs reuse the compiled
frameworks; pass `SKIP_TOOLCHAIN_BUILD=1` to skip the recipe step. What the
script does:

1. builds the kivy-ios recipes: `python3 kivy pillow` (note: **not**
   `cryptography`);
2. installs the pure-Python deps from `requirements-ios.txt`
   (`requests`, `qrcode`, `websocket-client`, `certifi`);
3. runs `toolchain create` to generate `build-ios/FEXT-ios/`;
4. runs `scripts/patch_xcode.py` to set the bundle id / version and install the
   FEXT `Info.plist` keys, icons and launch screen.

### Signed `.ipa` from CI (paid Apple Developer account)

Add these and the `ios-build` job also emits a **signed** `.ipa`:

- **Secrets:** `APPLE_CERT_P12_BASE64` (`base64 -i cert.p12`),
  `APPLE_CERT_PASSWORD`, `APPLE_PROVISIONING_PROFILE_BASE64`
  (`base64 -i profile.mobileprovision`)
- **Variables:** `APPLE_TEAM_ID`, `APPLE_PROFILE_NAME`,
  `IPA_METHOD` (`ad-hoc` for direct device install, `app-store` for TestFlight)

Install an **ad-hoc** `.ipa` via Apple Configurator, Finder (drag it onto the
device), or Xcode ▸ Devices & Simulators. Ad-hoc requires the device's **UDID**
to be in the provisioning profile.

### TestFlight / App Store

```bash
METHOD=app-store TEAM_ID=YOURTEAMID scripts/export_ipa.sh
xcrun altool --upload-app -t ios -f build-ios/ipa/export/FEXT.ipa \
  --apiKey <KEY_ID> --apiIssuer <ISSUER_ID>      # or drag into Transporter.app
```

See **App Store notes** below before any public submission.

## Prerequisites (build machine)

iOS binaries can only be produced on **macOS**. You need:

- macOS with **Xcode** + Command Line Tools (`xcode-select --install`)
- **Homebrew** (`build_ios.sh` uses it for `autoconf automake libtool pkg-config`)
- Python 3.9+
- An **Apple Developer account** for signing (only needed to run on a device or
  submit — the build itself does not need it)

## App Store notes (read before submitting publicly)

- **Transport (ATS).** As of v7 the client reaches the relay over **HTTPS/WSS**,
  but still at a **bare IP** (`https://118.189.201.104:50607`), not a domain.
  ATS can't scope an exception to an IP literal, so `ios/info_additions.plist`
  still sets `NSAllowsArbitraryLoads`. It's harmless for sideloading — FEXT's
  networking is Python sockets (`requests` + `websocket-client`, both verifying
  against `certifi`), which bypass ATS entirely, and every byte is already TLS
  over E2E ciphertext. **For public App Store review, stand the relay up behind
  a real domain, update `SERVER_URL` in `app/main.py`, and delete the
  `NSAppTransportSecurity` key** — Apple scrutinizes arbitrary-loads.
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
and a full macOS build (+ Release) on manual **workflow_dispatch**.

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
- **Relay on a domain.** The relay is HTTPS but pinned to a bare IP. A real
  domain would let ATS be tightened for App Store review and decouple installs
  from a single host IP. See App Store notes above.

## License

See [LICENSE](LICENSE). The client is published in full so anyone can audit it.
