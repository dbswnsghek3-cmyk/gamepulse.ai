"""FC 온라인 정적 사이트 위젯 — gamepulse/sim/fc_biz.py 와 같은 식의 JavaScript.

fcvoc : VOC 50건 출처·주제·방향 필터 · 검색 (원문 링크 · 연결 기획)
fccare : CLUB CARE 대시보드 7/30/90일 탭
fcrebuild : CLUB REBUILD 유지형/전환형
fcrival : MY CLUB WAR 라이벌 매치 선택 · 참여
fcfandom : 팬덤 경쟁 점수 (fc_biz.fandom 과 같은 식)
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

    def sel(i, lab, items):
        return (f'<label class="ox-f"><span>{lab}</span><select id="{i}">'
                + "".join(f"<option>{H.escape(c)}</option>" for c in ["전체"] + items) + "</select></label>")
    rows = "".join(
        f'<tr data-s="{H.escape(v["src"], quote=True)}" data-c="{H.escape(v["cat"], quote=True)}" data-t="{H.escape(v["tone"], quote=True)}" '
        f'data-q="{H.escape((v["title"] + " " + v["summary"]).lower(), quote=True)}">'
        f'<td data-label="번호">{v["id"]}</td><td data-label="출처 · 작성일">{H.escape(v["src"])}<br><small>{H.escape(v["date"])}</small></td>'
        f'<td data-label="제목 (원문 링크)"><a href="{H.escape(v["url"], quote=True)}" target="_blank" rel="noopener">{H.escape(v["title"])}</a></td>'
        f'<td data-label="요약">{H.escape(v["summary"])}</td><td data-label="주제">{H.escape(v["cat"])}</td><td data-label="방향">{H.escape(v["tone"])}</td>'
        f'<td data-label="연결 기획">{H.escape(v["link"])}</td></tr>'
        for v in V)
    return (f'<div class="ox-w" id="fxVoc"><div class="ox-fields four">{sel("fxVocS", "출처", sorted({v["src"] for v in V}))}{sel("fxVocC", "주제", order)}'
            f'{sel("fxVocT", "방향", ["부정", "중립", "긍정"])}'
            '<label class="ox-f ox-search"><span>검색 (제목·요약)</span><input type="search" id="fxVocQ" placeholder="예: 강화, 패드, 시세"></label></div>'
            '<p class="ox-note" id="fxVocN"></p><div class="gp-table-wrap ox-scroll"><table class="gp-table ow-table ox-mops fx-voc">'
            f'<tr><th>번호</th><th>출처 · 작성일</th><th>제목 (원문 링크)</th><th>요약</th><th>주제</th><th>방향</th><th>연결 기획</th></tr>{rows}</table></div></div>'
            "<script>(function(){var S=document.getElementById('fxVocS'),c=document.getElementById('fxVocC'),T=document.getElementById('fxVocT'),q=document.getElementById('fxVocQ'),tr=document.querySelectorAll('#fxVoc tr[data-c]');"
            "function m(sel,v){return sel.value==='전체'||v===sel.value;}"
            "function f(){var k=q.value.trim().toLowerCase(),n=0;tr.forEach(function(t){var ok=m(S,t.dataset.s)&&m(c,t.dataset.c)&&m(T,t.dataset.t)&&(!k||t.dataset.q.indexOf(k)>=0);t.hidden=!ok;if(ok)n++;});"
            "document.getElementById('fxVocN').textContent=n?(n+'건 표시 · 전체 '+tr.length+'건 · 제목을 누르면 원문'):'조건에 맞는 VOC가 없습니다';}"
            "[S,c,T].forEach(function(e){e.addEventListener('change',f);});q.addEventListener('input',f);f();})();</script>")


def _switch(wid: str, opts: list, on: int = 0) -> str:
    """여러 화면을 미리 만들어 두고 버튼으로 하나만 보이게 (Streamlit 화면과 같은 HTML)."""
    btns = "".join(f'<button type="button" class="ox-pill{" on" if k == on else ""}" data-i="{k}">{H.escape(n)}</button>' for k, (n, _) in enumerate(opts))
    panes = "".join(f'<div data-p="{k}"{"" if k == on else " hidden"}>{v}</div>' for k, (_, v) in enumerate(opts))
    return (f'<div class="ox-w" id="{wid}"><div class="ox-pills">{btns}</div>{panes}</div>'
            f"<script>(function(){{var b=document.getElementById('{wid}');b.querySelectorAll('.ox-pills [data-i]').forEach(function(x){{x.addEventListener('click',function(){{"
            "b.querySelectorAll('.ox-pills [data-i]').forEach(function(y){y.classList.toggle('on',y===x);});"
            "b.querySelectorAll('[data-p]').forEach(function(p){p.hidden=p.dataset.p!==x.dataset.i;});});});})();</script>")


def care(d: dict) -> str:
    from gamepulse.views.fconline import _care_mock
    ps = list(d["care"]["mock"]["periods"])
    o = [(p, _care_mock(d["care"], p)) for p in ps]
    return _switch("fxCare", o, on=1)          # 기본 30일 (Streamlit index=1 과 같게)


def rebuild(d: dict) -> str:
    from gamepulse.views.fconline import _rebuild_mock
    return _switch("fxRb", [("팀컬러 유지형", _rebuild_mock(d["rebuild"], "keep")), ("신규 팀컬러 전환형", _rebuild_mock(d["rebuild"], "switch"))])


def rival(d: dict) -> str:
    from gamepulse.views.fconline import _rival_html, mock
    o = [(r["name"], mock("MY CLUB WAR · 라이벌 매치 · 점수·기간은 가상",
                          '<div class="fx-stadium"><div class="fx-war-h">MY CLUB WAR<small>시즌 1 · 라이벌 위크</small></div>'
                          + _rival_html(r) + "</div>", "night")) for r in d["mcw"]["rivals"]]
    return (_switch("fxRival", o) + '<button type="button" class="ox-btn pri" id="fxJoin">라이벌 매치 참여 (콘셉트 · +30점)</button>'
            "<script>(function(){var n=0;document.getElementById('fxJoin').addEventListener('click',function(){n+=30;"
            "document.querySelectorAll('#fxRival .fx-vs-meta span:last-child').forEach(function(s){s.textContent='나의 기여 +'+(180+n)+'점';});});})();</script>")


def fandom(d: dict) -> str:
    fs = d["fandom_sim"]
    ins = "".join(f'<label class="ox-f"><span>{H.escape(n)} 참여 인원</span><input type="number" data-r="{k}" data-c="p" value="{p}" min="0" max="10000000" step="1000"></label>'
                  f'<label class="ox-f"><span>{H.escape(n)} 1인당 평균 점수</span><input type="number" data-r="{k}" data-c="a" value="{a}" min="0" max="10000" step="1"></label>'
                  for k, (n, p, a) in enumerate(fs["rows"]))
    chart = ('<div class="ox-chart"><div class="ow-chart-h"><div class="ow-chart-t">최종 경쟁 점수 (0~100) <span class="ox-k sim">가정 시뮬레이션</span></div>'
             '<div class="ow-chart-u">점 · 가상 팬덤 3개</div></div><div id="fxFanC" class="sx-chart-c" style="height:260px"></div></div>')
    return (f'<div class="ox-w" id="fxFan"><label class="ox-f"><span>누적 활동 점수 반영 비중 (%) · 평균 비중은 100 − 이 값 : <b id="fxFanWv">{fs["w_total"]}</b></span>'
            f'<input type="range" id="fxFanW" min="0" max="100" step="1" value="{fs["w_total"]}"></label>'
            f'<div class="ox-fields two">{ins}</div><div id="fxFanT"></div>{chart}</div>'
            f"<script>(function(){{var N={_j([r[0] for r in fs['rows']])};"
            "function sim(rows,wt){var w=Math.min(Math.max(+wt||0,0),100)/100;var o=rows.map(function(r){var p=Math.max(+r[1]||0,0),a=Math.max(+r[2]||0,0);return {name:r[0],people:p,avg:a,total:p*a};});"
            "var mt=Math.max.apply(null,o.map(function(r){return r.total;}).concat([0])),ma=Math.max.apply(null,o.map(function(r){return r.avg;}).concat([0]));"
            "o.forEach(function(r){r.n_total=mt>0?r.total/mt*100:0;r.n_avg=ma>0?r.avg/ma*100:0;r.score=r.n_total*w+r.n_avg*(1-w);});"
            "['total','avg','score'].forEach(function(k){o.slice().sort(function(a,b){return b[k]-a[k];}).forEach(function(r,i){r['rank_'+k]=i+1;});});return o;}"
            "window.fxFandom=sim;var W=document.getElementById('fxFanW'),ins=document.querySelectorAll('#fxFan input[data-r]');"
            "function draw(){var rows=N.map(function(n){return [n,0,0];});ins.forEach(function(i){rows[+i.dataset.r][i.dataset.c==='p'?1:2]=i.value;});"
            "var w=+W.value,r=sim(rows,w),f=function(x){return x.toFixed(1);};document.getElementById('fxFanWv').textContent=w;"
            "document.getElementById('fxFanT').innerHTML='<div class=\"gp-table-wrap\"><table class=\"gp-table ow-table ox-mops\"><tr><th>팬덤 (가상)</th><th>누적 점수</th><th>정규화 누적</th><th>정규화 평균</th><th>최종 ('+w+':'+(100-w)+')</th><th>누적만 순위</th><th>평균만 순위</th><th>최종 순위</th></tr>'"
            "+r.map(function(x){return '<tr><td>'+x.name+'</td><td>'+Math.round(x.total).toLocaleString('en-US')+'</td><td>'+f(x.n_total)+'</td><td>'+f(x.n_avg)+'</td><td><b>'+f(x.score)+'</b></td><td>'+x.rank_total+'위</td><td>'+x.rank_avg+'위</td><td><b>'+x.rank_score+'위</b></td></tr>';}).join('')+'</table></div>';"
            "if(window.Plotly)Plotly.react('fxFanC',[{type:'bar',x:r.map(function(x){return x.name;}),y:r.map(function(x){return x.score;}),marker:{color:'#16A34A'},text:r.map(function(x){return f(x.score);}),textposition:'outside',cliponaxis:false}],"
            "{margin:{l:50,r:16,t:20,b:40},yaxis:{title:'최종 경쟁 점수',range:[0,110],gridcolor:'#EEF2F7'},plot_bgcolor:'#fff',paper_bgcolor:'#fff',font:{size:12},showlegend:false},{displayModeBar:false,responsive:true});}"
            "W.addEventListener('input',draw);ins.forEach(function(i){i.addEventListener('input',draw);});draw();})();</script>")


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
            "+'<div class=\"'+(r.total<0?'neg':'acc')+'\"><span>'+r.x.months+'개월 누적 매출 보전</span><b>'+won(r.total)+'</b><small>순이익 아님 · 운영비 미차감</small></div></div><p class=\"ox-note\">계산: 추가 유지 = 결제 유저 × (기존 이탈률 − 개선 후 이탈률) · 월 보전 = 추가 유지 × 월평균 결제 · 누적 = 월 보전 × 기간 · 이탈률이 오히려 오르면 음수로 표시</p>';}"
            "window.fxKeep=sim;setv(C.d);draw();})();</script>")


def funnel(d: dict) -> str:
    cfg = d["sims"]["funnel"]
    chart = ('<div class="ox-chart"><div class="ow-chart-h"><div class="ow-chart-t">보수적 · 기준 · 낙관적: 기대 매출 vs 총 캠페인 비용 <span class="ox-k sim">가정 시뮬레이션</span></div>'
             '<div class="ow-chart-u">만 원 · 초록 = 기대 매출, 회색 = 비용 · 방문·가입·잔존율만 바꿈</div></div><div id="fxFunC" class="sx-chart-c" style="height:320px"></div></div>')
    return (f'<div class="ox-w" id="fxFun"><div id="fxFunRes"></div>{_inputs("ff", cfg).replace("가정값 바꾸기 <span", "가정값 바꾸기 · 퍼널 5개 · 결제 3개 · 비용 8개 항목 <span")}{chart}</div><script>(function(){{{_won_js()}{_wire("fxFun", cfg)}'
            "function sim(x0){var x=clamp(x0);x.d30=Math.min(x.d30,x.d7);var v=x.reach*x.visit/100,s=v*x.signup/100,d7=s*x.d7/100,d30=s*x.d30/100,ltv=x.pur/100*x.arppu*x.months,rev=d30*ltv,c=0;Object.keys(x).forEach(function(k){if(k.indexOf('c_')===0)c+=x[k];});"
            "function per(n){return n>0?c/n:null;}var den=d30*x.arppu*x.months;return {x:x,visits:v,signups:s,d7:d7,d30:d30,ltv:ltv,revenue:rev,cost:c,profit:rev-c,cpa:per(s),cost_d7:per(d7),cost_d30:per(d30),"
            "ratio:c>0?rev/c:null,bep_pur:den>0?c/den*100:null};}"
            "function w(x){return x===null?'—':(Math.abs(x)>=1e4?won(x):n0(x)+'원');}"
            "function draw(){var r=sim(cur());document.getElementById('fxFunRes').innerHTML='<div class=\"fx-funnel\"><span>방문 '+n0(r.visits)+'</span><i>→</i><span>가입 '+n0(r.signups)+'</span><i>→</i><span>D7 '+n0(r.d7)+'</span><i>→</i><span>D30 '+n0(r.d30)+'</span></div>'"
            "+'<div class=\"ox-res\"><div><span>총 캠페인 비용</span><b>'+won(r.cost)+'</b><small>CPA '+w(r.cpa)+' · D30 1명당 '+w(r.cost_d30)+'</small></div>'"
            "+'<div><span>D30 잔존 1명 LTV (매출 기준)</span><b>'+w(r.ltv)+'</b><small>결제율 × 월 결제액 × '+r.x.months+'개월</small></div>'"
            "+'<div><span>LTV 합계 ÷ 비용</span><b>'+(r.ratio===null?'—':Math.round(r.ratio*100)+'%')+'</b><small>기대 매출 '+won(r.revenue)+'</small></div>'"
            "+'<div class=\"'+(r.profit<0?'neg':'acc')+'\"><span>반영 비용 차감 후</span><b>'+won(r.profit)+'</b><small>손익분기 결제율 '+(r.bep_pur===null?'—':r.bep_pur.toFixed(1)+'%')+' · 순이익 아님</small></div></div>'"
            "+'<p class=\"ox-note\">신규 유저 마케팅은 첫 몇 달 안에 비용을 회수하기 어렵다 → 판단 기준은 허용 가능한 CPA와 D30 잔존 · 라이선스·개발비는 미확정이라 기본 0원</p>';"
            "if(!window.Plotly)return;var names=Object.keys(C.p),sc=names.map(function(n){var p=Object.assign({},C.d,C.p[n]),y=Object.assign({},r.x);['visit','signup','d7','d30'].forEach(function(k){y[k]=p[k];});return sim(y);});"
            "Plotly.react('fxFunC',[{type:'bar',x:names,y:sc.map(function(s){return s.revenue/1e4;}),name:'기대 매출 (D30 잔존 × LTV)',marker:{color:'#16A34A'},text:sc.map(function(s){return won(s.revenue);}),textposition:'outside',cliponaxis:false},"
            "{type:'bar',x:names,y:sc.map(function(s){return s.cost/1e4;}),name:'총 캠페인 비용',marker:{color:'#9CA3AF'},text:sc.map(function(s){return won(s.cost);}),textposition:'outside',cliponaxis:false}],"
            "{barmode:'group',margin:{l:60,r:16,t:30,b:40},legend:{orientation:'h',y:1.12,x:0},yaxis:{title:'만 원',tickformat:',',rangemode:'tozero',gridcolor:'#EEF2F7'},plot_bgcolor:'#fff',paper_bgcolor:'#fff',font:{size:12}},{displayModeBar:false,responsive:true});}"
            "window.fxFunnel=sim;setv(C.d);draw();})();</script>")


def widgets(root: Path) -> dict[str, str]:
    d = json.loads((root / "data" / "fconline" / "fc2.json").read_text(encoding="utf-8"))
    return {"fcvoc": voc(d), "fcpower": power(d), "fccare": care(d), "fcrebuild": rebuild(d), "fcrival": rival(d),
            "fcfandom": fandom(d), "fckeep": keep(d), "fcfunnel": funnel(d)}
