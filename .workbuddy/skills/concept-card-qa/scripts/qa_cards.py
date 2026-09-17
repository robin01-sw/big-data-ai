# -*- coding: utf-8 -*-
"""概念学习卡批量结构校验（stdlib only）。

用法:
    python qa_cards.py <learning-materials 目录> [--plain 150] [--tldr 120] [--refs 5]

退出码: 0 = 无硬失败；1 = 存在硬失败。

--- 两个必须知道的坑（都踩过） ---
1) 题库解析不能用 `options:\\s*\\[([\\s\\S]*?)\\]`。
   选项文本里含转义单引号时（如 'd = [\\'标题\\', \\'正文\\']'），非贪婪匹配会在选项
   内部的第一个 `]` 处提前收尾，把 4 个选项截成 0~2 个，从而**误报**「answer 索引
   越界 / 无选项」。必须借后面的 `answer:` 兜住右边界：
       options:\\s*\\[([\\s\\S]*?)\\]\\s*,\\s*\\n?\\s*answer:
2) 不要用 bash 内联 `python -c` 传正则。Windows Git Bash 下反斜杠会被吞
   （曾出现 `\\{\\s*level` 命中 0 次却查不出原因）。一律写成 .py 文件再执行。
"""

import argparse
import html as H
import re
import sys
from pathlib import Path

# 一些卡把「速读」写成 <p class="one">（一句话） + 紧跟的无 class <p>（一段），
# 且区块容器是 <div class="tldr">，不是 h2。用 h2 做边界会把整段正文算进来。
TLDR_RE = re.compile(r'<div class="tldr">([\s\S]*?)</div>')
PLAIN_RE = re.compile(r'<div class="plain">([\s\S]*?)</div>')
ONE_RE = re.compile(r'<p class="one">([\s\S]*?)</p>')
REST_RE = re.compile(r'<p(?![^>]*class)[^>]*>([\s\S]*?)</p>')
DETAIL_RE = re.compile(r'概念辨析[\s\S]*?</table>')
QBLOCK_RE = re.compile(r'\{\s*level:\s*(\d)')
OPT_RE = re.compile(r'options:\s*\[([\s\S]*?)\]\s*,\s*\n?\s*answer:')
ANS_RE = re.compile(r'answer:\s*(\d+)')
TEXT_RE = re.compile(r"text:\s*'((?:[^'\\]|\\.)*)'")
WHY_RE = re.compile(r"why:\s*'((?:[^'\\]|\\.)*)'")
QREF_RE = re.compile(r'ref:\s*(\d+)')
OPTSTR_RE = re.compile(r"'((?:[^'\\]|\\.)*)'")


def strip_tags(s: str) -> str:
    """去掉 script/style/标签并还原实体，用于字数统计。"""
    s = re.sub(r'<(script|style)[^>]*>[\s\S]*?</\1>', ' ', s)
    return H.unescape(re.sub(r'<[^>]+>', '', s))


def nchar(s: str) -> int:
    """非空白字符数。"""
    return len(re.sub(r'\s+', '', strip_tags(s)))


def parse_questions(s: str) -> list:
    """从内联 JS 里抽出题库。"""
    qs = []
    for m in QBLOCK_RE.finditer(s):
        start = m.start()
        nxt = s.find('{ level:', m.end())
        end = nxt if nxt != -1 else s.find('];', start)
        blk = s[start:end]
        om = OPT_RE.search(blk)
        am = ANS_RE.search(blk)
        tm = TEXT_RE.search(blk)
        wm = WHY_RE.search(blk)
        rm = QREF_RE.search(blk)
        opts = [H.unescape(o) for o in OPTSTR_RE.findall(om.group(1))] if om else []
        qs.append(dict(
            level=int(m.group(1)),
            text=H.unescape(tm.group(1)) if tm else '',
            options=opts,
            answer=int(am.group(1)) if am else -1,
            why=H.unescape(wm.group(1)) if wm else '',
            ref=int(rm.group(1)) if rm else 0,
        ))
    return qs


def check_card(p: Path, limits: dict):
    """返回 (硬失败列表, 告警列表, 指标 dict)。"""
    s = p.read_text(encoding='utf-8')
    fails, warns = [], []
    m = {}

    # 参考来源
    refs = re.findall(r'id="ref-(\d+)"', s)
    refids = sorted({int(x) for x in refs})
    m['refs'] = len(refids)
    if len(refids) < limits['refs']:
        fails.append(f"来源仅 {len(refids)} 条（需 ≥{limits['refs']}）")

    # 角标 ↔ 来源 双向对应
    cites = sorted({int(x) for x in re.findall(r'href="#ref-(\d+)"', s)})
    dangling = [c for c in cites if c not in refids]
    if dangling:
        fails.append(f'悬空角标 {dangling}（正文引了但来源列表里没有）')
    orphan = [r for r in refids if r not in cites]
    if orphan:
        # 有来源条但正文/题库从不引用：属真实缺陷（卡片自称「N 条可核查来源」）
        fails.append(f'孤立来源 {orphan}（列了但正文从不引用，需补挂载点或删除）')

    # 题库
    qs = parse_questions(s)
    m['nq'] = len(qs)
    if len(qs) != 8:
        fails.append(f'自测题 {len(qs)} 道（需恰好 8）')
    lv = {}
    for q in qs:
        lv[q['level']] = lv.get(q['level'], 0) + 1
    m['lv'] = ''.join(str(lv.get(i, 0)) for i in range(4))
    for i in range(4):
        if lv.get(i, 0) != 2:
            fails.append(f'L{i} 有 {lv.get(i, 0)} 道（需 2）')
    for k, q in enumerate(qs, 1):
        if not q['options']:
            fails.append(f'Q{k} 解析不到选项（若选项含转义单引号，先确认 OPT_RE 是否用了 answer: 锚点）')
        elif not (0 <= q['answer'] < len(q['options'])):
            fails.append(f'Q{k} answer={q["answer"]} 越界（共 {len(q["options"])} 项）')
        if not q['text']:
            fails.append(f'Q{k} 题干为空')
        if not q['why']:
            fails.append(f'Q{k} 解析为空')
        if q['ref'] and q['ref'] not in refids:
            fails.append(f'Q{k} 指向不存在的来源 [{q["ref"]}]')

    # 概念辨析
    dm = DETAIL_RE.search(s)
    rows = len(re.findall(r'<tr', dm.group(0))) - 1 if dm else 0
    m['desc'] = rows
    if rows < 3:
        fails.append(f'辨析表 {rows} 行（需 ≥3）')

    # 内联 SVG
    m['svg'] = len(re.findall(r'<svg', s))
    if m['svg'] < 1:
        fails.append('缺内联 SVG')

    # 60 秒速读
    td = TLDR_RE.search(s)
    m['tldr'] = 0
    if not td:
        fails.append('缺 tldr 区块')
    else:
        blk = td.group(1)
        one = ONE_RE.search(blk)
        rest = REST_RE.findall(blk)
        c1 = nchar(one.group(1)) if one else 0
        c2 = nchar(rest[0]) if rest else 0
        m['tldr'] = c1 + c2
        if not one:
            fails.append('tldr 缺 p.one 一句话')
        if c1 > 30:
            warns.append(f'速读一句话 {c1} 字（≤30）')
        if c2 > 90:
            warns.append(f'速读一段 {c2} 字（≤90）')
        if c1 + c2 > limits['tldr']:
            warns.append(f"速读合计 {c1 + c2} 字（≤{limits['tldr']}）")

    # 通俗理解
    pl = PLAIN_RE.search(s)
    m['plain'] = 0
    if not pl:
        fails.append('缺 .plain 通俗理解')
    else:
        blk = pl.group(1)
        body = re.sub(r'<span class="label">[\s\S]*?</span>', '', blk)
        m['plain'] = nchar(body)
        if m['plain'] > limits['plain']:
            warns.append(f"通俗理解 {m['plain']} 字（≤{limits['plain']}）")
        if re.search(r'<(strong|b)[\s>]', body):
            fails.append('通俗理解含加粗标签')
        if '我' in strip_tags(body):
            fails.append('通俗理解含第一人称「我」')
        if 'AI 辅助整理 · 本人已核查' not in blk:
            fails.append('通俗理解 label 不规范')

    # footer 双返回链接
    ft = s[s.rfind('<footer'):]
    if '../index.html' not in ft:
        fails.append('footer 缺「返回学习地图」链接')
    if 'href="index.html"' not in ft:
        fails.append('footer 缺「返回概念目录」链接')
    if '概念库第' not in ft:
        fails.append('footer 缺编号说明')

    # 无外部 CDN 依赖
    cdn = re.findall(r'<script[^>]+src=|<link[^>]+href="https?://', s)
    if cdn:
        fails.append(f'存在外部资源依赖 {cdn[:2]}')

    # 标签配对
    for tag in ['div', 'table', 'ol', 'ul', 'details', 'svg', 'tr', 'td']:
        o = len(re.findall(r'<' + tag + r'[\s>]', s))
        c = len(re.findall(r'</' + tag + r'>', s))
        if o != c:
            fails.append(f'<{tag}> 不配对 {o}/{c}')

    return fails, warns, m


def main():
    ap = argparse.ArgumentParser(description='概念学习卡批量结构校验')
    ap.add_argument('dir', help='learning-materials 目录')
    ap.add_argument('--plain', type=int, default=150, help='通俗理解字数上限（默认 150）')
    ap.add_argument('--tldr', type=int, default=120, help='速读合计字数上限（默认 120）')
    ap.add_argument('--refs', type=int, default=5, help='来源条数下限（默认 5）')
    ap.add_argument('--quiet', action='store_true', help='只打印失败项')
    a = ap.parse_args()

    root = Path(a.dir)
    if not root.is_dir():
        print(f'目录不存在：{root}', file=sys.stderr)
        return 2

    limits = dict(plain=a.plain, tldr=a.tldr, refs=a.refs)
    cards = sorted(p for p in root.glob('*.html') if p.name != 'index.html')
    if not cards:
        print(f'{root} 下没有找到卡片文件', file=sys.stderr)
        return 2

    all_fails, all_warns = [], []
    if not a.quiet:
        print('=' * 96)
        print(f"{'卡片':<34}{'来源':>4}{'题数':>5}{'L0-L3':>8}{'辨析':>5}{'SVG':>5}{'速读':>6}{'通俗':>6}")
        print('=' * 96)

    for p in cards:
        f, w, m = check_card(p, limits)
        all_fails += [f'{p.name}: {x}' for x in f]
        all_warns += [f'{p.name}: {x}' for x in w]
        if not a.quiet:
            print(f"{p.name[:-5]:<34}{m['refs']:>4}{m['nq']:>5}{m['lv']:>8}"
                  f"{m['desc']:>5}{m['svg']:>5}{m['tldr']:>6}{m['plain']:>6}")

    # 站内链接可达性（含两个索引页）
    missing = []
    for p in cards + [root / 'index.html', root.parent / 'index.html']:
        if not p.exists():
            continue
        for h in sorted(set(re.findall(r'href="([^"]+)"', p.read_text(encoding='utf-8')))):
            if h.startswith(('http', 'mailto:', 'javascript:', '#')):
                continue
            if not (p.parent / h).resolve().exists():
                missing.append(f'{p.parent.name}/{p.name} -> {h}')

    if not a.quiet:
        print('=' * 96)
        print(f'\n卡片数：{len(cards)}')
        print(f'死链：{len(missing)}')
        for x in missing:
            print('  MISS', x)

    print(f'\n{"#" * 96}')
    print(f'硬失败 {len(all_fails)} 项：')
    for x in all_fails:
        print('  x', x)
    print(f'\n告警 {len(all_warns)} 项：')
    for x in all_warns:
        print('  !', x)
    print()
    return 1 if (all_fails or missing) else 0


if __name__ == '__main__':
    sys.exit(main())
