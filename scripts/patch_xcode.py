#!/usr/bin/env python3
"""Inject FEXT's production identity into a freshly `toolchain create`-d
kivy-ios Xcode project: Info.plist keys, app icons, and the launch screen.

Kept idempotent and defensive — it locates the generated files by glob rather
than by hardcoded paths, so it survives small kivy-ios layout changes and can
be re-run after `toolchain update`.

    python3 scripts/patch_xcode.py --project build-ios/FEXT-ios \
        --assets ios --bundle-id com.you.fext --version 3.1.0 \
        --build-number 1 --display-name FEXT
"""
from __future__ import annotations

import argparse
import glob
import os
import plistlib
import re
import shutil
import sys


def log(msg: str) -> None:
    print(f"[patch_xcode] {msg}")


def warn(msg: str) -> None:
    print(f"[patch_xcode] WARNING: {msg}", file=sys.stderr)


def find_one(project: str, pattern: str) -> str | None:
    hits = glob.glob(os.path.join(project, "**", pattern), recursive=True)
    return sorted(hits, key=len)[0] if hits else None


# --- Info.plist ---------------------------------------------------------------
def patch_info_plist(project: str, assets: str, args) -> dict:
    plist_path = find_one(project, "*-Info.plist") or find_one(project,
                                                               "Info.plist")
    if not plist_path:
        warn("no Info.plist found; skipping plist patch.")
        return {}
    log(f"Info.plist: {os.path.relpath(plist_path, project)}")

    with open(plist_path, "rb") as fh:
        info = plistlib.load(fh)
    original = dict(info)

    additions_path = os.path.join(assets, "info_additions.plist")
    if os.path.isfile(additions_path):
        with open(additions_path, "rb") as fh:
            additions = plistlib.load(fh)
        _deep_merge(info, additions)
        log(f"merged {len(additions)} key(s) from info_additions.plist")
    else:
        warn(f"{additions_path} not found; only identity keys will be set.")

    # identity / versioning (always enforced from CLI)
    info["CFBundleIdentifier"] = args.bundle_id
    info["CFBundleShortVersionString"] = args.version
    info["CFBundleVersion"] = str(args.build_number)
    if args.display_name:
        info["CFBundleDisplayName"] = args.display_name
        info.setdefault("CFBundleName", args.display_name)

    with open(plist_path, "wb") as fh:
        plistlib.dump(info, fh)
    log(f"Info.plist updated (bundle={args.bundle_id}, "
        f"v{args.version}+{args.build_number}).")
    return original


def _deep_merge(dst: dict, src: dict) -> None:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = v


# --- app icons ----------------------------------------------------------------
def patch_icons(project: str, assets: str) -> None:
    src = os.path.join(assets, "AppIcon.appiconset")
    if not os.path.isdir(src):
        warn(f"{src} not found; skipping icons.")
        return
    dst = find_one(project, "AppIcon.appiconset")
    if not dst:
        # No asset catalog icon set — fall back to the legacy single icon.png.
        legacy = find_one(project, "icon.png")
        master = os.path.join(src, "icon-1024.png")
        if legacy and os.path.isfile(master):
            shutil.copyfile(master, legacy)
            log("no AppIcon.appiconset; replaced legacy icon.png instead.")
        else:
            warn("no AppIcon.appiconset and no icon.png; icons not installed.")
        return
    for name in os.listdir(dst):
        os.remove(os.path.join(dst, name))
    count = 0
    for name in os.listdir(src):
        shutil.copyfile(os.path.join(src, name), os.path.join(dst, name))
        count += 1
    log(f"installed {count} icon file(s) into "
        f"{os.path.relpath(dst, project)}")


# --- launch screen ------------------------------------------------------------
def patch_launch_screen(project: str, assets: str, original: dict) -> None:
    src = os.path.join(assets, "LaunchScreen.storyboard")
    if not os.path.isfile(src):
        warn(f"{src} not found; keeping the default launch screen.")
        return
    name = original.get("UILaunchStoryboardName")
    target = None
    if name:
        target = find_one(project, f"{name}.storyboard") or \
            find_one(project, f"{name}")
    if not target:
        target = find_one(project, "*.storyboard")
    if not target:
        warn("no existing launch storyboard to overwrite; leaving as-is so the "
             "Xcode project reference stays valid. Set the launch screen "
             "manually in Xcode if you want the FEXT branded one.")
        return
    shutil.copyfile(src, target)
    log(f"branded launch screen -> {os.path.relpath(target, project)}")


# --- project.pbxproj identity (best effort) -----------------------------------
def patch_pbxproj(project: str, args) -> None:
    pbx = find_one(project, "project.pbxproj")
    if not pbx:
        warn("project.pbxproj not found; relying on Info.plist values only.")
        return
    with open(pbx, "r", encoding="utf-8") as fh:
        text = fh.read()
    subs = {
        r"PRODUCT_BUNDLE_IDENTIFIER = [^;]+;":
            f"PRODUCT_BUNDLE_IDENTIFIER = {args.bundle_id};",
        r"MARKETING_VERSION = [^;]+;":
            f"MARKETING_VERSION = {args.version};",
        r"CURRENT_PROJECT_VERSION = [^;]+;":
            f"CURRENT_PROJECT_VERSION = {args.build_number};",
    }
    changed = 0
    for pat, repl in subs.items():
        text, n = re.subn(pat, repl, text)
        changed += n
    if changed:
        with open(pbx, "w", encoding="utf-8") as fh:
            fh.write(text)
        log(f"project.pbxproj: updated {changed} build-setting occurrence(s).")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="the *-ios project dir")
    ap.add_argument("--assets", default="ios", help="dir with plist/icons/etc")
    ap.add_argument("--bundle-id", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--build-number", default="1")
    ap.add_argument("--display-name", default="")
    args = ap.parse_args()

    if not os.path.isdir(args.project):
        warn(f"project dir {args.project} does not exist.")
        return 1
    log(f"patching {args.project}")
    original = patch_info_plist(args.project, args.assets, args)
    patch_icons(args.project, args.assets)
    patch_launch_screen(args.project, args.assets, original)
    patch_pbxproj(args.project, args)
    log("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
