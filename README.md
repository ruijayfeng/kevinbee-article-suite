# 凯冰内容生产套件

把五个独立的 Codex Skills 连成可选择阶段的内容流程：选题、中文写作与去 AI 味、正文配图与封面、公众号排版、小红书图文。套件本身位于 [`.agents/skills/kevinbee-article-suite`](.agents/skills/kevinbee-article-suite/SKILL.md)；五个上游 Skill 作为固定版本的 Git 子模块接入，仍由各自仓库维护。

## 安装

在希望使用套件的项目目录克隆：

```bash
git clone --recurse-submodules https://github.com/ruijayfeng/kevinbee-article-suite.git
```

进入克隆后的项目目录，Codex 就能从 `.agents/skills/` 发现六个 Skill。已有克隆升级时运行 `git pull` 和 `git submodule update --init --recursive`。普通更新以本仓库锁定的子模块提交为准；不要直接运行 `git submodule update --remote`，那会跳到尚未验证的新版本。

五个上游 Skill 均锁定经过核验的提交。雷达覆盖补查锁定 `d09350c`；写作可选配文与结构诊断已获作者认可并合入 main，锁定 `ddc5e48`，默认写作基线检查通过。小红书升级至 v1.1.0，锁定 `f97bdfd`：内容关系决定构图，凯冰按事件参与，完整文案、图内标签和手机阅读纳入质量复核；共享参考直接使用根目录资产。单独安装可使用对应 Release ZIP，套件使用本仓库锁定提交。

## 工作方式

| 环节 | Skill | 作用 |
| --- | --- | --- |
| 选题 | `zhihu-ai-editorial` | 有找近期方向的需求时收集线索；已有题目可跳过。 |
| 写作 | `zh-writing-humanizer` | 用原始材料写稿或改稿，检查中文表达和 AI 味。 |
| 图片 | `kevinbee-illustrations` | 判断正文是否需要新图，制作适合的正文图或封面。 |
| 排版 | `gzh-design` | 定稿后制作公众号 HTML；知乎稿可跳过。 |
| 小红书 | `kaibing-xhs-images` | 从原始素材或文章制作逐页文案、封面、内页和配文；写作 Skill 复核事实与语言。 |
| 编排 | `kevinbee-article-suite` | 判断要走哪些环节、维护交接和成稿回流。 |

套件不要求每次跑完所有环节。公众号和知乎稿从原始材料进入写作；小红书从原始素材或已有文章进入图文规划，复核逐页文案后出图，不先写长文。事实、图片证据和作者经历不能由套件补造。

公众号排版已锁定上游 main 的 `4b10fa6`，默认使用“凯冰·紧凑承接（原生正文版）”，也可选择“橄榄手记”；主题规则以排版 Skill 的主题索引为准。

## 小红书使用

可直接说：“用套件把这些笔记做成小红书图文”“把这篇文章改成小红书版本”“只规划不生图”“先做封面”或“修改第 3 页”。

小红书主写逐页文案和发布配文，中文写作 Skill 用基础规则复核，再同步文案和提示词、制作图片。封面与内页采用新 Skill 自带的已确认风格和 Q 版角色参考；当前任务明确授权整套时继续完成，不重复确认已有偏好。

内容规划沿用上游的完整问题、解释与图文分工规则，内页密度按内容和手机阅读决定，观感稳定而空间构图随每页关系变化。文案只在 `Text Content` 维护，复核保留画面贡献、来源与场景检查字段；结尾按当篇内容设计，暂不自动追加固定品牌尾页。本轮升级与样例复核见[同步记录](docs/validation/xiaohongshu/composition-sync-2026-10-07.md)。

交付支持规划、单封面和整套。整套需核对页序、最终 PNG 尺寸、图片与提示词文件、生成记录，以及中文、身份、证据与手机阅读。素材分类留在制作记录中；发布文案检查会拦住常见制作标签，确需上图的读者说明需记录内容与原因。文案或图片变化后旧核验失效，受影响页面重新制作和复核。视觉核验新增 `composition` 项；旧报告需补做实际构图检查后重新核验。具体字段与命令见 [小红书交接](.agents/skills/kevinbee-article-suite/references/xiaohongshu-handoff.md)。

小红书审阅稿包含逐页文字、发布标题与配文；快照记录平台，候选继承它。以后最多参考两份同平台且已认可、已复盘的文案；认可文案不改变视觉基准。三组不生图的流程样例见 [验证记录](docs/validation/xiaohongshu/README.md)。

## 成稿回流

交给用户审阅的完整文章会先留本地快照。用户改稿后，只需交回修改版；套件对比两版并记录具体差异。用户明确认可的版本才进入 `calibration/approved/`，以后可按题材选作写作参考。模型评审可以提出修改建议，不会自动把单篇稿件的写法升级成通用规则。操作说明见 [校准库](calibration/README.md)。

`calibration/drafts/` 和 `calibration/inbox/` 是本地文件夹，不进入 Git。认可后纳入版本控制的样本可能包含作者文章；公开分享前先检查其内容。本仓库目前不包含任何已认可文章。

## 验证

```bash
python3 .agents/skills/kevinbee-article-suite/scripts/test_check_handoff.py
python3 .agents/skills/kevinbee-article-suite/scripts/test_xhs_delivery.py
python3 .agents/skills/kevinbee-article-suite/scripts/test_suite_installation.py
python3 .agents/skills/kevinbee-article-suite/scripts/test_article_feedback.py
python3 .agents/skills/kevinbee-article-suite/scripts/test_writing_baseline.py
python3 .deps/kevinbee-illustrations/kevinbee-illustrations/scripts/validate.py
python3 .deps/gzh-design-skill/scripts/test_verify_content.py
python3 .deps/gzh-design-skill/scripts/test_theme_state.py
```

这些检查验证交接、版本失效、快照与平台继承、写作基线、固定依赖和部分上游包的结构一致性。小红书测试图片是临时合成夹具，不代表实际生图或视觉验收；文章与图片质量仍需对具体成品审阅。

## 依赖与许可

本仓库的编排 Skill 使用 MIT 许可。小红书依赖保留 MIT、NOTICE 和上游 LICENSES。各子模块遵循各自仓库的许可，尤其 `gzh-design-skill` 使用 AGPL。子模块固定提交，不复制、修改或替代其许可文件。`content-production-skills` 当前仓库未提供独立许可文件；使用与再分发时应以其仓库条款为准。
