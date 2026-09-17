---
name: push-local-repo
description: 把本地目录端到端推送到 Git 远程仓库的完整流程——环境探测、仓库初始化、.gitignore、提交身份、commit、关联或新建远端、push、hash 校验。当需要「把本地项目/代码/笔记/作业推到 GitHub」「提交并推送」「新建仓库并上传」「首次 push 到远程」「关联远程仓库」时使用。触发词：推送本地仓库、上传到 GitHub、提交并推送、关联远程仓库、首次 push、git init 后推送、本地改动要发布。
agent_created: true
---

# 推送本地仓库（端到端 Git 流程）

## 0. 铁律（先看这四条）

1. **push 是对外动作。** 执行前把「将推送的 commit 列表 + 远端地址 + 目标分支」摆给用户看并等确认。只有用户已明确说过「直接推」「不用问」时才跳过。
2. **不塞 AI 署名。** commit message 里禁止 `Co-Authored-By:` AI 工具行，也不改 author 字段去冒充别人。AI 痕迹只体现在内容里的诚实标注（如 README 的「AI 使用规范」一节）。
3. **不改写已有历史。** 不做 rebase / reset --hard / force push，除非用户明确要求；即便要求也必须用 `--force-with-lease=refs/heads/<branch>:<期望SHA>` 显式期望值，不用裸 `--force`。
4. **敏感文件靠事前拦截，不靠事后删除。** token、密钥、.env、大文件必须在第一次 `git add` 之前进 `.gitignore`——一旦进了历史，删文件也删不掉历史里的内容。

## 1. 环境探测（每次先做，不要凭记忆假设）

```bash
"C:/Users/19623/.workbuddy/binaries/python/versions/3.13.12/python.exe" \
  "<skill-dir>/scripts/preflight.py" [目标目录]
```

脚本只读，一次性输出：git/gh 定位与版本、仓库状态、变更清单（含**被 .gitignore 挡住的文件审计**）、敏感文件与大文件风险、以及建议的下一步命令。

本机已知事实（脚本会复核）：

| 项 | 情况 |
|---|---|
| sandbox 里的 `git` | PortableGit 自带，可用（`which git` → `/mingw64/bin/git`） |
| `gh` CLI | 已装在 `C:\Program Files\GitHub CLI\gh`（v2.99.0），**默认未登录** |
| 用户机器独立 Git | **已装**（2026-09-17 核实）：`%LOCALAPPDATA%\Programs\Git\cmd\git.exe`，v2.55.0，已在用户 PATH 里，全局身份也配好了。⚠️ **别只查 `C:\Program Files\Git` 就断言"没装"**——那是系统级路径，本机是**用户级**安装，2026-09-17 已因此误判过一次。要让用户自己敲命令时直接写 `git` 即可；仅当确认 PATH 不可用时才退回全路径 `C:\Users\<user>\.workbuddy\binaries\PortableGit\versions\<ver>\mingw64\bin\git.exe` |
| SSH 通道 | `~/.ssh/config` 里 github.com 已指向 `ssh.github.com:443`，但受限网络下常被掐 |

## 2. 先分流场景，再动手

| 场景 | 判定依据 | 走的步骤 |
|---|---|---|
| **A 全新目录** | 无 `.git` | §3 → §4 → §5 → §6 → §7 |
| **B 有本地仓库，缺远端** | 有 `.git`，`git remote -v` 为空 | §5（如有待提交）→ §6 → §7 |
| **C 已有远端，推新改动** | `remote -v` 有 origin | §5 → §7 |
| **D push 报网络错** | 连接超时 / CONNECT tunnel failed | 交给 `github-push-restricted-network` skill，本 skill 只做 §7 校验 |
| **E 已经同步，无事可推** | 工作区干净 **且** 远端 SHA == 本地 SHA | **直接告诉用户「已是最新」，收工** |

### 场景 E：确认「真的没事可做」需要三个独立证据

用户说「推送到远程仓库」时，**先判断有没有东西可推**，不要默认有活干。

```bash
git status -sb                         # 1. 干净？（无 M/A/??；无 ahead）
git ls-remote origin HEAD              # 2. 远端真实 SHA（最权威，顺带测网络）
git rev-parse HEAD                     #    == 本地 SHA → 内容完全一致
git push origin main                   # 3. git 自己的判决：Everything up-to-date
```

三条都成立 = 真的没东西可推，**如实汇报即完成任务**。

⚠️ **绝对不要为了「把推送这个动作做完」而制造 commit**（改注释、加空文件、`--allow-empty`）。
Robin 的仓库是学习记录，凭空多出来的 commit 是污染，会直接影响「GitHub 版本管理」这项评分。
没有改动就说没有改动。

两个容易误判的信号：

| 信号 | 含义 | 处理 |
|---|---|---|
| `git status -sb` 显示 `[gone]` | 远端同名分支**曾经**不存在（被删/改名），本地 remote-tracking ref 也丢了 | 先 `git fetch origin`；若远端确实没有该分支，再 `git push -u origin main` 重建。**不代表有东西要推** |
| 本地 `git rev-parse origin/main` 与远端 `ls-remote` 不一致 | remote-tracking ref 过期 | 以 `ls-remote` 为准，先 `git fetch` 再判断 |


## 3. 初始化仓库与忽略清单

```bash
git init -b main          # 直接用 main，避免 master→main 改名麻烦
```

写 `.gitignore`——按项目类型选一份基线，宁可多忽略：

```gitignore
# 通用
.DS_Store
Thumbs.db
*.log
.workbuddy/
# ↑ 若本项目要**把项目级 skill 一起入库共享**，就不能整目录忽略，
#   要收窄成：.workbuddy/skills/.workbuddy/ + .workbuddy/memory/
#   详见 §3「项目级 skill 本身也可能被挡住」
node_modules/
__pycache__/
*.py[cod]
.venv/
venv/
dist/
build/

# 敏感（最重要）
.env
.env.*
*.pem
*.key
*.p12
credentials.json
*token*.txt
secrets.*
```

同时做两件检查：

```bash
# 有没有敏感文件已经躺在目录里
find . -not -path './.git/*' \( -name '.env*' -o -name '*.pem' -o -name '*.key' -o -name '*credential*' -o -name '*secret*' \)

# 有没有大文件（GitHub 单文件硬上限 100MB，超过 50MB 就该警告用户）
find . -not -path './.git/*' -type f -size +50M
```

**写完忽略清单要回头审计一遍**——`.gitignore` 最容易误伤交付物：作业 notebook、脚本、
文档被顺手挡住，人却以为已经提交了。2026-09-17 实际踩过：`*.ipynb` 把 `scripts/01.ipynb`
挡了好几天，最后是人工核对时才发现的。`preflight.py` §3 已自动带这项审计。

```bash
# 列出所有被忽略的文件：`!!` 开头的就是被挡住的
git -c core.quotePath=false status --ignored --short -uall
```

里面若出现 `.ipynb` / `.py` / `.md` / `.docx` 这类**交付物**，基本是误伤，先确认再动手；
`.workbuddy/` 之类的工具运行时数据被忽略是有意为之，不用管。

### 项目级 skill 本身也可能被挡住（⚠️ 高频陷阱）

WorkBuddy 的项目级 skill 装在 **`{工作区}/.workbuddy/skills/<name>/`**，即
**skill 的落点取决于工作区设在哪一层**。

| 工作区设在 | skill 真实落点 | 后果 |
|---|---|---|
| **仓库根** `<repo>` | `<repo>/.workbuddy/skills/<name>/` | ✅ 与其它 skill 同层，好管理 |
| `.workbuddy/skills`（设深了一层） | `<repo>/.workbuddy/skills/.workbuddy/skills/<name>/` | ❌ 常被一条 `.workbuddy/skills/.workbuddy/` 忽略规则挡死 |

后果很隐蔽：**skill 本地能用，但永远进不了远端仓库**，用户以为已经备份了。
（2026-09-17 实际踩过：`push-local-repo` 建好后 `git status` 干净、远端也显示"最新"，
真相是它被 `.gitignore` 第 43 行挡住了，老师打开 GitHub 根本看不到。）

**修法一（首选）：把工作区指回仓库根。**
入口在**任务输入框左下角的「选择工作空间」**（官方文档「创建任务」页）。
改完 skill 落点自然回到 `<repo>/.workbuddy/skills/<name>/`。
注意：**改工作区不会移动磁盘上的任何文件**，已建的 skill/日志需要手动搬一次。

```bash
# 搬的时候用「先复制 → diff 比对 → 再删源」，别直接 mv
cp -r "<旧>/" "<新>/" && diff -r "<旧>" "<新>" && rm -rf "<旧>"
```

**修法二：把整目录忽略精确化为只忽略工作日志**（工作区改不了时用）

```gitignore
# .workbuddy/skills/.workbuddy/    ← 删掉这条（原意是挡日志，却连带挡了 skill）
.workbuddy/memory/              ← 换成这条：日志不入库，共享的 skill 入库
```

**修法三（最后手段）：单文件强加。** 脆弱——之后该文件的改动**不会出现在
`git status` / `git status --ignored` 里**，改了也不知道，容易漏提交。

```bash
git add -f ".workbuddy/skills/.workbuddy/skills/<name>/SKILL.md"
```

改 `.gitignore` 或挪 skill 位置都算**改项目约定，先问用户**再动手。


⚠️ **`.gitignore` 的注释必须单独占一行**：`#` 只在行首才算注释，
写成 `*.ipynb  # notebook 不要` 会把整串当成 pattern，规则**静默失效**。

若目标目录是工作区根（例如带 `.workbuddy/skills` 的仓库），先和用户确认**哪些子目录该进版本库**——把所有东西一股脑 `git add .` 是新手最常踩的坑。

## 4. 提交身份

优先用**仓库级**配置，不要动用户全局配置：

```bash
git config --local user.name  "<名字>"
git config --local user.email "<邮箱>"
```

本项目/本用户的既定约定：`robin01-sw <1962342855@qq.com>`。
提交前用 `git config --get user.name` 复核，别在 commit 之后才发现作者错了。

## 5. 提交

```bash
git status -sb            # 先看清全貌
git diff                  # 未暂存的改动
git diff --cached         # 已暂存的改动
git add <具体路径>          # 优先具体路径，慎用 git add .
git diff --cached | grep -iE '(token|secret|password|api[_-]?key|BEGIN .*PRIVATE KEY)'   # 暂存区密钥扫描
git commit -m "<message>"
```

规则：

- **按逻辑拆分 commit**，不要一个 `update` 打包所有东西。一个 commit 讲一件事。
- **message 风格**：动词开头、说清做了什么；需要时正文列点讲改动和参考来源。不要出现 AI 工具署名行。
- 提交前扫一遍暂存区（上面那条 grep），命中就停下来问用户。
- 用户是提交作者。不要用 `--author` 伪造，也不要 `--no-verify` 跳过 hook（除非用户明确要求）。

## 6. 关联或新建远端

**已有远端** → 直接进入 §7；若地址不对：

```bash
git remote -v
git remote add origin <url>          # 没有 remote 时
git remote set-url origin <url>      # 地址需要纠正时
```

**还没有远端仓库** → 两条路，按用户是否登录 gh 选：

**路 A · gh CLI（本机已装，最快，但要先登录）**

```bash
"/c/Program Files/GitHub CLI/gh" auth status     # 未登录则：gh auth login
"/c/Program Files/GitHub CLI/gh" repo create <repo-name> --private --source=. --remote=origin
# 故意不加 --push：让用户先看到 commit 再推
```

**路 B · 用户在网页手建空仓库**

提醒用户：**不要勾选** Add README / .gitignore / license。勾了远端就有 commit，本地 push 会被拒，得先 `git pull --rebase` 才能推。

拿到 URL 后：

```bash
git remote add origin <url>
git push -u origin main              # -u 建立 upstream，之后直接 git push
```

## 7. 推送与校验

```bash
git push -u origin main
```

推完做**三件套校验**（git hash 由内容+历史决定，hash 一致就等价于内容一致）：

```bash
git ls-remote origin HEAD   # 远端 HEAD 的 SHA
git rev-parse HEAD          # 本地 HEAD 的 SHA
git status -sb              # 应显示 "## main...origin/main"（无 ahead/behind）
git remote -v               # 确认 URL 没被临时命令改坏
```

两个 SHA 相同 = 推送成功。不相同或 push 报错 → 见 §8。

## 8. 推不上去时

网络受限场景（`Failed to connect to github.com:443`、`CONNECT tunnel failed 502`、`kex_exchange_identification ... connection abort`）**不要在本 skill 里瞎试**，直接加载 user-level skill：

> **`github-push-restricted-network`**

那里有：诊断顺序表（关键是先测 `git ls-remote`，`curl` 通 ≠ `git` 通）、`pushInsteadOf` 免落盘携带 PAT、`--force-with-lease` 显式期望值写法、以及让用户在宿主电脑用 PortableGit 兜底的完整命令。

本 skill 只负责在它成功后回到 §7 做校验。

## 9. 收尾

1. **提醒 revoke PAT**：GitHub → Settings → Developer settings → Tokens，删掉临时 token。
2. 若做过 force push：所有 commit hash 变了，之前看过仓库页的人需要刷新。
3. 把这次推送的仓库、分支、commit 摘要追加到项目 memory（`<project>/.workbuddy/memory/YYYY-MM-DD.md`）。
4. 若是学习/作品集仓库，额外分享一个 GitHub Pages 链接更稳（不受 commit history 变化影响）。

## 快速命令卡

```bash
# 场景 A 全流程
git init -b main
git config --local user.name "robin01-sw" && git config --local user.email "1962342855@qq.com"
git add <paths> && git commit -m "<message>"
git remote add origin <url>
git push -u origin main

# 忽略清单体检（改完 .gitignore 必跑一次，看有没有把交付物挡住）
git -c core.quotePath=false status --ignored --short -uall

# 场景 C 日常
git status -sb && git add <paths> && git commit -m "<message>" && git push
```

排错速查见 `references/troubleshooting.md`。
