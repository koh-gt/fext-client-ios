#!/usr/bin/env bash
# =============================================================================
#  publish_release.sh — attach the built .ipa(s) to a GitHub Release
# -----------------------------------------------------------------------------
#  Runs in CI after export_ipa.sh. Uses the `gh` CLI (preinstalled on GitHub
#  runners) with the workflow's GITHUB_TOKEN, so the job needs
#  `permissions: contents: write`.
#
#  It publishes whatever .ipa files export_ipa.sh produced:
#    * a SIGNED .ipa present  -> a full Release (directly installable).
#    * only the UNSIGNED .ipa -> a pre-release (must be re-signed to install).
#
#  Env:
#    APP_TITLE        base name            (default: FEXT)
#    PROJECT_VERSION  marketing version    (default: 3.1.0)
#    BUILD_NUMBER     build number         (default: 1)
#    SIGNED           "true" when a signed .ipa was produced (default: false)
#    BUILD_DIR        where the .ipa lives (default: ./build-ios)
#    GH_TOKEN         token for gh         (required — set to github.token)
#    GITHUB_SHA       commit to tag        (provided by Actions)
#    GITHUB_REPOSITORY owner/repo          (provided by Actions)
# =============================================================================
set -euo pipefail

APP_TITLE="${APP_TITLE:-FEXT}"
PROJECT_VERSION="${PROJECT_VERSION:-3.1.0}"
BUILD_NUMBER="${BUILD_NUMBER:-1}"
SIGNED="${SIGNED:-false}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$REPO_ROOT/build-ios}"

say() { printf '\033[1;33m[publish_release]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[publish_release] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

command -v gh >/dev/null 2>&1 || die "gh CLI not found (expected on GitHub runners)."

# Collect every .ipa export_ipa.sh wrote (unsigned in ipa/, signed in ipa/export/).
IPAS=()
while IFS= read -r -d '' f; do IPAS+=("$f"); done < <(
    find "$BUILD_DIR/ipa" -maxdepth 2 -name '*.ipa' -print0 2>/dev/null
)
[ "${#IPAS[@]}" -gt 0 ] || die "no .ipa found under $BUILD_DIR/ipa — run export_ipa.sh first."
say "Found ${#IPAS[@]} .ipa file(s): ${IPAS[*]}"

TAG="v${PROJECT_VERSION}-b${BUILD_NUMBER}"
TITLE="${APP_TITLE} ${PROJECT_VERSION} (build ${BUILD_NUMBER})"

if [ "$SIGNED" = "true" ]; then
    INSTALL='This release contains a **signed** `.ipa` — install it directly with
Apple Configurator, Finder (drag it onto the connected device), or
Xcode ▸ Devices & Simulators. An **ad-hoc** build installs only on devices whose
UDID is registered in the provisioning profile.'
    # Explicit so a later signed build promotes an earlier unsigned pre-release.
    PRERELEASE_ARG="--prerelease=false"
else
    INSTALL='This release contains an **unsigned** `.ipa`. iOS will not install it
directly — re-sign it with your Apple ID using [AltStore](https://altstore.io)
or [Sideloadly](https://sideloadly.io). A free Apple ID gives a 7-day install.'
    PRERELEASE_ARG="--prerelease=true"
fi

NOTES="**${TITLE}** — FEXT for iOS.

${INSTALL}

Built from \`${GITHUB_SHA:-HEAD}\` by the \`iOS\` workflow."

if gh release view "$TAG" >/dev/null 2>&1; then
    say "Release $TAG already exists — refreshing assets, notes and state."
    gh release upload "$TAG" "${IPAS[@]}" --clobber
    # shellcheck disable=SC2086  # PRERELEASE_ARG is a single --flag=value token.
    gh release edit "$TAG" --title "$TITLE" --notes "$NOTES" $PRERELEASE_ARG
else
    say "Creating release $TAG…"
    # shellcheck disable=SC2086  # PRERELEASE_ARG is a single --flag=value token.
    gh release create "$TAG" "${IPAS[@]}" \
        --title "$TITLE" --notes "$NOTES" \
        --target "${GITHUB_SHA:-HEAD}" $PRERELEASE_ARG
fi

say "DONE — https://github.com/${GITHUB_REPOSITORY:-<owner>/<repo>}/releases/tag/$TAG"
