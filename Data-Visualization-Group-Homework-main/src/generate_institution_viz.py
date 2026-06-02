"""
生成合作机构排名对比图：中国机构 Top15 vs 中东欧机构 Top15。
数据源：使用 125-135 合并排名表（125/135 数据已在同一行匹配）。
"""
import json, os
import pandas as pd

from common import (
    BASE_DIR, DIR_INSTITUTION, CEE_EXACT, TECH_BLUE_THEME as T,
    read_excel_safe, write_html, write_common_css, OUTPUT_DIR,
)

write_common_css()

def _safe_int(val):
    """安全转 int，失败返回 0。"""
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0

# ── 读取中国机构 125-135 合并表 ──────────────────────────────────
# 列: 135排名, 机构名, 135发文量, 占比, 125发文量, 增长率, 125排名, 位次变化
df_cn = read_excel_safe(
    os.path.join(DIR_INSTITUTION, "125-135中国机构所发合作文章数量.xlsx"),
    description="125-135中国机构",
)
cn_top = []
for _, row in df_cn.iterrows():
    name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
    if not name or name == "nan":
        continue
    p125 = _safe_int(row.iloc[4])
    p135 = _safe_int(row.iloc[2])
    rank_125 = _safe_int(row.iloc[6])
    rank_135 = _safe_int(row.iloc[0])
    rank_change = _safe_int(row.iloc[7]) if pd.notna(row.iloc[7]) else rank_125 - rank_135
    cn_top.append({
        "name": name, "name_en": "",
        "p125": p125, "p135": p135,
        "rank_total": 0,  # 后面重新计算
        "rank_125": rank_125,
        "rank_135": rank_135,
        "rank_change": rank_change,
        "delta": p135 - p125,
    })

# 计算 rank_total
cn_sorted = sorted(cn_top, key=lambda x: x["p125"] + x["p135"], reverse=True)
for i, inst in enumerate(cn_sorted):
    inst["rank_total"] = i + 1

# ── 读取中东欧机构 125-135 合并表 ──────────────────────────────
# 列: 135排名, 机构名, 国家, 135发文量, 占比, 125发文量, 占比, 125排名
df_cee = read_excel_safe(
    os.path.join(DIR_INSTITUTION, "125-135中东欧机构所发合作文章数量.xlsx"),
    description="125-135中东欧机构",
)
cee_top = []
for _, row in df_cee.iterrows():
    name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
    if not name or name == "nan":
        continue
    country = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
    p125 = _safe_int(row.iloc[5])
    p135 = _safe_int(row.iloc[3])
    rank_125 = _safe_int(row.iloc[7])
    rank_135 = _safe_int(row.iloc[0])
    rank_change = rank_125 - rank_135
    cee_top.append({
        "name": name, "name_en": "", "country": country,
        "p125": p125, "p135": p135,
        "rank_total": 0,
        "rank_125": rank_125,
        "rank_135": rank_135,
        "rank_change": rank_change,
        "delta": p135 - p125,
    })

cee_sorted = sorted(cee_top, key=lambda x: x["p125"] + x["p135"], reverse=True)
for i, inst in enumerate(cee_sorted):
    inst["rank_total"] = i + 1

print(f"CN institutions: {len(cn_top)}, CEE institutions: {len(cee_top)}")

html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>合作机构排名</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<link rel="stylesheet" href="common.css">
<style>
.main{display:grid;grid-template-columns:1fr 1fr;gap:24px;max-width:1400px;width:95%;margin:20px auto}
.panel{background:#fff;border:1px solid var(--c-border-lt);border-radius:16px;padding:24px 20px 18px;box-shadow:0 2px 12px rgba(0,0,0,0.06);min-height:480px}
.panel-head{display:flex;align-items:baseline;gap:8px;margin-bottom:4px}
.panel h3{font-size:16px;font-weight:700;margin:0}
.panel .sub{font-size:11px;color:#999;margin-bottom:16px}
.chart{width:100%}
.c-blue{color:var(--c-primary)}.c-purple{color:#3949ab}
.rank-change{display:inline-block;font-size:10px;margin-left:4px}
.rank-change.up{color:#2e7d32}
.rank-change.down{color:#c62828}
.rank-change.same{color:#999}
.chart-row{display:flex;align-items:center;gap:8px;padding:2px 0}
.chart-rank{flex:0 0 20px;text-align:center}
.chart-name{flex:0 0 150px;font-size:11px;color:#333;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.chart-bar-wrap{flex:1;height:22px;position:relative;display:flex;align-items:stretch}
.chart-bar-bg{position:absolute;inset:0;background:#f5f5f5;border-radius:4px}
.chart-bar-fill{position:absolute;top:0;height:100%;border-radius:4px;opacity:0.85;transition:width 0.7s}
.chart-bar-fill.positive{left:50%;background:#69f0ae}
.chart-bar-fill.negative{right:50%;background:#ff6e40}
.chart-bar-center{position:absolute;left:50%;top:0;width:1px;height:100%;background:#e0e0e0;transform:translateX(-0.5px)}
.chart-val{flex:0 0 65px;font-size:11px;color:#555;text-align:right;font-weight:500}
.chart-val.positive{color:#2e7d32}
.chart-val.negative{color:#c62828}
.tooltip-inner{padding:10px 14px}
.tooltip-inner b{color:var(--c-blue);font-size:13px}
.tooltip-inner .detail{font-size:11px;color:#ddd;line-height:1.7}
//.stats-summary{display:flex;justify-content:center;gap:32px;padding:14px 20px;background:#fff;border-bottom:1px solid var(--c-border-ft)}
//.stats-summary .item{text-align:center}
//.stats-summary .num{font-size:20px;font-weight:800;color:var(--c-primary)}
//.stats-summary .label{font-size:11px;color:#999;margin-top:2px}
@media(max-width:960px){.main{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="header"><h1>合作机构排名对比</h1><p>基于完整明细数据 | 中国 Top 15 vs 中东欧 Top 15 | 含 125/135 分期排名</p></div>
<div class="stats-summary" id="statsSummary"></div>
<div class="controls">
  <button class="mode-btn active" data-mode="total">总体 (125+135)</button>
  <div class="sep"></div>
  <button class="mode-btn" data-mode="125">125 期间</button>
  <button class="mode-btn" data-mode="135">135 期间</button>
  <button class="mode-btn delta" data-mode="delta">变化 (125→135)</button>
</div>
<div class="main">
  <div class="panel" id="panelCN">
    <div class="panel-head"><h3 class="c-blue">中国机构 Top 15</h3></div>
    <div class="sub" id="subCN">按 125+135 总发文量排序</div>
    <div class="chart" id="chartCN"></div>
  </div>
  <div class="panel" id="panelCEE">
    <div class="panel-head"><h3 class="c-purple">中东欧机构 Top 15</h3></div>
    <div class="sub" id="subCEE">按 125+135 总发文量排序 · 含国别</div>
    <div class="chart" id="chartCEE"></div>
  </div>
</div>
<div class="tooltip" id="tooltip"></div>
<script>
const CN = __CN_DATA__;
const CEE = __CEE_DATA__;
let currentMode = "total";

function getVal(d){
  if(currentMode==="125") return d.p125;
  if(currentMode==="135") return d.p135;
  if(currentMode==="delta") return d.delta;
  return d.p125+d.p135;
}
function getRank(d){
  if(currentMode==="125") return d.rank_125;
  if(currentMode==="135") return d.rank_135;
  return d.rank_total;
}
function getRankLabel(d){
  var rc=d.rank_change;
  if(rc>0) return {cls:"up",txt:"↑"+rc};
  if(rc<0) return {cls:"down",txt:"↓"+Math.abs(rc)};
  return {cls:"same",txt:"−"};
}

// d3.select("#statsSummary").html(
//   '<div class="item"><div class="num">'+CN.length+'</div><div class="label">中国机构(全量)</div></div>'+
//   '<div class="item"><div class="num">'+CEE.length+'</div><div class="label">中东欧机构(全量)</div></div>'+
//   '<div class="item"><div class="num">'+d3.sum(CN,d=>d.p125+d.p135).toLocaleString()+'</div><div class="label">中国总论文</div></div>'+
//   '<div class="item"><div class="num">'+d3.sum(CEE,d=>d.p125+d.p135).toLocaleString()+'</div><div class="label">中东欧总论文</div></div>'
// );

function drawPanel(containerId, data, accentColor, showCountry){
  var c=d3.select("#"+containerId);
  var isDelta=currentMode==="delta";
  var sorted=[...data].sort((a,b)=>getVal(b)-getVal(a));
  var vals=sorted.map(d=>getVal(d));
  var maxV=isDelta?d3.max(vals.map(Math.abs))||1:d3.max(vals)||1;

  c.selectAll(".chart-row").data(sorted).join(
    enter=>{
      var row=enter.append("div").attr("class","chart-row").style("opacity",0);
      row.transition().duration(400).delay((d,i)=>i*40).style("opacity",1);

      var rk=row.append("span").attr("class","chart-rank");
      if(isDelta){
        rk.append("span").attr("class",function(){return ""}).style("display","none");
      }else{
        rk.append("span").attr("class",d=>"rank-badge"+(getRank(d)<=3?" top"+getRank(d) :"")).text((d,i)=>i+1);
      }

      var nm=row.append("span").attr("class","chart-name")
        .text(d=>{var n=d.name.length>12?d.name.slice(0,11)+"..":d.name;if(showCountry&&d.country)n+=" ("+d.country+")";return n;});
      if(isDelta){
        var rcSpan=nm.append("span").attr("class",d=>"rank-change "+getRankLabel(d).cls).style("margin-left","3px");
        rcSpan.text(d=>getRankLabel(d).txt);
      }

      var bw=row.append("span").attr("class","chart-bar-wrap");
      bw.append("span").attr("class","chart-bar-bg");
      if(isDelta){
        bw.append("span").attr("class","chart-bar-center");
        var barPct=d=>(Math.abs(getVal(d))/maxV*50)+"%";
        var positiveFill=bw.filter(d=>getVal(d)>=0).append("span").attr("class","chart-bar-fill positive").style("width","0%");
        var negativeFill=bw.filter(d=>getVal(d)<0).append("span").attr("class","chart-bar-fill negative").style("width","0%");
        setTimeout(function(){
          positiveFill.style("width",barPct);
          negativeFill.style("width",barPct);
        },50);
      }else{
        bw.append("span").attr("class","chart-bar-fill").style("background",accentColor).style("left","0").style("width",d=>(getVal(d)/maxV*100)+"%");
      }

      var valText=isDelta?(d=>(getVal(d)>=0?"+"+getVal(d):getVal(d)).toLocaleString()+" 篇"):(d=>getVal(d).toLocaleString()+" 篇");
      row.append("span").attr("class",d=>"chart-val"+(isDelta?(getVal(d)>=0?" positive":" negative"):"")).text(valText);

      row.on("mouseenter",function(e,d){
        d3.select(this).select(".chart-bar-fill").style("opacity",1);
        var html='<div class="tooltip-inner"><b>'+d.name+'</b>'+(d.name_en?'<br><span style="color:#aaa;font-size:10px">'+d.name_en+'</span>':'');
        if(showCountry&&d.country) html+='<br><span style="color:#aaa;font-size:10px">'+d.country+'</span>';
        html+='<div class="detail">'+
          '125: '+d.p125.toLocaleString()+' 篇 (第'+d.rank_125+')<br>'+
          '135: '+d.p135.toLocaleString()+' 篇 (第'+d.rank_135+')<br>'+
          '合计: '+(d.p125+d.p135).toLocaleString()+' 篇<br>'+
          '变化: '+(d.delta>=0?'+':'')+d.delta+' 篇<br>'+
          '排名: '+getRankLabel(d).txt;
        d3.select("#tooltip").html(html).style("opacity",1);
      })
      .on("mousemove",function(e){d3.select("#tooltip").style("left",(e.pageX+14)+"px").style("top",(e.pageY-10)+"px")})
      .on("mouseleave",function(){
        d3.select(this).select(".chart-bar-fill").style("opacity",0.85);
        d3.select("#tooltip").style("opacity",0);
      });
    }
  );
}

function renderAll(){
  var modeLabels={"total":"125+135","125":"125","135":"135","delta":"变化量 (125→135)"};
  var isDelta=currentMode==="delta";

  // 按当前模式动态选取 Top 15
  var cnTop15=[...CN].sort((a,b)=>getVal(b)-getVal(a)).slice(0,15);
  var ceeTop15=[...CEE].sort((a,b)=>getVal(b)-getVal(a)).slice(0,15);

  d3.select("#subCN").text((isDelta?"按变化量排序 | ":"按 "+modeLabels[currentMode]+" 排序 | ")+"Top 15 · 候选池 "+CN.length+" 个");
  d3.select("#subCEE").text((isDelta?"按变化量排序 | ":"按 "+modeLabels[currentMode]+" 排序 | ")+"含国别 | Top 15 · 候选池 "+CEE.length+" 个");
  var cnColor=isDelta?"#69f0ae":"#4fc3f7";
  var ceeColor=isDelta?"#69f0ae":"#7c4dff";
  drawPanel("chartCN", cnTop15, cnColor, false);
  drawPanel("chartCEE", ceeTop15, ceeColor, true);
}

d3.selectAll(".mode-btn").on("click",function(){
  currentMode=this.dataset.mode;
  d3.selectAll(".mode-btn").classed("active",function(){return this.dataset.mode===currentMode});
  d3.selectAll(".mode-btn.delta").classed("active",currentMode==="delta");
  d3.select("#chartCN").selectAll("*").remove();
  d3.select("#chartCEE").selectAll("*").remove();
  renderAll();
});

renderAll();
</script>
</body>
</html>"""

html = html.replace("__CN_DATA__", json.dumps(cn_top, ensure_ascii=False))
html = html.replace("__CEE_DATA__", json.dumps(cee_top, ensure_ascii=False))
write_html(os.path.join(OUTPUT_DIR, "institution_visualization.html"), html, "机构排名")
print(f"  中国机构(候选池): {len(cn_top)}, 中东欧机构(候选池): {len(cee_top)}")
print("Done.")
