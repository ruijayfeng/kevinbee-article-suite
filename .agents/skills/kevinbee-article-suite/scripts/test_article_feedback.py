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

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp) / "calibration"
    before = Path(temp) / "xhs-draft.md"
    after = Path(temp) / "xhs-final.md"
    before.write_text("第 1 页：原始文案。\n", encoding="utf-8")
    after.write_text("第 1 页：作者修改的文案。\n", encoding="utf-8")
    call(root, "snapshot", str(before), "--platform", "xiaohongshu")
    draft_path = next((root / "drafts").glob("*/meta.json"))
    draft = json.loads(draft_path.read_text())
    assert draft["platform"] == "xiaohongshu"
    call(root, "capture", str(after), "--draft-id", draft["id"], "--platform", "wechat", ok=False)
    call(root, "capture", str(after), "--draft-id", draft["id"])
    meta_path = next((root / "inbox").glob("*/meta.json"))
    meta = json.loads(meta_path.read_text())
    assert meta["platform"] == "xiaohongshu"
    call(root, "approve", meta["id"], "--note", "认可文案；视觉另行确认")
    assert json.loads((root / "approved" / meta["id"] / "meta.json").read_text())["platform"] == "xiaohongshu"
    assert meta["id"] in call(root, "list", "--platform", "xiaohongshu").stdout
    assert meta["id"] not in call(root, "list", "--platform", "wechat").stdout

    # Old snapshots and samples have no platform; listing must not migrate them.
    del draft["platform"]
    draft_path.write_text(json.dumps(draft), encoding="utf-8")
    call(root, "capture", str(after), "--draft-id", draft["id"])
    legacy_path = next((root / "inbox").glob("*/meta.json"))
    legacy = json.loads(legacy_path.read_text())
    assert legacy["platform"] == "unspecified"
    del legacy["platform"]
    legacy_path.write_text(json.dumps(legacy), encoding="utf-8")
    saved = legacy_path.read_bytes()
    assert legacy["id"] not in call(root, "list", "--platform", "xiaohongshu").stdout
    assert legacy["id"] in call(root, "list", "--platform", "unspecified").stdout
    assert legacy_path.read_bytes() == saved
    call(root, "approve", legacy["id"])
    call(root, "retire", legacy["id"])
    assert "platform" not in json.loads((root / "approved" / legacy["id"] / "meta.json").read_text())
    call(root, "capture", str(after), "--platform", "xiaohongshu")
    direct = next((root / "inbox").glob("*/meta.json"))
    assert json.loads(direct.read_text())["platform"] == "xiaohongshu"

print("platform inheritance and legacy compatibility tests passed")
