#!/usr/bin/env python3
"""Guard the restored default writing behavior against route drift."""
from pathlib import Path
import subprocess

suite = Path(__file__).resolve().parents[1]
project = suite.parents[2]
writing = (project / ".agents/skills/zh-writing-humanizer").resolve()


def baseline(path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"v3.0.0-zh.3:{path}"], cwd=writing, text=True
    )


def section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


for path in (
    "references/routes/public-account-article.md",
    "references/profiles/public-account-voice.md",
):
    assert (writing / path).read_text() == baseline(path), path

old_skill = baseline("SKILL.md")
new_skill = (writing / "SKILL.md").read_text()
for start, end in (
    ("## Chinese AI-Tell Map", "## Mixed Chinese-English Handling"),
    ("## Mixed Chinese-English Handling", "## False Positives To Preserve"),
    ("## Process", "## Output"),
    ("## Quality Gate", "\0"),
):
    if end == "\0":
        assert old_skill.split(start, 1)[1] == new_skill.split(start, 1)[1], start
    else:
        assert section(old_skill, start, end) == section(new_skill, start, end), start

assert "only when the user asks for an explicit story map" in new_skill
suite_text = (suite / "SKILL.md").read_text()
contract = (suite / "references/pipeline-contract.md").read_text()
assert "默认公众号路线" in suite_text
assert "只有用户明确要求结构规划" in contract
print("writing baseline parity passed")
