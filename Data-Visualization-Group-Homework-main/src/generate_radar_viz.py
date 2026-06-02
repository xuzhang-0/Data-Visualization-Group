"""
生成多国学科门类雷达图。数据来源：国家×学科门类聚合矩阵。
可选 2-4 个国家进行对比。
"""
import json, os
import pandas as pd

from common import (
    BASE_DIR, DIR_COUNTRY_DISC,
    DISCIPLINE_CATEGORY, CATEGORY_ORDER, CATEGORY_COLORS,
    TECH_BLUE_THEME as T,
    read_excel_safe, write_html, write_common_css, OUTPUT_DIR,
)

write_common_css()

# ── 读取数据 ────────────────────────────────────────────────
xlsx_path = os.path.join(DIR_COUNTRY_DISC, "国家与学科.xlsx")
df = read_excel_safe(xlsx_path, description="国家与学科")

country_col = df.columns[0]
discipline_cols = df.columns[1:].tolist()

# 聚合: 国家 → {门类: 总发文量}
country_data = {}
for _, row in df.iterrows():
    name = str(row[country_col]).strip()
    cats = {cat: 0 for cat in CATEGORY_ORDER}
    total = 0
    for col in discipline_cols:
        disc = str(col).strip()
        cat = DISCIPLINE_CATEGORY.get(disc)
        if cat and cat in cats:
            val = int(row[col]) if pd.notna(row[col]) else 0
            cats[cat] += val
            total += val
    if total > 0:
        country_data[name] = {"categories": cats, "total": total}

countries_list = sorted(country_data.keys(), key=lambda n: country_data[n]["total"], reverse=True)
print(f"Loaded {len(countries_list)} countries for radar chart")

# 存储原始值（百分比），JS 端做每轴独立归一
radar_data = []
for name in countries_list:
    cd = country_data[name]
    cats_pct = {}
    for cat in CATEGORY_ORDER:
        cats_pct[cat] = round(cd["categories"][cat] / cd["total"] * 100, 1) if cd["total"] > 0 else 0
    radar_data.append({"name": name, "categories": cats_pct, "total": cd["total"]})

html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>学科门类雷达图</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<link rel="stylesheet" href="common.css">
<style>
body{display:flex;justify-content:center;align-items:center;min-height:100vh}
.main{background:#fff;border:1px solid #e0e0e0;border-radius:16px;padding:28px 24px 20px;box-shadow:0 2px 12px rgba(0,0,0,0.08);max-width:960px;width:95%}
h3{font-size:18px;font-weight:600;color:var(--c-primary);margin-bottom:4px}
.subtitle{font-size:11px;color:#bbb;margin-bottom:12px}
.controls{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.country-chip{padding:7px 18px;border:2px solid #ccc;border-radius:20px;background:#fafafa;color:#999;cursor:pointer;font-size:13px;transition:all 0.2s;font-family:inherit}
.country-chip:hover{border-color:var(--c-primary);color:var(--c-primary)}
.country-chip.selected{background:#e8eaf6;color:var(--c-primary);border-color:var(--c-primary);font-weight:600}
.country-chip.disabled{opacity:0.4;cursor:not-allowed}
.chart-wrap{position:relative;width:100%;height:600px;display:flex;justify-content:center}
.chart{width:100%;height:600px}
.legend{display:flex;flex-wrap:wrap;gap:18px;margin-top:10px;padding:10px 14px;background:#fafafa;border-radius:10px;justify-content:center}
.legend-item{display:flex;align-items:center;gap:6px;font-size:12px;color:#555}
.legend-dot{width:12px;height:12px;border-radius:50%;display:inline-block;border:2px solid rgba(255,255,255,0.8);box-shadow:0 1px 3px rgba(0,0,0,0.2)}
.tooltip{position:absolute;background:rgba(30,30,50,0.95);color:#fff;padding:12px 18px;border-radius:12px;font-size:12px;pointer-events:none;opacity:0;border:1px solid rgba(255,255,255,0.1);z-index:200;line-height:1.7;backdrop-filter:blur(8px);min-width:180px;box-shadow:0 4px 20px rgba(0,0,0,0.25)}
.tooltip b{color:#fff;font-size:14px}
.tooltip .tt-row{display:flex;justify-content:space-between;gap:16px}
.tooltip .tt-val{font-weight:600}
</style>
</head>
<body>
<div class="main">
<h3>🕸️ 学科门类雷达图 — 多国对比</h3>
<div class="subtitle">每轴独立归一 = 100%，展示各国相对学科优势</div>
<div class="controls" id="controls"></div>
<div class="chart" id="chart"></div>
<div class="legend" id="legend"></div>
</div>
<div class="tooltip" id="tooltip"></div>
<script>
const DATA = __DATA__;
const CATS = __CATS__;
const COLORS = ["#4fc3f7","#7c4dff","#ff6e40","#69f0ae","#ffd740"];

let selected = [DATA[0]?.name, DATA[1]?.name, DATA[2]?.name].filter(Boolean);

function renderControls(){
  const c = d3.select("#controls");
  c.selectAll("*").remove();
  c.selectAll(".country-chip").data(DATA).join("div")
    .attr("class",d=>"country-chip"+(selected.includes(d.name)?" selected":"")+((!selected.includes(d.name)&&selected.length>=5)?" disabled":""))
    .text(d=>d.name+" ("+d.total+" 篇)")
    .on("click",(e,d)=>{
      if(selected.includes(d.name)){selected=selected.filter(s=>s!==d.name);renderControls();drawRadar()}
      else if(selected.length<5){selected.push(d.name);renderControls();drawRadar()}
    });
}

function drawRadar(){
  const c=d3.select("#chart"); c.selectAll("*").remove();
  const l=d3.select("#legend"); l.selectAll("*").remove();
  const w=Math.max(c.node().clientWidth,400), h=600, R=Math.min(w,h)/2-90;
  const cx=w/2, cy=h/2-10;
  const svg=c.append("svg").attr("width",w).attr("height",h).append("g").attr("transform","translate("+cx+","+cy+")");

  const N=CATS.length;
  const angleSlice=Math.PI*2/N;

  // Grid: concentric polygons (spider web)
  [20,40,60,80,100].forEach((pct,i)=>{
    const pts=[];
    for(let j=0;j<N;j++){
      const a=angleSlice*j-Math.PI/2;
      pts.push([R*pct/100*Math.cos(a), R*pct/100*Math.sin(a)]);
    }
    svg.append("polygon").attr("points",pts.map(p=>p.join(",")).join(" "))
      .attr("fill","none").attr("stroke","#e8e8e8").attr("stroke-width",i===4?1.2:0.8)
      .attr("stroke-dasharray",i%2===0?"4,3":"none");
    svg.append("text").attr("x",4).attr("y",-R*pct/100).attr("dy","0.35em")
      .style("fill","#ddd").style("font-size","9px").text(pct+"%");
  });

  // Axes
  svg.selectAll(".axis").data(CATS).join("line")
    .attr("x1",0).attr("y1",0)
    .attr("x2",(d,i)=>R*Math.cos(angleSlice*i-Math.PI/2))
    .attr("y2",(d,i)=>R*Math.sin(angleSlice*i-Math.PI/2))
    .attr("stroke","#d0d0d0").attr("stroke-width",1);

  // Axis labels
  svg.selectAll(".label").data(CATS).join("text")
    .attr("x",(d,i)=>(R+20)*Math.cos(angleSlice*i-Math.PI/2))
    .attr("y",(d,i)=>(R+20)*Math.sin(angleSlice*i-Math.PI/2))
    .attr("text-anchor",(d,i)=>{const a=angleSlice*i;return Math.abs(Math.cos(a))<0.1?"middle":Math.cos(a)>0?"start":"end"})
    .attr("dy","0.35em").style("fill","#667").style("font-size","12px").style("font-weight","500").text(d=>d);

  // Per-category normalization
  const selectedData = selected.map(name=>DATA.find(d=>d.name===name)).filter(Boolean);
  if(selectedData.length===0){c.append("div").style("text-align","center").style("padding","120px 0").style("color","#bbb").text("请选择至少一个国家");return}
  const maxPerCat={};
  CATS.forEach(cat=>{maxPerCat[cat]=d3.max(selectedData,d=>d.categories[cat]||0)||1});
  const normVal=(country,cat)=>((country.categories[cat]||0)/maxPerCat[cat])*100;
  const radarLine=d3.lineRadial().curve(d3.curveLinearClosed).radius(d=>R*d.nval/100).angle((d,i)=>i*angleSlice);

  // Draw each country
  selectedData.forEach((country,si)=>{
    const pts=CATS.map((cat,i)=>({nval:normVal(country,cat),cat,orig:country.categories[cat]||0,index:i}));
    const col=COLORS[si%COLORS.length];

    const path=svg.append("path").datum(pts)
      .attr("d",radarLine).attr("fill",col).attr("fill-opacity",0.1)
      .attr("stroke",col).attr("stroke-width",2.5).attr("stroke-opacity",0.85)
      .attr("stroke-linejoin","round");

    // Animate stroke draw-in
    const plen=path.node().getTotalLength();
    path.attr("stroke-dasharray",plen+" "+plen).attr("stroke-dashoffset",plen)
      .transition().duration(800).delay(si*200).attr("stroke-dashoffset",0)
      .transition().duration(200).attr("fill-opacity",0.13);

    // Data dots (animated in)
    svg.selectAll(".dot"+si).data(pts).join("circle")
      .attr("cx",d=>R*d.nval/100*Math.cos(angleSlice*d.index-Math.PI/2))
      .attr("cy",d=>R*d.nval/100*Math.sin(angleSlice*d.index-Math.PI/2))
      .attr("r",0).attr("fill",col).attr("stroke","#fff").attr("stroke-width",2.5)
      .transition().delay(600+si*200).duration(300).attr("r",5);

    // Hover tooltips (after all animations)
    setTimeout(()=>{
      svg.selectAll(".dot"+si).data(pts).join("circle")
        .attr("cx",d=>R*d.nval/100*Math.cos(angleSlice*d.index-Math.PI/2))
        .attr("cy",d=>R*d.nval/100*Math.sin(angleSlice*d.index-Math.PI/2))
        .attr("r",5).attr("fill",col).attr("stroke","#fff").attr("stroke-width",2.5).style("cursor","pointer")
        .on("mouseenter",function(e,d){
          d3.select(this).transition().duration(150).attr("r",9).attr("stroke-width",3);
          let bestCountry="",bestVal=0;
          selectedData.forEach(sc=>{const v=sc.categories[d.cat]||0;if(v>bestVal){bestVal=v;bestCountry=sc.name}});
          const isBest=country.name===bestCountry;
          showTooltip(e,
            '<b style="color:'+col+'">'+country.name+'</b> &mdash; <b>'+d.cat+'</b>'+
            '<div class="tt-row"><span>'+country.name+'</span><span class="tt-val">'+d.orig+'%</span></div>'+
            (isBest?'<div class="tt-row" style="color:#69f0ae"><span>🥇 该门类最高</span><span class="tt-val">'+d.orig+'%</span></div>':
              '<div class="tt-row"><span>'+bestCountry+' (最高)</span><span class="tt-val">'+bestVal+'%</span></div>')
          );
        })
        .on("mousemove",function(e){d3.select("#tooltip").style("left",(e.pageX+16)+"px").style("top",(e.pageY-10)+"px")})
        .on("mouseleave",function(){d3.select(this).transition().duration(150).attr("r",5).attr("stroke-width",2.5);hideTooltip()});
    },1000+si*200);
  });

  // Legend
  selectedData.forEach((country,i)=>{
    const col=COLORS[i%COLORS.length];
    l.append("div").attr("class","legend-item")
      .html('<span class="legend-dot" style="background:'+col+'"></span> '+country.name+' <span style="color:#bbb;font-size:11px">('+country.total+' 篇)</span>');
  });
}

function showTooltip(e,html){d3.select("#tooltip").html(html).style("opacity",1).style("left",(e.pageX+16)+"px").style("top",(e.pageY-10)+"px")}
function hideTooltip(){d3.select("#tooltip").style("opacity",0)}

renderControls();
drawRadar();
window.addEventListener("resize",drawRadar);
</script>
</body>
</html>"""

html = html.replace("__DATA__", json.dumps(radar_data, ensure_ascii=False))
html = html.replace("__CATS__", json.dumps(CATEGORY_ORDER, ensure_ascii=False))
write_html(os.path.join(OUTPUT_DIR, "radar_visualization.html"), html, "雷达图")
print(f"  Countries: {len(radar_data)}, Categories: {len(CATEGORY_ORDER)}")
print("Done.")
