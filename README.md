# 凯冰内容生产套件

把四个独立的 Codex Skills 连成一条可选择阶段的文章流程：选题、中文写作与去 AI 味、正文配图与封面、公众号排版。套件本身位于 [`.agents/skills/kevinbee-article-suite`](.agents/skills/kevinbee-article-suite/SKILL.md)；四个上游 Skill 作为固定版本的 Git 子模块接入，仍由各自仓库维护。

## 安装

在希望使用套件的项目目录克隆：

```bash
git clone --recurse-submodules https://github.com/ruijayfeng/kevinbee-article-suite.git
```

进入克隆后的项目目录，Codex 就能从 `.agents/skills/` 发现五个 Skill。已有克隆升级时运行 `git pull` 和 `git submodule update --init --recursive`。普通更新以本仓库锁定的子模块提交为准；不要直接运行 `git submodule update --remote`，那会跳到尚未验证的新版本。

这份仓库固定了当前联调版本，适合试用和复核。雷达覆盖补查已合入上游 main，锁定 `d09350c`；写作仍锁定功能分支的 `1bdce71`，默认写作基线检查通过，可选路线正在做作者验收。使用时以锁定提交为准。

## 工作方式

| 环节 | Skill | 作用 |
| --- | --- | --- |
| 选题 | `zhihu-ai-editorial` | 有找近期方向的需求时收集线索；已有题目可跳过。 |
| 写作 | `zh-writing-humanizer` | 用原始材料写稿或改稿，检查中文表达和 AI 味。 |
| 图片 | `kevinbee-illustrations` | 判断正文是否需要新图，制作适合的正文图或封面。 |
| 排版 | `gzh-design` | 定稿后制作公众号 HTML；知乎稿可跳过。 |
| 编排 | `kevinbee-article-suite` | 判断要走哪些环节、维护交接和成稿回流。 |

套件不要求每次跑完所有环节。提供原始笔记、截图说明、实测结果或旧稿时，直接交给写作环节；文章定稿后再做封面和排版。事实、图片证据和作者经历不能由套件补造。

公众号排版已锁定上游 main 的 `4b10fa6`，默认使用“凯冰·紧凑承接（原生正文版）”，也可选择“橄榄手记”；主题规则以排版 Skill 的主题索引为准。

## 成稿回流

交给用户审阅的完整文章会先留本地快照。用户改稿后，只需交回修改版；套件对比两版并记录具体差异。用户明确认可的版本才进入 `calibration/approved/`，以后可按题材选作写作参考。模型评审可以提出修改建议，不会自动把单篇稿件的写法升级成通用规则。操作说明见 [校准库](calibration/README.md)。

`calibration/drafts/` 和 `calibration/inbox/` 是本地文件夹，不进入 Git。认可后纳入版本控制的样本可能包含作者文章；公开分享前先检查其内容。本仓库目前不包含任何已认可文章。

## 验证

```bash
python3 .agents/skills/kevinbee-article-suite/scripts/test_check_handoff.py
python3 .agents/skills/kevinbee-article-suite/scripts/test_article_feedback.py
python3 .agents/skills/kevinbee-article-suite/scripts/test_writing_baseline.py
python3 .deps/kevinbee-illustrations/kevinbee-illustrations/scripts/validate.py
python3 .deps/gzh-design-skill/scripts/test_verify_content.py
python3 .deps/gzh-design-skill/scripts/test_theme_state.py
```

这些检查验证交接、快照、写作基线及部分上游包的结构和内容一致性；文章的语言质量仍需对具体成稿做人工审阅。

## 依赖与许可

本仓库的编排 Skill 使用 MIT 许可。各子模块遵循各自仓库的许可，尤其 `gzh-design-skill` 使用 AGPL。子模块固定提交，不复制、修改或替代其许可文件。`content-production-skills` 当前仓库未提供独立许可文件；使用与再分发时应以其仓库条款为准。
