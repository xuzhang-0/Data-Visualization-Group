# 中国-中东欧学术合作可视化系统

基于 **D3.js v7** 的交互式数据可视化项目，展示中国与中东欧 17 国（CEE）在 2011–2020 年（125–135 期间）的学术合作论文数据。  
课程汇报用，浏览器打开即用，**无需服务器**。

---

## 🚀 快速开始

### 1️⃣ 安装依赖

```bash
# 使用 pip 部署
pip install -r requirements.txt

# 使用 uv 部署
uv sync
```

### 2️⃣ 一键生成全部图表

```bash
# 进入虚拟环境
source ./.venv/bin/activate
cd src
python run_all.py

# 如果使用 uv
uv run ./src/run_all.py
```

### 3️⃣ 浏览

打开 `docs/index.html`，通过顶部标签导航浏览全部页面。

---

## 🗺️ 页面介绍

| # | 页面 | 图表类型 | 功能亮点 |
|---|------|---------|---------|
| 📋 | **概览** | 统计数字 + 项目介绍 | 四大核心数据展示 |
| 📈 | **时间趋势** | 柱状图 + 折线图（双Y轴） | 2011-2020 发文量趋势，125/135 分界线 |
| 🗺️ | **地理分布** | Choropleth 地图 | 三模式切换（125/135/综合）、放大缩小、机构红点、排名侧栏 |
| 📊 | **国家排名** | 横向条形图 | 三模式切换（125/135/变化量）、点击查看国家简介 |
| 🥧 | **学科网络** | 双饼图 + 力导向网络 | 学科关联图谱、搜索高亮、饼图引导线 |
| 🏛️ | **机构排名** | 双栏横向条形图 | 中国 vs 中东欧 Top 15、三模式切换、排名变化对比 |
| 👥 | **团队** | 信息卡片 | 项目结论、组员信息、数据来源 |

---

## ✨ 已实现的功能特性

### 可视化效果
- **深蓝渐变标题栏** — 所有图表页面顶部统一风格
- **入场动画** — 条形图宽度从 0 过渡、力导向图模拟、折线描边动画
- **饼图引导线** — ≥5% 切片内部标注，<5% 悬停展示
- **悬停 tooltip** — 所有图表均支持，带毛玻璃效果
- **响应式布局** — 适配不同屏幕宽度

### 交互功能
- **标签式导航** — 顶部 7 个标签切换页面，iframe 延迟加载
- **模式切换** — 国家排名和机构排名支持 125/135/总体三模式
- **地图缩放** — +/−/⟲ 按钮 + 滚轮缩放
- **学科搜索** — 网络图中高亮搜索学科
- **国家简介** — 点击条形图展示国家详情

### 数据处理
- Python pandas 读取 Excel，数据嵌入 HTML
- TopoJSON → GeoJSON 转换并缓存（`.geo_cache.json`）
- 每轴独立归一化（雷达图学科对比）

---

## 📁 项目结构

```
├── data/                          # 📊 原始数据
│   ├── 1.中东欧群体发文数量/
│   ├── 2.各国发文量（135-125）/
│   ├── 3.中东欧群体合作领域/
│   ├── 4.各国合作领域/
│   ├── 5.合作机构/
│   └── world-50m.json             # TopoJSON 世界地图
│
├── src/                           # 🐍 Python 源代码
│   ├── common.py                  # 共享常量、映射表、工具函数
│   ├── run_all.py                 # 一键生成全部 HTML
│   ├── generate_trend_viz.py      # → trend_visualization.html
│   ├── generate_map_viz.py        # → cee_map_visualization.html
│   ├── generate_bar_viz.py        # → cee_bar_ranking.html
│   ├── generate_visualization.py  # → discipline_visualization.html
│   ├── generate_institution_viz.py# → institution_visualization.html
│   ├── generate_radar_viz.py      # → radar_visualization.html
│   └── discipline_correlation.py  # → discipline_graph.json（可选 AI 分析）
│
├── docs/                          # 🌐 生成的可视化页面（GitHub Pages）
│   ├── index.html                 # 📋 概览页面
│   ├── common.css                 # 公共样式
│   ├── trend_visualization.html   # 📈 时间趋势页面
│   ├── cee_map_visualization.html # 🗺️ 地理分布页面
│   ├── cee_bar_ranking.html       # 📊 国家排名页面
│   ├── discipline_visualization.html # 🥧 学科网络页面
│   ├── institution_visualization.html # 🏛️ 机构排名页面
│   ├── radar_visualization.html   # 📐 学科对比页面
│   ├── discipline_graph.json      # 学科关联图数据
│   └── .geo_cache.json            # GeoJSON 缓存（自动生成）
│
├── requirements.txt               # Python 依赖
├── uv.lock                        # uv 部署锁文件
├── pyproject.toml                  # uv 配置文件
├── .gitignore
└── README.md
```

---

## 🏗️ 架构说明

```
data/ (Excel)  ──▶  src/ (Python 脚本)
                       │
                       ├── common.py 提供常量与工具
                       ├── pandas 读取 + 处理数据
                       ├── 数据嵌入 HTML 模板
                       ├── D3.js v7 渲染
                       │
                       ▼
                  docs/ (自包含 HTML + CSS)
```

- **数据处理**: Python 3 + pandas + openpyxl
- **可视化**: D3.js v7（CDN 加载）
- **AI 分析**: DeepSeek API（可选）
- **地图数据**: Natural Earth 50m TopoJSON
- **样式管理**: `common.css`（CSS 变量驱动，Python 脚本自动生成）
- **输出**: 纯静态文件，浏览器直接打开

---

## 🤖 （可选）重新运行 AI 学科关联分析

需要 DeepSeek API Key：

```bash
cd src
export DEEPSEEK_API_KEY=你的key   # Mac/Linux
python discipline_correlation.py
```

---

## 📊 数据来源

Web of Science 数据库，2011–2020 年中国与中东欧 17 国合作发表的学术论文数据。  
涵盖 93 个学科领域，按 125（2011-2015）和 135（2016-2020）两个五年期分组分析。

---

## 🛠️ 技术栈

| 层 | 技术 |
|----|------|
| 数据处理 | Python 3, pandas, openpyxl |
| 可视化 | D3.js v7 |
| 地图 | Natural Earth 50m, TopoJSON/GeoJSON |
| AI | DeepSeek, Mimo |
| 工具 | uv, pip, VS Code, Trae |
| 样式 | CSS 变量 + 公共样式表 |
| 部署 | 静态文件，浏览器直接打开 |
