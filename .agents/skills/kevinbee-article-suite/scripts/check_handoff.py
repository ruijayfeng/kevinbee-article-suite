#!/usr/bin/env python3
"""Validate deterministic parts of an article-package Markdown file."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

REQUIRED = [
    "## Status", "## Reader Question", "## Sources",
    "## Draft", "## Delivery",
]
PLACEHOLDERS = re.compile(r"【待补|TODO|TBD|待补素材|图片URL", re.I)
BACKTICK_PATH = re.compile(r"`([^`]+)`")
PATH_FIELD = re.compile(r"(?:^|[ \t])(?:markdown|story_map|html|preview|verification):[ \t]*([^\s]+)", re.M)
WEB = re.compile(r"https?://", re.I)


def section(text: str, heading: str) -> str:
    match = re.search(
        rf"^{re.escape(heading)}\s*$\n(.*?)(?=^##\s|\Z)",
        text,
        re.M | re.S,
    )
    return match.group(1) if match else ""


def field(block: str, name: str) -> str:
    match = re.search(rf"^-\s*{re.escape(name)}:\s*(.*?)\s*$", block, re.M)
    return match.group(1).strip() if match else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("package")
    ap.add_argument("--publish-ready", action="store_true")
    args = ap.parse_args()
    package = Path(args.package).expanduser().resolve()
    if not package.is_file():
        print(f"ERROR missing package: {package}")
        return 1
    text = package.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []
    for heading in REQUIRED:
        if heading not in text:
            errors.append(f"missing heading: {heading}")
    stage = re.search(r"^stage:\s*([^\s]+)", text, re.M)
    platform = re.search(r"^target_platform:\s*([^\s]+)", text, re.M)
    if not stage:
        errors.append("missing stage")
    if not platform:
        errors.append("missing target_platform")
    raw_paths = BACKTICK_PATH.findall(text)
    raw_paths.extend(PATH_FIELD.findall(text))
    for raw in raw_paths:
        raw = raw.strip().strip("`")
        if not raw or WEB.match(raw) or raw in {"working", "final"}:
            continue
        candidate = (package.parent / raw).resolve() if not Path(raw).is_absolute() else Path(raw)
        if not candidate.exists():
            warnings.append(f"referenced path not found: {raw}")
    pending = sorted(set(PLACEHOLDERS.findall(text)))
    if pending:
        message = "pending placeholders: " + ", ".join(pending)
        (errors if args.publish_ready else warnings).append(message)
    if args.publish_ready:
        if not stage or stage.group(1) != "publish-ready":
            errors.append("stage must be publish-ready")
        if "revision_status: final" not in text:
            errors.append("revision_status must be final")
        if platform and platform.group(1) == "wechat":
            for delivery_field in ("html:", "preview:", "verification:"):
                if delivery_field not in text:
                    errors.append(f"wechat delivery missing {delivery_field[:-1]}")
        cover = section(text, "## Cover")
        if field(cover, "requested") == "yes":
            if not field(cover, "image"):
                errors.append("requested cover missing image")
            if not field(cover, "promise"):
                errors.append("requested cover missing promise")
            if field(cover, "crop_verified") != "yes":
                errors.append("requested cover crop_verified must be yes")
        share = section(text, "## Share Copy")
        if field(share, "requested") == "yes":
            if not field(share, "copy"):
                errors.append("requested share copy missing copy")
            if not field(share, "traceable_to"):
                errors.append("requested share copy missing traceable_to")
    for item in warnings:
        print("WARN", item)
    for item in errors:
        print("ERROR", item)
    print(f"checked {package}: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
