"""
读取中东欧各国125与135所发合作文章数量.xlsx 和 world-50m.json，
Python 端完成 TopoJSON→GeoJSON 转换（带缓存），生成深蓝科技风 choropleth 地图。
"""
import json, os
import pandas as pd

from common import (
    BASE_DIR, DATA_DIR, DIR_COUNTRY, DIR_INSTITUTION,
    CN_TO_ISO, NEIGHBOR_ISO, NON_EUROPEAN_ISO, TECH_BLUE_THEME as T,
    read_excel_safe, write_html, load_json, write_common_css, OUTPUT_DIR
)

write_common_css()

# ═══════════════════════════════════════════════════════════════════
# 1. 读取 Excel
# ═══════════════════════════════════════════════════════════════════
xlsx_path = os.path.join(DIR_COUNTRY, "中东欧各国125与135所发合作文章数量.xlsx")
df = read_excel_safe(xlsx_path, description="中东欧各国发文量")
name_col = df.columns[0]

country_data = {}
for _, row in df.iterrows():
    cn_name = str(row[name_col]).strip()
    iso = CN_TO_ISO.get(cn_name)
    if iso:
        country_data[iso] = {
            "name_cn": cn_name,
            "papers_125": int(row[df.columns[4]]),
            "papers_135": int(row[df.columns[1]]),
            "papers_sum": int(row[df.columns[4]]) + int(row[df.columns[1]]),
        }
print(f"Matched countries from Excel: {len(country_data)}")

# ═══════════════════════════════════════════════════════════════════
# 1b. 机构数据
# ═══════════════════════════════════════════════════════════════════
inst_path = os.path.join(DIR_INSTITUTION, "125-135中东欧机构所发合作文章数量.xlsx")
df_inst = read_excel_safe(inst_path, description="中东欧机构数据")
inst_name_col = df_inst.columns[1]; inst_country_col = df_inst.columns[2]
inst_135_col = df_inst.columns[3]; inst_125_col = df_inst.columns[5]

institutions_data = []
for _, row in df_inst.iterrows():
    cn_country = str(row[inst_country_col]).strip()
    iso = CN_TO_ISO.get(cn_country)
    if iso:
        institutions_data.append({
            "name": str(row[inst_name_col]).strip(), "country_iso": iso,
            "country_cn": cn_country,
            "papers_125": int(row[inst_125_col]), "papers_135": int(row[inst_135_col]),
            "papers_sum": int(row[inst_125_col]) + int(row[inst_135_col]),
        })
print(f"Institutions loaded: {len(institutions_data)}")

# ═══════════════════════════════════════════════════════════════════
# 2. TopoJSON → GeoJSON（带缓存）
# ═══════════════════════════════════════════════════════════════════
CACHE_PATH = os.path.join(OUTPUT_DIR, ".geo_cache.json")
TOPO_PATH = os.path.join(DATA_DIR, "world-50m.json")

def build_geojson():
    topo = load_json(TOPO_PATH, description="world-50m.json")
    scale = topo.get("transform", {}).get("scale", [1, 1])
    translate = topo.get("transform", {}).get("translate", [0, 0])
    arcs = topo["arcs"]

    def decode_arc(ai):
        raw = arcs[ai] if ai >= 0 else arcs[~ai]
        abs_pts = []; x = y = 0
        for pt in raw: x += pt[0]; y += pt[1]; abs_pts.append([x, y])
        if ai < 0: abs_pts.reverse()
        return [[p[0]*scale[0]+translate[0], p[1]*scale[1]+translate[1]] for p in abs_pts]

    def decode_ring(ais):
        coords = []
        for ai in ais:
            ac = decode_arc(ai)
            coords.extend(ac[1:] if coords else ac)
        return coords

    def decode_geometry(geom):
        if geom["type"] == "Polygon": return {"type": "Polygon", "coordinates": [decode_ring(ag) for ag in geom["arcs"]]}
        elif geom["type"] == "MultiPolygon": return {"type": "MultiPolygon", "coordinates": [[decode_ring(ag) for ag in pg] for pg in geom["arcs"]]}

    features = []
    for geom in topo["objects"]["countries"]["geometries"]:
        features.append({"type": "Feature", "id": geom.get("id"), "properties": geom.get("properties", {}), "geometry": decode_geometry(geom)})
    world_geo = {"type": "FeatureCollection", "features": features}
    print(f"GeoJSON features (full): {len(world_geo['features'])}")

    target_iso = set(country_data.keys())
    keep_iso = target_iso | set(NEIGHBOR_ISO.keys())

    def feature_bbox(feat):
        coords = []
        def coll(c):
            if isinstance(c[0], (int, float)): coords.append(c)
            else:
                for s in c: coll(s)
        coll(feat["geometry"]["coordinates"])
        if not coords: return None
        return (min(p[0] for p in coords), max(p[0] for p in coords), min(p[1] for p in coords), max(p[1] for p in coords))

    filtered = []
    for f in world_geo["features"]:
        fid = str(f.get("id", "")); bbox = feature_bbox(f)
        if not bbox: continue
        mnx, mxx, mny, mxy = bbox
        cee_r = (-12, 45, 34, 72)
        overlaps = mxx > cee_r[0] and mnx < cee_r[1] and mxy > cee_r[2] and mny < cee_r[3]
        if fid in NON_EUROPEAN_ISO: continue
        if fid in keep_iso or overlaps:
            props = f.get("properties", {})
            props["display_name"] = country_data[fid]["name_cn"] if fid in country_data else (NEIGHBOR_ISO.get(fid, props.get("name", fid)))
            props["iso"] = fid
            filtered.append(f)
    return {"type": "FeatureCollection", "features": filtered}

topo_mtime = os.path.getmtime(TOPO_PATH)
cache_valid = os.path.exists(CACHE_PATH) and os.path.getmtime(CACHE_PATH) >= topo_mtime
if cache_valid:
    geo_filtered = load_json(CACHE_PATH, description="GeoJSON cache")
    print(f"Using cached GeoJSON ({len(geo_filtered['features'])} features)")
else:
    print("Building GeoJSON from TopoJSON...")
    geo_filtered = build_geojson()
    with open(CACHE_PATH, "w", encoding="utf-8") as f: json.dump(geo_filtered, f, ensure_ascii=False)
    print(f"GeoJSON cached ({len(geo_filtered['features'])} features)")

geo_json_str = json.dumps(geo_filtered, ensure_ascii=False)
print(f"Embedding: {len(geo_json_str)/1024:.0f} KB")

# ═══════════════════════════════════════════════════════════════════
# 3. HTML
# ═══════════════════════════════════════════════════════════════════
html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>合作论文地理分布</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<link rel="stylesheet" href="common.css">
<style>
.controls{align-items:center}
.label-btn{padding:8px 22px;border:1.5px solid #d1c4e9;border-radius:20px;background:#f5f5f5;color:#999;cursor:pointer;font-size:13px;font-weight:500;transition:all 0.2s}
.label-btn:hover{background:#f3e5f5;color:#666}
.label-btn.active{background:#ede7f6;color:#3949ab;border-color:#3949ab}
.main-container{display:flex;gap:16px;padding:16px;max-width:1500px;margin:0 auto}
.map-panel{flex:1;background:#fff;border:1px solid #e8e8e8;border-radius:14px;padding:16px;box-shadow:0 2px 12px rgba(0,0,0,0.06);min-height:600px}
.map-title{font-size:15px;font-weight:600;color:var(--c-primary);margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #e0e0e0}
.map-container{width:100%;height:640px}
.side-panel{flex:0 0 320px;display:flex;flex-direction:column;gap:16px}
.rank-panel{background:#fff;border:1px solid #e8e8e8;border-radius:14px;padding:16px;box-shadow:0 2px 12px rgba(0,0,0,0.06);flex:1}
.rank-title{font-size:14px;font-weight:600;color:#3949ab;margin-bottom:10px}
.rank-list{max-height:480px;overflow-y:auto}
.rank-row{display:flex;align-items:center;gap:8px;padding:6px 8px;border-bottom:1px solid #fafafa;font-size:12px;transition:background 0.15s}
.rank-row:hover{background:#f0f0ff;border-radius:6px}
.rank-badge{width:22px;height:22px;border-radius:11px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:11px;color:#fff;flex-shrink:0;background:#e0e0e0}
.rank-badge.top1{background:#ffd740;color:#0a0e27}
.rank-badge.top2{background:#b0bec5;color:#0a0e27}
.rank-badge.top3{background:#bcaaa4;color:#0a0e27}
.rank-name{flex:1;font-weight:500;color:#666}
.rank-val{font-weight:600;color:var(--c-primary);white-space:nowrap;font-size:11px}
.rank-bar{height:5px;border-radius:3px;flex-shrink:0}
.legend-container{margin-top:12px;padding:8px 12px;background:#fafafa;border-radius:8px}
.legend-title{font-size:11px;color:#bbb;margin-bottom:4px}
.zoom-controls{position:absolute;bottom:24px;right:20px;display:flex;flex-direction:column;gap:5px;z-index:10}
.zoom-btn{width:36px;height:36px;border-radius:50%;border:1.5px solid #d0d0d0;background:#fff;color:#555;font-size:20px;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.12);transition:all 0.15s;font-family:inherit;line-height:1}
.zoom-btn:hover{background:#e8eaf6;border-color:var(--c-primary);color:var(--c-primary)}
</style>
</head>
<body>
<div class="header"><h1>中东欧国家合作论文地理分布</h1><p>蓝色越亮 = 合作论文越多 | 鼠标悬停查看详情</p></div>
<div class="controls">
  <button class="mode-btn active" data-mode="125">125 期间</button>
  <button class="mode-btn" data-mode="135">135 期间</button>
  <button class="mode-btn" data-mode="sum">综合 (125+135)</button>
  <span class="sep"></span>
  <button class="label-btn active" id="labelToggle">机构标签: 开</button>
</div>
<div class="main-container">
<div class="map-panel" style="position:relative"><div class="map-title" id="mapTitle">合作论文地理分布 — 125 期间</div><div class="map-container" id="mapChart"></div><div class="zoom-controls"><button class="zoom-btn" onclick="zoomIn()">+</button><button class="zoom-btn" onclick="zoomOut()">−</button><button class="zoom-btn" onclick="zoomReset()" style="font-size:14px">⟲</button></div><div class="legend-container" id="legendBox"></div></div>
<div class="side-panel"><div class="rank-panel"><div class="rank-title">各国合作论文排名</div><div class="rank-list" id="rankList"></div></div></div>
</div>
<div class="tooltip" id="tooltip"></div>
<script>
const GEO_JSON=__GEO_JSON__, COUNTRY_DATA=__COUNTRY_DATA__, NEIGHBOR_ISO=new Set(__NEIGHBOR_LIST__), INSTITUTIONS=__INSTITUTIONS_JSON__;
let currentMode="125", showLabels=true;

function getPapers(iso){const d=COUNTRY_DATA[iso];return d?(currentMode==="125"?d.papers_125:currentMode==="135"?d.papers_135:d.papers_sum):0}

function drawMap(){
  d3.select("#mapChart").selectAll("*").remove();
  const w=d3.select("#mapChart").node().clientWidth, h=620;
  const svg=d3.select("#mapChart").append("svg").attr("width",w).attr("height",h);
  const zoom=d3.zoom().scaleExtent([1,15]).on("zoom",(e)=>{d3.select("#mapGroup").attr("transform",e.transform)});
  svg.call(zoom).on("dblclick.zoom",null);
  const proj=d3.geoMercator().center([18,50]).scale(w*0.88).translate([w/2,h/2]);
  const pathGen=d3.geoPath().projection(proj);
  const allVals=Object.values(COUNTRY_DATA).map(d=>currentMode==="125"?d.papers_125:currentMode==="135"?d.papers_135:d.papers_sum);
  const maxVal=d3.max(allVals)||1;

  const colorScale=d3.scaleSequential(d3.interpolateRgb("#0d2137","#ebf5fb")).domain([0,maxVal]);

  const mapG=svg.append("g").attr("id","mapGroup");
  mapG.append("rect").attr("width",w*3).attr("height",h*3).attr("x",-w).attr("y",-h).attr("fill","#e8f0f8");

  mapG.append("g").selectAll("path").data(GEO_JSON.features).join("path")
    .attr("d",pathGen)
    .attr("fill",d=>{const iso=d.properties.iso;if(COUNTRY_DATA[iso]){const v=getPapers(iso);return v>0?colorScale(v):"#e8e8e8"}return"#f2f2f2"})
    .attr("stroke",d=>COUNTRY_DATA[d.properties.iso]?"#7986cb":"#f5f5f5")
    .attr("stroke-width",d=>COUNTRY_DATA[d.properties.iso]?1.2:0.5)
    .on("mouseenter",function(e,d){const iso=d.properties.iso;if(COUNTRY_DATA[iso]){d3.select(this).attr("stroke-width",2.5).attr("stroke","#4fc3f7").style("filter","drop-shadow(0 0 6px rgba(79,195,247,0.5))");const dd=COUNTRY_DATA[iso];showTooltip(e,`<b style="color:#fff">${dd.name_cn}</b><br>125: ${dd.papers_125.toLocaleString()} 篇<br>135: ${dd.papers_135.toLocaleString()} 篇<br>合计: ${dd.papers_sum.toLocaleString()} 篇`)}else if(NEIGHBOR_ISO.has(iso))showTooltip(e,`<span style="color:#bbb">${d.properties.display_name||iso} (邻国)</span>`)})
    .on("mousemove",function(e){d3.select("#tooltip").style("left",(e.pageX+14)+"px").style("top",(e.pageY-10)+"px")})
    .on("mouseleave",function(e,d){if(COUNTRY_DATA[d.properties.iso]){d3.select(this).attr("stroke-width",1.2).attr("stroke","#7986cb").style("filter","none")}hideTooltip()});

  mapG.append("g").selectAll("text").data(GEO_JSON.features).join("text")
    .attr("transform",d=>`translate(${pathGen.centroid(d)})`)
    .attr("text-anchor","middle").attr("dy","0.35em")
    .style("font-size",d=>COUNTRY_DATA[d.properties.iso]?"10px":"8px").style("font-weight",d=>COUNTRY_DATA[d.properties.iso]?"700":"400")
    .style("fill","#fff").style("stroke","rgba(0,0,0,0.7)").style("stroke-width","0.6px").style("paint-order","stroke")
    .style("pointer-events","none").text(d=>d.properties.display_name||d.properties.iso);

  if(showLabels) drawInstLabels(mapG,proj,pathGen);
  drawLegend(maxVal, colorScale);
  d3.select("#mapTitle").text(`合作论文地理分布 — ${currentMode==="125"?"125 期间":currentMode==="135"?"135 期间":"综合 (125+135)"}`);
}

function drawInstLabels(svg,proj,pathGen){
  const byC={};INSTITUTIONS.forEach(i=>{const iso=i.country_iso;if(!byC[iso])byC[iso]=[];byC[iso].push(i)});
  const fMap={};GEO_JSON.features.forEach(f=>{const iso=f.properties.iso;if(iso&&COUNTRY_DATA[iso])fMap[iso]=f});
  const allP=INSTITUTIONS.map(d=>currentMode==="125"?d.papers_125:currentMode==="135"?d.papers_135:d.papers_sum);
  const rS=d3.scaleSqrt().domain([1,d3.max(allP)||1]).range([3,11]);
  for(const[iso,insts]of Object.entries(byC)){
    const feat=fMap[iso];if(!feat)continue;
    const[cx,cy]=pathGen.centroid(feat);
    insts.sort((a,b)=>(currentMode==="125"?b.papers_125-b.papers_125:currentMode==="135"?b.papers_135-b.papers_135:b.papers_sum-a.papers_sum));
    insts.forEach((inst,i)=>{const v=currentMode==="125"?inst.papers_125:currentMode==="135"?inst.papers_135:inst.papers_sum;const ang=i/insts.length*Math.PI*2+0.5;const dist=18+i*4;const mx=cx+Math.cos(ang)*dist,my=cy+Math.sin(ang)*dist;
    svg.append("circle").attr("cx",mx).attr("cy",my).attr("r",rS(v)).attr("fill","#ff6e40").attr("stroke","#0a0e27").attr("stroke-width",1.5).attr("opacity",0.82).style("cursor","pointer")
    .on("mouseenter",function(e){d3.select(this).attr("fill","#7c4dff").attr("stroke","#fff").attr("stroke-width",2).transition().duration(120).attr("r",rS(v)*1.3);showTooltip(e,`<b>${inst.name}</b><br>${inst.country_cn}<br>125: ${inst.papers_125} | 135: ${inst.papers_135}<br>合计: ${inst.papers_sum} 篇`)})
    .on("mousemove",function(e){d3.select("#tooltip").style("left",(e.pageX+14)+"px").style("top",(e.pageY-10)+"px")})
    .on("mouseleave",function(){d3.select(this).attr("fill","#ff6e40").attr("stroke","#0a0e27").attr("stroke-width",1.5).transition().duration(120).attr("r",rS(v))});});
  }
}

function drawLegend(maxVal,cs){
  const lb=d3.select("#legendBox");lb.selectAll("*").remove();lb.append("div").attr("class","legend-title").text("论文数量");
  const svg=lb.append("svg").attr("width",240).attr("height",32);
  const g=svg.append("defs").append("linearGradient").attr("id","mlg");g.append("stop").attr("offset","0%").attr("stop-color","#0d2137");g.append("stop").attr("offset","100%").attr("stop-color","#ebf5fb");
  svg.append("rect").attr("x",0).attr("y",2).attr("width",180).attr("height",14).attr("rx",3).style("fill","url(#mlg)");
  for(let i=0;i<=4;i++){const v=Math.round(maxVal*i/4);svg.append("text").attr("x",180*i/4).attr("y",28).attr("text-anchor","middle").style("fill","#667").style("font-size","9px").text(v);}
}

function drawRankList(){
  const c=d3.select("#rankList");c.selectAll("*").remove();
  const entries=Object.values(COUNTRY_DATA).map(d=>({...d,papers:currentMode==="125"?d.papers_125:currentMode==="135"?d.papers_135:d.papers_sum})).sort((a,b)=>b.papers-a.papers);
  const mp=entries[0]?.papers||1;
  c.selectAll(".rank-row").data(entries).join("div").attr("class","rank-row")
    .html((d,i)=>`<span class="rank-badge${i<3?' top'+(i+1):''}">${i+1}</span><span class="rank-name">${d.name_cn}</span><span class="rank-val">${d.papers.toLocaleString()} 篇</span><span class="rank-bar" style="width:${Math.max(d.papers/mp*80,3)}px;background:${i<3?'#4fc3f7':'#555'}"></span>`);
}

function showTooltip(e,h){d3.select("#tooltip").html(h).style("opacity",1).style("left",(e.pageX+14)+"px").style("top",(e.pageY-10)+"px")}
function hideTooltip(){d3.select("#tooltip").style("opacity",0)}

d3.selectAll(".mode-btn").on("click",function(){currentMode=this.dataset.mode;d3.selectAll(".mode-btn").classed("active",function(){return this.dataset.mode===currentMode});updateAll()});
d3.select("#labelToggle").on("click",function(){showLabels=!showLabels;d3.select(this).classed("active",showLabels).text(showLabels?"机构标签: 开":"机构标签: 关");updateAll()});
function zoomIn(){const el=document.querySelector("#mapChart svg");if(!el)return;const z=d3.zoom().scaleExtent([1,15]);d3.select(el).transition().duration(300).call(z.scaleBy,1.5)}
function zoomOut(){const el=document.querySelector("#mapChart svg");if(!el)return;const z=d3.zoom().scaleExtent([1,15]);d3.select(el).transition().duration(300).call(z.scaleBy,0.65)}
function zoomReset(){const el=document.querySelector("#mapChart svg");if(!el)return;d3.select("#mapGroup").attr("transform",null);const z=d3.zoom().scaleExtent([1,15]);d3.select(el).transition().duration(300).call(z.transform,d3.zoomIdentity)}
function updateAll(){drawMap();drawRankList()}
updateAll();
</script>
</body>
</html>"""

html = html.replace("__GEO_JSON__", geo_json_str)
html = html.replace("__COUNTRY_DATA__", json.dumps(country_data, ensure_ascii=False))
html = html.replace("__NEIGHBOR_LIST__", json.dumps(list(NEIGHBOR_ISO.keys())))
html = html.replace("__INSTITUTIONS_JSON__", json.dumps(institutions_data, ensure_ascii=False))
write_html(os.path.join(OUTPUT_DIR, "cee_map_visualization.html"), html, "地理分布热力图")
print(f"  Countries: {len(country_data)}, Features: {len(geo_filtered['features'])}")
print("Done.")
