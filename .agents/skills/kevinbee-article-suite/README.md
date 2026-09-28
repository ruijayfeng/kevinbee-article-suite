# 套件 Skill 与配图 Skill 的维护边界

套件负责文章各阶段的选择和交接；凯冰是谁、正文图与封面如何构图、使用哪些角色资产、怎样验收，均由独立的 [kevinbee-illustrations](https://github.com/ruijayfeng/kevinbee-illustrations/blob/feat/narrative-image-roles/README.md) 维护。套件通过 `.deps/kevinbee-illustrations` 锁定其提交，并由 `.agents/skills/kevinbee-illustrations` 符号链接加载同一份 Skill；这里不保存第二套配图规则。

## 套件特有的配合

以下约定处理 Skill 之间的接口，而不是修改配图 Skill 的角色或视觉标准：

- **写作 → 图片**：文章已有的截图、过程图、结果图及其用途随正文一起交给配图 Skill；是否需要概念图由配图 Skill 判断。交接字段见 [article-handoff.md](references/article-handoff.md)，阶段边界见 [pipeline-contract.md](references/pipeline-contract.md)。
- **正文 → 封面**：标题和正文判断定稿后，套件才路由到配图 Skill 的 `cover` 模式；封面的视觉与质量门仍由配图 Skill 定义。
- **图片 → 排版**：套件记录图的角色与路径，并交给排版环节；概念图不能冒充实测证据，本地预览也不等于已在目标平台上传成功。

## 同步约定

独立配图 Skill 更新时，以其仓库为唯一修改源。套件检查上述交接是否仍兼容，运行配图包校验及套件相关测试，再推进 `.deps/kevinbee-illustrations` 的锁定提交。锁定点是经过验证的版本，不要求在上游每次提交瞬间自动跟随。

若未来确有只适用于套件的跨 Skill 处理，在套件的 `SKILL.md` 或对应交接参考中实现，并在本 README 说明**触发场景、与独立 Skill 的边界、验证方式**。人物设定、资产、隐喻方法和正文／封面质量标准仍回到独立配图 Skill 修改，然后同步锁定点。
