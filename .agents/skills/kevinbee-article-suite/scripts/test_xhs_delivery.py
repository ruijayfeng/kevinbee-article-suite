#!/usr/bin/env python3
"""Exercise complete, partial, stale and malformed Xiaohongshu deliveries.

Images and generation records below are synthetic test fixtures, not real runs.
"""
from pathlib import Path
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

from xhs_delivery import load, review_text

SCRIPTS = Path(__file__).parent


def png(path: Path, color: int = 255, width: int = 1080, height: int = 1440) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    data = (b"\x00" + bytes([color]) * width) * height
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(data)) + chunk(b"IEND", b""))


class DeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = self.root / "article-package.md"
        self.make_delivery()

    def call(self, script: str, *args: str, ok: bool = True) -> subprocess.CompletedProcess:
        result = subprocess.run([sys.executable, str(SCRIPTS / script), *args], text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result

    def export(self) -> None:
        self.call("xhs_delivery.py", "review-copy", str(self.package))

    def verify(self, visual: bool = True, ok: bool = True) -> subprocess.CompletedProcess:
        return self.call("xhs_delivery.py", "verify", str(self.package),
                         *(["--visual-reviewed"] if visual else []), ok=ok)

    def ready(self, ok: bool = True) -> subprocess.CompletedProcess:
        return self.call("check_handoff.py", str(self.package), "--publish-ready", ok=ok)

    def replace(self, before: str, after: str) -> None:
        self.package.write_text(self.package.read_text().replace(before, after), encoding="utf-8")

    def make_delivery(self, scope: str = "series", count: int = 2) -> None:
        (self.root / "source.md").write_text("Synthetic source; no actual product claims.\n", encoding="utf-8")
        pages = []
        outline = "# Xiaohongshu Infographic Series Outline\n\n"
        for order in range(1, count + 1):
            role = "cover" if order == 1 else "content"
            pages.append(f"| {order} | {role} | `{order:02d}-{role}.png` | `prompts/{order:02d}-{role}.md` |")
            (self.root / "prompts").mkdir(exist_ok=True)
            (self.root / f"prompts/{order:02d}-{role}.md").write_text(f"Test page {order}: 原始文案\n", encoding="utf-8")
            png(self.root / f"{order:02d}-{role}.png", color=250 - order)
            outline += (f"## Image {order} of {count}\n\n**Position**: {role}\n\n"
                        f"**Text Content**:\n- Title: 第 {order} 页\n- Points: 原始文案\n\n"
                        "**Visual Concept**: Synthetic visual fixture\n\n---\n\n")
        (self.root / "outline.md").write_text(outline, encoding="utf-8")
        (self.root / "caption.md").write_text("# 发布标题\n\n测试配文。\n\n#测试\n", encoding="utf-8")
        (self.root / "generation-record.json").write_text(json.dumps({"tool": "synthetic-test-fixture"}), encoding="utf-8")
        self.package.write_text(f"""# Article Package
## Status
stage: publish-ready
target_platform: xiaohongshu
## Reader Question
测试读者问题
## Sources
Synthetic fixture only.
## Original Materials
- `source.md` — 原始素材
## Draft
- markdown: `review-copy.md`
- revision_status: final
## Xiaohongshu
- delivery_scope: {scope}
- output_dir: `.`
- outline: `outline.md`
- caption: `caption.md`
- generation_record: `generation-record.json`
- page_count: {count}
## XHS Pages
| order | role | image | prompt |
| --- | --- | --- | --- |
{chr(10).join(pages)}
## Delivery
- verification: `verification.json`
""", encoding="utf-8")
        self.export()

    def test_series_and_cover_complete(self) -> None:
        self.verify()
        self.ready()
        (self.root / "verification.json").unlink()
        self.make_delivery("cover", 1)
        self.verify()
        self.ready()

    def test_plan_without_images_and_prompt_files(self) -> None:
        self.replace("delivery_scope: series", "delivery_scope: plan")
        self.replace("stage: publish-ready", "stage: drafting")
        for path in self.root.glob("*.png"):
            path.unlink()
        for path in (self.root / "prompts").glob("*"):
            path.unlink()
        (self.root / "generation-record.json").unlink()
        self.call("check_handoff.py", str(self.package))
        self.ready(ok=False)

    def test_partial_sample_is_not_complete_series(self) -> None:
        self.verify()
        (self.root / "02-content.png").unlink()
        self.ready(ok=False)
        self.replace("stage: publish-ready", "stage: illustrated")
        self.call("check_handoff.py", str(self.package))

    def test_missing_and_duplicate_page(self) -> None:
        self.verify()
        row = "| 2 | content | `02-content.png` | `prompts/02-content.md` |"
        original = self.package.read_text()
        for changed in ("", row.replace("| 2 |", "| 1 |"), row.replace("content", "cover")):
            with self.subTest(changed=changed):
                self.package.write_text(original.replace(row, changed), encoding="utf-8")
                self.ready(ok=False)

    def test_missing_files_wrong_size_and_pending_copy(self) -> None:
        self.verify()
        for name in ("01-cover.png", "prompts/01-cover.md", "generation-record.json", "verification.json", "caption.md"):
            with self.subTest(name=name):
                path = self.root / name
                data = path.read_bytes()
                path.unlink()
                self.ready(ok=False)
                path.write_bytes(data)
        png(self.root / "01-cover.png", width=100)
        self.verify(ok=False)
        png(self.root / "01-cover.png", color=249)
        (self.root / "caption.md").write_text("【待补素材】", encoding="utf-8")
        self.export()
        self.verify(ok=False)

    def test_separate_images_and_prompts_per_page(self) -> None:
        for before, after in (("`02-content.png`", "`01-cover.png`"),
                              ("`prompts/02-content.md`", "`prompts/01-cover.md`")):
            original = self.package.read_text()
            self.replace(before, after)
            self.verify(ok=False)
            self.package.write_text(original, encoding="utf-8")

    def test_visual_review_never_inferred(self) -> None:
        self.verify(visual=False)
        self.ready(ok=False)
        self.verify()
        self.ready()

    def test_copy_changes_require_new_prompt_and_image(self) -> None:
        self.verify()
        old = (self.root / "outline.md").read_text()
        (self.root / "outline.md").write_text(old.replace("原始文案", "新文案", 1), encoding="utf-8")
        self.ready(ok=False)
        self.export()
        self.verify(ok=False)
        (self.root / "prompts/01-cover.md").write_text("Updated prompt: 新文案\n", encoding="utf-8")
        self.verify(ok=False)
        png(self.root / "01-cover.png", color=128)
        self.verify()
        self.ready()
        self.assertTrue(list(self.root.glob("review-copy-backup-*.md")))
        self.assertTrue(list(self.root.glob("verification-backup-*.json")))

    def test_caption_change_needs_new_report_but_not_new_images(self) -> None:
        self.verify()
        (self.root / "caption.md").write_text("新标题\n\n新的发布配文。\n", encoding="utf-8")
        self.ready(ok=False)
        self.export()
        self.ready(ok=False)
        self.verify()
        self.ready()

    def test_any_artifact_change_invalidates_report(self) -> None:
        self.verify()
        for name in ("prompts/01-cover.md", "generation-record.json", "review-copy.md", "01-cover.png"):
            with self.subTest(name=name):
                path = self.root / name
                data = path.read_bytes()
                path.write_bytes(data + b"\n")
                self.ready(ok=False)
                path.write_bytes(data)
        self.ready()

    def test_review_view_contains_copy_and_caption_without_visual_fields(self) -> None:
        text = review_text(self.package, load(self.package))
        self.assertIn("第 1 页", text)
        self.assertIn("测试配文", text)
        self.assertNotIn("Synthetic visual fixture", text)
        self.assertNotIn("**Position**", text)

    def test_production_labels_cannot_be_verified_for_publishing(self) -> None:
        path = self.root / "outline.md"
        old = path.read_text()
        path.write_text(old.replace("- Points: 原始文案", "- Points: 原始文案\n概念示意，非工具实测", 1), encoding="utf-8")
        self.export()
        self.verify(ok=False)
        self.ready(ok=False)

    def test_reader_conditions_and_explicit_disclosure_remain_valid(self) -> None:
        path = self.root / "outline.md"
        old = path.read_text()
        path.write_text(old.replace("- Points: 原始文案", "- Points: 结果只适用于单人任务\n概念示意", 1)
                       .replace("**Visual Concept**: Synthetic visual fixture",
                                "**Reader Disclosure**: 概念示意\n**Disclosure Reason**: 教学界面需与真实截图区分\n**Visual Concept**: Synthetic visual fixture", 1), encoding="utf-8")
        (self.root / "caption.md").write_text("这篇只介绍思路，未做网页或视频效果测试。\n", encoding="utf-8")
        self.export()
        self.verify()
        self.ready()

    def test_protect_sources_from_export_and_verification(self) -> None:
        self.replace("markdown: `review-copy.md`", "markdown: `outline.md`")
        self.call("xhs_delivery.py", "review-copy", str(self.package), ok=False)

    def test_malformed_outline_and_record_fail_cleanly(self) -> None:
        original = (self.root / "outline.md").read_text()
        for text in (original.replace("Image 2 of 2", "Image 1 of 2"),
                     original.replace("**Text Content**:", "**Missing**:", 1)):
            (self.root / "outline.md").write_text(text, encoding="utf-8")
            self.call("xhs_delivery.py", "review-copy", str(self.package), ok=False)
        (self.root / "outline.md").write_text(original, encoding="utf-8")
        for data in ("{", "[]", "null"):
            (self.root / "generation-record.json").write_text(data, encoding="utf-8")
            self.verify(ok=False)

    def test_broken_png_and_prior_report_fail_cleanly(self) -> None:
        image = self.root / "01-cover.png"
        data = image.read_bytes()
        for broken in (b"not a PNG", data[:24], data[:-4]):
            image.write_bytes(broken)
            self.verify(ok=False)
        image.write_bytes(data)
        report = self.root / "verification.json"
        for broken in ("[]", '{"version":1,"state":[]}', '{"version":1,"state":{"pages":[null]}}'):
            report.write_text(broken, encoding="utf-8")
            result = self.verify(ok=False)
            self.assertNotIn("Traceback", result.stderr)
            self.ready(ok=False)


if __name__ == "__main__":
    unittest.main()
