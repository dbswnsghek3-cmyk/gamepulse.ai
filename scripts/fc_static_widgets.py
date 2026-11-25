"""FC 온라인 정적 사이트 위젯 — gamepulse/sim/fc_biz.py 와 같은 식의 JavaScript.

fcvoc : VOC 50건 주제 필터 · 검색 (원문 링크 포함)
fcpower : BP 실질 구매력
fckeep : 기존 결제 유저 이탈 방지 (프리셋·초기화·가정값)
fcfunnel : MY CLUB WAR 퍼널 (프리셋·초기화·가정값 · 시나리오 차트)
"""

from __future__ import annotations

import html as H
import json
from collections import Counter
from pathlib import Path

PCT = {"churn0", "churn1", "visit", "signup", "d7", "d30", "pur"}


def _j(o) -> str:
    return json.dumps(o, ensure_ascii=False).replace("</", "<\\/")


def _won_js() -> str:
    return ("function won(x){var a=Math.abs(x),s=x<0?'−':'';if(a>=1e8)return s+(a/1e8).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})+'억 원';"
            "return s+Math.round(a/1e4).toLocaleString('en-US')+'만 원';}function n0(x){return Math.round(x).toLocaleString('en-US');}")


def _inputs(prefix: str, cfg: dict) -> str:
    pres = "".join(f'<button type="button" class="ox-btn" data-pre="{H.escape(n)}">{H.escape(n)}</button>' for n in cfg["presets"])
    ins = "".join(f'<label class="ox-f"><span>{H.escape(lab)}</span><input type="number" data-k="{k}" min="{lo}" max="{hi}" step="{st}"></label>'
                  for k, lab, lo, hi, st in cfg["fields"])
    return (f'<div class="ox-presets">{pres}<button type="button" class="ox-btn" data-pre="__reset">초기화</button></div>'
            f'<details class="sx-exp"><summary>가정값 바꾸기 <span class="sx-more">펼쳐보기</span></summary><div class="sx-exp-b"><div class="ox-fields three">{ins}</div></div></details>')


def _wire(box_id: str, cfg: dict) -> str:
    return (f"var C={_j({'f': cfg['fields'], 'd': cfg['defaults'], 'p': cfg['presets']})}, box=document.getElementById('{box_id}'), ins=box.querySelectorAll('input[data-k]');"
            "function clamp(x0){var x={};C.f.forEach(function(f){var v=parseFloat(x0[f[0]]);if(!isFinite(v))v=C.d[f[0]];x[f[0]]=Math.min(Math.max(v,f[2]),f[3]);});return x;}"
            "function cur(){var x={};ins.forEach(function(i){x[i.dataset.k]=i.value;});return x;}function setv(x){ins.forEach(function(i){i.value=x[i.dataset.k];});}"
            "ins.forEach(function(i){i.addEventListener('input',draw);i.addEventListener('change',function(){setv(clamp(cur()));draw();});});"
            "box.querySelectorAll('[data-pre]').forEach(function(b){b.addEventListener('click',function(){var n=b.dataset.pre;setv(n==='__reset'?C.d:Object.assign({},C.d,C.p[n]));draw();});});")


def voc(d: dict) -> str:
    V = d["voc"]
    order = [c for c, _ in Counter(v["cat"] for v in V).most_common()]
    opts = "".join(f"<option>{H.escape(c)}</option>" for c in ["전체"] + order)
    rows = "".join(
        f'<tr data-c="{H.escape(v["cat"], quote=True)}" data-q="{H.escape((v["title"] + " " + v["summary"]).lower(), quote=True)}">'
        f'<td data-label="번호">{v["id"]}</td><td data-label="출처 · 작성일">{H.escape(v["src"])}<br><small>{H.escape(v["date"])}</small></td>'
        f'<td data-label="제목 (원문 링크)"><a href="{H.escape(v["url"], quote=True)}" target="_blank" rel="noopener">{H.escape(v["title"])}</a></td>'
        f'<td data-label="요약">{H.escape(v["summary"])}</td><td data-label="주제">{H.escape(v["cat"])}</td><td data-label="방향">{H.escape(v["tone"])}</td></tr>'
        for v in V)
    return (f'<div class="ox-w" id="fxVoc"><div class="ox-fields two"><label class="ox-f"><span>주제</span><select id="fxVocC">{opts}</select></label>'
            '<label class="ox-f ox-search"><span>검색 (제목·요약)</span><input type="search" id="fxVocQ" placeholder="예: 강화, 패드, 시세"></label></div>'
            '<p class="ox-note" id="fxVocN"></p><div class="gp-table-wrap ox-scroll"><table class="gp-table ow-table ox-mops fx-voc">'
            f'<tr><th>번호</th><th>출처 · 작성일</th><th>제목 (원문 링크)</th><th>요약</th><th>주제</th><th>방향</th></tr>{rows}</table></div></div>'
            "<script>(function(){var c=document.getElementById('fxVocC'),q=document.getElementById('fxVocQ'),tr=document.querySelectorAll('#fxVoc tr[data-c]');"
            "function f(){var k=q.value.trim().toLowerCase(),n=0;tr.forEach(function(t){var ok=(c.value==='전체'||t.dataset.c===c.value)&&(!k||t.dataset.q.indexOf(k)>=0);t.hidden=!ok;if(ok)n++;});"
            "document.getElementById('fxVocN').textContent=n+'건 표시 · 전체 '+tr.length+'건 · 제목을 누르면 원문';}"
            "c.addEventListener('change',f);q.addEventListener('input',f);f();})();</script>")


def power(d: dict) -> str:
    p = d["bp_power"]
    labs = [("c0", "기존 구단 가치 (조 BP)", p["club0"]), ("c1", "변경 후 구단 가치 (조 BP)", p["club1"]),
            ("t0", "기존 목표 선수 가격 (조 BP)", p["target0"]), ("t1", "변경 후 목표 선수 가격 (조 BP)", p["target1"])]
    ins = "".join(f'<label class="ox-f"><span>{lab}</span><input type="number" id="fxPw{k}" value="{v}" min="0" step="1"></label>' for k, lab, v in labs)
    return (f'<div class="ox-w" id="fxPw"><div class="ox-fields basic">{ins}</div><div id="fxPwOut"></div></div>'
            "<script>(function(){function g(k){var v=parseFloat(document.getElementById('fxPw'+k).value);return isFinite(v)&&v>=0?v:0;}"
            "function pct(x){return x===null?'—':(x>=0?'+':'−')+Math.abs(Math.round(x))+'%';}"
            "function draw(){var c0=g('c0'),c1=g('c1'),t0=g('t0'),t1=g('t1'),nom=c0>0?(c1/c0-1)*100:null,p0=t0>0?c0/t0:null,p1=t1>0?c1/t1:null,"
            "real=(p0&&p1!==null)?(p1/p0-1)*100:null;var it=[[pct(nom),'명목 구단 가치 변화'],[pct(real),'목표 선수 기준 구매력 변화'],[p1===null?'—':p1.toFixed(1)+'명분','지금 구단 가치로 살 수 있는 목표 선수']];"
            "document.getElementById('fxPwOut').innerHTML='<div class=\"ox-stats\">'+it.map(function(x){return '<div><b>'+x[0]+'</b><span>'+x[1]+'</span><small>가정 시뮬레이션</small></div>';}).join('')+'</div>';}"
            "document.querySelectorAll('#fxPw input').forEach(function(i){i.addEventListener('input',draw);});window.fxPower=function(a,b,c,e){"
            "document.getElementById('fxPwc0').value=a;document.getElementById('fxPwc1').value=b;document.getElementById('fxPwt0').value=c;document.getElementById('fxPwt1').value=e;draw();};draw();})();</script>")


def keep(d: dict) -> str:
    cfg = d["sims"]["keep"]
    return (f'<div class="ox-w" id="fxKeep"><div id="fxKeepRes"></div>{_inputs("fk", cfg)}</div><script>(function(){{{_won_js()}{_wire("fxKeep", cfg)}'
            "function sim(x0){var x=clamp(x0),l0=x.payers*x.churn0/100,l1=x.payers*x.churn1/100,k=l0-l1,m=k*x.arppu;return {x:x,lost0:l0,lost1:l1,kept:k,monthly:m,total:m*x.months};}"
            "function draw(){var r=sim(cur());document.getElementById('fxKeepRes').innerHTML='<div class=\"ox-res\"><div><span>기존 이탈 예상</span><b>'+n0(r.lost0)+'명</b><small>이탈률 '+r.x.churn0+'%</small></div>'"
            "+'<div><span>개선 후 이탈 예상</span><b>'+n0(r.lost1)+'명</b><small>이탈률 '+r.x.churn1+'%</small></div>'"
            "+'<div><span>추가 유지 유저</span><b>'+n0(r.kept)+'명</b><small>월 매출 보전 '+won(r.monthly)+'</small></div>'"
            "+'<div class=\"acc\"><span>'+r.x.months+'개월 누적 매출 보전</span><b>'+won(r.total)+'</b><small>순이익 아님 · 운영비 미차감</small></div></div>';}"
            "window.fxKeep=sim;setv(C.d);draw();})();</script>")


def funnel(d: dict) -> str:
    cfg = d["sims"]["funnel"]
    chart = ('<div class="ox-chart"><div class="ow-chart-h"><div class="ow-chart-t">보수적 · 기준 · 낙관적: 기대 매출 vs 마케팅 비용 <span class="ox-k sim">가정 시뮬레이션</span></div>'
             '<div class="ow-chart-u">만 원 · 진한 색 = 기대 매출, 회색 = 비용 · 방문·가입·잔존율만 바꿈</div></div><div id="fxFunC" class="sx-chart-c" style="height:320px"></div></div>')
    return (f'<div class="ox-w" id="fxFun"><div id="fxFunRes"></div>{_inputs("ff", cfg)}{chart}</div><script>(function(){{{_won_js()}{_wire("fxFun", cfg)}'
            "function sim(x0){var x=clamp(x0);x.d30=Math.min(x.d30,x.d7);var v=x.reach*x.visit/100,s=v*x.signup/100,d7=s*x.d7/100,d30=s*x.d30/100,ltv=x.pur/100*x.arppu*x.months,rev=d30*ltv,c=x.cost;"
            "function per(n){return n>0?c/n:null;}var den=d30*x.arppu*x.months;return {x:x,visits:v,signups:s,d7:d7,d30:d30,ltv:ltv,revenue:rev,cost:c,profit:rev-c,cpa:per(s),cost_d7:per(d7),cost_d30:per(d30),"
            "ratio:c>0?rev/c:null,bep_pur:den>0?c/den*100:null};}"
            "function w(x){return x===null?'—':(Math.abs(x)>=1e4?won(x):n0(x)+'원');}"
            "function draw(){var r=sim(cur());document.getElementById('fxFunRes').innerHTML='<div class=\"fx-funnel\"><span>방문 '+n0(r.visits)+'</span><i>→</i><span>가입 '+n0(r.signups)+'</span><i>→</i><span>D7 '+n0(r.d7)+'</span><i>→</i><span>D30 '+n0(r.d30)+'</span></div>'"
            "+'<div class=\"ox-res\"><div><span>신규 가입 CPA</span><b>'+w(r.cpa)+'</b><small>D7 1명당 '+w(r.cost_d7)+' · D30 1명당 '+w(r.cost_d30)+'</small></div>'"
            "+'<div><span>D30 잔존 1명 LTV</span><b>'+w(r.ltv)+'</b><small>결제율 × 월 결제액 × '+r.x.months+'개월</small></div>'"
            "+'<div><span>기대 매출 ÷ 비용</span><b>'+(r.ratio===null?'—':Math.round(r.ratio*100)+'%')+'</b><small>기대 매출 '+won(r.revenue)+' · 비용 '+won(r.cost)+'</small></div>'"
            "+'<div class=\"'+(r.profit<0?'neg':'acc')+'\"><span>비용 차감 후</span><b>'+won(r.profit)+'</b><small>손익분기 결제율 '+(r.bep_pur===null?'—':r.bep_pur.toFixed(1)+'%')+'</small></div></div>'"
            "+'<p class=\"ox-note\">신규 유저 마케팅은 첫 몇 달 안에 비용을 회수하기 어렵다 → 판단 기준은 허용 가능한 CPA(가입자 1명의 기대 매출)와 D30 잔존이다.</p>';"
            "if(!window.Plotly)return;var names=Object.keys(C.p),sc=names.map(function(n){var p=Object.assign({},C.d,C.p[n]),y=Object.assign({},r.x);['visit','signup','d7','d30'].forEach(function(k){y[k]=p[k];});return sim(y);});"
            "Plotly.react('fxFunC',[{type:'bar',x:names,y:sc.map(function(s){return s.revenue/1e4;}),name:'기대 매출 (D30 잔존 × LTV)',marker:{color:'#16A34A'},text:sc.map(function(s){return won(s.revenue);}),textposition:'outside',cliponaxis:false},"
            "{type:'bar',x:names,y:sc.map(function(s){return s.cost/1e4;}),name:'마케팅 비용',marker:{color:'#9CA3AF'},text:sc.map(function(s){return won(s.cost);}),textposition:'outside',cliponaxis:false}],"
            "{barmode:'group',margin:{l:60,r:16,t:30,b:40},legend:{orientation:'h',y:1.12,x:0},yaxis:{title:'만 원',tickformat:',',rangemode:'tozero',gridcolor:'#EEF2F7'},plot_bgcolor:'#fff',paper_bgcolor:'#fff',font:{size:12}},{displayModeBar:false,responsive:true});}"
            "window.fxFunnel=sim;setv(C.d);draw();})();</script>")


def widgets(root: Path) -> dict[str, str]:
    d = json.loads((root / "data" / "fconline" / "fc2.json").read_text(encoding="utf-8"))
    return {"fcvoc": voc(d), "fcpower": power(d), "fckeep": keep(d), "fcfunnel": funnel(d)}
