#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_lesson_assignment.py —— 概念编号 ↔ 课次归属 的跨文档一致性校验

问题背景
--------
一套「学习地图 + 概念目录页 + 概念卡」的材料里，同一个概念的课次归属会同时出现在
至少三个地方：

  1. 地图 HTML 的概念表     <tr><td>13</td><td><a href="...">文本分类</a></td><td>第 3 课</td>
  2. 地图 MD   的概念表      | 13 | [文本分类](...) | 第 3 课 | ...
  3. 目录页的分课次卡片分组   <h3>第 3 课 · ...</h3> ... <div class="num">概念 13</div>

三者由不同时间、不同批次的编辑维护，**极易漂移**。实测踩过一次：课程安排里第 3 课的
课堂产出物是「分类器 + 评估报告」，但构成它的概念 13「文本分类」、14「模型评估」
却标在第 4 课——地图、MD、目录页三处一起错，任何单文档抽查都发现不了。

用法
----
    python check_lesson_assignment.py <地图HTML> <地图MD> <目录页HTML>

    例：
    python check_lesson_assignment.py \
        python-ai-4lessons/index.html \
        python-ai-4lessons/python-ai-4-lessons-map.md \
        python-ai-4lessons/learning-materials/index.html

退出码：0 = 三处一致；1 = 存在不一致或覆盖不全；2 = 参数/文件问题。

注意：本脚本只比对「编号 → 课次」的映射，不判断归属**本身**是否合理。
归属合理性要靠人看（例如产出物在哪一课、前置概念是否真的更早）。
"""

import re
import sys
import pathlib


# ---------------------------------------------------------------- 抽取器

def norm_lesson(raw: str) -> str:
    """把各种写法归一到可比较的标记。

    '第 3 课' / '第3课' / '第 3 课 · AI 基础' → 'L3'
    '跨课连接' / '跨课'                        → 'CROSS'
    """
    t = re.sub(r'\s+', '', raw)
    # 先判「跨课」：枢纽卡的标题常写成「跨课连接 · 第 4 课之后读」，
    # 若先匹配「第 N 课」会被标题里的「第 4 课之后读」抢走，误判成 L4。
    if '跨课' in t or '枢纽' in t:
        return 'CROSS'
    m = re.search(r'第([0-9一二三四五六七八九十]+)课', t)
    if m:
        d = m.group(1)
        cn = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
              '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
        return 'L%d' % (int(d) if d.isdigit() else cn.get(d, 0))
    return '?' + t[:10]


def from_map_html(path: pathlib.Path) -> dict:
    """地图 HTML 概念表：<tr><td>NN</td><td><a href="...">名</a></td><td>课次</td>"""
    s = path.read_text(encoding='utf-8')
    out = {}
    for m in re.finditer(
            r'<tr>\s*<td>(\d{2})</td>\s*<td>\s*<a[^>]*>([^<]+)</a>\s*</td>\s*<td>([^<]+)</td>',
            s):
        out[m.group(1)] = (norm_lesson(m.group(3)), m.group(2).strip())
    return out


def from_map_md(path: pathlib.Path) -> dict:
    """地图 MD 概念表：| 13 | [文本分类](path) | 第 3 课 | ..."""
    s = path.read_text(encoding='utf-8')
    out = {}
    for line in s.splitlines():
        m = re.match(r'\|\s*(\d{2})\s*\|\s*\[([^\]]+)\][^|]*\|\s*([^|]+?)\s*\|', line)
        if m:
            out[m.group(1)] = (norm_lesson(m.group(3)), m.group(2).strip())
    return out


def from_dir_page(path: pathlib.Path) -> dict:
    """目录页：<h3>课次标题</h3> ... 块内出现的 <div class="num">概念 NN</div>"""
    s = path.read_text(encoding='utf-8')
    out = {}
    # 按 h3 切块
    blocks = re.split(r'<h3[^>]*>', s)
    for b in blocks[1:]:
        head = b.split('</h3>')[0]
        body = b.split('</h3>', 1)[1] if '</h3>' in b else ''
        lesson = norm_lesson(re.sub(r'<[^>]+>', ' ', head))
        for m in re.finditer(r'<div class="num">\s*概念\s*(\d{2})', body):
            out[m.group(1)] = (lesson, '')
    return out


# ---------------------------------------------------------------- 主流程

def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2

    targets = [
        ('地图 HTML', pathlib.Path(argv[1]), from_map_html),
        ('地图 MD', pathlib.Path(argv[2]), from_map_md),
        ('目录页', pathlib.Path(argv[3]), from_dir_page),
    ]

    for label, p, _ in targets:
        if not p.exists():
            print('找不到文件：%s（%s）' % (p, label))
            return 2

    data = {}
    for label, p, fn in targets:
        data[label] = fn(p)

    for label, d in data.items():
        if not d:
            print('!! %s 未解析出任何概念，请检查表格式是否与脚本预期一致' % label)
            return 2

    nums = sorted(set().union(*[set(d) for d in data.values()]))
    labels = [t[0] for t in targets]

    w = 8
    head = '概念'.ljust(4) + '名称'.ljust(w + 4) + ''.join(l.ljust(w + 4) for l in labels)
    print(head)
    print('-' * len(head))

    def disp(s):
        """中文按 2 列宽计算的显示宽度。"""
        return sum(2 if ord(c) > 0x2E80 else 1 for c in s)

    bad = 0
    for n in nums:
        vals = [data[l].get(n, ('—', ''))[0] for l in labels]
        name = next((data[l][n][1] for l in labels if n in data[l] and data[l][n][1]), '')
        for l in labels:
            if n in data[l] and len(data[l][n][1]) > len(name):
                name = data[l][n][1]
        pad = ' ' * max(2, w + 4 - disp(name))
        row = n.ljust(4) + name + pad + ''.join(v.ljust(w + 4) for v in vals)
        flag = ''
        uniq = set(v for v in vals if v != '—')
        if len(uniq) > 1:
            flag = '   <== 不一致'
            bad += 1
        elif '—' in vals:
            flag = '   <== 有文档未覆盖'
            bad += 1
        print(row + flag)

    print()
    if bad:
        print('发现 %d 处问题。' % bad)
        print('提示：不一致不代表某一处一定错——先确认「课堂产出物在哪一课」，')
        print('      再让构成该产出物的概念归到同一课（或更早的课）。')
        return 1

    print('三处一致，共 %d 个概念。' % len(nums))
    print('（注意：脚本只验证「编号→课次」映射一致，不判断归属本身是否合理。）')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
