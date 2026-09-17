#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""push-local-repo 的只读体检脚本。

用法:
    python preflight.py [目标目录]        # 默认当前目录

只做读取和报告，不执行任何写操作（不 add / 不 commit / 不 push / 不改配置）。
输出结构化的「环境 + 仓库 + 风险 + 建议下一步」，供 SKILL.md 第 1 步使用。
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys

# ---------------------------------------------------------------- 基础工具

def _fix_stdout() -> None:
    """Windows 控制台按 UTF-8 输出，避免中文乱码。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def sh(args: list[str], cwd: str | None = None, timeout: int = 20) -> tuple[int, str]:
    """执行命令，返回 (returncode, 合并后的输出)。异常一律转成非零返回码。"""
    try:
        p = subprocess.run(
            args, cwd=cwd, timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        return p.returncode, (p.stdout or "").strip()
    except subprocess.TimeoutExpired:
        return 124, f"<超时 {timeout}s>"
    except FileNotFoundError:
        return 127, "<命令不存在>"
    except Exception as exc:  # noqa: BLE001
        return 1, f"<{type(exc).__name__}: {exc}>"


def head(text: str, n: int = 15) -> str:
    lines = text.splitlines()
    if len(lines) <= n:
        return text
    return "\n".join(lines[:n]) + f"\n... (共 {len(lines)} 行，已截断)"


def section(title: str) -> None:
    print(f"\n{'=' * 4} {title} {'=' * 4}")


ADVICE: list[str] = []


def advise(cmd: str) -> None:
    ADVICE.append(cmd)


# ---------------------------------------------------------------- 环境探测

def find_git() -> str | None:
    found = shutil.which("git")
    if found:
        return found
    home = os.path.expanduser("~")
    pattern = os.path.join(
        home, ".workbuddy", "binaries", "PortableGit", "versions", "*",
        "mingw64", "bin", "git.exe",
    )
    hits = sorted(glob.glob(pattern))
    return hits[-1] if hits else None


def find_gh() -> str | None:
    found = shutil.which("gh")
    if found:
        return found
    for cand in (
        r"C:\Program Files\GitHub CLI\gh.exe",
        r"C:\Program Files (x86)\GitHub CLI\gh.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "GitHubCLI", "gh.exe"),
    ):
        if cand and os.path.isfile(cand):
            return cand
    return None


def probe_environment(git: str | None, gh: str | None) -> None:
    section("1. 环境")
    if git:
        _, ver = sh([git, "--version"])
        print(f"git   : {git}")
        print(f"        {ver}")
    else:
        print("git   : 未找到！需要安装 git 或定位 PortableGit")
        print("        参考路径: %USERPROFILE%\\.workbuddy\\binaries\\PortableGit\\versions\\<ver>\\mingw64\\bin\\git.exe")

    if gh:
        _, ver = sh([gh, "--version"])
        print(f"gh    : {gh}")
        print(f"        {ver.splitlines()[0] if ver else ''}")
        code, status = sh([gh, "auth", "status"], timeout=25)
        if code == 0:
            print("        登录状态: 已登录 → 可用 gh repo create 一键建远端")
        else:
            print("        登录状态: 未登录 → 需要 `gh auth login`，或让用户在网页手建空仓库")
    else:
        print("gh    : 未安装（不影响，走网页手建远端即可）")

    proxy = {
        k: v for k, v in os.environ.items()
        if k.lower() in ("http_proxy", "https_proxy", "all_proxy") and v
    }
    print(f"代理  : {proxy if proxy else '无'}"
          f"{'  ← 代理可能是 git push 被拦的原因' if proxy else ''}")


# ---------------------------------------------------------------- 仓库状态

def probe_repo(root: str, git: str) -> bool:
    section("2. 仓库状态")
    code, _ = sh([git, "rev-parse", "--is-inside-work-tree"], cwd=root, timeout=10)
    if code != 0:
        print("状态  : 不是 git 仓库 → 走「场景 A：全新目录」")
        print("下一步: git init -b main  然后写 .gitignore")
        advise("git init -b main")
        return False

    _, top = sh([git, "rev-parse", "--show-toplevel"], cwd=root)
    print(f"仓库根: {top}")
    if os.path.normcase(os.path.normpath(top)) != os.path.normcase(os.path.normpath(root)):
        print(f"注意  : 目标目录是子目录，实际仓库根在上方（{top}）")

    _, branch = sh([git, "rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    code, _ = sh([git, "rev-parse", "--verify", "HEAD"], cwd=root)
    print(f"分支  : {branch}{'' if code == 0 else '   (还没有任何 commit → 首次提交)'}")

    _, author = sh([git, "config", "--get", "user.name"], cwd=root)
    _, email = sh([git, "config", "--get", "user.email"], cwd=root)
    print(f"作者  : {author or '<未配置>'} <{email or '<未配置>'}>")
    if not author or not email:
        print("        需要先配仓库级身份:")
        advise('git config --local user.name "<名字>" && git config --local user.email "<邮箱>"')

    _, remotes = sh([git, "remote", "-v"], cwd=root)
    print("远端  :")
    if remotes:
        for line in remotes.splitlines():
            print(f"        {line}")
        if "origin" not in remotes:
            print("        没有 origin → 需要 git remote add origin <url>")
    else:
        print("        <无> → 走「场景 B：有本地仓库，缺远端」")
        print("        两条路: (a) gh repo create <name> --private --source=. --remote=origin")
        print("                (b) 用户在网页建空仓库（不要勾 README/LICENSE）再 git remote add")

    _, upstream = sh([git, "status", "-sb"], cwd=root)
    print("跟踪  :")
    first = upstream.splitlines()[0] if upstream else ""
    print(f"        {first}")
    if "..." not in first:
        print("        (无 upstream → 首次推送用 git push -u origin <branch>)")
    elif "[gone]" in first:
        print("        !! upstream 已失效：远端同名分支不存在（被删或改名）")
        print("           先 git fetch origin 确认，再用 git push -u origin <branch> 重建")
        advise("git fetch origin && git push -u origin " + branch)

    # 与远端的差异（只读，需要网络；失败不阻塞）
    if remotes and "origin" in remotes:
        code, ahead = sh([git, "rev-list", "--count", "@{u}..HEAD"], cwd=root, timeout=30)
        if code == 0:
            print(f"ahead : {ahead} 个本地 commit 未推送")
        else:
            print("ahead : <无法计算，可能需要先 fetch 或网络不通>")
    return True


# ---------------------------------------------------------------- 变更与风险

# 只跳过体积大且不该进版本库的目录。注意不要跳过 .workbuddy——有些项目
# 的正文内容（skills / memory）就在里面，跳过会漏扫。
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".idea", ".vscode"}

SENSITIVE_NAMES = (".env", ".env.local", ".env.production")
SENSITIVE_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".keystore", ".sqlite", ".db")
SENSITIVE_KEYWORDS = ("credential", "secret", "token", "id_rsa", "password", ".npmrc", ".pgpass")

SECRET_PATTERN = (
    r"(token|secret|password|passwd|api[_-]?key|BEGIN [A-Z ]*PRIVATE KEY|"
    r"ghp_[A-Za-z0-9]{20,}|github_pat_|sk-[A-Za-z0-9]{20,})"
)


def is_sensitive(name: str) -> bool:
    low = name.lower()
    if low in SENSITIVE_NAMES or low.endswith(SENSITIVE_SUFFIXES):
        return True
    return any(k in low for k in SENSITIVE_KEYWORDS)


def probe_changes(root: str, git: str) -> None:
    section("3. 变更清单")
    _, status = sh([git, "status", "--porcelain"], cwd=root)
    if not status:
        print("工作区: 干净，没有待提交改动")
    else:
        lines = status.splitlines()
        untracked = [l for l in lines if l.startswith("??")]
        staged = [l for l in lines if l[:2].strip() and not l.startswith("??")]
        print(f"工作区: 共 {len(lines)} 项改动（已暂存 {len(staged)}，未跟踪 {len(untracked)}）")
        print(head("\n".join(lines), 20))

    _, staged = sh([git, "diff", "--cached", "--name-only"], cwd=root)
    if staged:
        print("\n已暂存文件:")
        print(head(staged, 20))
        code, hits = sh(
            [git, "diff", "--cached", "-U0"],
            cwd=root, timeout=30,
        )
        if code == 0 and hits:
            import re
            matched = [
                l for l in hits.splitlines()
                if l.startswith("+") and re.search(SECRET_PATTERN, l, re.IGNORECASE)
            ]
            if matched:
                print("\n!! 暂存区疑似含密钥，提交前必须处理:")
                print(head("\n".join(matched), 10))


# 被 .gitignore 挡住的文件里出现这些扩展名，多半是误伤：作业 notebook / 脚本 /
# 文档被顺手忽略掉，人却以为「已经提交了」。2026-09-17 实际踩过——
# `*.ipynb` 把 scripts/01.ipynb 挡了好几天，直到人工核对才发现。
DELIVERABLE_SUFFIXES = (
    ".ipynb", ".py", ".js", ".ts", ".md", ".txt", ".html",
    ".docx", ".pdf", ".xlsx", ".pptx", ".sql", ".yaml", ".yml",
)


def probe_ignored(root: str, git: str) -> None:
    """列出被忽略的文件：它们永远不会被 git add 到，最容易「以为传上去了其实没有」。"""
    # core.quotePath=false：否则中文路径会输出成八进制转义，看不出到底是哪个文件
    code, out = sh(
        [git, "-c", "core.quotePath=false", "status", "--ignored", "--short", "-uall"],
        cwd=root, timeout=30,
    )
    if code != 0:
        print("\n被忽略文件: <无法获取>")
        return
    ignored = [l[3:].strip() for l in out.splitlines() if l.startswith("!!")]
    if not ignored:
        print("\n被忽略文件: 无")
        return
    print(f"\n被忽略文件: {len(ignored)} 个（这些**不会**进库，git add 也加不进去）")
    print(head("\n".join(ignored), 15))
    # `.workbuddy/` 下的东西被忽略基本都是有意的（工具运行时数据），不算误伤，不报噪音。
    suspect = [
        p for p in ignored
        if p.lower().endswith(DELIVERABLE_SUFFIXES) and ".workbuddy/" not in p.lower()
    ]
    if suspect:
        print("\n!! 其中含代码 / notebook / 文档，可能是误伤（先确认它是否真该被忽略）:")
        print(head("\n".join(suspect), 10))


def probe_risks(root: str, git: str) -> None:
    section("4. 风险扫描")
    gi = os.path.join(root, ".gitignore")
    if os.path.isfile(gi):
        try:
            with open(gi, "r", encoding="utf-8", errors="replace") as fh:
                n = len([l for l in fh if l.strip() and not l.startswith("#")])
            print(f".gitignore: 存在（{n} 条规则）")
        except OSError as exc:
            print(f".gitignore: 存在但读取失败 ({exc})")
    else:
        print(".gitignore: 不存在 → 强烈建议先创建（尤其含 .env / 密钥 / node_modules 时）")

    # 已跟踪的敏感文件（最危险：已经进了历史）
    _, tracked = sh([git, "ls-files"], cwd=root)
    tracked_sensitive = [p for p in tracked.splitlines() if p and is_sensitive(os.path.basename(p))]
    if tracked_sensitive:
        print("\n!! 已被 git 跟踪的敏感文件（删文件也删不掉历史，需 revoke 密钥）:")
        print(head("\n".join(tracked_sensitive), 10))

    sensitive: list[str] = []
    big: list[str] = []
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            scanned += 1
            if scanned > 40000:
                break
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            if is_sensitive(fn):
                sensitive.append(rel)
            try:
                if os.path.getsize(full) > 50 * 1024 * 1024:
                    big.append(f"{rel}  ({os.path.getsize(full) / 1048576:.1f} MB)")
            except OSError:
                pass
        if scanned > 40000:
            print(f"(目录过大，扫描在 {scanned} 个文件处停止)")
            break

    print(f"\n扫描范围: {scanned} 个文件（已跳过 {'/'.join(sorted(SKIP_DIRS))}）")
    if sensitive:
        print("\n疑似敏感文件（确认已进 .gitignore，再执行 git add）:")
        print(head("\n".join(sensitive), 15))
    else:
        print("疑似敏感文件: 无")

    if big:
        print("\n!! 大文件（GitHub 单文件硬上限 100MB，>50MB 建议用 Git LFS 或移出版本库）:")
        print(head("\n".join(big), 10))
    else:
        print("大文件(>50MB): 无")


# ---------------------------------------------------------------- 结论

def report() -> None:
    section("5. 建议下一步")
    if not ADVICE:
        print("仓库状态看起来正常。按 SKILL.md §5 提交 → §7 推送 → §7 三件套校验。")
        print("推送前记得把 commit 清单和远端地址给用户确认。")
    else:
        for i, a in enumerate(ADVICE, 1):
            print(f"{i}. {a}")
    print("\n提示: push 报网络错 → 换用 `github-push-restricted-network` skill。")


def main() -> int:
    _fix_stdout()
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
    print("push-local-repo · 只读体检")
    print(f"目标目录: {root}")
    if not os.path.isdir(root):
        print(f"错误: 目录不存在 → {root}")
        return 2

    git = find_git()
    gh = find_gh()
    probe_environment(git, gh)

    if not git:
        print("\n没有 git，后续检查无法进行。")
        return 2

    if probe_repo(root, git):
        probe_changes(root, git)
        probe_ignored(root, git)
        probe_risks(root, git)
    report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
