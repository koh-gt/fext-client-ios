#!/usr/bin/env bash
# =============================================================================
#  build_ios.sh — reproducible kivy-ios build of the FEXT client
# -----------------------------------------------------------------------------
#  Produces an Xcode project (<title>-ios/) ready to open, sign and archive for
#  TestFlight / the App Store. MUST run on macOS with Xcode installed — iOS
#  binaries cannot be produced on Linux.
#
#  Usage:
#      scripts/build_ios.sh                 # build everything, first run
#      APP_TITLE=FEXT BUNDLE_ID=com.you.fext scripts/build_ios.sh
#      SKIP_TOOLCHAIN_BUILD=1 scripts/build_ios.sh   # re-create project only
#
#  Environment overrides (all optional):
#      APP_TITLE            display/base name         (default: FEXT)
#      BUNDLE_ID            CFBundleIdentifier         (default: com.example.fext)
#      PROJECT_VERSION      marketing version          (default: 7.0.0)
#      BUILD_NUMBER         CFBundleVersion            (default: 1)
#      BUILD_DIR            where to generate/build    (default: ./build-ios)
#      SKIP_TOOLCHAIN_BUILD =1 to skip the long recipe compile if already done
# =============================================================================
set -euo pipefail

APP_TITLE="${APP_TITLE:-FEXT}"
BUNDLE_ID="${BUNDLE_ID:-com.example.fext}"
PROJECT_VERSION="${PROJECT_VERSION:-7.0.0}"
BUILD_NUMBER="${BUILD_NUMBER:-1}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$REPO_ROOT/app"
BUILD_DIR="${BUILD_DIR:-$REPO_ROOT/build-ios}"
VENV="$BUILD_DIR/.venv-kivy-ios"

say() { printf '\033[1;33m[build_ios]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[build_ios] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# ---- 0. sanity ---------------------------------------------------------------
[ "$(uname -s)" = "Darwin" ] || die "iOS builds require macOS + Xcode."
command -v xcodebuild >/dev/null 2>&1 || die "Xcode not found (xcodebuild)."
command -v python3 >/dev/null 2>&1 || die "python3 not found."
[ -f "$APP_DIR/main.py" ] || die "missing $APP_DIR/main.py"

say "Xcode:   $(xcodebuild -version | head -1)"
say "Title:   $APP_TITLE     Bundle: $BUNDLE_ID     Version: $PROJECT_VERSION ($BUILD_NUMBER)"
mkdir -p "$BUILD_DIR"
# kivy-ios writes dist/ and build/ into the CWD, and `toolchain create` reads
# the frameworks from that same dist/. Run every toolchain step from BUILD_DIR
# so the build cache, the compiled frameworks and the generated project all
# live together (and can be cached as one directory in CI).
cd "$BUILD_DIR"

# ---- 1. host build deps (best effort via Homebrew) ---------------------------
if command -v brew >/dev/null 2>&1; then
    say "Ensuring host build tools (autoconf automake libtool pkg-config)…"
    brew list autoconf   >/dev/null 2>&1 || brew install autoconf
    brew list automake    >/dev/null 2>&1 || brew install automake
    brew list libtool     >/dev/null 2>&1 || brew install libtool
    brew list pkg-config  >/dev/null 2>&1 || brew install pkg-config
else
    say "Homebrew not found — assuming autoconf/automake/libtool/pkg-config are present."
fi

# ---- 2. isolated venv with kivy-ios -----------------------------------------
if [ ! -d "$VENV" ]; then
    say "Creating kivy-ios venv at $VENV"
    python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python3 -m pip install --quiet --upgrade pip wheel
say "Installing kivy-ios + Cython + cookiecutter…"
# Cython is a host requirement for kivy-ios's Cython recipes (Kivy 2.3.1).
# kivy-ios doesn't install it for you, so pin a version known to build Kivy.
python3 -m pip install --quiet "kivy-ios>=2024.10" cookiecutter "Cython==3.0.11"

# ---- 3. compile the recipes (LONG: 20–60 min the first time) -----------------
#   python3  -> CPython for iOS      kivy -> Kivy + SDL2 stack
#   pillow   -> PIL (QR rendering).  cryptography is deliberately NOT built.
if [ "${SKIP_TOOLCHAIN_BUILD:-0}" != "1" ]; then
    say "Building toolchain recipes: python3 kivy pillow  (this takes a while)…"
    toolchain build python3 kivy pillow
else
    say "SKIP_TOOLCHAIN_BUILD=1 — reusing previously built recipes."
fi

# ---- 4. pure-Python runtime deps into the iOS site-packages ------------------
say "Installing pure-Python deps into the iOS site-packages…"
toolchain pip install -r "$REPO_ROOT/requirements-ios.txt"

# ---- 5. generate the Xcode project ------------------------------------------
# (already in $BUILD_DIR, alongside dist/)
PROJECT_DIR="$BUILD_DIR/${APP_TITLE}-ios"
if [ -d "$PROJECT_DIR" ]; then
    say "Refreshing app sources in existing project (keeping build settings)…"
    toolchain update "${APP_TITLE}-ios" || true
    rsync -a --delete "$APP_DIR"/ "$PROJECT_DIR/YourApp/"
else
    say "Creating Xcode project ${APP_TITLE}-ios…"
    toolchain create "$APP_TITLE" "$APP_DIR"
fi

# kivy-ios lowercases/normalises the dir name in some versions — locate it.
if [ ! -d "$PROJECT_DIR" ]; then
    PROJECT_DIR="$(find "$BUILD_DIR" -maxdepth 1 -type d -name '*-ios' | head -1)"
fi
[ -d "$PROJECT_DIR" ] || die "could not locate the generated *-ios project dir."
say "Project generated at: $PROJECT_DIR"

# ---- 6. inject FEXT identity, Info.plist, icons and launch screen ------------
say "Patching Xcode project (Info.plist / icons / launch screen)…"
python3 "$REPO_ROOT/scripts/patch_xcode.py" \
    --project "$PROJECT_DIR" \
    --assets  "$REPO_ROOT/ios" \
    --bundle-id "$BUNDLE_ID" \
    --version "$PROJECT_VERSION" \
    --build-number "$BUILD_NUMBER" \
    --display-name "$APP_TITLE"

cat <<EOF

$(say "DONE.")
Next steps (signing needs your Apple Developer account, so it stays manual):

  1. open "$PROJECT_DIR/$(basename "$PROJECT_DIR" -ios).xcodeproj"
  2. In "Signing & Capabilities": pick your Team, confirm Bundle Identifier
     = $BUNDLE_ID.
  3. Product ▸ Archive, then distribute to TestFlight / the App Store.

  Command-line archive+export (once signing is set) is documented in README.md.
EOF
