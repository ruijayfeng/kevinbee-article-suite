#!/usr/bin/env python3
"""Export Xiaohongshu copy and record versioned delivery verification.

Visual review is an explicit reviewer attestation, never inferred from files.
All paths in the package are relative to the package, not the output directory.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import zlib

PENDING = re.compile(r"【待补|TODO|TBD|待补素材|图片URL", re.I)
VISUAL_CHECKS = ("text", "identity", "evidence", "phone_readability", "composition")


def block(text: str, heading: str) -> str:
    match = re.search(rf"^{re.escape(heading)}\s*$\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def fields(text: str) -> dict[str, str]:
    return {key: value.strip().strip("`") for key, value in
            re.findall(r"^-\s*([a-z_]+):[ \t]*(.*?)\s*$", text, re.M)}


def resolve(package: Path, raw: str) -> Path:
    if not raw or raw == "-":
        raise ValueError("missing file path")
    path = Path(raw)
    return (package.parent / path).resolve() if not path.is_absolute() else path.resolve()


def load(package: Path) -> dict:
    text = package.read_text(encoding="utf-8")
    if not re.search(r"^target_platform:\s*xiaohongshu\s*$", text, re.M):
        raise ValueError("expected target_platform: xiaohongshu")
    spec = fields(block(text, "## Xiaohongshu"))
    if spec.get("delivery_scope") not in {"plan", "cover", "series"}:
        raise ValueError("xiaohongshu delivery_scope must be plan, cover or series")
    count = int(spec.get("page_count", "0"))
    if count < 1 or (spec["delivery_scope"] == "cover" and count != 1):
        raise ValueError("page_count must be positive; cover requires exactly one page")
    if spec["delivery_scope"] == "series" and count < 2:
        raise ValueError("series requires at least two pages; use cover for one page")
    for key in ("output_dir", "outline", "caption"):
        if not spec.get(key) or spec[key] == "-":
            raise ValueError(f"xiaohongshu missing {key}")
    rows = []
    for line in block(text, "## XHS Pages").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if cells[0] == "order" or all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        if len(cells) != 4 or not cells[0].isdigit():
            raise ValueError("XHS Pages rows must contain order | role | image | prompt")
        order = int(cells[0])
        role = cells[1]
        if role not in {"cover", "content", "ending"}:
            raise ValueError(f"invalid page role: {role}")
        rows.append(dict(order=order, role=role, image=cells[2], prompt=cells[3]))
    if rows and [row["order"] for row in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("XHS Pages must be ordered consecutively without duplicates")
    if rows and (rows[0]["role"] != "cover" or any(row["role"] == "cover" for row in rows[1:])):
        raise ValueError("only the first page must be the cover")
    if len(rows) > count:
        raise ValueError("XHS Pages exceeds page_count")
    return {"fields": spec, "pages": rows, "count": count,
            "draft": fields(block(text, "## Draft")),
            "delivery": fields(block(text, "## Delivery"))}


def outline_pages(path: Path, count: int) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    headings = list(re.finditer(r"^## Image (\d+) of (\d+)\s*$", text, re.M))
    if len(headings) != count:
        raise ValueError("outline page count does not match page_count")
    pages = []
    for index, match in enumerate(headings):
        if (int(match[1]), int(match[2])) != (index + 1, count):
            raise ValueError("outline page headings must be consecutive and use the correct total")
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        page = text[match.end():end].strip()
        content = re.search(r"^\*\*Text Content\*\*:[ \t]*\n(.*?)(?=^\*\*[^\n]+\*\*:|^---\s*$|\Z)", page, re.M | re.S)
        if not content or not content[1].strip():
            raise ValueError(f"outline page {index + 1} missing Text Content")
        pages.append({"order": index + 1, "plan": page, "copy": content[1].strip()})
    return pages


def review_text(package: Path, spec: dict) -> str:
    pages = outline_pages(resolve(package, spec["fields"]["outline"]), spec["count"])
    caption = resolve(package, spec["fields"]["caption"]).read_text(encoding="utf-8").strip()
    if not caption:
        raise ValueError("caption is empty")
    parts = ["# 小红书审阅稿"]
    parts.extend(f"## 第 {page['order']} 页\n\n{page['copy']}" for page in pages)
    parts.append(f"## 发布标题、配文与话题\n\n{caption}")
    return "\n\n".join(parts) + "\n"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_state(package: Path, raw: str) -> dict:
    path = resolve(package, raw)
    if not path.is_file():
        raise ValueError(f"missing file: {raw}")
    data = path.read_bytes()
    if not data.strip():
        raise ValueError(f"empty file: {raw}")
    return {"path": raw, "sha256": digest(data)}


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as source:
        if source.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"not a PNG: {path.name}")
        size = None
        has_pixels = False
        while True:
            header = source.read(8)
            if len(header) != 8:
                raise ValueError(f"incomplete PNG: {path.name}")
            length, kind = struct.unpack(">I4s", header)
            if length > path.stat().st_size:
                raise ValueError(f"invalid PNG chunk: {path.name}")
            data = source.read(length)
            crc = source.read(4)
            if len(data) != length or len(crc) != 4 or struct.unpack(">I", crc)[0] != zlib.crc32(kind + data):
                raise ValueError(f"damaged PNG chunk: {path.name}")
            if size is None:
                if kind != b"IHDR" or length != 13:
                    raise ValueError(f"missing PNG header: {path.name}")
                size = struct.unpack(">II", data[:8])
            elif kind == b"IDAT":
                has_pixels = has_pixels or bool(data)
            elif kind == b"IEND":
                if length or not has_pixels:
                    raise ValueError(f"incomplete PNG: {path.name}")
                return size


def current_state(package: Path, spec: dict) -> dict:
    values = spec["fields"]
    if values["delivery_scope"] == "plan":
        raise ValueError("planning-only delivery cannot be publish-ready")
    if len(spec["pages"]) != spec["count"]:
        raise ValueError("XHS Pages count does not match page_count")
    if not resolve(package, values["output_dir"]).is_dir():
        raise ValueError("output_dir does not exist")
    files = {key: file_state(package, values.get(key, ""))
             for key in ("outline", "caption", "generation_record")}
    files["review_copy"] = file_state(package, spec["draft"].get("markdown", ""))
    for key in ("outline", "caption", "review_copy"):
        if PENDING.search(resolve(package, files[key]["path"]).read_text(encoding="utf-8")):
            raise ValueError(f"pending placeholders in {key}")
    generation = json.loads(resolve(package, values["generation_record"]).read_text(encoding="utf-8"))
    if not isinstance(generation, (dict, list)) or not generation:
        raise ValueError("generation_record must be nonempty JSON")
    if resolve(package, spec["draft"]["markdown"]).read_text(encoding="utf-8") != review_text(package, spec):
        raise ValueError("review copy is out of sync; update outline/caption and export review-copy")
    plans = outline_pages(resolve(package, values["outline"]), spec["count"])
    copy_checker = Path(__file__).resolve().parents[2] / "kaibing-xhs-images/scripts/check_publish_copy.py"
    if not copy_checker.is_file():
        raise ValueError("missing kaibing-xhs-images publish-copy checker; install the suite's fixed dependencies")
    copy_check = subprocess.run([sys.executable, str(copy_checker), str(resolve(package, values["outline"]))],
                                text=True, capture_output=True)
    if copy_check.returncode:
        raise ValueError(copy_check.stdout.strip() or copy_check.stderr.strip() or "publish copy check failed")
    pages = []
    for row, plan in zip(spec["pages"], plans):
        image = file_state(package, row["image"])
        prompt = file_state(package, row["prompt"])
        if png_size(resolve(package, row["image"])) != (1080, 1440):
            raise ValueError(f"page {row['order']} final PNG must be 1080x1440")
        if PENDING.search(resolve(package, row["prompt"]).read_text(encoding="utf-8")):
            raise ValueError(f"pending placeholders in page {row['order']} prompt")
        pages.append({"order": row["order"], "role": row["role"], "image": image,
                      "prompt": prompt, "plan_sha256": digest(plan["plan"].encode("utf-8"))})
    if len({resolve(package, row["image"]) for row in spec["pages"]}) != spec["count"]:
        raise ValueError("each page must have its own image file")
    if len({resolve(package, row["prompt"]) for row in spec["pages"]}) != spec["count"]:
        raise ValueError("each page must have its own prompt file")
    return {"delivery_scope": values["delivery_scope"], "page_count": spec["count"],
            "output_dir": values["output_dir"], "files": files, "pages": pages}


def validate(package: Path, ready: bool) -> list[str]:
    try:
        spec = load(package)
        if not ready:
            return []
        state = current_state(package, spec)
        report_path = resolve(package, spec["delivery"].get("verification", ""))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if not isinstance(report, dict) or report.get("version") != 1 or report.get("state") != state:
            raise ValueError("xiaohongshu verification is stale or invalid; recheck delivery")
        visual = report.get("visual_checks", {})
        if not isinstance(visual, dict) or any(visual.get(key) is not True for key in VISUAL_CHECKS):
            raise ValueError("xiaohongshu visual review is pending")
        return []
    except (ValueError, OSError, UnicodeError, struct.error, KeyError, TypeError) as exc:
        return [str(exc)]


def save_version(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") == text:
            return
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S%f")
        path.rename(path.with_name(f"{path.stem}-backup-{stamp}{path.suffix}"))
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    export = sub.add_parser("review-copy", help="export the text-only review view")
    export.add_argument("package", type=Path)
    verify = sub.add_parser("verify", help="record file checks; visual review stays pending by default")
    verify.add_argument("package", type=Path)
    verify.add_argument("--visual-reviewed", action="store_true",
                        help="attest that text, identity, evidence, phone readability and composition were actually reviewed")
    args = parser.parse_args()
    try:
        package = args.package.expanduser().resolve()
        spec = load(package)
        if args.action == "review-copy":
            path = resolve(package, spec["draft"].get("markdown", ""))
            sources = {resolve(package, spec["fields"][key]) for key in ("outline", "caption")}
            if path in sources:
                raise ValueError("review copy must be separate from outline and caption")
            save_version(path, review_text(package, spec))
        else:
            state = current_state(package, spec)
            path = resolve(package, spec["delivery"].get("verification", ""))
            tracked = {resolve(package, item["path"]) for item in state["files"].values()}
            tracked.update(resolve(package, row[key]["path"]) for row in state["pages"] for key in ("image", "prompt"))
            if path in tracked:
                raise ValueError("verification must be separate from delivery files")
            if path.exists():
                old = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(old, dict) or old.get("version") != 1 or not isinstance(old.get("state"), dict):
                    raise ValueError("existing verification is invalid; preserve it and restore a valid prior report")
                prior_rows = old["state"].get("pages")
                if not isinstance(prior_rows, list) or any(not isinstance(row, dict) or not isinstance(row.get("order"), int) for row in prior_rows):
                    raise ValueError("existing verification has invalid pages")
                old_pages = {row["order"]: row for row in prior_rows}
                for row in state["pages"]:
                    prior = old_pages.get(row["order"])
                    if prior and prior.get("plan_sha256") != row["plan_sha256"]:
                        if any(prior.get(key, {}).get("sha256") == row[key]["sha256"] for key in ("image", "prompt")):
                            raise ValueError(f"page {row['order']} changed; revise its prompt and regenerate its image before verification")
            report = {"version": 1, "state": state,
                      "visual_checks": {key: args.visual_reviewed for key in VISUAL_CHECKS}}
            save_version(path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(f"saved {path}")
        return 0
    except (ValueError, OSError, UnicodeError, struct.error, KeyError, TypeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
