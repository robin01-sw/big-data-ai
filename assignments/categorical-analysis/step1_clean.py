# -*- coding: utf-8 -*-
"""
第 1 步：数据读取 + 清理 + 类别转化
------------------------------------
输入：类别变量练习数据.csv（原始问卷文本，父亲工作 / 母亲工作 两列自由填答）
输出：
    outputs/cleaned_data.csv   清理后的明细（含原始值、清理值、职业大类）
    outputs/mapping_table.csv  原始单位名 → 职业大类 的对照表（便于人工核对）
    outputs/step1_report.txt   清理过程记录

说明：
    原始数据是"单位名称"这种自由文本，不是可以直接统计的类别变量。
    所以必须先做两件事：
      (1) 清理：去空格、去换行、空值统一标记；
      (2) 转化：按填答内容把每个单位名归到一个"职业大类"，
          这一步是可核查的规则 + 个别手工修正（见 OVERRIDES）。
"""

import os
import re
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "类别变量练习数据.csv")
OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

log_lines = []


def log(msg=""):
    print(msg)
    log_lines.append(str(msg))


# ---------------------------------------------------------------- 1. 读取
def read_raw(path):
    """文件可能是 UTF-8，也可能是 Excel 另存的 GBK，逐个编码尝试。"""
    for enc in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
        try:
            df = pd.read_csv(path, encoding=enc, dtype=str)
            log(f"[读取] 编码 = {enc}，行数 = {len(df)}，列 = {list(df.columns)}")
            return df
        except UnicodeDecodeError:
            continue
    raise RuntimeError("无法识别文件编码")


df = read_raw(RAW)

# 统一列名，避免空格/全角差异
df.columns = [c.strip() for c in df.columns]

# ---------------------------------------------------------------- 2. 清理
# 单元格里存在 Excel 换行（"市经济合作局\n"），先去掉所有空白字符（含换行、全角空格）
def clean_text(s):
    if pd.isna(s):
        return ""
    s = str(s)
    s = s.replace("\u3000", " ")          # 全角空格
    s = re.sub(r"\s+", "", s)             # 去掉所有空白，包括换行
    s = s.strip(" ,，、;；")
    return s


for col in df.columns:
    df[col] = df[col].map(clean_text)

# 空字符串 → 缺失值（NA）
df = df.replace("", pd.NA)
log(f"[清理] 去空白后，父亲工作缺失 {df['父亲工作'].isna().sum()} 条，"
    f"母亲工作缺失 {df['母亲工作'].isna().sum()} 条")

# 完全重复的记录：检出不删除，只标注（可能是两个不同家庭填了同样的单位）
df["是否重复"] = df.duplicated(subset=["父亲工作", "母亲工作"], keep=False)
n_dup = df["是否重复"].sum()
log(f"[清理] 完全重复的记录 {n_dup} 条（保留，仅标注；可能为不同家庭，不作为错误删除）")

# ---------------------------------------------------------------- 3. 类别转化
# 职业大类的划分依据"就业单位性质"：公共部门 / 国企 / 民营 / 个体 / 家庭主妇 / 无业未填
CATS = [
    "公共部门（党政机关·事业单位）",
    "国有企业",
    "民营企业",
    "个体经营",
    "家庭主妇",
    "无业·未填",
]

# 3.1 个别需要人工判断的原始值（关键词规则会判错，必须手工指定）
OVERRIDES = {
    # 名字里带"局"但是企业（工程局、铁路局这类），不能当党政机关
    "陕西省水利水电第三工程局": "国有企业",
    "中铁六局太原铁路建设公司": "国有企业",
    "中国兵器工业公司三冶炼": "国有企业",
    "二十一冶": "国有企业",
    "银光聚银化工有限公司": "国有企业",     # 兵器工业集团下属企业
    "市给排水（集团）有限公司": "国有企业",  # 市政公用国企
    "农行XXX县支行": "国有企业",            # 国有大型银行
    "广东省中海油": "国有企业",              # 中国海油（央企）省级分公司
    # 带"中心"但是个体/民营门店
    "区建豪汽修中心": "个体经营",
    "万盛体能拓展中心鑫多米便利店": "个体经营",
    # 填答内容不是有效单位，无法判断就业状态
    "家庭父母": "无业·未填",
    "家庭父亲": "无业·未填",
    "无": "无业·未填",
}

# 3.2 关键词规则（按顺序匹配，先命中先归类；顺序本身会影响结果，所以把"更像机构"的放前面）
RULES = [
    ("家庭主妇", ["家庭主妇", "全职太太"]),
    # 个体经营：以门面/店铺/摊位的字号命名，通常没有"公司"字样
    ("个体经营", ["个体", "店", "馆", "食府", "菜市场", "菜市", "浴", "足", "便利店",
                  "烟酒", "杂粮", "农资", "药", "工具", "汽修"]),
    ("国有企业", ["中铁", "中国兵器", "冶金", "建设集团", "给排水", "支行", "银行",
                  "供电", "电网", "烟草", "邮政", "铁路局", "工程局"]),
    # 公共部门：机关名称后缀 + 学校医院等事业单位
    ("公共部门（党政机关·事业单位）",
     ["局", "委员会", "委", "办", "政府", "法院", "检察院", "监狱", "公安", "交警",
      "学校", "中学", "大学", "学院", "教工", "医院", "保健站", "防疫", "疾控",
      "中心", "街道", "社区", "管委会", "团委", "纪委", "支队", "管理处", "电大",
      "监测", "执法队", "研究院", "图书馆", "融媒体"]),
    # 其余以公司/厂/旅行社等命名的，按民营企业处理
    ("民营企业", ["公司", "有限责任公司", "厂", "旅行社", "事务所", "集团", "文化",
                  "大健康", "咨询", "工程", "科技"]),
]


def classify(raw, side=""):
    """把原始单位名映射到职业大类，返回 (类别, 命中的依据)"""
    if pd.isna(raw):
        return "无业·未填", "空值"
    s = str(raw)
    if s in OVERRIDES:
        return OVERRIDES[s], "人工指定"
    for cat, kws in RULES:
        for kw in kws:
            if kw in s:
                return cat, f"命中关键词「{kw}」"
    return "民营企业", "默认（未命中规则，按一般企业处理）"


rows = []
for side, col in (("父亲", "父亲工作"), ("母亲", "母亲工作")):
    for raw in df[col]:
        cat, why = classify(raw, side)
        rows.append({"角色": side, "原始填答": "（空）" if pd.isna(raw) else raw,
                     "职业大类": cat, "判定依据": why})

map_df = pd.DataFrame(rows).drop_duplicates(subset=["角色", "原始填答", "职业大类"])
map_df.to_csv(os.path.join(OUT, "mapping_table.csv"), index=False, encoding="utf-8-sig")

df["父亲职业"] = df["父亲工作"].map(lambda x: classify(x, "父亲")[0])
df["母亲职业"] = df["母亲工作"].map(lambda x: classify(x, "母亲")[0])

# 未命中规则、被默认归为企业的情况，单独提示，方便人工复核
default_hits = map_df[map_df["判定依据"].str.startswith("默认")]
log(f"\n[转化] 共处理原始值 {len(map_df)} 个（含角色区分）")
if len(default_hits):
    log("[转化] 以下值没有命中规则，被默认当作民营企业，请人工复核：")
    for _, r in default_hits.iterrows():
        log(f"        - {r['角色']}：{r['原始填答']}")
else:
    log("[转化] 所有值均由规则或人工指定归类，无默认兜底项")

# 粗分类：3 类，用于列联表单元格太少时做稳健检验
COARSE = {
    "公共部门（党政机关·事业单位）": "体制内（公共部门+国企）",
    "国有企业": "体制内（公共部门+国企）",
    "民营企业": "市场化（民营+个体）",
    "个体经营": "市场化（民营+个体）",
    "家庭主妇": "家庭/未就业",
    "无业·未填": "家庭/未就业",
}
df["父亲职业_粗"] = df["父亲职业"].map(COARSE)
df["母亲职业_粗"] = df["母亲职业"].map(COARSE)

df.insert(0, "编号", range(1, len(df) + 1))
df.to_csv(os.path.join(OUT, "cleaned_data.csv"), index=False, encoding="utf-8-sig")

log("\n[转化] 父亲职业分布：")
log(df["父亲职业"].value_counts().to_string())
log("\n[转化] 母亲职业分布：")
log(df["母亲职业"].value_counts().to_string())
log(f"\n[输出] 明细 → outputs/cleaned_data.csv，对照表 → outputs/mapping_table.csv")

with open(os.path.join(OUT, "step1_report.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))
