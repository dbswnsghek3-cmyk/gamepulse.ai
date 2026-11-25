"""오버워치 정적 사이트용 JavaScript 데모 — YOUR CHOICE 패키지 · 신규 스킨+RE:START 손익 시뮬레이터.

Streamlit 화면의 ox-js-start ~ ox-js-end 구역을 이 HTML 로 바꾼다 (export_static.overwatch_body).
가정값·필드·프리셋은 data/overwatch/business.json, 계산식은 gamepulse/sim/ow_business.py 와 같은 순서로 옮겼다.
"""

from __future__ import annotations

import html as H
import json
import sys
from pathlib import Path


def _j(o) -> str:
    return json.dumps(o, ensure_ascii=False).replace("</", "<\\/")


def pkg_demo(root: Path) -> str:
    """YOUR CHOICE 선택형 패키지 시뮬레이터 · gamepulse/sim/ow_business.package_sim 과 같은 식."""
    sys.path.insert(0, str(root))
    from gamepulse.sim.ow_business import tier_prices
    bz = json.loads((root / "data" / "overwatch" / "business.json").read_text(encoding="utf-8"))
    ch = bz["your_choice"]
    s = ch["sim"]
    cfg = {"fields": s["fields"], "defaults": s["defaults"], "base": ch["base_price"], "n": [t["n"] for t in ch["tiers"]],
           "prices": tier_prices(ch)}
    inp = "".join(f'<label class="ox-f"><span>{H.escape(f["label"])} <small>({H.escape(f["unit"])})</small></span>'
                  f'<input type="number" data-p="{f["key"]}" min="{f["min"]}" max="{f["max"]}" step="{f["step"]}"></label>' for f in s["fields"])
    return f"""<div class="ox-demo-pkg" id="oxPkg"><div id="oxPkgRes"></div>
<div class="ox-fields three">{inp}</div><div class="ox-presets"><button type="button" class="ox-btn" id="oxPkgReset">초기화</button></div></div>
<script>(function(){{
var C={_j(cfg)};
var ins=document.querySelectorAll('#oxPkg input[data-p]');
function won(x){{var a=Math.abs(x), s=x<0?'−':''; if(a>=1e8) return s+(a/1e8).toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}})+'억 원'; return s+Math.round(a/1e4).toLocaleString('en-US')+'만 원';}}
function n0(x){{return Math.round(x).toLocaleString('en-US');}}
function sim(x0){{
  var x={{}}; C.fields.forEach(function(f){{var v=parseFloat(x0[f.key]); if(!isFinite(v)) v=C.defaults[f.key]; x[f.key]=Math.min(Math.max(v,f.min),f.max);}});
  var sh=[x.s1,x.s3,x.s5], tot=sh[0]+sh[1]+sh[2], ok=Math.abs(tot-100)<1e-6, rev0=x.exposed*x.conv0/100*C.base;
  var o={{x:x,total:tot,ok:ok,rev0:rev0}}; if(!ok) return o;
  var buyers=x.exposed*x.conv1/100, avg=0, nn=0, disc=0;
  for(var i=0;i<3;i++){{avg+=sh[i]/100*C.prices[i]; nn+=sh[i]/100*C.n[i]; disc+=sh[i]/100*(C.n[i]*C.base-C.prices[i]);}}
  o.buyers=buyers; o.avg=avg; o.rev1=buyers*avg; o.skins=buyers*nn; o.discount=buyers*disc; o.diff=o.rev1-rev0;
  o.diffPct=rev0>0?o.diff/rev0*100:null; o.discPct=(o.rev1+o.discount)>0?o.discount/(o.rev1+o.discount)*100:null; return o;
}}
function cur(){{var x={{}}; ins.forEach(function(i){{x[i.dataset.p]=i.value;}}); return x;}}
function setv(x){{ins.forEach(function(i){{i.value=x[i.dataset.p];}});}}
function draw(){{
  var r=sim(cur()), el=document.getElementById('oxPkgRes');
  if(!r.ok){{el.innerHTML='<div class="ox-verdict loss"><b>구매 비중 합계 '+(+r.total.toFixed(2))+'%</b> → 100%가 되도록 고쳐 주세요<small>개별 · 3개 · 5개 패키지 비중의 합이 100%일 때만 계산합니다.</small></div>'; return;}}
  el.innerHTML='<div class="ox-res"><div><span>예상 구매자</span><b>'+n0(r.buyers)+'명</b><small>노출 × 개선 후 전환율</small></div>'
   +'<div><span>평균 결제 금액</span><b>'+n0(r.avg)+'원</b><small>구매 비중 × 패키지 가격</small></div>'
   +'<div><span>예상 매출</span><b>'+won(r.rev1)+'</b><small>기존 '+won(r.rev0)+'</small></div>'
   +'<div class="'+(r.diff<0?'neg':'pos')+'"><span>기존 대비 증감</span><b>'+won(r.diff)+'</b><small>증감률 '+(r.diffPct===null?'—':(r.diffPct>=0?'+':'')+r.diffPct.toFixed(1)+'%')+'</small></div></div>'
   +'<p class="ox-note">할인으로 덜 받는 금액 '+won(r.discount)+' (정가 기준 매출의 '+(r.discPct===null?'—':r.discPct.toFixed(1)+'%')+') · 판매 스킨 '+n0(r.skins)+'개 · 기존 매출은 구매자가 개별 스킨 1개를 산다고 가정했다. 이미 여러 개를 개별로 사던 유저가 패키지로 옮기면 1인당 결제액은 오히려 줄 수 있다.</p>';
}}
ins.forEach(function(i){{i.addEventListener('input',draw); i.addEventListener('change',function(){{var x=sim(cur()).x; setv(x); draw();}});}});
document.getElementById('oxPkgReset').addEventListener('click',function(){{setv(C.defaults); draw();}});
window.oxPkgSim=sim;   /* 검증용 */
setv(C.defaults); draw();
}})();</script>"""


def biz_demo(root: Path) -> str:
    sys.path.insert(0, str(root))
    from gamepulse.sim.ow_business import D7_DAYS, DAYS, GUARD_TEXT, VERDICT_TEXT
    bz = json.loads((root / "data" / "overwatch" / "business.json").read_text(encoding="utf-8"))
    sim = bz["simulation"]

    def inp(f):
        return (f'<label class="ox-f"><span>{H.escape(f["label"])} <small>({H.escape(f["unit"])})</small></span>'
                f'<input type="number" data-k="{f["key"]}" min="{f["min"]}" max="{f["max"]}" step="{f["step"]}" title="{H.escape(f["help"])}"></label>')
    basic = "".join(inp(f) for f in sim["fields"] if f.get("basic"))
    adv = "".join(inp(f) for f in sim["fields"] if not f.get("basic"))
    presets = "".join(f'<button type="button" class="ox-btn" data-preset="{H.escape(n)}">{H.escape(n)}</button>' for n in sim["presets"])
    cfg = {"fields": sim["fields"], "defaults": sim["defaults"], "presets": sim["presets"], "days": sim.get("period_days", DAYS),
           "d7days": sim.get("d7_only_days", D7_DAYS), "vt": VERDICT_TEXT, "guard": GUARD_TEXT}
    chart = lambda i, h, t, u: (f'<div class="ox-chart"><div class="ow-chart-h"><div class="ow-chart-t">{t} <span class="ox-k sim">가정 시뮬레이션</span></div>'  # noqa: E731
                                f'<div class="ow-chart-u">{u}</div></div><div id="{i}" class="sx-chart-c" style="height:{h}px"></div></div>')
    return f"""<div class="ox-demo-biz" id="oxBiz">
<div id="oxBizRes"></div>
<div class="ox-presets">{presets}<button type="button" class="ox-btn" data-preset="__reset">초기화</button></div>
<div class="ox-fields basic">{basic}</div>
<details class="sx-exp ox-adv"><summary>고급 설정 · 잠식률 · 잔존율 개선폭 · PUR · ARPPU · 수수료 · 개발비 · 기타 운영비 <span class="sx-more">펼쳐보기</span></summary>
<div class="sx-exp-b"><div class="ox-fields">{adv}</div></div></details>
{chart("oxBizCurve", 340, "구매 전환율에 따른 분기 이익 · 점선 = 손익분기", "만 원 · 파랑 = 이익, 빨강 = 손실")}
<div class="ox-chart2">{chart("oxBizScen", 320, "보수적 · 기본 · 낙관적 시나리오 이익", "만 원 · 전환율·잠식률·잔존 개선·PUR·ARPPU만 바꾸고 나머지는 현재 입력")}
{chart("oxBizWf", 320, "총매출에서 이익까지 차감 구조", "만 원 · 파랑 = 더함, 회색 = 뺌")}</div>
<details class="sx-exp"><summary>계산 순서 · 공식 · 현재 값 <span class="sx-more">펼쳐보기</span></summary><div class="sx-exp-b" id="oxBizSteps"></div></details>
</div>
<script>(function(){{
var C={_j(cfg)}, F={{}}; C.fields.forEach(function(f){{F[f.key]=f;}});
var BLUE='#2563EB', GRAY='#94A3B8', RED='#DC2626';
var box=document.getElementById('oxBiz'), ins=box.querySelectorAll('input[data-k]');
function won(x){{var a=Math.abs(x), s=x<0?'−':''; if(a>=1e8) return s+(a/1e8).toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}})+'억 원'; return s+Math.round(a/1e4).toLocaleString('en-US')+'만 원';}}
function n0(x){{return Math.round(x).toLocaleString('en-US');}}
function clamp(x){{var o={{}}; C.fields.forEach(function(f){{var v=parseFloat(x[f.key]); if(!isFinite(v)) v=C.defaults[f.key]; o[f.key]=Math.min(Math.max(v,f.min),f.max);}}); o.d30_uplift=Math.min(o.d30_uplift,o.d7_uplift); return o;}}
function sim(x0){{
  var x=clamp(x0), fee=x.fee/100;
  var buyers=x.exposed*x.conv/100, gross=buyers*x.price, cannib=gross*x.cannib/100, skin=gross-cannib;
  var r30=x.inflow*x.d30_uplift/100, r7=x.inflow*(x.d7_uplift-x.d30_uplift)/100, active=r30+r7*C.d7days/C.days;
  var ret=active*x.pur/100*x.arppu, pre=skin+ret, feeAmt=pre*fee, net=pre-feeAmt;
  var dev=x.dev_mm*x.mm_cost, cost=dev+x.marketing+x.other_cost, profit=net-cost;
  var perPt=x.exposed/100*x.price*(1-x.cannib/100)*(1-fee), need=cost-ret*(1-fee), bep=null, st;
  if(need<=0){{bep=0;st='already';}} else if(perPt<=0){{st='impossible';}} else {{bep=need/perPt; st=bep<=100?'ok':'impossible';}}
  var bepB=(bep!==null&&st!=='impossible')?Math.ceil(x.exposed*bep/100):null, roi=cost>0?profit/cost*100:null, v;
  if(st==='already') v='profit'; else if(st==='impossible'||!bep) v='loss'; else {{var q=x.conv/bep; v=q>=1.2?'profit':(q>=0.8?'near':'loss');}}
  return {{x:x,buyers:buyers,gross:gross,cannib:cannib,skin:skin,active:active,ret:ret,fee:feeAmt,net:net,dev:dev,cost:cost,profit:profit,bep:bep,st:st,bepB:bepB,roi:roi,v:v}};
}}
function cur(){{var x={{}}; ins.forEach(function(i){{x[i.dataset.k]=i.value;}}); return x;}}
function setv(x){{ins.forEach(function(i){{i.value=x[i.dataset.k];}});}}
function lay(yt,xt){{return {{margin:{{l:70,r:20,t:16,b:48}},font:{{size:12}},showlegend:false,yaxis:{{title:yt,tickformat:',',zeroline:false,gridcolor:'#EEF2F7'}},xaxis:xt||{{}},plot_bgcolor:'#fff',paper_bgcolor:'#fff'}};}}
var P={{displayModeBar:false,responsive:true}};
function draw(){{
  var r=sim(cur()), x=r.x;
  var bep=r.st==='ok'?r.bep.toFixed(1)+'%':(r.st==='already'?'0%':'달성 불가');
  var bs={{ok:'구매 유저 '+(r.bepB===null?'—':n0(r.bepB))+'명 필요',already:'스킨 판매 없이도 손익분기',impossible:'현재 노출·가격·수수료로는 100%여도 미달'}}[r.st];
  var t=C.vt[r.v];
  document.getElementById('oxBizRes').innerHTML='<div class="ox-res"><div><span>예상 구매 유저</span><b>'+n0(r.buyers)+'명</b><small>노출 × 구매 전환율</small></div>'
   +'<div><span>순증 매출 (수수료 차감 후)</span><b>'+won(r.net)+'</b><small>스킨 '+won(r.skin)+' + 잔존 '+won(r.ret)+' (차감 전)</small></div>'
   +'<div class="'+(r.profit<0?'neg':'pos')+'"><span>예상 사업 이익</span><b>'+won(r.profit)+'</b><small>ROI '+(r.roi===null?'—':(r.roi>=0?'+':'')+Math.round(r.roi)+'%')+' · 총비용 '+won(r.cost)+'</small></div>'
   +'<div><span>손익분기 구매 전환율</span><b>'+bep+'</b><small>'+bs+'</small></div></div>'
   +'<div class="ox-verdict '+r.v+'"><b>'+t[0]+'</b> → '+t[1]+'<small>'+C.guard+'</small></div>';
  var steps=[['1 예상 구매 유저','노출 유저 × 구매 전환율',n0(r.buyers)+'명'],['2 신규 스킨 총매출','구매 유저 × 판매 가격',won(r.gross)],
   ['3 기존 상품 매출 잠식액','총매출 × 잠식률',won(-r.cannib)],['4 순증 상품 매출','2 − 3',won(r.skin)],
   ['5 순증 활성 유저','유입 × D30 개선폭 + 유입 × (D7 − D30 개선폭) × 30/91',n0(r.active)+'명'],['6 잔존 추가 매출','5 × PUR × ARPPU (분기)',won(r.ret)],
   ['7 수수료','(4 + 6) × '+x.fee+'%',won(-r.fee)],['8 수수료 차감 후 순증 매출','4 + 6 − 7',won(r.net)],
   ['9 총비용','개발 인월 × 인월당 비용 + 마케팅 + 기타',won(-r.cost)],['10 예상 사업 이익','8 − 9','<b>'+won(r.profit)+'</b>'],
   ['11 손익분기 구매 전환율','(총비용 − 잔존 매출 × (1 − 수수료)) ÷ (노출 × 가격 × (1 − 잠식률) × (1 − 수수료))',r.st==='ok'?r.bep.toFixed(2)+'%':(r.st==='already'?'0%':'달성 불가')],
   ['12 ROI','이익 ÷ 총비용',r.roi===null?'—':(r.roi>=0?'+':'')+r.roi.toFixed(1)+'%']];
  document.getElementById('oxBizSteps').innerHTML='<div class="gp-table-wrap"><table class="gp-table ow-table"><tr><th>단계</th><th>계산</th><th>현재 값</th></tr>'
   +steps.map(function(s){{return '<tr><td data-label="단계">'+s[0]+'</td><td data-label="계산">'+s[1]+'</td><td data-label="현재 값">'+s[2]+'</td></tr>';}}).join('')+'</table></div>'
   +'<p class="ox-note">분기(91일) 기준 · 수수료는 유저 결제액에만 적용 · 잔존 추가 매출은 스킨 매출과 따로 계산 · D30 잔존 유저는 D7 잔존 유저에 포함되므로 더하지 않음</p>';
  if(!window.Plotly) return;
  var hi=Math.min(100,Math.max(5,2*x.conv,r.st==='ok'?2*r.bep:0)), xs=[], ys=[];
  for(var i=0;i<41;i++){{var c=hi*i/40; xs.push(c); ys.push(sim(Object.assign({{}},x,{{conv:c}})).profit/1e4);}}
  var tr=[{{x:xs,y:ys.map(function(y){{return y>=0?y:null;}}),mode:'lines',line:{{color:BLUE,width:3}},hovertemplate:'%{{x:.1f}}% · %{{y:,.0f}}만 원<extra></extra>'}},
          {{x:xs,y:ys.map(function(y){{return y<0?y:null;}}),mode:'lines',line:{{color:RED,width:3}},hovertemplate:'%{{x:.1f}}% · %{{y:,.0f}}만 원<extra></extra>'}},
          {{x:[x.conv],y:[r.profit/1e4],mode:'markers',marker:{{size:12,color:r.profit>=0?BLUE:RED,line:{{color:'#fff',width:2}}}},hovertemplate:'현재 %{{x:.1f}}% · %{{y:,.0f}}만 원<extra></extra>'}}];
  var L=lay('분기 이익 (만 원)',{{title:'구매 전환율 (%)',ticksuffix:'%'}});
  L.shapes=[{{type:'line',xref:'paper',x0:0,x1:1,y0:0,y1:0,line:{{color:'#9CA3AF',width:1}}}}];
  if(r.st==='ok'){{L.shapes.push({{type:'line',x0:r.bep,x1:r.bep,yref:'paper',y0:0,y1:1,line:{{color:'#1F2937',dash:'dot',width:1}}}});
    L.annotations=[{{x:r.bep,y:0,text:'손익분기 '+r.bep.toFixed(1)+'%',showarrow:false,yshift:14,xanchor:'left',xshift:4}}];}}
  Plotly.react('oxBizCurve',tr,L,P);
  var names=Object.keys(C.presets), keys={{}}; names.forEach(function(n){{Object.keys(C.presets[n]).forEach(function(k){{keys[k]=1;}});}});
  var sc=names.map(function(n){{var p=Object.assign({{}},C.defaults,C.presets[n]), y=Object.assign({{}},x); Object.keys(keys).forEach(function(k){{y[k]=p[k];}}); return sim(y).profit/1e4;}});
  var L2=lay('분기 이익 (만 원)'); L2.shapes=[{{type:'line',xref:'paper',x0:0,x1:1,y0:0,y1:0,line:{{color:'#9CA3AF',width:1}}}}];
  Plotly.react('oxBizScen',[{{type:'bar',x:names,y:sc,marker:{{color:sc.map(function(v){{return v>=0?BLUE:RED;}})}},text:sc.map(function(v){{return won(v*1e4);}}),textposition:'outside',cliponaxis:false,hovertemplate:'%{{x}} · %{{y:,.0f}}만 원<extra></extra>'}}],L2,P);
  var wf=[['스킨 총매출',r.gross,'relative'],['잠식',-r.cannib,'relative'],['잔존 매출',r.ret,'relative'],['수수료',-r.fee,'relative'],
          ['개발비',-r.dev,'relative'],['마케팅',-x.marketing,'relative'],['기타',-x.other_cost,'relative'],['이익',r.profit,'total']];
  Plotly.react('oxBizWf',[{{type:'waterfall',x:wf.map(function(w){{return w[0];}}),y:wf.map(function(w){{return w[1]/1e4;}}),measure:wf.map(function(w){{return w[2];}}),
    increasing:{{marker:{{color:BLUE}}}},decreasing:{{marker:{{color:GRAY}}}},totals:{{marker:{{color:r.profit>=0?BLUE:RED}}}},connector:{{line:{{color:'#E5E7EB'}}}},
    text:wf.map(function(w){{return won(w[1]);}}),textposition:'outside',cliponaxis:false,hovertemplate:'%{{x}} · %{{y:,.0f}}만 원<extra></extra>'}}],lay('만 원'),P);
}}
ins.forEach(function(i){{i.addEventListener('input',draw); i.addEventListener('change',function(){{var x=clamp(cur()); setv(x); draw();}});}});
box.querySelectorAll('[data-preset]').forEach(function(b){{b.addEventListener('click',function(){{
  var n=b.dataset.preset; setv(n==='__reset'?C.defaults:Object.assign({{}},C.defaults,C.presets[n])); draw();}});}});
window.oxBizSim=sim;   /* 검증용 */
setv(C.defaults); draw();
}})();</script>"""


def demos(root: Path) -> dict[str, str]:
    return {"pkg": pkg_demo(root), "biz": biz_demo(root)}
