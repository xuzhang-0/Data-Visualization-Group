"""
调用 DeepSeek 大模型分析中国学科之间的关联性强弱，
输出学科作为点、强关联作为边的图关系数据。

依赖: pip install openai
"""

import json
import os
import sys

from common import DISCIPLINE_CATEGORY, CATEGORY_ORDER, CATEGORY_COLORS, check_python_deps, OUTPUT_DIR

if not check_python_deps("openai"):
    print("请先安装依赖: pip install openai")
    print("然后重新运行此脚本。")
    sys.exit(1)

from openai import OpenAI

# ============================================================
# 所有待分析的学科列表
# ============================================================
DISCIPLINES = [
    "世界史", "中医学", "中药学", "临床医学", "交通运输工程",
    "仪器科学与技术", "体育学", "作物学", "信息与通信工程", "光学工程",
    "公共卫生与预防医学", "公共管理", "兵器科学与技术", "兽医学", "农业工程",
    "农业资源与环境", "农林经济管理", "冶金工程", "力学", "动力工程及工程热物理",
    "化学", "化学工程与技术", "医学技术", "口腔医学", "哲学",
    "园艺学", "图书情报与档案管理", "土木工程", "地球物理学", "地理学",
    "地质学", "地质资源与地质工程", "城乡规划学", "基础医学", "大气科学",
    "天文学", "安全科学与工程", "工商管理", "应用经济学", "建筑学",
    "心理学", "戏剧与影视学", "护理学", "控制科学与工程", "政治学",
    "教育学", "数学", "新闻传播学", "机械工程", "材料科学与工程",
    "林业工程", "林学", "核科学与技术", "植物保护", "民族学",
    "水产", "水利工程", "法学", "测绘科学与技术", "海洋科学",
    "物理学", "特种医学", "环境科学与工程", "理论经济学", "生态学",
    "生物医学工程", "生物学", "生物工程", "电子科学与技术", "电气工程",
    "畜牧学", "石油与天然气工程", "矿业工程", "社会学", "科学技术史",
    "管理科学与工程", "系统科学", "纺织科学与工程", "统计学", "网络空间安全",
    "考古学", "航空宇航科学与技术", "船舶与海洋工程", "艺术学理论", "草学",
    "药学", "计算机科学与技术", "设计学", "软件工程", "轻工技术与工程",
    "音乐与舞蹈学", "风景园林学", "食品科学与工程",
]

SYSTEM_PROMPT = """你是一个学科分类与知识体系专家。你需要分析给定的中国学科列表，识别出学科之间关联性强的配对。

判断"关联性强"的标准：
1. 学科之间共享核心理论、方法论或技术工具
2. 学科之间有明显的交叉研究领域或交叉学科
3. 一个学科的研究成果直接影响或支撑另一个学科
4. 学科在课程体系或学术机构中通常归属同一大类

注意：学科的门类（category）已经预先确定，你不需要自行分类。
你只需要根据以下映射填入 category 字段。

请输出一个 JSON，格式如下：
{
  "nodes": [{"id": "学科名", "category": "对应门类"}],
  "edges": [{"source": "学科A", "target": "学科B", "relation": "关联原因简述"}]
}

要求：
- category 必须严格使用下方提供的门类映射
- edges 只包含关联性强的配对，不要包含弱关联
- edges 的 relation 字段简要说明关联原因（10个字以内）
- 确保 edges 中的 source 和 target 都在 nodes 中出现
- 输出必须是合法的 JSON，不要有额外的解释文字"""


def build_user_prompt() -> str:
    disciplines_str = "\n".join(f"- {d}" for d in DISCIPLINES)
    # 构建学科→门类映射表文本
    cat_map_str = "\n".join(f"- {disc} → {cat}" for disc, cat in sorted(DISCIPLINE_CATEGORY.items()) if disc in DISCIPLINES)
    return f"""请分析以下 {len(DISCIPLINES)} 个学科之间的关联性，输出学科节点和强关联关系。

学科 → 门类映射（category 必须严格按此填写）：
{cat_map_str}

学科列表：
{disciplines_str}

请直接输出 JSON，不要包含任何其他文字。"""


def call_deepseek(api_key: str) -> dict:
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=64000,
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt()},
        ],
    )

    text = response.choices[0].message.content.strip()

    # 尝试提取 JSON（处理模型可能包裹在 ```json 中的情况）
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:]) if lines[0].startswith("```") else text
        if text.endswith("```"):
            text = text[:-3].strip()

    return json.loads(text)


def validate_and_clean(data: dict) -> dict:
    """校验并清理输出数据"""
    node_ids = {n["id"] for n in data.get("nodes", [])}

    # 过滤无效边
    valid_edges = []
    for e in data.get("edges", []):
        src, tgt = e.get("source"), e.get("target")
        if src in node_ids and tgt in node_ids and src != tgt:
            valid_edges.append(e)

    # 补充遗漏的学科节点（使用官方门类映射）
    for d in DISCIPLINES:
        if d not in existing_ids:
            cat = DISCIPLINE_CATEGORY.get(d, "未分类")
            data["nodes"].append({"id": d, "category": cat})

    data["edges"] = valid_edges
    return data


def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("请设置环境变量 DEEPSEEK_API_KEY")
        print("  Windows: set DEEPSEEK_API_KEY=your-key-here")
        print("  Linux/Mac: export DEEPSEEK_API_KEY=your-key-here")
        sys.exit(1)

    print(f"共 {len(DISCIPLINES)} 个学科，正在调用 DeepSeek 大模型分析关联关系...")
    print("（由于学科数量多，此过程可能需要 1-2 分钟）\n")

    try:
        result = call_deepseek(api_key)
        result = validate_and_clean(result)
    except Exception as e:
        print(f"调用失败: {e}")
        sys.exit(1)

    # 保存结果
    output_path = os.path.join(OUTPUT_DIR, "discipline_graph.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 输出统计
    nodes = result.get("nodes", [])
    edges = result.get("edges", [])
    categories = {}
    for n in nodes:
        cat = n.get("category", "未分类")
        categories[cat] = categories.get(cat, 0) + 1

    print(f"结果已保存至: {output_path}")
    print(f"\n=== 统计信息 ===")
    print(f"学科节点数: {len(nodes)}")
    print(f"强关联边数: {len(edges)}")
    print(f"\n学科分类分布:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} 个学科")
    print(f"\n关联性最强的 Top 10 学科（按边数）:")
    degree = {}
    for e in edges:
        degree[e["source"]] = degree.get(e["source"], 0) + 1
        degree[e["target"]] = degree.get(e["target"], 0) + 1
    for name, cnt in sorted(degree.items(), key=lambda x: -x[1])[:10]:
        print(f"  {name}: {cnt} 条关联")


if __name__ == "__main__":
    main()
