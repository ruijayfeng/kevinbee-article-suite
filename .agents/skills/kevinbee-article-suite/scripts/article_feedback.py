#!/usr/bin/env python3
"""Snapshot and promote user article revisions for later writing calibration."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys


DEFAULT_ROOT = Path(__file__).resolve().parents[4] / "calibration"


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_article(path: str) -> tuple[Path, bytes]:
    source = Path(path).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() not in {".md", ".txt"}:
        raise ValueError(f"expected an existing .md or .txt article: {source}")
    data = source.read_bytes()
    if not data.strip():
        raise ValueError(f"empty article: {source}")
    data.decode("utf-8")
    return source, data


def write_meta(folder: Path, meta: dict) -> None:
    (folder / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def snapshot(args: argparse.Namespace) -> None:
    source, article = read_article(args.article)
    draft_id = f"{stamp()}-{digest(article)[:10]}"
    folder = args.root / "drafts" / draft_id
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "before.md").write_bytes(article)
    write_meta(folder, {
        "id": draft_id,
        "label": args.label or source.stem,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "before_sha256": digest(article),
        "source_name": source.name,
    })
    print(f"draft snapshot {draft_id} in {folder}")


def saved_draft(root: Path, draft_id: str) -> bytes:
    if Path(draft_id).name != draft_id:
        raise ValueError("provide a draft ID, not a path")
    folder = root / "drafts" / draft_id
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    data = (folder / "before.md").read_bytes()
    if digest(data) != meta["before_sha256"]:
        raise ValueError(f"draft changed since snapshot: {folder}")
    return data


def capture(args: argparse.Namespace) -> None:
    source, article = read_article(args.article)
    if args.draft_id:
        before_data = saved_draft(args.root, args.draft_id)
    else:
        before_data = read_article(args.before)[1] if args.before else None
    sample_id = f"{stamp()}-{digest(article)[:10]}"
    folder = args.root / "inbox" / sample_id
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "article.md").write_bytes(article)
    if before_data:
        (folder / "before.md").write_bytes(before_data)
    write_meta(folder, {
        "id": sample_id,
        "label": args.label or source.stem,
        "status": "candidate",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "article_sha256": digest(article),
        "before_sha256": digest(before_data) if before_data else None,
        "draft_snapshot_id": args.draft_id or None,
        "source_name": source.name,
        "user_note": args.note or "",
        "supersedes": args.supersedes or None,
    })
    print(f"captured {sample_id} in {folder}")


def find(args: argparse.Namespace) -> tuple[Path, dict]:
    if not args.sample_id or Path(args.sample_id).name != args.sample_id:
        raise ValueError("provide a sample ID, not a path")
    for state in ("inbox", "approved"):
        folder = args.root / state / args.sample_id
        if folder.is_dir():
            meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
            if digest((folder / "article.md").read_bytes()) != meta["article_sha256"]:
                raise ValueError(f"article changed since capture: {folder}")
            if meta.get("before_sha256") and digest((folder / "before.md").read_bytes()) != meta["before_sha256"]:
                raise ValueError(f"before article changed since capture: {folder}")
            return folder, meta
    raise ValueError(f"sample not found: {args.sample_id}")


def approve(args: argparse.Namespace) -> None:
    folder, meta = find(args)
    if folder.parent.name != "inbox" or meta["status"] != "candidate":
        raise ValueError("only a candidate can be approved")
    target = args.root / "approved" / args.sample_id
    if target.exists():
        raise ValueError(f"target already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(folder), str(target))
    meta["status"] = "approved"
    meta["approved_at"] = datetime.now(timezone.utc).isoformat()
    meta["approval_note"] = args.note or ""
    write_meta(target, meta)
    (target / "review.md").write_text(
        f"# {meta['label']} — 回流复盘\n\n"
        f"- 用户认可说明：{args.note or '用户明确认可；未提供具体理由'}\n"
        "- 适用题材与任务：待复盘\n"
        "- 用户明确偏好：待复盘\n"
        "- 前后可定位差异：待复盘；若无前稿则注明\n"
        "- 不可迁移的经历与事实：待复盘\n"
        "- 待验证假设：待复盘\n",
        encoding="utf-8",
    )
    print(f"approved {args.sample_id} in {target}; complete review.md before reuse")


def retire(args: argparse.Namespace) -> None:
    folder, meta = find(args)
    if folder.parent.name != "approved" or meta["status"] != "approved":
        raise ValueError("only an approved sample can be retired")
    meta["status"] = "retired"
    meta["retired_at"] = datetime.now(timezone.utc).isoformat()
    meta["retirement_note"] = args.note or ""
    write_meta(folder, meta)
    print(f"retired {args.sample_id}; snapshot retained")


def list_samples(args: argparse.Namespace) -> None:
    for state in ("inbox", "approved"):
        for folder in sorted((args.root / state).glob("*/meta.json")):
            meta = json.loads(folder.read_text(encoding="utf-8"))
            print(f"{meta['id']}\t{meta['status']}\t{meta['label']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("snapshot")
    p.add_argument("article")
    p.add_argument("--label")
    p = sub.add_parser("capture")
    p.add_argument("article")
    before = p.add_mutually_exclusive_group()
    before.add_argument("--before")
    before.add_argument("--draft-id")
    p.add_argument("--label")
    p.add_argument("--note")
    p.add_argument("--supersedes")
    p = sub.add_parser("approve")
    p.add_argument("sample_id")
    p.add_argument("--note")
    p = sub.add_parser("retire")
    p.add_argument("sample_id")
    p.add_argument("--note")
    sub.add_parser("list")
    args = parser.parse_args()
    args.root = args.root.expanduser().resolve()
    try:
        {"snapshot": snapshot, "capture": capture, "approve": approve, "retire": retire, "list": list_samples}[args.action](args)
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
