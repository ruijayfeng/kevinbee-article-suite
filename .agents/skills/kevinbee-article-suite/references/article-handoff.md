# 文章包交接格式

跨 Skill 处理同一篇文章时，在项目目录维护 `article-package.md`。它记录材料和产物位置，不替文章预设叙事结构。

```markdown
# Article Package

## Status
stage: material | drafting | illustrated | layout | publish-ready
target_platform: wechat | zhihu | other

## Reader Question
这篇文章要回答的读者问题。

## Sources
- [来源名](URL)：它支持哪项事实。

## Original Materials
- `relative/path` — 原始笔记、已有草稿、提示词、运行结果、截图说明或对话

## Draft
- markdown: `relative/path`
- revision_status: working | final
- review_snapshot: 留给用户审阅前保存的快照 ID；尚未交付时留空

## Delivery
- verification: `relative/path`
```

只有确实有助于这篇文章时，才补 `Author Context`、`Cases`、`Voice Evidence`、`story_map`、`Images`、`Cover` 或 `Share Copy`。不要为填表而制造案例卡，也不要在写作前用案例卡替换原始材料。

图片、封面和配文是正文定稿后的独立交接；需要时记录产物路径及它与正文的对应位置。概念图不能记作测试结果。公众号发布时还需记录 HTML、预览和图片实际上传后的检查结果。
