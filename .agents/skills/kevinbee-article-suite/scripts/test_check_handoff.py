#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import tempfile

CHECK = Path(__file__).with_name("check_handoff.py")
BASE = """# Article Package
## Status
stage: {stage}
target_platform: zhihu
theme: 凯冰·明亮编辑
## Reader Question
读者问题
## Author Context
作者背景
## Sources
- [source](https://example.com)
## Original Materials
- `notes.md` — 原始笔记
## Draft
- markdown: `article.md`
- revision_status: {revision}
## Delivery
- verification: `verify.md`
"""

def run(path: Path, ready: bool = False) -> int:
    cmd = [sys.executable, str(CHECK), str(path)]
    if ready:
        cmd.append("--publish-ready")
    return subprocess.run(cmd, capture_output=True, text=True).returncode

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    for name in ("article.md", "verify.md", "notes.md"):
        (root / name).write_text("fixture", encoding="utf-8")
    package = root / "article-package.md"
    package.write_text(BASE.format(stage="drafting", revision="working"), encoding="utf-8")
    assert run(package) == 0
    assert run(package, True) == 1
    package.write_text(BASE.format(stage="publish-ready", revision="final"), encoding="utf-8")
    assert run(package, True) == 0
    package.write_text(package.read_text(encoding="utf-8") + "\n## Cover\n- requested: yes\n", encoding="utf-8")
    assert run(package, True) == 1
    package.write_text(BASE.format(stage="publish-ready", revision="final"), encoding="utf-8")
    package.write_text(package.read_text(encoding="utf-8") + "\n【待补素材】\n", encoding="utf-8")
    assert run(package, True) == 1
print("check_handoff tests passed")
