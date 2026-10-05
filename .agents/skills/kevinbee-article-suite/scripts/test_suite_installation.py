#!/usr/bin/env python3
"""Check fixed dependency entries, licensed XHS assets and local references."""
from pathlib import Path
import configparser
import hashlib
import json
import re
import subprocess

suite = Path(__file__).resolve().parents[4]
entries = suite / ".agents/skills"
names = ("kevinbee-article-suite", "zh-writing-humanizer", "zhihu-ai-editorial",
         "kevinbee-illustrations", "gzh-design-skill", "kaibing-xhs-images")
for name in names:
    skill = entries / name / "SKILL.md"
    assert skill.is_file(), f"missing entry: {name}"
    for raw in re.findall(r"\]\(([^)]+\.md)\)", skill.read_text(encoding="utf-8")):
        if not raw.startswith(("http:", "https:")) and "<" not in raw:
            assert (skill.parent / raw).is_file(), f"missing reference: {name}/{raw}"

config = configparser.ConfigParser()
config.read(suite / ".gitmodules")
assert len(config.sections()) == 5, "expected five fixed upstream dependencies"
section = config['submodule ".deps/kaibing-xhs-images"']
assert section["url"] == "https://github.com/ruijayfeng/kaibing-xhs-images.git"
dependency = suite / section["path"]
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=dependency, text=True).strip()
index = subprocess.check_output(["git", "ls-files", "--stage", section["path"]], cwd=suite, text=True).split()
assert index[:2] == ["160000", head], "XHS dependency differs from the locked gitlink"
for name in ("LICENSE", "NOTICE.md"):
    assert (dependency / name).is_file()
assert (dependency / "LICENSES").is_dir()
xhs = entries / "kaibing-xhs-images"
assert (xhs / "scripts/check_publish_copy.py").is_file(), "missing upstream publish-copy checker"
manifest = json.loads((xhs / "assets/approved-style-v1/manifest.json").read_text(encoding="utf-8"))
assert (xhs / manifest["identity_reference"]).is_file()
for item in manifest["pages"]:
    data = (xhs / item["file"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == item["sha256"], item["file"]
for name in ("kaibing-integration.md", "approved-style.md", "config/default-preferences.md",
             "kevinbee/ip-core.md", "kevinbee/character-model.md", "kevinbee/source-manifest.yaml"):
    assert (xhs / "references" / name).is_file(), name
print(f"six skill entries and fixed XHS assets passed ({head[:7]})")
