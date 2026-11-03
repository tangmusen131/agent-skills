# 原创 Agent Skills 第一批（3 个）

本目录包含三个**完全原创**的 Agent Skills 包，按 [Agent Skills](https://agentskills.io/specification) 常见约定编写（`SKILL.md` + 可选 `references/`）。正文为英文，便于全球平台上架；本说明为中文。

| 目录 | name | 一句话卖点 |
|------|------|------------|
| `skill-acceptance-auditor/` | `skill-acceptance-auditor` | 上架/安装前验收 SKILL.md：评分 + 通过/不通过 + 修改清单（不绑单一商店 API） |
| `decision-log-gatekeeper/` | `decision-log-gatekeeper` | 把会议/聊天整理成决策日志，强制区分 Decision / Discussion / Open，禁止静默编造决定 |
| `saas-renewal-brief/` | `saas-renewal-brief` | 根据账单/用量/合同摘录生成续约谈判简报（含砍价锚点与 walk-away；非法律意见） |

## 每个包里有什么

每个子目录至少包含：

- `SKILL.md` — YAML frontmatter（`name`、`description` 等）+ 可执行工作流
- `references/` — 配套模板或清单（英文）

## 如何安装

### 方式 A：`npx skills add`（若你的平台/CLI 支持）

在支持 Agent Skills 生态的环境中，可将本仓库或本目录发布到可访问的 git 地址后执行类似：

```bash
npx skills add <你的仓库或包地址>
# 或按各平台文档指定单个 skill 子路径
```

具体子命令以你使用的 CLI / 商店文档为准；本包**不依赖**某一家商店的私有 API。

### 方式 B：手动拷贝

1. 把三个子目录（或你需要的其中一个）复制到代理技能搜索路径，例如：
   - `.agents/skills/<skill-name>/`
   - 或客户端文档写明的 `skills/` 目录
2. 确认文件夹名与 `SKILL.md` frontmatter 里的 `name` 一致。
3. 重启或刷新代理，使新 skill 被索引。
4. 用描述中的触发场景试跑一次（例如粘贴一份会议记录测试 `decision-log-gatekeeper`）。

## 许可建议

建议使用 **MIT** License。发布前请：

1. 作者字段已设为 GitHub 账号 `tangmusen131`；若要改成真名或组织名，改各 `SKILL.md` 的 `metadata.author` 即可。
2. 在仓库根目录（或每个 skill 目录）添加 `LICENSE` 文件，版权行写上你的名字与年份。
3. 若平台要求单独的 `license` 字段，保持与 LICENSE 文件一致（当前 frontmatter 已写 `license: MIT`）。

## 免责声明

- 这些 skill 是**工作流模板**，由 AI 代理按说明执行；作者不对特定平台上的运行结果作担保。
- `saas-renewal-brief` 明确**不是法律意见**，不能替代律师审查合同。
- `decision-log-gatekeeper` 产出的是结构化日志，不是法定会议纪要或人事档案。
- `skill-acceptance-auditor` 的「抄袭样板」检查仅为**启发式结构审查**，不构成法律上的侵权鉴定。
- 使用前请自行满足你所在司法辖区与公司的合规要求；不要用这些 skill 从事欺诈、伪造单据或未授权访问。

## 质量说明

- 正文为原创撰写，禁止当作「改写网上已有 skill」的产物再分发时谎称来源。
- 若你修改了步骤或模板，请Bump `metadata.version` 并在你自己的 changelog 中记录。

—
作者：`tangmusen131` · 许可建议：MIT
