---
name: kevinbee-article-suite
description: Orchestrate Chinese content for WeChat, Zhihu, or Xiaohongshu from topics, raw materials, or existing articles through writing, visuals, delivery, and user-approved copy feedback; skip unused stages.
---

# 凯冰内容生产套件

把选题、写作、正文图片和平台交付连成一条可审查的文章流程。套件负责路由和交接；各专项 Skill 保留自己的规则与真值源。

小红书图文、封面、文章转图文或指定页修改，先读 [xiaohongshu-handoff.md](references/xiaohongshu-handoff.md)：`kaibing-xhs-images` 主导分析、逐页文案、配文和图片，`zh-writing-humanizer` 只用基础规则复核事实与语言。原始素材可直接做图文，不先写长文。只规划停在文案；只要封面按一页交付；整套按计划页数验收。跨平台任务各建文章包，共享来源材料。

## 路由

以下步骤用于公众号与知乎文章；小红书使用上面的专用分支。

1. 先识别用户已经给出的内容：既定题目、作者材料、公开来源、平台、现有草稿、图片与目标交付。不要为了跑满流程重复询问或调用无关环节。
2. 用户要找近期方向时，调用 `zhihu-ai-editorial`。题目已经确定时，直接核对必要来源并进入写作，不强制先跑热点雷达。
3. 公众号或知乎文章调用 `zh-writing-humanizer` 的默认公众号路线。把原始笔记、草稿、截图说明、提示词、运行结果和来源直接交给写作 Skill；已有整理表可以附上，但不代替原始材料。文章形态、叙事顺序和语风由写作 Skill 决定，套件不另建一套写作规则。
4. 需要正文图片时调用 `kevinbee-illustrations` 的 `article-body` 模式。先传入已有图片及其用途，只有文章存在认知断点时才生成隐喻图。
5. 需要封面时，在标题与正文判断定稿后调用 `kevinbee-illustrations` 的 `cover` 模式；不要把正文隐喻图直接放大成封面。
6. 需要文章配文时，在正文定稿后调用 `zh-writing-humanizer` 的文章配文路线。配文只从正文抽取，不新增结论或承诺。
7. 公众号交付调用 `gzh-design`，凯冰内容显式指定“凯冰·紧凑承接（原生正文版）”。知乎交付跳过公众号 HTML。

## 成稿回流

每次把完整文章交给用户审阅前，先按 [feedback-loop.md](references/feedback-loop.md) 保存交付稿快照，并在文章包记录快照 ID。用户提供修改版，或把稿件放进本项目的 `calibration/inbox/` 时，直接用快照做前后对比，不要求用户寻找修改前稿。修改版先作为候选；只有用户明确说“这版认可、可作为以后参考”，才收录为已认可样本。以后写作按题材与文章任务选择少量相关样本，理解其叙事选择和语言习惯，不能照搬句子、口癖或把旧文章事实带进新文章。

模型评审用于比较草稿与已认可样本、指出可定位的差异并提出修改假设。用户的实际修改和取舍才决定样本是否进入参考库；单次评分不得自动改写写作 Skill 的通用规则。

## 文章包

开始跨 Skill 交接前，读 [article-handoff.md](references/article-handoff.md)，在项目目录维护一份 `article-package.md`。只填写已有事实；未知项留空或标记状态，不补写经历。

文章包用于保存：读者问题、平台、原始材料路径、来源、写作产物、图片和交付文件。案例卡、声音摘录和 story map 只在这篇文章确实需要时添加。原始材料与概念图片必须分开记录。

整理好的案例卡不能冒充原始笔记，但也不要求作者为每句自然反应提供逐字原话。事实和经历必须有依据；允许根据材料自然表达，不为了规避 AI 味压短文章。

## 流程与停止边界

读 [pipeline-contract.md](references/pipeline-contract.md) 决定当前任务需要哪些阶段。每个上游产物通过对应检查后再交给下游：

- 灵感卡不是文章提纲；
- 写作稿未定稿时不进入最终排版；
- 结果图、过程图和概念图不得互相冒充；
- HTML 合规不代表文章叙事通过；
- 本地图片能预览不代表已在公众号中可用。

阶段产物可以独立交付。用户只要文章，不生成图片或 HTML；用户只要排版，不重新写作。

## 确定性检查

完成文章包或准备发布时运行：

```bash
python3 scripts/check_handoff.py /absolute/path/to/article-package.md
python3 scripts/check_handoff.py /absolute/path/to/article-package.md --publish-ready
```

脚本只检查必要字段、引用文件、链接和占位状态。鲜活度、叙事推进与作者声音必须由写作 Skill 和人工盲读判断，不能用脚本分数替代。
