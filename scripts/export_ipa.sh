#!/usr/bin/env bash
# =============================================================================
#  export_ipa.sh — turn the generated Xcode project into an installable .ipa
# -----------------------------------------------------------------------------
#  Runs AFTER scripts/build_ios.sh has generated build-ios/<Title>-ios/.
#  MUST run on macOS with Xcode. Produces one of:
#
#    METHOD=unsigned      an UNSIGNED .ipa (Payload/<App>.app zipped). Install
#                         it with AltStore or Sideloadly, which re-sign it with
#                         your (free) Apple ID. No paid account, no Mac needed
#                         if you let CI build it. 7-day validity on a free ID.
#    METHOD=development    signed for your registered devices (needs TEAM_ID +
#                         a development cert/profile in the keychain).
#    METHOD=ad-hoc         signed for the specific device UDIDs in an ad-hoc
#                         profile (paid Apple Developer account).
#    METHOD=app-store      signed for TestFlight / App Store upload.
#
#  Usage:
#    METHOD=unsigned scripts/export_ipa.sh
#    METHOD=ad-hoc TEAM_ID=ABCDE12345 scripts/export_ipa.sh
#    METHOD=ad-hoc TEAM_ID=ABCDE12345 PROFILE_NAME="FEXT AdHoc" \
#        scripts/export_ipa.sh          # manual signing (CI-friendly)
# =============================================================================
set -euo pipefail

METHOD="${METHOD:-unsigned}"
APP_TITLE="${APP_TITLE:-FEXT}"
TEAM_ID="${TEAM_ID:-}"
PROFILE_NAME="${PROFILE_NAME:-}"
BUNDLE_ID="${BUNDLE_ID:-com.example.fext}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$REPO_ROOT/build-ios}"
OUT="${OUT:-$BUILD_DIR/ipa}"

say() { printf '\033[1;33m[export_ipa]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[export_ipa] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(uname -s)" = "Darwin" ] || die "exporting an .ipa requires macOS + Xcode."
command -v xcodebuild >/dev/null 2>&1 || die "Xcode not found (xcodebuild)."

PROJ="$(find "$BUILD_DIR" -maxdepth 2 -name '*.xcodeproj' | head -1)"
[ -n "$PROJ" ] || die "no .xcodeproj under $BUILD_DIR — run scripts/build_ios.sh first."
SCHEME="$(xcodebuild -project "$PROJ" -list -json \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["project"]["schemes"][0])')"
mkdir -p "$OUT"
say "Project: $PROJ"
say "Scheme:  $SCHEME     Method: $METHOD"

# ---- unsigned: build the .app, zip it into an .ipa Payload -------------------
if [ "$METHOD" = "unsigned" ]; then
    DD="$BUILD_DIR/DerivedData"
    say "Building UNSIGNED .app…"
    xcodebuild -project "$PROJ" -scheme "$SCHEME" -configuration Release \
        -sdk iphoneos -derivedDataPath "$DD" \
        CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY="" \
        build
    APP="$(find "$DD" -maxdepth 4 -name '*.app' -type d | head -1)"
    [ -n "$APP" ] || die "no .app produced."
    STAGE="$(mktemp -d)"
    mkdir -p "$STAGE/Payload"
    cp -R "$APP" "$STAGE/Payload/"
    IPA="$OUT/${APP_TITLE}-unsigned.ipa"
    (cd "$STAGE" && zip -qry "$IPA" Payload)
    rm -rf "$STAGE"
    say "WROTE $IPA"
    say "Install it with AltStore or Sideloadly (they re-sign with your Apple ID)."
    exit 0
fi

# ---- signed: archive then export --------------------------------------------
[ -n "$TEAM_ID" ] || die "METHOD=$METHOD needs TEAM_ID=<your 10-char Apple Team ID>."
ARCHIVE="$BUILD_DIR/${APP_TITLE}.xcarchive"

say "Archiving (signed, team $TEAM_ID)…"
xcodebuild -project "$PROJ" -scheme "$SCHEME" -configuration Release \
    -sdk iphoneos -archivePath "$ARCHIVE" \
    DEVELOPMENT_TEAM="$TEAM_ID" \
    archive

# Build the ExportOptions plist for the chosen method (manual signing when a
# PROFILE_NAME is given, else automatic).
PLIST="$OUT/ExportOptions-${METHOD}.plist"
python3 - "$PLIST" "$METHOD" "$TEAM_ID" "$BUNDLE_ID" "$PROFILE_NAME" <<'PY'
import plistlib, sys
out, method, team, bundle, profile = sys.argv[1:6]
opts = {
    "method": method,
    "teamID": team,
    "compileBitcode": False,
    "stripSwiftSymbols": True,
    "destination": "export",
}
if method == "app-store":
    opts["uploadSymbols"] = True
if profile:
    opts["signingStyle"] = "manual"
    opts["provisioningProfiles"] = {bundle: profile}
else:
    opts["signingStyle"] = "automatic"
with open(out, "wb") as fh:
    plistlib.dump(opts, fh)
print(f"wrote {out} ({method}, {'manual' if profile else 'automatic'} signing)")
PY

say "Exporting .ipa…"
xcodebuild -exportArchive -archivePath "$ARCHIVE" \
    -exportOptionsPlist "$PLIST" -exportPath "$OUT/export"

IPA="$(find "$OUT/export" -maxdepth 1 -name '*.ipa' | head -1)"
[ -n "$IPA" ] || die "export produced no .ipa (check signing identity/profile)."
say "WROTE $IPA"
case "$METHOD" in
  development|ad-hoc)
    say "Install via Apple Configurator, Xcode ▸ Devices, or drag onto the device in Finder." ;;
  app-store)
    say "Upload with: xcrun altool --upload-app -f \"$IPA\" … (or Transporter)." ;;
esac
