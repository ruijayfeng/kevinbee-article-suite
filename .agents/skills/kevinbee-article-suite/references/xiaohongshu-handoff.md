# 小红书分支：制作、复核与交接

只在用户要小红书图文、封面、文章转图文或修改指定页时读取。`kaibing-xhs-images` 是分页、视觉和生成规则的真值源；本文件只规定跨 Skill 的分工与记录。

## 制作流程

1. 确认已有素材、目标读者和任务范围；有题目直接继续，需要近期方向时才用灵感雷达。沿用用户当次要求、项目偏好和小红书 Skill 随包默认值。只规划不调用生图。
2. 把原始笔记、观点、工具材料或已有文章交给 `kaibing-xhs-images`，生成 `analysis.md`、`outline.md` 与 `caption.md`。已有文章保留原稿路径与来源，按小红书重建阅读顺序，保留决定结论的条件、失败与限制；直接创作不先写长文。跨平台各建文章包，共享材料路径。
3. 在出图前交给 `zh-writing-humanizer` 做嵌入式基础复核，检查事实、人称、数字、夸张承诺、重复总结和 AI 味，并按小红书集成指南检查发布文案是否混入制作元数据。保留页面编号、主要任务、布局、角色、证据与参考字段；只改文案，不加载公众号长文路线。需要增删页面时返回小红书 Skill 调整分页。
4. 小红书 Skill 将复核结果同步到 `outline.md` 的 `Text Content` 和 `caption.md`，再写提示词。封面、内页和指定页修改均由它负责，角色与风格规则、参考图输入、样张、授权、重试和原图备份沿用它自己的流程。
5. 默认先检查新主题样张；当前任务已明确授权整套时继续，不重复询问已确认偏好。每张最终图逐字核对，并检查人物身份、证据分类和手机可读性。仅封面按一页交付；整套按计划页数交付，样张完成不代表整套完成。
6. 导出审阅稿、保存快照并完成版本核验后交付。用户改稿先保存回流候选，再把修改同步到源文案；改动涉及某页时更新该页提示词、生成新候选并重新检查。配文单独修改不要求重生成无关图片。

## 文件与文章包

沿用 `output/小红书/YYYY-MM-DD/topic-slug/`，用户明确输出位置时按其要求。下例将文章包放在本轮输出目录；所有路径相对于文章包。`outline.md` 保持上游的 `## Image N of TOTAL` 和 `**Text Content**:` 格式，逐页文案仅维护这一份；`caption.md` 包含发布标题、正文配文和话题。

```markdown
# Article Package

## Status
stage: drafting
target_platform: xiaohongshu

## Reader Question
读者这次要解决的具体问题。

## Sources
- [来源](https://example.com)：支持的事实；纯个人材料可注明无公开来源。

## Original Materials
- `source-notes.md` — 原始笔记或文章；保留真实截图路径和证据类型

## Draft
- markdown: `review-copy.md`
- revision_status: working
- review_snapshot:

## Xiaohongshu
- delivery_scope: series
- output_dir: `.`
- outline: `outline.md`
- caption: `caption.md`
- generation_record: `generation-record.json`
- page_count: 3

## XHS Pages
| order | role | image | prompt |
| --- | --- | --- | --- |
| 1 | cover | `01-cover-topic.png` | `prompts/01-cover-topic.md` |
| 2 | content | `02-content-example.png` | `prompts/02-content-example.md` |
| 3 | ending | `03-ending-check.png` | `prompts/03-ending-check.md` |

## Delivery
- verification: `verification.json`
```

`delivery_scope` 仅允许 `plan`、`cover`、`series`。`page_count` 是本次计划交付页数；封面为 1，整套至少 2，不强制凑固定页数。只规划可列计划图片路径或用 `-` 标记未生成；生成记录尚未存在时可留路径。中途样张保持 `drafting` 或 `illustrated`，只有完整核验后才设置 `stage: publish-ready` 和 `revision_status: final`。第一页为封面，后续角色为 `content` 或 `ending`；不强制末页互动模板。

小红书不另填公众号的 `Cover`、`Share Copy` 区来重复记录同一产物。源文案、发布标题和图片上的文字要互相兑现。素材分类记录在上游定义的 `Evidence Status` 与生成记录中；上图说明是否必要、制作字段与发布文字如何分开，以上游集成指南为准。需要实测却没有材料时留待补，阻止整套发布准备通过。

## 导出、核验与快照

从套件 Skill 根目录运行，下列 `<文章包>` 和 `<审阅稿>` 使用真实文件路径：

```bash
python3 scripts/xhs_delivery.py review-copy <文章包>
python3 scripts/article_feedback.py snapshot <审阅稿> --platform xiaohongshu
python3 scripts/xhs_delivery.py verify <文章包>
python3 scripts/check_handoff.py <文章包>
```

`review-copy` 从逐页 `Text Content` 与 `caption.md` 导出纯文本，写入 `Draft.markdown`。这是审阅与回流视图，不能直接改成新真值源；收到用户修改版时先留候选，再按页同步回 `outline.md` 和 `caption.md` 并重新导出。快照 ID 写回 `Draft.review_snapshot`。导出和核验文件覆盖前自动备份，原始文案与图片继续遵循上游备份规则。

`verify` 核对文件、页数、PNG 尺寸和文案同步，调用上游发布文案检查器，并保存 SHA-256 摘要。它默认将视觉检查记为未完成。只有实际检查中文与页脚、人物身份（无人页检查不出现错误人物）、证据分类和手机阅读，且确认图片没有混入制作指令后，才运行：

```bash
python3 scripts/xhs_delivery.py verify <文章包> --visual-reviewed
python3 scripts/check_handoff.py <文章包> --publish-ready
```

`--visual-reviewed` 记录复核者的明确声明，不代表脚本会看图。版本报告记录文案、审阅稿、提示词、最终图和生成记录摘要；任一产物变化会使原核验失效。已有报告时，某页规划变化必须同时更新该页提示词并生成不同内容的新图才能重新核验；配文变化只需重新导出和复核。不要删除旧报告以绕过检查。

发布准备要求全部最终图为 PNG、1080×1440、页序连续、每页独立图片和提示词、非空生成记录，以及最新且视觉检查完成的核验报告。只规划只运行普通检查。生成工具不可用时保留规划与当前产物、说明具体阻塞点，不记录虚假成功。

## 文案参考与视觉参考

小红书文案回流读取 [feedback-loop.md](feedback-loop.md)，只复用最多两份同平台、已认可且复盘完成的相关文案。图片认可和文本认可分开记录，视觉基准由上游 `approved-style.md` 管理。角色资产随固定依赖接入，升级时核对来源与用户已认可样例，套件不另复制角色规则。
