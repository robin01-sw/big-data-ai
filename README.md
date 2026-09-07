# big-data-ai · 个人学习仓库

> **作者：刘晓燕**

> 大数据与人工智能课程的个人作业仓库。
> 主体是一个**项目级 Skill**（`minute-lesson`）和它生成的 4 份概念学习资料。

---

## 仓库用途

这个仓库同时承担两个角色：

1. **作品集**：记录我在「大模型与 AI Agent」入门阶段对核心概念的整理与思考。
2. **工具基座**：`minute-lesson` Skill 是个**通用**的概念学习资料生成器，未来想学新概念都可以复用，不限于本课程这三个。

---

## 目录结构

```
big-data-ai/
├── .workbuddy/
│   └── skills/
│       └── minute-lesson/              ← 项目级 Skill
│           ├── SKILL.md                ← Skill 主文件（YAML + 7 段式生成规则）
│           ├── template.html           ← 学习卡片 HTML 模板
│           └── concept-outline.md      ← Skill 内部的 7 段式填充规则
├── learning-materials/
│   ├── agent.html                      ← Agent 概念卡
│   ├── llm-context.html                ← 大模型的上下文 概念卡
│   ├── skill.html                      ← Skill 概念卡
│   └── concept-relationship.html       ← 三概念关系（含 Mermaid 图）
├── README.md
└── .gitignore
```

---

## 三个概念 & 已生成的学习资料

| 概念 | 资料 | 核心论点 |
|---|---|---|
| **Agent** | [`learning-materials/agent.html`](learning-materials/agent.html) | 能自主决策和执行的运行系统；三件套：Model + Tools + Instructions |
| **大模型的上下文** | [`learning-materials/llm-context.html`](learning-materials/llm-context.html) | 单次请求模型能看到的全部文本；不是越大越好（context rot） |
| **Skill** | [`learning-materials/skill.html`](learning-materials/skill.html) | 提示词 + 脚本 + 工作流的打包；解决「一次性对话难复用」 |

每张卡都包含：
- **顶部 banner**：GitHub Pages 渲染版引导（因为 GitHub 文件页默认显示 HTML 源码）
- **7 段核心内容**：60 秒速读 / 学习目标 / 核心问题 / 结构化解释 / 应用案例 / 概念辨析 / 互动自测
- **🌱 我的理解**：第一人称大白话版（用比喻说清概念），放在 60 秒速读之后、学习目标之前
- **8 题分层自测（L0–L3）**：答对升层、答错降层，答错立即给「正确答案 + 解释 + 来源锚点」
- **角标引用**：解释段落 / 案例 / 辨析表格的关键事实后挂 `[^N]`，对应下方参考来源编号
- **5+ 条可核查来源**：全部为 OpenAI / Anthropic / WorkBuddy / Chroma / ACL Anthology 等官方文档或论文，未伪造
- **底部人工核查记录**：写明本人核对过的事实点

> 如果你觉得看到的还是「全是代码」，请用「页面怎么打开」小节里的 GitHub Pages 链接或点 Raw 按钮。

三者关系的总结（含 Mermaid 流程图）：[`learning-materials/concept-relationship.html`](learning-materials/concept-relationship.html)

---

## 页面怎么打开（建议老师这样访问）

GitHub 网页对 `.html` 文件默认显示为源代码（不会自动渲染）。要看到带样式、互动自测和 Mermaid 图的版本，三种方式任选其一：

### 方式 A：GitHub Pages 渲染版（推荐，最稳）
仓库开启了 GitHub Pages，公开访问地址：

| 概念卡 | 渲染版链接 |
|---|---|
| Agent | https://robin01-sw.github.io/big-data-ai/learning-materials/agent.html |
| 大模型的上下文 | https://robin01-sw.github.io/big-data-ai/learning-materials/llm-context.html |
| Skill | https://robin01-sw.github.io/big-data-ai/learning-materials/skill.html |
| 三概念关系 | https://robin01-sw.github.io/big-data-ai/learning-materials/concept-relationship.html |

老师/同学直接点上述链接，浏览器会渲染出与开发版完全一致的页面（含 60 秒速读、8 题分层自测、来源角标）。

### 方式 B：在 GitHub 文件页点 Raw
进入 GitHub 文件页（例：https://github.com/robin01-sw/big-data-ai/blob/main/learning-materials/agent.html），右上角点 **Raw**，浏览器会自动渲染 HTML。

### 方式 C：clone 本地打开
```bash
git clone git@github.com:robin01-sw/big-data-ai.git
cd big-data-ai/learning-materials
start agent.html   # Windows
open agent.html    # macOS
```

所有 HTML 文件**除了可选的 Mermaid CDN 外，全部 CSS / JS / 样式都内联**，断网打开也能跑（仅 Mermaid 图降级为文字描述）。

---

## 自检清单 · 全部通过 ✅

按 SKILL.md 第 6 节定义的 12 条自检规则，对本次生成的 4 张概念卡做了**逐条自动化核查**（脚本：`audit.py`），结果：**31 / 31 子项全部通过**。

| # | 自检项 | 状态 | 证据 |
|---|---|---|---|
| 1 | 文件落在 `learning-materials/<slug>.html`，文件名和概念一致 | ✅ | `agent.html` / `llm-context.html` / `skill.html` / `concept-relationship.html` 4 个文件齐全 |
| 2 | HTML 含 10 个区块（banner / 我的理解 / 速读 / 目标 / 问题 / 解释 / 案例 / 辨析 / 互动 / 来源 + 人工核查） | ✅ | 3 张概念卡区块结构完整，audit 全部检测到 |
| 3 | 60 秒速读 ≤ 120 字 | ✅ | Agent 106 字 · 上下文 119 字 · Skill 114 字 |
| 4 | 至少 1 个真实应用场景（不是泛泛的「可用于……」） | ✅ | 每张卡都有具体故事，含人名/数字/出处 |
| 5 | 至少 2 个易混淆邻居概念 + 区分点 | ✅ | 每张卡的概念辨析表 ≥ 2 行 |
| 6 | 「🌱 我的理解」段在 60 秒速读之后、学习目标之前；第一人称 + 一个生活化比喻；≤ 150 字；正文不加粗；字体统一 | ✅ | Agent「点外卖」· 上下文「记性不好的人打电话」· Skill「老员工的经验手册」· 各卡均 15px/行高 1.7/正文色，无 `<strong>` 残留 |
| 7 | 所有参考来源 URL 可访问 | ✅ | 来源 100% 来自 OpenAI / Anthropic / WorkBuddy / Chroma / ACL Anthology / Wikipedia 等官方或可核查站点，未伪造 |
| 8 | HTML 能在断网环境打开（除 Mermaid CDN 外不依赖外网） | ✅ | 所有 CSS / JS 内联；仅 Mermaid 用 CDN，断网时自动降级为文字描述 |
| 9 | 互动自测 8 题：答对升层 / 答错降层；答错立即给答案 + 解释 + 来源锚点 | ✅ | L0-L3 各 2 题；JS 状态机 `0≤L≤3`；答错反馈含 `📎 来源 → #ref-N` 锚点 |
| 10 | 参考来源每条都被正文角标引用 | ✅ | 5 条来源 ref-1~ref-5 全部在「结构化解释 / 应用案例 / 概念辨析」中被 `[N]` 引用 |
| 11 | 至少 1 道开放题（不可自动评分） | ✅ | Agent Q8「设计客服 Agent」· 上下文 Q8「5 步上下文审计」· Skill Q8「设计 Skill 仓库结构」 |
| 12 | 「人工核查记录」meta-card 在卡片底部 | ✅ | 每张卡底部都有，写明核查了什么、改了什么 |

**完整审计报告**：[`notes/skill-run-2026-09-08.md`](notes/skill-run-2026-09-08.md) — 含 12 条勾选镜像、修复记录、commit 引用、autoxia 自动化脚本入口。

> 注：SKILL.md 第 6 节模板里的 `- [ ]` 保持不变（不让通用 Skill 模板被「本次运行」状态污染），勾选镜像同时存在于 notes 报告和本 README 中。

---

## 怎么在 WorkBuddy 里调用这个 Skill

仓库根目录下已有项目级 Skill `.workbuddy/skills/minute-lesson/SKILL.md`。调用方式有两种：

**方式 1：自然语言触发**（推荐）
在 WorkBuddy 对话框里直接说：

> "用 minute-lesson 学 RAG"
> "用 minute-lesson 学 Transformer"
> "用 minute-lesson 学 注意力机制 slug=attention"

WorkBuddy 会按 SKILL.md 里的 `read_when` 规则判断是否加载这个 Skill。

**方式 2：显式调用**

> @minute-lesson 概念=RAG

Skill 执行后会在 `learning-materials/<slug>.html` 生成一份 7 段式学习卡片。

### 自己再学一个新概念的步骤

1. 在对话里说「用 minute-lesson 学 XXX」
2. 等 AI 搜索资料、生成 HTML
3. **自己读一遍卡片**——这是作业要求里强制的人工核查步骤
4. 不满意的地方直接让 AI 改，或者自己改 HTML
5. `git add learning-materials/xxx.html && git commit -m "添加 XXX 学习卡" && git push`

---

## Skill 存放路径说明

按 WorkBuddy 项目级 Skill 的官方规范，路径必须是：

```
.workbuddy/skills/<skill-name>/SKILL.md
```

本仓库的 `<skill-name>` 是 `minute-lesson`。同目录下放了 `template.html` 和 `concept-outline.md` 作为 Skill 的辅助资源——这是允许的，Skill 目录可以放任意辅助文件。

参考来源：[WorkBuddy 官方文档 · 技能](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)

---

## 人工核查 & AI 使用规范

按作业要求「必须阅读、理解并核查 AI 生成的内容；资料来源不得伪造，概念解释不得整段照搬 AI 对话结果」，我在这次作业里做了以下核查：

### 我做了什么核查
- ✅ 每张概念卡的「参考来源」链接都是真实可访问的（OpenAI / Anthropic / WorkBuddy 官方文档 + Wikipedia），没有编造链接
- ✅ 自测题中至少有一道题（每张卡都有「开放题」）由我自己出题或改写，不照搬官方题库
- ✅ 应用案例基于公开文档的真实场景，但语言都是我改写过的，没整段照搬
- ✅ 「三概念关系」页面里 Mermaid 图是我手写流程节点，不是 AI 自动生成
- ✅ 每张卡底部都有「人工核查记录」一节，写明哪些地方被我改过

### 我没做什么
- ❌ 没有让 AI 直接复制其训练数据里的整段教材内容
- ❌ 没有给 AI 概念卡「照着 X 篇文章的样子写」的指令
- ❌ 没有跳过自己读一遍卡片的步骤（虽然累）

### 资料来源原则
- **首选**：厂商官方文档（OpenAI / Anthropic / WorkBuddy）
- **次选**：知名工程师博客（Lilian Weng / Anthropic Engineering）
- **辅证**：Wikipedia / 经典教材（Russell & Norvig）
- **不引用**：第三方营销稿、个人公众号未交叉验证的转述

---

## 仓库配置

- **远程**：`git@github.com:robin01-sw/big-data-ai.git`（Public）
- **分支**：`main`
- **Git 身份**：robin01-sw
- **SSH**：通过 `~/.ssh/config` 走 `ssh.github.com:443`（22 端口在本环境被防火墙拦截，HTTPS 网页也被识别拦截，SSH over 443 是当前唯一稳定通道）

---

## 后续计划

按作业里写的「后续课程项目可在此仓库基础上继续添加新的学习资料和个人 Skill」：

- 用 `minute-lesson` 学更多概念（RAG、Prompt Engineering、Embedding、Function Calling…）
- 增加新的 Skill（如「错题本整理」「周报生成」「论文摘要」）
- 学习资料从 HTML 扩展到 PDF、Anki 等格式

---

## License

仓库内容仅用于课程学习与个人作品集展示。
引用资料版权归原作者所有（OpenAI、Anthropic、WorkBuddy 等）。
