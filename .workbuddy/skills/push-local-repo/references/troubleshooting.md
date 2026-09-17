# 排错速查（push-local-repo）

按「报错 → 原因 → 解法」查。网络层的疑难杂症（超时、隧道被拦、PAT）**不在本文件**，去 user-level skill `github-push-restricted-network`。

## 提交阶段

| 报错 | 原因 | 解法 |
|---|---|---|
| `fatal: not a git repository` | 目录不在仓库内 | `git init -b main`，或 `cd` 到仓库根；先用 `git rev-parse --show-toplevel` 确认根在哪 |
| `Author identity unknown` / `Please tell me who you are` | 没配 user.name/user.email | `git config --local user.name "..."` + `user.email` |
| `nothing to commit, working tree clean` | 改动已被提交，或文件被 `.gitignore` 挡住 | `git status --porcelain` 确认；被忽略的文件用 `git check-ignore -v <file>` 查明是哪条规则 |
| `git add` 后文件没进暂存区 | `.gitignore` 命中或路径写错 | `git check-ignore -v <path>`；确认路径，注意 shell 通配符展开 |
| 想撤销 `git add` | 误暂存 | `git restore --staged <path>`（保留工作区改动） |
| 想改最后一次 commit message | 打错字 | `git commit --amend -m "<新的>"`（**仅限还没 push**；已 push 则等于改写历史，要用户确认） |
| 误提交了敏感文件，还没 push | — | `git restore --staged <file>` → 加进 `.gitignore` → 重新 commit。**若已 push 或已进历史：删文件无效，必须去平台 revoke 该密钥** |

## 远端关联阶段

| 报错 | 原因 | 解法 |
|---|---|---|
| `'origin' already exists` | 重复 add | `git remote set-url origin <url>` |
| `remote origin already exists` 但地址是错的 | 之前配错了 | `git remote -v` 看当前值 → `git remote set-url origin <正确url>` |
| 远端页面已有 README，push 被拒 | 远端有本地没有的 commit | `git pull --rebase origin main` 后再 push；建仓库时别勾 README/LICENSE 可避免 |
| `repository not found`（HTTPS） | 仓库名/owner 拼错，或 token 无该仓库权限 | 核对 URL；确认 PAT 勾了 `repo` scope，且对私有仓库有授权 |

## 推送阶段

| 报错 | 原因 | 解法 |
|---|---|---|
| `src refspec main does not match any` | 本地还没有 commit，或分支名不是 main | `git log --oneline -1` 确认有提交；用 `git branch --show-current` 看真实分支名 |
| `error: src refspec origin does not match any` | 把 URL 当第一个位置参数了（`git push <URL>` 不是这个语法） | 用 `git push origin main`，或改成 `git remote set-url` / `pushInsteadOf` 写法 |
| `failed to push some refs ... non-fast-forward` | 远端领先 | `git pull --rebase origin main` 再 push。**不要**上 `--force` |
| `stale info` / `remote ref changed` | `--force-with-lease` 的期望值不对 | 先 `git ls-remote origin HEAD` 取真实 SHA，显式写进 `--force-with-lease=refs/heads/main:<SHA>` |
| `updates were rejected because the remote contains work` | 同上（远端领先） | pull --rebase |
| `remote: Permission to ... denied` | 凭证无权限 / 用错账号 | 检查 PAT scope 与账号；`git remote -v` 看是否 URL 里嵌了旧 token |
| `Support for password authentication was removed` | 用了账号密码而非 token | 改用 PAT（见受限网络 skill） |

## 校验阶段

| 现象 | 判断 | 处理 |
|---|---|---|
| `git ls-remote origin HEAD` 与 `git rev-parse HEAD` 相同 | **成功**（hash 由内容+历史决定） | 完成，进入收尾 |
| `git status -sb` 显示 `ahead N` | 还有 N 个 commit 没推上去 | 重新 push，或检查是不是推错分支 |
| `git status -sb` 显示 `behind N` | 本地落后远端 | `git pull --rebase` |
| 本地看不到远端新分支 | remote-tracking ref 过期 | `git fetch origin` |
| push 显示成功但网页没变 | CDN 缓存 / 看的是旧分支 / 默认分支不是它 | 刷新；核对仓库的默认分支设置 |

## 一些容易搞混的点

- **`git pull` 默认会不会产生 merge commit**：建议 `git pull --rebase`，历史干净且不会有意外 merge。
- **`main` vs `master`**：`git init -b main` 一步到位；已经是 master 想改名 → `git branch -m master main`（本地）＋远端改名后 `git push -u origin main` 并删除远端 master。
- **`gh` 没登录不等于不能推**：`gh` 只用于「建仓库」这类 API 操作，push 走 git 自身的凭证。
- **`.gitignore` 对已跟踪文件无效**：已跟踪的文件需要 `git rm --cached <file>` 才停止跟踪。
