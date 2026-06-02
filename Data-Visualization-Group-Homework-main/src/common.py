"""
共享常量与工具函数 — 中国-中东欧学术合作可视化项目
======================================================
本模块被 generate_visualization.py / generate_bar_viz.py /
generate_map_viz.py / discipline_correlation.py 共同引用。
"""

import os
import sys

# Windows 控制台 UTF-8 支持（避免 emoji 乱码）
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════
# 路径常量
# ═══════════════════════════════════════════════════════════════════
SRC_DIR      = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)
BASE_DIR     = PROJECT_ROOT
DATA_DIR     = os.path.join(PROJECT_ROOT, "data")
OUTPUT_DIR   = os.path.join(PROJECT_ROOT, "docs")

# ── 数据子目录 ──────────────────────────────────────────────────
DIR_OVERVIEW     = os.path.join(DATA_DIR, "1.中东欧群体发文数量")
DIR_COUNTRY      = os.path.join(DATA_DIR, "2.各国发文量（135-125）")
DIR_DISCIPLINE   = os.path.join(DATA_DIR, "3. 中东欧群体合作领域")
DIR_COUNTRY_DISC = os.path.join(DATA_DIR, "4. 各国合作领域")
DIR_INSTITUTION  = os.path.join(DATA_DIR, "5. 合作机构")

# ═══════════════════════════════════════════════════════════════════
# 学科 → 门类映射（2018年4月《学位授予和人才培养学科目录》）
# ═══════════════════════════════════════════════════════════════════
DISCIPLINE_CATEGORY = {
    # 01 哲学
    "哲学": "哲学",
    # 02 经济学
    "理论经济学": "经济学", "应用经济学": "经济学",
    # 03 法学
    "法学": "法学", "政治学": "法学", "社会学": "法学", "民族学": "法学",
    # 04 教育学
    "教育学": "教育学", "心理学": "教育学", "体育学": "教育学",
    # 05 文学
    "新闻传播学": "文学",
    # 06 历史学
    "世界史": "历史学", "考古学": "历史学",
    # 07 理学
    "数学": "理学", "物理学": "理学", "化学": "理学", "天文学": "理学",
    "地理学": "理学", "大气科学": "理学", "海洋科学": "理学",
    "地球物理学": "理学", "地质学": "理学", "生物学": "理学",
    "系统科学": "理学", "科学技术史": "理学", "生态学": "理学", "统计学": "理学",
    # 08 工学
    "力学": "工学", "机械工程": "工学", "光学工程": "工学",
    "仪器科学与技术": "工学", "材料科学与工程": "工学", "冶金工程": "工学",
    "动力工程及工程热物理": "工学", "电气工程": "工学", "电子科学与技术": "工学",
    "信息与通信工程": "工学", "控制科学与工程": "工学",
    "计算机科学与技术": "工学", "建筑学": "工学", "土木工程": "工学",
    "水利工程": "工学", "测绘科学与技术": "工学", "化学工程与技术": "工学",
    "地质资源与地质工程": "工学", "矿业工程": "工学",
    "石油与天然气工程": "工学", "纺织科学与工程": "工学",
    "轻工技术与工程": "工学", "交通运输工程": "工学",
    "船舶与海洋工程": "工学", "航空宇航科学与技术": "工学",
    "兵器科学与技术": "工学", "核科学与技术": "工学", "农业工程": "工学",
    "林业工程": "工学", "环境科学与工程": "工学", "生物医学工程": "工学",
    "食品科学与工程": "工学", "城乡规划学": "工学", "风景园林学": "工学",
    "软件工程": "工学", "生物工程": "工学", "安全科学与工程": "工学",
    "网络空间安全": "工学",
    # 09 农学
    "作物学": "农学", "园艺学": "农学", "农业资源与环境": "农学",
    "植物保护": "农学", "畜牧学": "农学", "兽医学": "农学",
    "林学": "农学", "水产": "农学", "草学": "农学",
    # 10 医学
    "基础医学": "医学", "临床医学": "医学", "口腔医学": "医学",
    "公共卫生与预防医学": "医学", "中医学": "医学", "药学": "医学",
    "中药学": "医学", "特种医学": "医学", "医学技术": "医学", "护理学": "医学",
    # 12 管理学
    "管理科学与工程": "管理学", "工商管理": "管理学",
    "农林经济管理": "管理学", "公共管理": "管理学",
    "图书情报与档案管理": "管理学",
    # 13 艺术学
    "艺术学理论": "艺术学", "音乐与舞蹈学": "艺术学",
    "戏剧与影视学": "艺术学", "设计学": "艺术学",
}

# ── 门类固定顺序 + 颜色 ─────────────────────────────────────────
CATEGORY_ORDER = [
    "哲学", "经济学", "法学", "教育学", "文学", "历史学",
    "理学", "工学", "农学", "医学", "管理学", "艺术学",
]
CATEGORY_COLORS = {
    "哲学": "#9C27B0", "经济学": "#FF9800", "法学": "#795548",
    "教育学": "#2196F3", "文学": "#E91E63", "历史学": "#607D8B",
    "理学": "#4CAF50", "工学": "#F44336", "农学": "#8BC34A",
    "医学": "#00BCD4", "管理学": "#3F51B5", "艺术学": "#FF5722",
}

# ═══════════════════════════════════════════════════════════════════
# 国家名映射
# ═══════════════════════════════════════════════════════════════════

# Excel 英文名 → 中文名（generate_bar_viz.py 用）
CEE_EXACT = {
    "POLAND": "波兰", "CZECH REPUBLIC": "捷克", "GREECE": "希腊",
    "ROMANIA": "罗马尼亚", "HUNGARY": "匈牙利", "CROATIA": "克罗地亚",
    "SLOVENIA": "斯洛文尼亚", "SLOVAKIA": "斯洛伐克", "LITHUANIA": "立陶宛",
    "BULGARIA": "保加利亚", "ESTONIA": "爱沙尼亚", "LATVIA": "拉脱维亚",
    "MONTENEGRO": "黑山", "BOSNIA & HERZEGOVINA": "波黑", "SERBIA": "塞尔维亚",
    "MACEDONIA": "北马其顿", "ALBANIA": "阿尔巴尼亚",
}

# 中文名 → ISO 数字编码（generate_map_viz.py 用）
CN_TO_ISO = {
    "波兰": "616", "捷克": "203", "希腊": "300", "罗马尼亚": "642",
    "匈牙利": "348", "克罗地亚": "191", "斯洛文尼亚": "705", "斯洛伐克": "703",
    "立陶宛": "440", "保加利亚": "100", "爱沙尼亚": "233", "拉脱维亚": "428",
    "黑山": "499", "波黑": "070", "塞尔维亚": "688", "北马其顿": "807",
    "马其顿": "807", "阿尔巴尼亚": "008",
}

# 邻国 ISO（地图渲染用，保证地理连续）
NEIGHBOR_ISO = {
    "040": "奥地利", "276": "德国", "380": "意大利",
    "804": "乌克兰", "112": "白俄罗斯", "498": "摩尔多瓦",
    "792": "土耳其", "643": "俄罗斯", "756": "瑞士",
    "826": "英国", "250": "法国", "724": "西班牙",
}

# 非欧洲领土 ISO（地图排除）
NON_EUROPEAN_ISO = {
    '840', '012', '434', '504', '364', '368', '376', '400',
    '422', '682', '760', '788', '398',
}

# ═══════════════════════════════════════════════════════════════════
# 科技深蓝主题配色
# ═══════════════════════════════════════════════════════════════════
TECH_BLUE_THEME = {
    "bg_primary": "#0a0e27",
    "bg_secondary": "#111633",
    "bg_card": "rgba(15,20,45,0.85)",
    "accent_blue": "#4fc3f7",
    "accent_purple": "#7c4dff",
    "accent_cyan": "#00e5ff",
    "accent_orange": "#ff6e40",
    "text_primary": "#e0e0e0",
    "text_secondary": "#8899aa",
    "border": "rgba(100,140,255,0.12)",
    "border_glow": "rgba(100,180,255,0.25)",
    "shadow": "0 4px 24px rgba(0,0,0,0.4)",
    "gradient_bg": "linear-gradient(135deg, #0a0e27 0%, #111633 50%, #1a1f3a 100%)",
    "gradient_header": "linear-gradient(135deg, #0d1b3e, #1a2d5a)",
    "map_ocean": "#0d1b3e",
    "map_nodata": "#151d35",
    "map_colors": ["#0d2137", "#1a5276", "#2980b9", "#5dade2", "#aed6f1", "#ebf5fb"],
    "chart_colors": ["#4fc3f7", "#7c4dff", "#00e5ff", "#ff6e40", "#69f0ae", "#ffd740", "#ff4081", "#40c4ff"],
}

# ═══════════════════════════════════════════════════════════════════
# 公共 CSS 样式
# ═══════════════════════════════════════════════════════════════════
COMMON_CSS = """:root{--c-primary:#1a237e;--c-primary-dark:#283593;--c-blue:#4fc3f7;--c-purple:#7c4dff;--c-cyan:#00e5ff;--c-orange:#ff6e40;--c-green:#69f0ae;--c-bg:#f0f2f5;--c-text:#333;--c-muted:#bbb;--c-border:#e0e0e0;--c-border-lt:#e8e8e8;--c-border-ft:#eee}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:var(--c-bg);color:var(--c-text)}
.header{background:linear-gradient(135deg,var(--c-primary),var(--c-primary-dark));color:#fff;padding:18px 30px;text-align:center;border-bottom:1px solid var(--c-border)}
.header h1{font-size:20px;font-weight:600;color:#fff}
.header p{font-size:12px;color:rgba(255,255,255,0.7);margin-top:4px}
.tooltip{position:absolute;background:rgba(0,0,0,0.82);color:#fff;padding:8px 14px;border-radius:8px;font-size:12px;line-height:1.6;pointer-events:none;opacity:0;border:1px solid rgba(0,0,0,0.2);z-index:200}
.controls{display:flex;justify-content:center;gap:10px;padding:12px 20px;background:#fff;border-bottom:1px solid var(--c-border-ft)}
.mode-btn{padding:8px 22px;border:1.5px solid #ccc;border-radius:20px;background:#f5f5f5;color:#999;cursor:pointer;font-size:13px;font-weight:500;transition:all 0.2s}
.mode-btn:hover{background:#eee;color:#666}
.mode-btn.active{background:#e8eaf6;color:var(--c-primary);border-color:var(--c-primary)}
.mode-btn.delta{color:var(--c-orange);border-color:#ffccbc}
.mode-btn.delta.active{background:#fbe9e7;color:var(--c-orange);border-color:var(--c-orange)}
.sep{width:1px;height:18px;background:var(--c-border-ft);margin:0 4px}
.rank-badge{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:11px;font-size:11px;font-weight:700;background:#e0e0e0;color:#fff;flex-shrink:0}
.rank-badge.top1{background:#ffd740;color:#0a0e27}
.rank-badge.top2{background:#b0bec5;color:#0a0e27}
.rank-badge.top3{background:#bcaaa4;color:#0a0e27}
"""

CSS_PATH = os.path.join(OUTPUT_DIR, "common.css")

def write_common_css():
    with open(CSS_PATH, "w", encoding="utf-8") as f:
        f.write(COMMON_CSS.lstrip("\n"))
    print(f"✔ common.css 已更新 ({os.path.getsize(CSS_PATH)} bytes)")

# ═══════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════

def read_excel_safe(path, required_cols=None, description=""):
    """安全读取 Excel，带文件存在性检查和列校验。"""
    import pandas as pd

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"[{description or 'read_excel'}] 文件不存在: {path}"
        )
    df = pd.read_excel(path)
    if required_cols is not None:
        actual = set(df.columns)
        missing = set(required_cols) - actual
        if missing:
            raise ValueError(
                f"[{description or 'read_excel'}] 缺少必需列 {missing}\n"
                f"  文件: {path}\n  实际列: {list(df.columns)}"
            )
    return df


def write_html(output_path, content, report_name=""):
    """写入 HTML 并打印大小报告。"""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else BASE_DIR, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    size_kb = os.path.getsize(output_path) / 1024
    label = f" [{report_name}]" if report_name else ""
    print(f"✔ 生成: {output_path}{label}  ({size_kb:.1f} KB)")


def load_json(path, description=""):
    """安全读取 JSON 文件。"""
    import json
    if not os.path.exists(path):
        raise FileNotFoundError(f"[{description or 'load_json'}] 文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_python_deps(*packages):
    """检查 Python 依赖是否安装，未安装则给出提示。"""
    missing = []
    for pkg in packages:
        try:
            __import__(pkg.replace("-", "_").split(">=")[0].split("==")[0])
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"⚠ 缺少依赖: {', '.join(missing)}")
        print(f"  请运行: pip install {' '.join(missing)}")
        return False
    return True
