"""오버워치 정적 사이트: Streamlit 위젯(선택·슬라이더·입력·버튼)을 실제로 동작하는 JavaScript 로 바꾼다.

Streamlit 화면의 <div class="ox-js-start" data-demo="키"> ~ ox-js-end 구역을 여기서 만든 HTML 로 교체한다.
데이터·계산식은 Streamlit 과 같은 원본(data/overwatch/*.json·*.csv, gamepulse/sim/restart_sim.py)을 쓴다.

- ops : 02 유저 의견 보기·방향·페이지·검색 (원문 링크 포함 전체 63건)
- a   : 03 A 복귀 브리핑 (마지막 접속 시점 선택 · 3분 요약 단계 이동 · 나중에 보기)
- b   : 03 B 전투 학습 카드 (상대 영웅·기술 선택 · 연습해 보기 · 다시 보지 않기)
- c   : 03 C 첫 10경기 미션 (진행 경기 수 · 미션 끄기)
- ss  : 06 표본 계산기
- ret : 06 잔존율 시뮬레이션 (설정 → D7·D30 · 첫 10경기 퍼널 · DAU)
"""

from __future__ import annotations

import html as H
import json
import math
import sys
from pathlib import Path
from statistics import NormalDist


def _j(o) -> str:
    return json.dumps(o, ensure_ascii=False, default=str).replace("</", "<\\/")


def _sel(i: str, label: str, opts: list[str], val: str = "") -> str:
    o = "".join(f'<option{" selected" if x == val else ""}>{H.escape(x)}</option>' for x in opts)
    return f'<label class="ox-f"><span>{H.escape(label)}</span><select id="{i}">{o}</select></label>'


def _num(i: str, label: str, v, lo, hi, step) -> str:
    return (f'<label class="ox-f"><span>{H.escape(label)}</span>'
            f'<input type="number" id="{i}" value="{v}" min="{lo}" max="{hi}" step="{step}"></label>')


# ----------------------------------------------------------------------
def ops_widget(root: Path) -> str:
    from gamepulse.data.overwatch_data import OPINION_CATEGORIES, load_json, load_opinions, opinion_codes
    from gamepulse.views.overwatch import _opinion_card
    rs = load_json("restart.json")
    ops = load_opinions()
    v = ops[ops["verified"]].sort_values("published_date", ascending=False)
    rep = set(rs["rep_opinions"])
    n_rep = int(v["opinion_id"].isin(rep).sum())
    items = [{"id": r["opinion_id"], "rep": r["opinion_id"] in rep, "codes": opinion_codes(r), "tone": r["sentiment"],
              "card": _opinion_card(r)} for _, r in v.iterrows()]
    cols = [("opinion_id", "의견 번호"), ("platform", "플랫폼"), ("published_date", "작성일"), ("user_type", "유형"), ("sentiment", "방향"),
            ("issue_category", "주 분류"), ("issue_tags", "보조 분류"), ("summary_ko", "요약"), ("quote_original", "원문 발췌")]
    rows = "".join(
        f'<tr data-q="{H.escape((str(r["summary_ko"]) + " " + str(r["quote_original"])).lower(), quote=True)}">'
        + "".join(f'<td data-label="{lab}">{H.escape(str(r[k]))}</td>' for k, lab in cols)
        + f'<td data-label="원문"><a href="{H.escape(str(r["source_url"]), quote=True)}" target="_blank" rel="noopener">열기</a></td>'
        f'<td data-label="확인일">{H.escape(str(r["collected_date"]))}</td></tr>' for _, r in v.iterrows())
    head = "".join(f"<th>{lab}</th>" for _, lab in cols) + "<th>원문</th><th>확인일</th>"
    rep_label = f"대표 의견 {n_rep}건"
    return f"""<div class="ox-w" id="oxOps">
<div class="ox-fields three">{_sel("oxOpsView", "보기", [rep_label] + OPINION_CATEGORIES, rep_label)}{_sel("oxOpsTone", "의견 방향", ["전체", "부정", "중립", "긍정"], "전체")}
<div class="ox-f"><span>페이지</span><div class="ox-pager"><button type="button" class="ox-btn" id="oxOpsPrev">이전</button><b id="oxOpsPage">1 / 1</b><button type="button" class="ox-btn" id="oxOpsNext">다음</button></div></div></div>
<div class="ow-grid2" id="oxOpsCards"></div>
<label class="ox-f ox-search"><span>전체 표 검색어 (요약·원문 발췌)</span><input type="search" id="oxOpsQ" placeholder="예: 영웅, 복귀, hero"></label>
<p class="ox-note" id="oxOpsCount"></p>
<div class="gp-table-wrap ox-scroll"><table class="gp-table ow-table" id="oxOpsTable"><tr>{head}</tr>{rows}</table></div></div>
<script>(function(){{
var D={_j(items)}, REP={_j(rep_label)}, per=4, page=1;
var view=document.getElementById('oxOpsView'), tone=document.getElementById('oxOpsTone');
function list(){{ return D.filter(function(o){{ return (view.value===REP ? o.rep : o.codes.indexOf(view.value)>=0) && (tone.value==='전체' || o.tone===tone.value); }}); }}
function draw(){{
  var L=list(), pages=Math.max(1, Math.ceil(L.length/per)); page=Math.min(Math.max(page,1),pages);
  var chunk=L.slice((page-1)*per, page*per);
  document.getElementById('oxOpsCards').innerHTML = chunk.length ? chunk.map(function(o){{return o.card;}}).join('') : '<div class="sx-alert info">조건에 맞는 의견이 없습니다.</div>';
  document.getElementById('oxOpsPage').textContent = page+' / '+pages+' · '+L.length+'건';
  document.getElementById('oxOpsPrev').disabled = page<=1; document.getElementById('oxOpsNext').disabled = page>=pages;
}}
view.addEventListener('change',function(){{page=1;draw();}}); tone.addEventListener('change',function(){{page=1;draw();}});
document.getElementById('oxOpsPrev').addEventListener('click',function(){{page--;draw();}});
document.getElementById('oxOpsNext').addEventListener('click',function(){{page++;draw();}});
var q=document.getElementById('oxOpsQ'), trs=document.querySelectorAll('#oxOpsTable tr[data-q]');
function filt(){{ var k=q.value.trim().toLowerCase(), n=0; trs.forEach(function(t){{ var ok=!k||t.dataset.q.indexOf(k)>=0; t.hidden=!ok; if(ok) n++; }});
  document.getElementById('oxOpsCount').textContent='표 '+n+'건 표시 · 전체 '+trs.length+'건 · 원문 링크는 각 행의 \\'열기\\''; }}
q.addEventListener('input',filt); draw(); filt();
}})();</script>"""


# ----------------------------------------------------------------------
def a_widget(root: Path) -> str:
    import pandas as pd
    from gamepulse.data.overwatch_data import load_json, load_timeline
    from gamepulse.views.overwatch import LAST_ACCESS
    heroes, tl = load_json("heroes.json"), load_timeline()
    data = {}
    for label, cutoff in LAST_ACCESS.items():
        new = [[h["name"], h["new_2026"][5:]] for h in heroes["heroes"] if h.get("new_2026") and h["new_2026"] > cutoff]
        changed = [h["name"] for h in heroes["heroes"] if h.get("role_changed") and h["role_changed"] > cutoff]
        rows = tl[tl["date"].notna() & (tl["type"] == "시스템") & tl["status"].str.startswith("공식") & (tl["date"] > pd.Timestamp(cutoff))]
        data[label] = {"new": new, "changed": changed, "sys": [[f"{r.date:%m-%d}", r.title] for r in rows.sort_values("date").itertuples()]}
    labels = list(LAST_ACCESS)
    radios = "".join(f'<button type="button" class="ox-pill{" on" if i == 0 else ""}" data-last="{H.escape(x)}">{H.escape(x)}</button>'
                     for i, x in enumerate(labels))
    return f"""<div class="ox-w" id="oxA"><div class="ox-f"><span>예시 계정의 마지막 접속 시점</span><div class="ox-pills">{radios}</div></div>
<div id="oxAHead"></div><div id="oxABody"></div></div>
<script>(function(){{
var D={_j(data)}, last={_j(labels[0])}, step=0;
var badge='<span class="gp-badge k-mock">기획 시안</span>';
function esc(s){{return String(s).replace(/[&<>"]/g,function(c){{return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c];}});}}
function draw(){{
  var d=D[last], total=d['new'].length+d.changed.length+d.sys.length;
  document.getElementById('oxAHead').innerHTML='<div class="ow-proto coral"><div class="ow-proto-bar"><span>RE:START 복귀 브리핑</span>'+badge+'</div>'
    +'<div class="ow-proto-h">다시 오신 것을 환영합니다</div><div class="ow-proto-s">마지막 접속 이후 <b>'+total+'개</b>가 바뀌었습니다 · 예상 3분</div>'
    +'<div class="ow-proto-chips"><span>신규 영웅 '+d['new'].length+'</span><span>바뀐 영웅 '+d.changed.length+'</span><span>새 시스템 '+d.sys.length+'</span></div></div>';
  var b=document.getElementById('oxABody');
  if(step===0){{ b.innerHTML='<div class="ox-btns"><button type="button" class="ox-btn pri" data-a="1">3분 요약 보기</button><button type="button" class="ox-btn" data-a="-1">나중에 보기</button></div>'; }}
  else if(step===-1){{ b.innerHTML='<div class="sx-alert info">메뉴 &gt; 복귀 브리핑에서 언제든 다시 볼 수 있습니다. (기획 시안)</div><div class="ox-btns"><button type="button" class="ox-btn" data-a="0">다시 열기</button></div>'; }}
  else if(step<=3){{
    var cards={{1:['1/3 · 새로 나온 영웅', d['new'].map(function(h){{return '<span class="ow-hero new">'+esc(h[0])+'<small>'+h[1]+'</small></span>';}}).join('')||'<p>이 기간에 새로 나온 영웅이 없습니다.</p>'],
      2:['2/3 · 바뀐 영웅', d.changed.map(function(h){{return '<span class="ow-hero changed">'+esc(h)+' · 공격 → 지원</span>';}}).join('')||'<p>역할이 바뀐 영웅이 없습니다.</p>'],
      3:['3/3 · 새 시스템', d.sys.length?'<ul>'+d.sys.map(function(r){{return '<li><b>'+r[0]+'</b> '+esc(r[1])+'</li>';}}).join('')+'</ul>':'<p>새 시스템 변경이 없습니다.</p>']}}[step];
    b.innerHTML='<div class="ow-proto-card mock coral"><div class="ow-proto-card-t">'+cards[0]+'</div><div class="ow-heroes small">'+cards[1]+'</div><div class="ow-proto-card-s">출처: 공식 패치노트·공식 영웅 페이지</div></div>'
      +'<div class="ox-btns"><button type="button" class="ox-btn" data-a="'+Math.max(step-1,0)+'">이전</button><button type="button" class="ox-btn pri" data-a="'+(step+1)+'">'+(step<3?'다음':'완료')+'</button><button type="button" class="ox-btn" data-a="-1">건너뛰기</button></div>';
  }} else {{ b.innerHTML='<div class="sx-alert success">브리핑 완료 · 이제 빠른 대전으로 감각을 되찾아 보세요. (기획 시안)</div><div class="ox-btns"><button type="button" class="ox-btn" data-a="0">처음으로</button></div>'; }}
}}
document.getElementById('oxA').addEventListener('click',function(e){{
  var p=e.target.closest('[data-last]'); if(p){{ last=p.dataset.last; step=0; document.querySelectorAll('#oxA [data-last]').forEach(function(x){{x.classList.toggle('on',x===p);}}); draw(); return; }}
  var a=e.target.closest('[data-a]'); if(a){{ step=+a.dataset.a; draw(); }}
}});
draw();
}})();</script>"""


# ----------------------------------------------------------------------
def b_widget(root: Path) -> str:
    from gamepulse.data.overwatch_data import load_json
    sk = load_json("heroes.json").get("skills_verified", [])
    data = {s["hero"]: {"skills": s["skills"], "source": s["source"]} for s in sk}
    heroes = list(data)
    return f"""<div class="ox-w" id="oxB"><div class="ox-fields two">{_sel("oxBHero", "어려웠던 상대 영웅 (유저가 선택)", heroes, heroes[0] if heroes else "")}
{_sel("oxBSkill", "확인할 기술", data[heroes[0]]["skills"] if heroes else [])}</div><div id="oxBCard"></div>
<div class="ox-btns"><button type="button" class="ox-btn pri" data-b="p">연습해 보기</button><button type="button" class="ox-btn" data-b="o">다시 보지 않기</button></div><div id="oxBMsg"></div></div>
<script>(function(){{
var D={_j(data)}, hs=document.getElementById('oxBHero'), ks=document.getElementById('oxBSkill');
var M={{p:'연습장으로 이동해 이 기술을 상대해 보는 흐름입니다. 실제 게임 연동은 블리자드 개발 협업이 필요합니다. (기획 시안)',
        o:'설정에서 카드 표시를 끄거나 하루 표시 횟수를 줄일 수 있습니다. (기획 시안)'}};
function esc(s){{return String(s).replace(/[&<>"]/g,function(c){{return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c];}});}}
function fill(){{ ks.innerHTML=D[hs.value].skills.map(function(s){{return '<option>'+esc(s)+'</option>';}}).join(''); }}
function draw(){{ var h=hs.value, s=ks.value;
  document.getElementById('oxBCard').innerHTML='<div class="ow-proto dark"><div class="ow-proto-bar"><span>전투 학습 카드 · 수동형</span><span class="gp-badge k-mock">기획 시안</span></div>'
   +'<div class="ow-proto-s">선택한 상대 <b>'+esc(h)+'</b> · 핵심 기술 1개와 대처 선택지</div><div class="ow-skill"><div class="ow-skill-icon">스킬<br>이미지<br>자리</div><div>'
   +'<div class="ow-skill-n">'+esc(s)+'</div><div class="ow-skill-d">기술 특징 · 공식 영웅 페이지 설명 연동 예정 <small>(검증 전 미입력)</small></div>'
   +'<div class="ow-skill-tip">대응 예시 · 혼자 정면으로 맞서지 말고 아군 근처에서 싸우기 <small>(예시 문구 · 게임 디자인 검수 필요)</small></div></div></div>'
   +'<div class="ow-proto-card-s">기술 이름: <a href="'+esc(D[h].source)+'" target="_blank" rel="noopener">공식 패치노트</a> 표기</div></div>';
  document.getElementById('oxBMsg').innerHTML=''; }}
hs.addEventListener('change',function(){{fill();draw();}}); ks.addEventListener('change',draw);
document.querySelectorAll('#oxB [data-b]').forEach(function(b){{b.addEventListener('click',function(){{document.getElementById('oxBMsg').innerHTML='<div class="sx-alert info">'+M[b.dataset.b]+'</div>';}});}});
draw();
}})();</script>"""


# ----------------------------------------------------------------------
def c_widget(root: Path) -> str:
    from gamepulse.views.overwatch import MISSIONS
    return f"""<div class="ox-w" id="oxC"><div class="ox-ctl"><label>진행한 경기 수 (예시) <output id="oxCV">4</output></label>
<input type="range" id="oxCR" min="0" max="10" step="1" value="4" aria-label="진행한 경기 수"><label class="ox-toggle"><input type="checkbox" id="oxCOff"> 미션 끄기</label></div>
<div id="oxCOut"></div></div>
<script>(function(){{
var M={_j(MISSIONS)}, r=document.getElementById('oxCR'), off=document.getElementById('oxCOff');
function esc(s){{return String(s).replace(/[&<>"]/g,function(c){{return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c];}});}}
function draw(){{ var n=+r.value; document.getElementById('oxCV').textContent=n; var o=document.getElementById('oxCOut');
  if(off.checked){{ o.innerHTML='<div class="sx-alert info">미션을 껐습니다. 언제든 다시 켤 수 있고 알림 빈도도 조절할 수 있습니다. (기획 시안)</div>'; return; }}
  var segs=''; for(var i=1;i<=10;i++) segs+='<span class="'+(i<=n?'on':'')+'">'+i+'</span>';
  var blocks=M.map(function(m){{ var a=m[0], b=m[1], done=n>=b, act=a<=n+1&&n+1<=b&&!done, st=done?'완료':(act?'진행 중':'대기');
    return '<div class="ow-mission '+(done?'done':(act?'active':''))+'"><div class="ow-mission-h">'+a+'~'+b+'경기 · 학습 목표: '+esc(m[2])+'<span>'+st+'</span></div>'
      +m[3].map(function(x){{return '<div class="ow-mission-i">'+(done?'✓':'○')+' '+esc(x[0])+'<small>확인: '+esc(x[1])+'</small></div>';}}).join('')+'</div>'; }}).join('');
  o.innerHTML='<div class="ow-proto narrow"><div class="ow-proto-bar"><span>첫 10경기 학습 미션</span><span class="gp-badge k-mock">기획 시안</span></div><div class="ow-progress">'+segs+'</div><div class="ow-grid3">'+blocks+'</div>'
   +'<div class="ow-proto-card-s">보상 예시: 외형 아이템 (확정 아님 · 경쟁 밸런스에 영향 없는 보상만 검토)</div></div>'; }}
r.addEventListener('input',draw); off.addEventListener('change',draw); draw();
}})();</script>"""


# ----------------------------------------------------------------------
def ss_widget(root: Path) -> str:
    from gamepulse.data.overwatch_data import load_json
    from gamepulse.sim.restart_sim import experiment_plan
    rs = load_json("restart.json")
    r = experiment_plan(rs["experiment"])["seg"]["복귀"]
    nd = NormalDist()
    za = {str(a): nd.inv_cdf(1 - a / 2) for a in (0.01, 0.05, 0.10)}
    zb = {str(p): nd.inv_cdf(p) for p in (0.8, 0.9)}
    return f"""<div class="ox-w" id="oxSS"><div class="ox-fields three">
{_num("oxSSBase", "대조군 D7 (%, 가정)", float(r["base"]["D7"]), 1, 99, 1)}{_num("oxSSMde", "MDE · 배정 기준 (%p)", round(float(r["mde"]["D7"]), 2), 0.1, 30, 0.1)}
{_num("oxSSPart", "기능 참여율 (%, 가정)", int(r["participation"]), 1, 100, 1)}{_sel("oxSSAlpha", "유의수준", ["0.01", "0.05", "0.1"], "0.05")}
{_sel("oxSSPower", "검정력", ["0.8", "0.9"], "0.8")}{_num("oxSSWeekly", "주당 유입 (명, 가정)", int(r["weekly"]), 100, 10000000, 1000)}</div><div id="oxSSOut"></div></div>
<script>(function(){{
var ZA={_j(za)}, ZB={_j(zb)};
function g(i){{return document.getElementById(i);}}
function cl(v,lo,hi,d){{v=parseFloat(v); if(!isFinite(v)) v=d; return Math.min(Math.max(v,lo),hi);}}
function n2(p1,p2,za,zb){{ if(!(p1>0&&p1<1&&p2>0&&p2<1)||p1===p2) return null; var pb=(p1+p2)/2;
  var num=Math.pow(za*Math.sqrt(2*pb*(1-pb))+zb*Math.sqrt(p1*(1-p1)+p2*(1-p2)),2); return Math.ceil(num/Math.pow(p2-p1,2)); }}
function draw(){{ var base=cl(g('oxSSBase').value,1,99,30), mde=cl(g('oxSSMde').value,0.1,30,2), part=cl(g('oxSSPart').value,1,100,40), wk=cl(g('oxSSWeekly').value,100,1e7,10000);
  var za=ZA[g('oxSSAlpha').value==='0.1'?'0.1':g('oxSSAlpha').value], zb=ZB[g('oxSSPower').value];
  var n=n2(base/100, Math.min(base+mde,99.9)/100, za, zb);
  var t=[['참여자 기준 필요 개선 폭','+'+(mde/part*100).toFixed(1)+'%p','MDE ÷ 참여율'],['그룹당 필요 표본',n===null?'—':n.toLocaleString('en-US')+'명','두 비율 차이 검정'],
         ['배정 기간',n===null?'—':Math.ceil(2*n/wk)+'주','두 그룹 합 ÷ 주당 유입']];
  g('oxSSOut').innerHTML='<div class="ow-tiles">'+t.map(function(x){{return '<div class="ow-tile"><div class="ow-tile-l">'+x[0]+'</div><div class="ow-tile-v">'+x[1]+'</div><div class="ow-tile-s">'+x[2]+'</div></div>';}}).join('')+'</div>'; }}
document.querySelectorAll('#oxSS input, #oxSS select').forEach(function(e){{e.addEventListener('input',draw); e.addEventListener('change',draw);}});
window.oxSSN=n2; draw();
}})();</script>"""


# ----------------------------------------------------------------------
RET_FIELDS = [  # (키, 라벨, 최소, 최대, 간격) · 기본값은 restart.json experiment
    ("n_new", "신규 코호트 (명)", 0, 10000000, 1000), ("n_ret", "복귀 코호트 (명)", 0, 10000000, 1000),
    ("new_D1", "신규 D1 (%)", 0, 100, 1), ("new_D7", "신규 D7 (%)", 0, 100, 1), ("new_D30", "신규 D30 (%)", 0, 100, 1),
    ("ret_D1", "복귀 D1 (%)", 0, 100, 1), ("ret_D7", "복귀 D7 (%)", 0, 100, 1), ("ret_D30", "복귀 D30 (%)", 0, 100, 1),
    ("p_new", "신규 미션 참여율 (%)", 0, 100, 1), ("p_ret", "복귀 브리핑 시작률 (%)", 0, 100, 1),
    ("u1", "개선 폭 D1 (%p)", 0, 20, 0.5), ("u7", "개선 폭 D7 (%p)", 0, 20, 0.5), ("u30", "개선 폭 D30 (%p)", 0, 20, 0.5),
    ("f1", "접속 → 첫 경기 (%)", 0, 100, 1), ("f3", "첫 경기 → 3경기 (%)", 0, 100, 1), ("f10", "3경기 → 10경기 (%)", 0, 100, 1),
    ("fu3", "참여자 3경기 개선 (%p)", 0, 30, 0.5), ("fu10", "참여자 10경기 개선 (%p)", 0, 30, 0.5),
    ("bd", "코호트 외 활성 유저 (명/일)", 0, 100000000, 10000), ("act", "잔존 유저 일일 접속 확률 (%)", 1, 100, 1),
    ("arr", "유입 기간 (일)", 1, 60, 1), ("hz", "관측 기간 (일)", 30, 180, 10)]


def ret_defaults(rs: dict) -> dict:
    ex = rs["experiment"]
    co, fn, up = ex["cohorts"], ex["funnel"], ex["uplift"]
    return {"n_new": co["신규"]["size"], "n_ret": co["복귀"]["size"],
            **{f"new_{d}": co["신규"]["base"][d] for d in ("D1", "D7", "D30")}, **{f"ret_{d}": co["복귀"]["base"][d] for d in ("D1", "D7", "D30")},
            "p_new": co["신규"]["participation"], "p_ret": co["복귀"]["participation"], "u1": up["D1"], "u7": up["D7"], "u30": up["D30"],
            "f1": fn["first"], "f3": fn["m3"], "f10": fn["m10"], "fu3": fn["up3"], "fu10": fn["up10"],
            "bd": 100000, "act": 50, "arr": 14, "hz": 90, "d7_of_10": fn["d7_of_10"]}


def ret_widget(root: Path) -> str:
    from gamepulse.data.overwatch_data import load_json
    rs = load_json("restart.json")
    dflt = ret_defaults(rs)
    inputs = "".join(_num(f"oxR_{k}", lab, dflt[k], lo, hi, st) for k, lab, lo, hi, st in RET_FIELDS)
    chain = "".join(f"<tr><td data-label=\"개선 방향\">{H.escape(k['lever'])}</td><td data-label=\"전략\">{H.escape(k['strategies'])}</td>"
                    f"<td data-label=\"확인할 지표\">{H.escape(' · '.join(k['leading']))}</td></tr>" for k in rs["kpi_chain"])
    chart = lambda i, h: f'<div class="ox-chart"><div class="ow-chart-h"><div class="ow-chart-t" id="{i}T"></div><div class="ow-chart-u" id="{i}U"></div></div><div id="{i}" class="sx-chart-c" style="height:{h}px"></div></div>'  # noqa: E731
    return f"""<details class="sx-exp" id="oxRetRes"><summary>잔존율 시뮬레이션 결과 · D7·D30 · 첫 10경기 퍼널 · DAU (가정) <span class="sx-more">펼쳐보기</span></summary>
<div class="sx-exp-b"><div id="oxRetWarn"></div>{chart("oxRet1", 520)}{chart("oxRet2", 400)}{chart("oxRet3", 400)}
<p><b>KPI 연결 구조 (가설)</b></p><div class="gp-table-wrap"><table class="gp-table ow-table"><tr><th>개선 방향</th><th>전략</th><th>확인할 지표</th></tr>{chain}</table></div>
<p class="ox-note">계산식 — 개선 후 잔존율 = 기존 잔존율 + 참여율 × 개선 폭 (D1 ≥ D7 ≥ D30 보정) · 전체 잔존율 = 인원 가중 평균 · 적응 퍼널 = 이전 단계 × 전환율 (신규 코호트만) · DAU = 코호트 외 활성 유저 + Σ 일별 유입 × 잔존 곡선 × 일일 접속 확률 · 기존 유저는 실험 대상이 아니며 불만·신고율로만 관찰</p></div></details>
<details class="sx-exp" id="oxRetSet"><summary>잔존율 시뮬레이션 설정 (가정값) · 값을 바꾸면 위 결과가 바로 바뀜 <span class="sx-more">펼쳐보기</span></summary>
<div class="sx-exp-b"><div class="ox-fields three">{inputs}</div><div class="ox-btns"><button type="button" class="ox-btn" id="oxRetReset">초기화</button></div>
<p class="ox-note">퍼널은 KPI '첫 10경기 완료율'과 같이 신규 코호트만으로 계산합니다.</p></div></details>
<script>(function(){{
var DF={_j(dflt)}, F={_j([[k, lo, hi] for k, _, lo, hi, _ in RET_FIELDS])}, BLUE='#2563EB', GRAY='#94A3B8';
function g(i){{return document.getElementById(i);}}
function vals(){{ var x={{}}; F.forEach(function(f){{ var v=parseFloat(g('oxR_'+f[0]).value); if(!isFinite(v)) v=DF[f[0]]; x[f[0]]=Math.min(Math.max(v,f[1]),f[2]); }}); x.d7_of_10=DF.d7_of_10; return x; }}
function up(base,p,u){{ var D=['D1','D7','D30'], o={{}}, w=[], raw={{}}; D.forEach(function(d){{ raw[d]=base[d]+p/100*u[d]; o[d]=Math.min(Math.max(raw[d],0),100); }});
  if(o.D7>o.D1){{o.D7=o.D1; w.push('개선 후 D7 이 D1 보다 커져 D7 = D1 로 보정했습니다. (D7 개선 폭을 줄이세요)');}}
  if(o.D30>o.D7){{o.D30=o.D7; w.push('개선 후 D30 이 D7 보다 커져 D30 = D7 로 보정했습니다. (D30 개선 폭을 줄이세요)');}}
  if(D.some(function(d){{return raw[d]>100;}})) w.push('개선 후 잔존율이 100%를 넘어 100%로 제한했습니다.'); return [o,w]; }}
function curve(r,h){{ var eps=1e-4, T=[0,1,7,30], R=[1,r.D1/100,r.D7/100,r.D30/100].map(function(v){{return Math.log(Math.max(v,eps));}}), out=[];
  var slope=(R[3]-R[2])/23; for(var t=0;t<=h;t++){{ var l; if(t>30) l=R[3]+slope*(t-30); else {{ var k=t<=1?0:(t<=7?1:2); l=R[k]+(R[k+1]-R[k])*(t-T[k])/(T[k+1]-T[k]); }}
  out.push(Math.min(Math.max(Math.exp(l),0),1)); }} return out; }}
function sim(x){{
  var C=[{{name:'신규',size:x.n_new,base:{{D1:x.new_D1,D7:x.new_D7,D30:x.new_D30}},p:x.p_new}},{{name:'복귀',size:x.n_ret,base:{{D1:x.ret_D1,D7:x.ret_D7,D30:x.ret_D30}},p:x.p_ret}}];
  var errs=[]; C.forEach(function(c){{ if(!(c.base.D1>=c.base.D7&&c.base.D7>=c.base.D30)) errs.push(c.name+': 기존 잔존율은 D1 ≥ D7 ≥ D30 이어야 합니다.'); }});
  if(errs.length) return {{errs:errs}};
  var U={{D1:x.u1,D7:x.u7,D30:x.u30}}, warn=[], rates={{}};
  C.forEach(function(c){{ var r=up(c.base,c.p,U); rates[c.name]=r[0]; r[1].forEach(function(m){{warn.push('['+c.name+'] '+m);}}); }});
  var total=x.n_new+x.n_ret, cats=[], before=[], after=[];
  ['D7','D30'].forEach(function(d){{ ['복귀','신규'].forEach(function(n){{ var c=C.filter(function(z){{return z.name===n;}})[0]; cats.push(n+' '+d); before.push(c.base[d]); after.push(rates[n][d]); }});
    var bu=0, nu=0; C.forEach(function(c){{ bu+=c.size*c.base[d]/100; nu+=c.size*rates[c.name][d]/100; }});
    cats.push('전체 '+d); before.push(total?bu/total*100:NaN); after.push(total?nu/total*100:NaN); }});
  var ft=x.n_new, pav=ft?x.p_new/100:0, cb=[x.f1,x.f3,x.f10], ci=[x.f1,Math.min(x.f3+pav*x.fu3,100),Math.min(x.f10+pav*x.fu10,100)];
  function chain(cv){{ var v=[ft]; cv.forEach(function(c){{v.push(v[v.length-1]*c/100);}}); return v; }}
  var fb=chain(cb), fi=chain(ci), h=x.hz, a=x.act/100;
  function dau(R){{ var tot=[]; for(var i=0;i<=h;i++) tot.push(x.bd); C.forEach(function(c){{ var r=curve(R[c.name],h), daily=c.size/Math.max(x.arr,1);
    for(var s=0;s<Math.min(x.arr,h+1);s++) for(var t=s;t<=h;t++) tot[t]+=daily*r[t-s]*a; }}); return tot; }}
  var baseR={{}}; C.forEach(function(c){{baseR[c.name]=c.base;}});
  return {{cats:cats,before:before,after:after,warn:warn,funnel:{{b:fb,i:fi,total:ft}},dauB:dau(baseR),dauN:dau(rates),h:h}};
}}
function pp(v){{return (v>=0?'+':'−')+Math.abs(v).toFixed(1)+'%p';}}
function lay(){{return {{margin:{{l:8,r:20,t:44,b:44}},font:{{size:13}},barmode:'group',bargap:0.28,bargroupgap:0.06,legend:{{orientation:'h',yanchor:'bottom',y:1.02,x:0}},plot_bgcolor:'#fff',paper_bgcolor:'#fff'}};}}
var P={{displayModeBar:false,responsive:true}};
function hpair(id,cats,b,a,names,xmax,xt){{
  var lab=cats.map(function(c,i){{return c+'  <b>'+pp(a[i]-b[i])+'</b>';}}), L=lay();
  L.yaxis={{autorange:'reversed',automargin:true}}; L.xaxis={{title:xt,range:[0,xmax||Math.max.apply(null,b.concat(a))*1.25],ticksuffix:'%'}};
  Plotly.react(id,[{{type:'bar',orientation:'h',y:lab,x:b,name:names[0],marker:{{color:GRAY}},text:b.map(function(v){{return v.toFixed(1)+'%';}}),textposition:'outside',cliponaxis:false}},
    {{type:'bar',orientation:'h',y:lab,x:a,name:names[1],marker:{{color:BLUE}},text:a.map(function(v){{return v.toFixed(1)+'%';}}),textposition:'outside',cliponaxis:false}}],L,P); }}
function draw(){{
  var r=sim(vals());
  if(r.errs){{ g('oxRetWarn').innerHTML=r.errs.map(function(e){{return '<div class="sx-alert exception">'+e+'</div>';}}).join('')+'<div class="sx-alert info">설정에서 D1 ≥ D7 ≥ D30 이 되도록 고쳐 주세요.</div>'; return; }}
  g('oxRetWarn').innerHTML=r.warn.map(function(w){{return '<div class="sx-alert warning">'+w+'</div>';}}).join('');
  if(!window.Plotly) return;
  var ri=r.cats.indexOf('복귀 D7');
  g('oxRet1T').textContent='복귀 D7 '+r.before[ri].toFixed(1)+'% → '+r.after[ri].toFixed(1)+'% (참여율 × 개선 폭)'; g('oxRet1U').textContent='% · 회색 = 대조군, 진한 색 = 실험군 · 이름 옆 = 변화 폭';
  hpair('oxRet1',r.cats,r.before,r.after,['도입 전 · 대조군 (가정 기준값)','도입 후 · 실험군 (가정)'],null,'잔존율 (%)');
  var f=r.funnel, T=f.total, st=['접속','첫 경기','3경기 완료','10경기 완료'], fb=f.b.map(function(v){{return T?v/T*100:0;}}), fi=f.i.map(function(v){{return T?v/T*100:0;}});
  g('oxRet2T').textContent='신규 10경기 완료 '+fb[3].toFixed(1)+'% → '+fi[3].toFixed(1)+'% · 완료율만 오르고 D7이 그대로면 미션 수정'; g('oxRet2U').textContent='신규 접속 대비 % · 회색 = 대조군, 진한 색 = 실험군';
  hpair('oxRet2',st,fb,fi,['도입 전 · 대조군 (가정)','도입 후 · 실험군 (가정)'],118,'접속 대비 (%)');
  var days=[]; for(var d=0;d<=r.h;d++) days.push(d); var diff=r.dauN[r.h]-r.dauB[r.h];
  g('oxRet3T').textContent=r.h+'일차 DAU 차이 '+(diff>=0?'+':'−')+Math.round(Math.abs(diff)).toLocaleString('en-US')+'명 → DAU 대신 코호트 잔존율로 판단'; g('oxRet3U').textContent='명/일 · 세로축 0부터';
  var L=lay(); L.xaxis={{title:'코호트 유입 시작 후 경과일 (일)'}}; L.yaxis={{title:'DAU (명)',tickformat:',',rangemode:'tozero',range:[0,Math.max.apply(null,r.dauB.concat(r.dauN))*1.1]}};
  Plotly.react('oxRet3',[{{x:days,y:r.dauB,name:'현재 · 대조군 (가정)',mode:'lines',line:{{color:GRAY,width:3}}}},{{x:days,y:r.dauN,name:'RE:START 적용 · 실험군 (가정)',mode:'lines',line:{{color:BLUE,width:2,dash:'dot'}}}}],L,P);
}}
document.querySelectorAll('#oxRetSet input').forEach(function(e){{e.addEventListener('input',draw);}});
g('oxRetReset').addEventListener('click',function(){{F.forEach(function(f){{g('oxR_'+f[0]).value=DF[f[0]];}}); draw();}});
g('oxRetRes').addEventListener('toggle',function(){{ if(this.open){{ draw(); if(window.Plotly) ['oxRet1','oxRet2','oxRet3'].forEach(function(i){{Plotly.Plots.resize(i);}}); }} }});
window.oxRetSim=function(x){{return sim(Object.assign({{}},DF,x));}};
draw();
}})();</script>"""


SUBTAB_JS = """<script>(function(){
  /* 오버워치: 하위 탭(A·B·C 데모 등)을 한 번에 하나만 보이는 진짜 탭으로 */
  document.querySelectorAll('.ow-pane .sx-tabs').forEach(function(box){
    var nav=box.querySelector('.sx-tabnav'); if(!nav) return; var links=nav.querySelectorAll('a'), secs=box.querySelectorAll(':scope > .sx-tab');
    function show(i){ secs.forEach(function(s,j){ s.hidden = j!==i; }); links.forEach(function(a,j){ a.classList.toggle('on', j===i); a.setAttribute('aria-selected', String(j===i)); });
      if(window.Plotly) secs[i].querySelectorAll('.sx-chart-c').forEach(function(c){ if(!c.closest('details:not([open])')) Plotly.Plots.resize(c); }); }
    links.forEach(function(a,i){ a.setAttribute('role','tab'); a.addEventListener('click',function(e){ e.preventDefault(); show(i); }); });
    show(0);
  });
})();</script>"""


def widgets(root: Path) -> dict[str, str]:
    sys.path.insert(0, str(root))
    return {"ops": ops_widget(root), "a": a_widget(root), "b": b_widget(root), "c": c_widget(root),
            "ss": ss_widget(root), "ret": ret_widget(root)}
