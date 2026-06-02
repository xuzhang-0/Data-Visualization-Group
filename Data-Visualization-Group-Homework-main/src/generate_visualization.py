"""
读取国家与学科.xlsx、中东欧群体合作领域表格和 discipline_graph.json，
生成科技深蓝风 D3.js 可视化 HTML（双饼图 + 力导向网络）。
饼图小比例标签使用外部引导线。
"""
import json, os
import pandas as pd

from common import (
    BASE_DIR, DATA_DIR, DIR_COUNTRY_DISC, DIR_DISCIPLINE,
    DISCIPLINE_CATEGORY, CATEGORY_ORDER, CATEGORY_COLORS, TECH_BLUE_THEME as T,
    read_excel_safe, write_html, load_json, write_common_css, OUTPUT_DIR,
)

write_common_css()

xlsx_path = os.path.join(DIR_COUNTRY_DISC, "国家与学科.xlsx")
df = read_excel_safe(xlsx_path, description="国家与学科")
country_col = df.columns[0]
discipline_cols = df.columns[1:].tolist()

countries_data = []
for _, row in df.iterrows():
    name = str(row[country_col]).strip()
    papers = {str(col): int(row[col]) for col in discipline_cols}
    total = sum(papers.values())
    if total > 0: countries_data.append({"name": name, "papers": papers, "total": total})

def read_agg(path, nci=1, vci=2):
    dfa = read_excel_safe(path, description=os.path.basename(path))
    papers = {}
    for _, row in dfa.iterrows(): papers[str(row.iloc[nci]).strip()] = int(row.iloc[vci])
    return papers

f125 = os.path.join(DIR_DISCIPLINE, "125我国与中东欧国家在各学科所发合作文章数量.xlsx")
f135 = os.path.join(DIR_DISCIPLINE, "135我国与中东欧国家在各学科所发合作文章数量.xlsx")
papers_125 = read_agg(f125); papers_135 = read_agg(f135)
all_discs = set(list(papers_125.keys()) + list(papers_135.keys()))
papers_sum = {d: papers_125.get(d,0)+papers_135.get(d,0) for d in all_discs}

agg_data = {
    "125": {"name": "总体 (125)", "papers": papers_125, "total": sum(papers_125.values())},
    "135": {"name": "总体 (135)", "papers": papers_135, "total": sum(papers_135.values())},
    "sum": {"name": "总体 (125+135)", "papers": papers_sum, "total": sum(papers_sum.values())},
}

graph_path = os.path.join(OUTPUT_DIR, "discipline_graph.json")
graph_data = load_json(graph_path, description="discipline_graph.json")

# ═══════════════════════════════════════════════════════════════════
html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>学科合作关系可视化</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<link rel="stylesheet" href="common.css">
<style>
.country-buttons{display:flex;flex-wrap:wrap;justify-content:center;align-items:center;gap:7px;padding:10px 18px;background:#fff;border-bottom:1px solid var(--c-border-ft)}
.country-btn{padding:6px 14px;border:1.5px solid #d0d0d0;border-radius:18px;background:#fafafa;color:#999;cursor:pointer;font-size:12px;font-weight:500;transition:all 0.2s}
.country-btn:hover{background:#eee;color:#666}
.country-btn.active{background:#e8eaf6;color:var(--c-primary);border-color:var(--c-primary)}
.country-btn.agg{color:var(--c-orange);border-color:#ffccbc}
.country-btn.agg.active{background:#fbe9e7;color:var(--c-orange);border-color:var(--c-orange)}
.sub-buttons{display:flex;gap:4px;margin-left:3px}
.sub-btn{padding:4px 10px;border:1.5px solid #fbe9e7;border-radius:12px;background:#fafafa;color:#999;cursor:pointer;font-size:10px;transition:all 0.2s}
.sub-btn:hover{background:#fff3e0}
.sub-btn.active{background:#fbe9e7;color:var(--c-orange);border-color:var(--c-orange)}
.main-layout{display:flex;gap:18px;padding:18px;max-width:1580px;margin:0 auto}
.left-panel{flex:0 0 430px;display:flex;flex-direction:column;gap:14px}
.network-panel{flex:1;min-width:580px}
.pie-block{background:#fff;border:1px solid #e8e8e8;border-radius:12px;padding:14px;box-shadow:0 2px 12px rgba(0,0,0,0.06)}
.network-block{background:#fff;border:1px solid #e8e8e8;border-radius:12px;padding:16px;box-shadow:0 2px 12px rgba(0,0,0,0.06)}
.panel-title{font-size:13px;font-weight:600;color:var(--c-primary);margin-bottom:6px;padding-bottom:4px;border-bottom:1.5px solid #e8e8e8}
.pie-container{width:100%;height:340px}
.network-container{width:100%;height:680px;border:1px solid #eee;border-radius:8px;background:#fafafa}
.info-bar{display:flex;gap:14px;padding:0 0 8px;font-size:11px;color:#bbb;flex-wrap:wrap;align-items:center}
.info-bar span{background:#fafafa;padding:2px 10px;border-radius:10px}
.toolbar{display:flex;gap:6px;align-items:center;margin-bottom:6px}
.search-input{padding:5px 12px;border:1.5px solid #e0e0e0;border-radius:16px;font-size:11px;width:160px;outline:none;background:#fafafa;color:#666;transition:border-color 0.2s}
.search-input:focus{border-color:var(--c-primary)}
.search-input::placeholder{color:#bbb}
.hl-node circle{stroke:var(--c-blue)!important;stroke-width:3.5!important;filter:drop-shadow(0 0 6px rgba(79,195,247,0.5))}
.hl-node text{fill:var(--c-blue)!important;font-weight:800!important}
</style>
</head>
<body>
<div class="header"><h1>国家与学科合作关系可视化</h1></div>
<div class="country-buttons" id="countryButtons"></div>
<div class="main-layout">
<div class="left-panel">
<div class="pie-block"><div class="panel-title" id="pieTitle">合作领域分布</div><div class="pie-container" id="pieChart"></div></div>
<div class="pie-block"><div class="panel-title" id="catPieTitle">学科门类占比</div><div class="pie-container" id="catPieChart"></div></div>
</div>
<div class="network-block network-panel">
<div class="panel-title">学科关联网络</div>
<div class="toolbar"><input class="search-input" type="text" id="searchInput" placeholder="🔍 搜索学科…" oninput="onSearch(this.value)"/></div>
<div class="info-bar" id="infoBar"></div>
<div class="network-container" id="networkChart"></div>
</div>
</div>
<div class="tooltip" id="tooltip"></div>
<script>
const COUNTRIES=__COUNTRIES__, AGG_DATA=__AGG_DATA__, GRAPH_EDGES=__GRAPH_EDGES__, DISC_CAT=__DISC_CAT__, CAT_ORDER=__CAT_ORDER__, CAT_COLORS=__CAT_COLORS__;
const PIE_COLORS=["#4fc3f7","#7c4dff","#00e5ff","#ff6e40","#69f0ae","#ffd740","#ff4081","#40c4ff","#b388ff","#84ffff","#ff8a80","#b2ff59"];

let currentCountry=COUNTRIES[0], isAgg=false, aggKey="125", searchTerm="";

function renderButtons(){
  const c=d3.select("#countryButtons");c.selectAll("*").remove();
  c.selectAll("button.country-btn").data(COUNTRIES).join("button")
    .attr("class",d=>"country-btn"+(isAgg?"":d.name===currentCountry.name?" active":""))
    .text(d=>d.name).on("click",(e,d)=>{isAgg=false;currentCountry=d;updateBtn();updateAll()});
  c.append("span").attr("class","sep");
  c.append("button").attr("class","country-btn agg"+(isAgg?" active":"")).text("总体数据")
    .on("click",()=>{isAgg=true;aggKey="125";updateBtn();updateSub();updateAll()});
  c.append("span").attr("class","sub-buttons").attr("id","subs");updateSub();
}
function updateSub(){const c=d3.select("#subs");c.selectAll("*").remove();if(!isAgg)return;
c.selectAll("button").data(["125","135","sum"]).join("button").attr("class",d=>"sub-btn"+(d===aggKey?" active":"")).text(d=>({125:"125",135:"135",sum:"总和"})[d]).on("click",(e,d)=>{aggKey=d;updateSub();updateAll()})}
function updateBtn(){d3.selectAll("button.country-btn").attr("class",function(){const t=d3.select(this).text();if(t==="总体数据")return"country-btn agg"+(isAgg?" active":"");const mc=COUNTRIES.find(c=>c.name===t);return"country-btn"+(!isAgg&&mc&&mc.name===currentCountry.name?" active":"")})}
function getCD(){if(isAgg){const a=AGG_DATA[aggKey];return{name:a.name,papers:a.papers,total:a.total}}return currentCountry}

// ═══════════════════════ PIE 1 — 学科 + 引导线 ═══════════════════════
function drawDiscPie(){
  const data=getCD();d3.select("#pieTitle").text(`合作领域分布 — ${data.name}`);
  const W=390,H=320,R=Math.min(W,H)/2-24;
  d3.select("#pieChart").selectAll("*").remove();
  const svg=d3.select("#pieChart").append("svg").attr("width",W).attr("height",H)
    .append("g").attr("transform",`translate(${W/2},${H/2})`);
  const total=data.total;
  let entries=Object.entries(data.papers).map(([k,v])=>({name:k,value:v})).sort((a,b)=>b.value-a.value);
  const keep=[],other=[];
  for(const e of entries){if(e.value/total>=0.02)keep.push(e);else other.push(e)}
  const otherSum=d3.sum(other,d=>d.value);
  let pd=keep.map((d,i)=>({...d,color:PIE_COLORS[i%PIE_COLORS.length]}));
  if(otherSum>0)pd.push({name:"其他",value:otherSum,color:"#555"});

  const pie=d3.pie().value(d=>d.value).sort(null);
  const arc=d3.arc().innerRadius(55).outerRadius(R);
  const arcs=pie(pd);

  svg.selectAll("path").data(arcs).join("path")
    .attr("d",arc).attr("fill",d=>d.data.color).attr("stroke","#0a0e27").attr("stroke-width",1.5)
    .on("mouseenter",function(e,d){d3.select(this).transition().duration(120).attr("d",d3.arc().innerRadius(55).outerRadius(R+6));showTooltip(e,`${d.data.name}: ${d.data.value} 篇 (${(d.data.value/total*100).toFixed(1)}%)`)})
    .on("mouseleave",function(){d3.select(this).transition().duration(120).attr("d",arc);hideTooltip()});

  // Labels: only inline labels for >=5%, <5% → hover only
  svg.selectAll(".plbl").data(arcs).join("g").attr("class","plbl").each(function(d){
    const pct=d.data.value/total*100;
    if(pct<5||d.data.name==="其他")return;
    const [cx,cy]=arc.centroid(d);
    d3.select(this).append("text").attr("x",cx).attr("y",cy).attr("text-anchor","middle").attr("dy","0.35em")
      .style("font-size",pct>=10?"11px":"10px").style("font-weight","600").style("fill","#0a0e27").style("pointer-events","none")
      .text(d.data.name.length>4?d.data.name.slice(0,3)+"..":d.data.name);
  });

  svg.append("text").attr("text-anchor","middle").attr("dy","-0.4em").style("fill","#667").style("font-size","10px").text("总计");
  svg.append("text").attr("text-anchor","middle").attr("dy","1em").style("fill","#4fc3f7").style("font-size","14px").style("font-weight","700").text(total);
}

// ═══════════════════════ PIE 2 — 门类 + 引导线 ═══════════════════════
function drawCatPie(){
  const data=getCD();d3.select("#catPieTitle").text(`学科门类占比 — ${data.name}`);
  const catCounts={};
  for(const[disc,count]of Object.entries(data.papers)){const cat=DISC_CAT[disc]||"未分类";catCounts[cat]=(catCounts[cat]||0)+count}
  const total=d3.sum(Object.values(catCounts));
  let cd=[];const small=[];
  for(const cat of CAT_ORDER){const v=catCounts[cat]||0;if(v<=0)continue;if(v/total>=0.02)cd.push({name:cat,value:v,color:CAT_COLORS[cat]||"#999"});else small.push({name:cat,value:v})}
  const ss=d3.sum(small,d=>d.value)+(catCounts["未分类"]||0);
  if(ss>0)cd.push({name:"其他",value:ss,color:"#555"});

  const W=390,H=320,R=Math.min(W,H)/2-24;
  const container=d3.select("#catPieChart");container.selectAll("*").remove();
  const svg=container.append("svg").attr("width",W).attr("height",H).append("g").attr("transform",`translate(${W/2},${H/2})`);
  const pie=d3.pie().value(d=>d.value).sort(null);
  const arc=d3.arc().innerRadius(55).outerRadius(R);
  const arcs=pie(cd);

  svg.selectAll("path").data(arcs).join("path")
    .attr("d",arc).attr("fill",d=>d.data.color).attr("stroke","#0a0e27").attr("stroke-width",1.5)
    .on("mouseenter",function(e,d){d3.select(this).transition().duration(120).attr("d",d3.arc().innerRadius(55).outerRadius(R+6));showTooltip(e,`${d.data.name}: ${d.data.value} 篇 (${(d.data.value/total*100).toFixed(1)}%)`)})
    .on("mouseleave",function(){d3.select(this).transition().duration(120).attr("d",arc);hideTooltip()});

  svg.selectAll(".clbl").data(arcs).join("g").attr("class","clbl").each(function(d){
    const pct=d.data.value/total*100;
    if(pct<5||d.data.name==="其他")return;
    const [cx,cy]=arc.centroid(d);
    d3.select(this).append("text").attr("x",cx).attr("y",cy).attr("text-anchor","middle").attr("dy","0.35em")
      .style("font-size",pct>=10?"11px":"10px").style("font-weight","600").style("fill","#0a0e27").style("pointer-events","none")
      .text(d.data.name);
  });

  svg.append("text").attr("text-anchor","middle").attr("dy","-0.4em").style("fill","#667").style("font-size","10px").text("总计");
  svg.append("text").attr("text-anchor","middle").attr("dy","1em").style("fill","#7c4dff").style("font-size","14px").style("font-weight","700").text(total);
}

// ═══════════════════════ NETWORK ═══════════════════════
let netNodes=[], netEdges=[];

function drawNetwork(){
  const data=getCD();d3.select("#networkChart").selectAll("*").remove();
  const w=d3.select("#networkChart").node().clientWidth, h=650;
  const svg=d3.select("#networkChart").append("svg").attr("width",w).attr("height",h);
  const papers=data.papers;
  let entries=Object.entries(papers).filter(d=>d[1]>0);entries.sort((a,b)=>b[1]-a[1]);
  const top11=new Set(entries.slice(0,11).map(d=>d[0]));
  const paperDiscs=new Set(Object.keys(papers).filter(k=>papers[k]>0));
  const connected=new Set(top11);const adj={};
  for(const e of GRAPH_EDGES){if(!adj[e.source])adj[e.source]=new Set();if(!adj[e.target])adj[e.target]=new Set();adj[e.source].add(e.target);adj[e.target].add(e.source)}
  for(const n of top11){if(adj[n])for(const nb of adj[n]){if(paperDiscs.has(nb))connected.add(nb)}}
  const es=new Set(),el=[];for(const e of GRAPH_EDGES){if(connected.has(e.source)&&connected.has(e.target)){const k=[e.source,e.target].sort().join("|||");if(!es.has(k)){es.add(k);el.push({source:e.source,target:e.target,relation:e.relation})}}}
  netNodes=[];const nm={};let ci=0;
  for(const n of connected){if(papers[n]!==undefined){const isT=top11.has(n);netNodes.push({id:n,papers:papers[n],isTop11:isT,color:isT?["#4fc3f7","#7c4dff","#00e5ff","#ff6e40","#69f0ae","#ffd740","#ff4081","#40c4ff","#b388ff","#84ffff","#ff8a80"][ci++%11]:"#aaa"});nm[n]=netNodes[netNodes.length-1]}}
  netEdges=el.filter(e=>nm[e.source]&&nm[e.target]);

  const rS=d3.scaleSqrt().domain([1,d3.max(netNodes,d=>d.papers)||1]).range([7,45]);
  const sim=d3.forceSimulation(netNodes).force("link",d3.forceLink(netEdges).id(d=>d.id).distance(90).strength(0.35)).force("charge",d3.forceManyBody().strength(-320)).force("center",d3.forceCenter(w/2,h/2)).force("collision",d3.forceCollide().radius(d=>rS(d.papers)+4));

  const zg=svg.append("g");
  let eci=0;

  const link=zg.append("g").selectAll("line").data(netEdges).join("line")
    .attr("stroke",d=>{const b=top11.has(d.source)&&top11.has(d.target);return b?["#4fc3f7","#7c4dff","#00e5ff","#ff6e40","#69f0ae","#ffd740","#ff4081","#40c4ff","#b388ff","#84ffff","#ff8a80"][(eci++)%11]:"#eee"})
    .attr("stroke-width",d=>top11.has(d.source)&&top11.has(d.target)?2:1.2)
    .attr("opacity",d=>top11.has(d.source)&&top11.has(d.target)?0.85:0.7);

  const node=zg.append("g").selectAll("g").data(netNodes).join("g")
    .attr("class",d=>"net-node nn-"+d.id.replace(/\s/g,"_"))
    .call(d3.drag().on("start",(e,d)=>{if(!e.active)sim.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y}).on("drag",(e,d)=>{d.fx=e.x;d.fy=e.y}).on("end",(e,d)=>{if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null}));

  node.append("circle").attr("r",d=>rS(d.papers)).attr("fill",d=>d.color).attr("stroke",d=>d.isTop11?"#999":"#bbb").attr("stroke-width",d=>d.isTop11?2:1).attr("opacity",0.88)
    .on("mouseenter",function(e,d){d3.select(this).attr("opacity",1).attr("stroke-width",3).attr("stroke","#fff").style("filter","drop-shadow(0 0 8px "+d.color+")");showTooltip(e,`<b>${d.id}</b><br>合作论文: ${d.papers} 篇${d.isTop11?" (前11)":""}`)})
    .on("mouseleave",function(e,d){d3.select(this).attr("opacity",0.88).attr("stroke-width",d.isTop11?2:1).attr("stroke",d.isTop11?"#999":"#f5f5f5").style("filter","none");hideTooltip()});

  node.append("text").text(d=>d.id).attr("class",d=>"nlbl nl-"+d.id.replace(/\s/g,"_"))
    .attr("dx",d=>rS(d.papers)+5).attr("dy",4)
    .style("font-size",d=>d.isTop11?"11px":"9px").style("font-weight",d=>d.isTop11?"600":"400")
    .style("fill",d=>d.isTop11?"#333":"#555").style("pointer-events","none");

  sim.on("tick",()=>{link.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);node.attr("transform",d=>`translate(${d.x},${d.y})`)});
  d3.select("#infoBar").html(`<span>数据源: ${data.name}</span><span>显示学科: ${netNodes.length}</span><span>关联边: ${netEdges.length}</span>`);
  svg.call(d3.zoom().scaleExtent([0.3,4]).on("zoom",(e)=>{zg.attr("transform",e.transform)}));
  if(searchTerm)applySearch(searchTerm);
}

// ═══════════════════════ SEARCH ═══════════════════════
function onSearch(t){searchTerm=t.trim().toLowerCase();if(!searchTerm){d3.selectAll(".net-node").classed("hl-node",false);d3.selectAll(".net-node circle,.nlbl").style("opacity",null);d3.selectAll("line").attr("opacity",null);return}applySearch(searchTerm)}
function applySearch(t){
  const matched=new Set(netNodes.filter(n=>n.id.toLowerCase().includes(t)).map(n=>n.id));
  d3.selectAll(".net-node").each(function(d){d3.select(this).classed("hl-node",matched.has(d.id));d3.select(this).select("circle").style("opacity",matched.has(d.id)?1:0.1);d3.select(this).select("text").style("opacity",matched.has(d.id)?1:0.1)});
  d3.selectAll("line").attr("opacity",d=>matched.has(d.source.id)||matched.has(d.target.id)?0.8:0.03);
}

function showTooltip(e,h){d3.select("#tooltip").html(h).style("opacity",1).style("left",(e.pageX+14)+"px").style("top",(e.pageY-10)+"px")}
function hideTooltip(){d3.select("#tooltip").style("opacity",0)}
function updateAll(){drawDiscPie();drawCatPie();drawNetwork()}

renderButtons();updateAll();
</script>
</body>
</html>"""

html = html.replace("__COUNTRIES__", json.dumps(countries_data, ensure_ascii=False))
html = html.replace("__AGG_DATA__", json.dumps(agg_data, ensure_ascii=False))
html = html.replace("__GRAPH_EDGES__", json.dumps(graph_data.get("edges", []), ensure_ascii=False))
html = html.replace("__DISC_CAT__", json.dumps(DISCIPLINE_CATEGORY, ensure_ascii=False))
html = html.replace("__CAT_ORDER__", json.dumps(CATEGORY_ORDER, ensure_ascii=False))
html = html.replace("__CAT_COLORS__", json.dumps(CATEGORY_COLORS, ensure_ascii=False))

write_html(os.path.join(OUTPUT_DIR, "discipline_visualization.html"), html, "学科合作网络")
all_disc = list(countries_data[0]["papers"].keys()) if countries_data else []
unmapped = [d for d in all_disc if d not in DISCIPLINE_CATEGORY]
print(f"  Countries: {len(countries_data)}, Disciplines: {len(all_disc)}, Mapped: {len(all_disc)-len(unmapped)}")
if unmapped: print(f"  Unmapped: {unmapped}")
print("Done.")
