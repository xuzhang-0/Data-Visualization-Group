"""
生成 2011-2020 年中东欧合作发文量时间趋势图。
柱状图 + 占比折线（双Y轴），带五年期分隔线。
"""
import json, os
import pandas as pd

from common import (
    BASE_DIR, DIR_OVERVIEW, TECH_BLUE_THEME as T,
    read_excel_safe, write_html, write_common_css, OUTPUT_DIR,
)

write_common_css()

xlsx_path = os.path.join(DIR_OVERVIEW, "2011-2020所发合作文章数量.xlsx")
df = read_excel_safe(xlsx_path, description="时间趋势数据")

trend_data = []
for _, row in df.iterrows():
    try:
        year = int(row.iloc[0])
        cee = float(row.iloc[1])
        china = float(row.iloc[2])
        ratio = float(row.iloc[3])
        trend_data.append({"year": year, "cee": int(cee), "china": int(china), "ratio": round(ratio, 2)})
    except (ValueError, TypeError):
        continue

print(f"Loaded {len(trend_data)} years of trend data")

html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>合作发文时间趋势</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<link rel="stylesheet" href="common.css">
<style>
.chart-wrap{background:#fff;border:1px solid #e0e0e0;border-radius:16px;padding:32px 28px 20px;box-shadow:0 2px 12px rgba(0,0,0,0.08);max-width:900px;width:95%;margin:20px auto}
h2{font-size:20px;font-weight:600;color:var(--c-primary);margin-bottom:4px}
.sub{font-size:12px;color:#999;margin-bottom:18px}
.chart{width:100%;height:480px}
.annotation{font-size:11px;fill:var(--c-purple);font-weight:600}
</style>
</head>
<body>
<div class="header"><h1>中国-中东欧合作发文量趋势 (2011–2020)</h1><p>柱状图: 中东欧合作发文量 | 折线: 占中国总发文量比例 | 虚线: 125/135 分界</p></div>
<div class="chart-wrap">
<div class="chart" id="chart"></div>
</div>
<div class="tooltip" id="tooltip"></div>
<script>
const DATA = __DATA__;
const W = document.getElementById("chart").clientWidth;
const H = 460;
const M = {top:24,right:56,bottom:48,left:60};

const svg = d3.select("#chart").append("svg").attr("width",W).attr("height",H);
const g = svg.append("g").attr("transform",`translate(${M.left},${M.top})`);
const iw=W-M.left-M.right, ih=H-M.top-M.bottom;

const x=d3.scaleBand().domain(DATA.map(d=>d.year)).range([0,iw]).padding(0.25);
const y1=d3.scaleLinear().domain([0,d3.max(DATA,d=>d.cee)*1.15]).range([ih,0]);
const y2=d3.scaleLinear().domain([0,d3.max(DATA,d=>d.ratio)*1.2]).range([ih,0]);

// Axes
g.append("g").call(d3.axisLeft(y1).ticks(6).tickFormat(d=>d/1000+"k")).selectAll("text").style("fill","#8899aa").style("font-size","11px");
g.selectAll(".domain,.tick line").style("stroke","#eee");
g.append("g").attr("transform",`translate(0,${ih})`).call(d3.axisBottom(x).tickFormat(d=>d)).selectAll("text").style("fill","#8899aa").style("font-size","12px");
g.selectAll(".domain").style("stroke","#ccc");

g.append("g").attr("transform",`translate(${iw},0)`).call(d3.axisRight(y2).ticks(6).tickFormat(d=>d+"%")).selectAll("text").style("fill","#7c4dff").style("font-size","11px");

// Bars with enter animation
g.selectAll("rect").data(DATA).join("rect")
  .attr("x",d=>x(d.year)).attr("y",ih).attr("width",x.bandwidth()).attr("height",0)
  .attr("fill","#4fc3f7").attr("rx",3).attr("opacity",0.85)
  .transition().duration(800).delay((d,i)=>i*60)
  .attr("y",d=>y1(d.cee)).attr("height",d=>ih-y1(d.cee));

// Re-bind for static positions after transition
setTimeout(()=>{
g.selectAll("rect").data(DATA).join("rect")
  .attr("x",d=>x(d.year)).attr("y",d=>y1(d.cee)).attr("width",x.bandwidth()).attr("height",d=>ih-y1(d.cee))
  .attr("fill","#4fc3f7").attr("rx",3).attr("opacity",0.85)
  .on("mouseenter",function(e,d){d3.select(this).attr("fill","#00e5ff").attr("opacity",1);
    d3.select("#tooltip").style("opacity",1).html(`<b>${d.year}</b><br>中东欧发文: ${d.cee.toLocaleString()} 篇<br>中国总发文: ${d.china.toLocaleString()} 篇<br>占比: ${d.ratio}%`)
    .style("left",(e.pageX+14)+"px").style("top",(e.pageY-10)+"px");})
  .on("mouseleave",function(){d3.select(this).attr("fill","#4fc3f7").attr("opacity",0.85);d3.select("#tooltip").style("opacity",0);});
},900);

// Ratio line
const line=d3.line().x(d=>x(d.year)+x.bandwidth()/2).y(d=>y2(d.ratio)).curve(d3.curveMonotoneX);
const path=g.append("path").datum(DATA).attr("fill","none").attr("stroke","#7c4dff").attr("stroke-width",2.5).attr("d",line);
const totalLen=path.node().getTotalLength();
path.attr("stroke-dasharray",totalLen).attr("stroke-dashoffset",totalLen)
  .transition().duration(1200).delay(300).attr("stroke-dashoffset",0);

// Ratio dots
g.selectAll("circle.rdot").data(DATA).join("circle").attr("class","rdot")
  .attr("cx",d=>x(d.year)+x.bandwidth()/2).attr("cy",d=>y2(d.ratio)).attr("r",4)
  .attr("fill","#7c4dff").attr("stroke","#0a0e27").attr("stroke-width",2).attr("opacity",0)
  .transition().duration(400).delay((d,i)=>800+i*60).attr("opacity",1);

// Divider line at 2015.5
g.append("line").attr("x1",x(2015)+x.bandwidth()).attr("x2",x(2015)+x.bandwidth())
  .attr("y1",0).attr("y2",ih).attr("stroke","#bbb").attr("stroke-dasharray","6,4").attr("stroke-width",1.5);
g.append("text").attr("x",x(2015)+x.bandwidth()/2).attr("y",-8).attr("text-anchor","middle")
  .attr("class","annotation").text("125 | 135");

// Y labels
g.append("text").attr("x",-42).attr("y",-10).style("fill","#4fc3f7").style("font-size","11px").text("发文量");
g.append("text").attr("x",iw+42).attr("y",-10).style("fill","#7c4dff").style("font-size","11px").style("text-anchor","end").text("占比");
</script>
</body>
</html>"""

html = html.replace("__DATA__", json.dumps(trend_data, ensure_ascii=False))
write_html(os.path.join(OUTPUT_DIR, "trend_visualization.html"), html, "时间趋势图")
print(f"  Years: {len(trend_data)}")
print("Done.")
