#!/usr/bin/env python3
"""Exercise capture, explicit promotion, integrity check, and retirement."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile


SCRIPT = Path(__file__).with_name("article_feedback.py")


def call(root: Path, *args: str, ok: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True, text=True,
    )
    assert (result.returncode == 0) == ok, result.stderr or result.stdout
    return result


with tempfile.TemporaryDirectory() as temp:
    root = Path(temp) / "calibration"
    article = Path(temp) / "user-final.md"
    before = Path(temp) / "draft.md"
    article.write_text("我试了两次，第二次才看懂它为什么卡住。\n", encoding="utf-8")
    before.write_text("这个工具具有重要意义。\n", encoding="utf-8")
    call(root, "snapshot", str(before), "--label", "测试文章")
    draft_meta = next((root / "drafts").glob("*/meta.json"))
    draft_id = json.loads(draft_meta.read_text(encoding="utf-8"))["id"]
    before.write_text("交付路径后来被覆盖。\n", encoding="utf-8")
    call(root, "capture", str(article), "--draft-id", draft_id, "--label", "测试文章")
    meta_file = next((root / "inbox").glob("*/meta.json"))
    sample_id = json.loads(meta_file.read_text(encoding="utf-8"))["id"]
    assert not (root / "approved" / sample_id).exists()
    call(root, "approve", sample_id, "--note", "这版可以作为参考")
    approved = root / "approved" / sample_id
    assert (approved / "article.md").read_text(encoding="utf-8") == article.read_text(encoding="utf-8")
    assert (approved / "before.md").read_text(encoding="utf-8") == "这个工具具有重要意义。\n"
    assert json.loads((approved / "meta.json").read_text(encoding="utf-8"))["draft_snapshot_id"] == draft_id
    assert "approved" in call(root, "list").stdout
    call(root, "approve", sample_id, ok=False)
    (approved / "article.md").write_text("被覆盖", encoding="utf-8")
    call(root, "retire", sample_id, ok=False)
    (approved / "article.md").write_text(article.read_text(encoding="utf-8"), encoding="utf-8")
    call(root, "retire", sample_id, "--note", "撤回")
    assert json.loads((approved / "meta.json").read_text(encoding="utf-8"))["status"] == "retired"

print("article feedback tests passed")
