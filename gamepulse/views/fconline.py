"""FC 온라인 — 축구 게임인가, 주식 게임인가? (2026-11 개편 · 7탭 · 가독성 우선 · MY CLUB WAR 대표 기획)

01 개요·시장 · 02 BM 강점 · 03 유저 VOC 50 · 04 구단 가치 (CLUB CARE · CLUB REBUILD) · 05 MY CLUB WAR · 06 FAIR PLAY · 07 사업성·실행
- 사실·VOC·기획: data/fconline/fc2.json (이전 자료 fc.json 은 보존) · 계산: gamepulse/sim/fc_biz.py (정적 JS 와 같은 식)
- 실제 화면: assets/fconline/*.jpg (작성자 캡처 · 계정 정보 블러) · 기획 화면은 HTML 콘셉트 (실제 게임 화면 아님)
- 받지 못한 캡처는 '이미지 준비 중' 자리 (파일을 assets/fconline/ 에 넣으면 자동 표시)
- 정적 사이트: ox-js-start ~ ox-js-end 구역을 scripts/fc_static_widgets.py 의 JS 위젯으로 교체
이전 화면 코드는 fconline_v1.py 에 보관.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from html import escape
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from gamepulse.sim import fc_biz as B
from gamepulse.ui.brief import brief_html, flow_html
from gamepulse.ui.components import html
from gamepulse.views.overwatch import _jpg_b64, bullets, h, ox_badge_legend, ox_chart_card, stats, table
from gamepulse.views.overwatch import won as owon
# 던전앤파이터 화면이 이 모듈에서 가져다 쓰는 공용 함수 (개편 전 코드 그대로 · fconline_v1)
from gamepulse.views.fconline_v1 import conclude, lead, sol_card, tr, won  # noqa: F401,E402

ROOT = Path(__file__).resolve().parents[2]
DATA, ASSETS = ROOT / "data" / "fconline", ROOT / "assets" / "fconline"
SECTIONS = [("01", "개요·시장"), ("02", "BM 강점"), ("03", "유저 VOC 50"), ("04", "구단 가치"),
            ("05", "MY CLUB WAR"), ("06", "FAIR PLAY"), ("07", "사업성·실행")]
TAB_LABELS = [f"{n} {t}" for n, t in SECTIONS]
TAB_KEY = "fc_tab"
ACC, DARK, GRAY, RED = "#16A34A", "#166534", "#9CA3AF", "#DC2626"   # 테마 · 진한 그린 · 비교 기준 · 하락 (범례와 같은 색)
CAP = "작성자 캡처 · 2026-11-23 · 계정 정보 블러"
PCT_KEYS = {"churn0", "churn1", "visit", "signup", "d7", "d30", "pur"}


@st.cache_data(show_spinner=False)
def load() -> dict:
    return json.loads((DATA / "fc2.json").read_text(encoding="utf-8"))


OFF_CAP = "FC 온라인 공식 홈페이지 배너 · 2026-11-26 수집 · ⓒ NEXON · EA"


def fig(name: str, label: str, cap: str = CAP) -> str:
    p = ASSETS / name
    if not p.is_file():
        return ""
    off = name.startswith("off_")
    kind, cap = ("공식 이미지", OFF_CAP) if off else ("실제 게임 화면", cap)
    return (f'<figure class="ox-fig real{" off" if off else ""}"><details class="ox-zoom"><summary title="클릭하면 크게 보기">'
            f'<img src="data:image/jpeg;base64,{_jpg_b64(str(p), p.stat().st_mtime)}" alt="{escape(label)}" loading="lazy"></summary></details>'
            f'<figcaption><b>{kind}</b>{escape(label)} · {escape(cap)}</figcaption></figure>')


def slot(name: str, label: str) -> str:
    """받은 캡처는 실제 화면으로, 아직 없으면 '이미지 준비 중' 자리."""
    return fig(name, label) or (f'<div class="fx-slot"><b>이미지 준비 중</b><span>{escape(label)}</span>'
                                f'<small>assets/fconline/{escape(name)}</small></div>')


EFFECT = {"CLUB CARE": "급락 유저 <b>D30 잔존 · 기존 결제 유지</b> (검증 전)",
          "CLUB REBUILD": "급락 유저 <b>D7·D30 유지 · 재건 완료</b> (검증 전)",
          "MY CLUB WAR": "<b>신규 가입 → D30 정착</b> · 허용 CPA 안에서 (검증 전)",
          "FAIR PLAY": "<b>보정 승률 격차 축소 · 공정성 만족도</b> (검증 전)"}


def brief4(d: dict, key: str, tag: str = "기획 시안") -> str:
    """01 탭 '문제 → 근거 → 해결 → 효과' 표의 같은 행을 기획 첫머리 4칸으로."""
    row = next(r for r in d["summary4"] if r[0] == key)
    return brief_html(escape(row[1]), escape(row[2]), escape(row[3]), EFFECT[key] + f"<br><small>판단 KPI · {escape(row[4])}</small>",
                      name=key, tag=tag)


def src(url: str, text: str) -> str:
    return f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener">{escape(text)}</a>' if url else escape(text)


def mock(tag: str, inner: str, cls: str = "") -> str:
    return f'<div class="fx-mock {cls}"><div class="fx-mock-tag">기획 콘셉트 · 실제 게임 화면 아님 · {escape(tag)}</div>{inner}</div>'


def dots(items: list[str]) -> str:
    return " · ".join(escape(x) for x in items)


def _tab_from_query() -> str:
    q = str(st.query_params.get("tab", ""))
    return next((lab for lab in TAB_LABELS if lab.startswith(q.zfill(2)[:2])), TAB_LABELS[0]) if q else TAB_LABELS[0]


def _sync_tab_param() -> None:
    st.query_params["page"] = "fconline"
    st.query_params["tab"] = str(st.session_state.get(TAB_KEY, TAB_LABELS[0]))[:2]


def tab_nav() -> int:
    if st.session_state.get(TAB_KEY) not in TAB_LABELS:
        st.session_state[TAB_KEY] = _tab_from_query()
    sel = st.radio("섹션 선택", TAB_LABELS, key=TAB_KEY, horizontal=True, label_visibility="collapsed", on_change=_sync_tab_param)
    return TAB_LABELS.index(sel)


def js(key: str) -> None:
    html(f'<div class="ox-js-start" data-demo="{key}"></div>')


def js_end() -> None:
    html('<div class="ox-js-end"></div>')


# ======================================================================
def render() -> None:
    d = load()
    html('<div class="gp-ow-page gp-fc-page"></div>')   # 오버워치와 같은 개편 레이아웃 · 색은 FC 테마(#16A34A)
    cv, mc = d["cover"], d["mcw"]
    img = fig("main_screen.jpg", "FC 온라인 메인 화면")
    html(f'<div class="owx-hero ox-cover fx-cover"><div class="owx-t"><div class="ow-cover-t">{escape(cv["kicker"])}</div>'
         f'<div class="owx-q" role="heading" aria-level="1">{escape(cv["title"])}</div><p class="owx-s">{escape(cv["subtitle"])}</p>'
         '<div class="fx-dirs">' + "".join(f'<span><b>{n}</b>{escape(t)}</span>' for n, t in cv["directions"]) + "</div></div>"
         + (f'<div class="fx-cover-img">{img}</div>' if img else "") + "</div>")
    html('<div class="fx-nums">' + "".join(f'<div><b>{escape(v)}</b><span>{escape(l)}</span><small>{escape(s)}</small></div>'
                                           for v, l, s in cv["numbers"]) + "</div>")
    html(f'<a class="fx-mcw-strip" href="#t05"><span>대표 기획</span><b>MY CLUB WAR</b><em>{escape(mc["slogan"])}</em>'
         f'<small>실제 구단 팬덤이 시즌 리그로 겨루는 8주 캠페인 → 05 탭</small></a>')
    html('<div class="fx-4 slim">' + "".join(f'<div><em>{escape(n)}</em><span>{escape(g)}</span></div>' for n, g in d["final"]) + "</div>")
    i = tab_nav()
    ox_badge_legend()
    html(f'<div class="ow-pane-mark" data-tab="{SECTIONS[i][0]}"></div>')
    [t1, t2, t3, t4, t5, t6, t7][i](d)
    st.caption(f"{d['disclaimer']} · 자료 확인일 {d['checked_at']}")


# ----------------------------------------------------------------------
# 01 개요·시장
def t1(d: dict) -> None:
    m = d["market"]
    h("국내 PC방 상위권 축구 게임 · 실제 축구 일정과 이용이 함께 움직인다", "real", num="01", name="게임 개요 · 시장 경쟁력",
      lead="넥슨 서비스 · EA SPORTS 라이선스 · 조사 기준일 2026-11-25 · PC방 점유율은 축구 게임 장르 점유율이 아니다")
    html('<div class="fx-nums big">' + "".join(f'<div><b>{escape(v)}</b><span>{escape(l)}</span><small>{src(u, s)}</small></div>'
                                               for v, l, s, u in m["key"]) + "</div>")
    x = [a for a, _ in m["usage"]]
    y = [b for _, b in m["usage"]]
    f = go.Figure(go.Bar(x=x, y=y, marker_color=ACC, text=[f"{v}만" for v in y], textposition="outside", cliponaxis=False))
    f.update_yaxes(title="주간 PC방 사용시간 (만 시간)", rangemode="tozero", range=[0, max(y) * 1.25])
    ox_chart_card(f, key="fcusage", kind="real", title="월드컵(6/11 개막) 기간 주간 사용시간 84만 → 124만 시간 (+47.6%)",
                  unit="만 시간 · 더로그 한 기관 자료만 · 세로축 0부터", kpis=[], analysis="축구 이벤트와 함께 늘어난 것은 관찰이며 인과로 단정하지 않는다",
                  decision="", basis="", height=300, legend=False, cols=("주차", "사용시간 (만 시간)"))
    h("강점 세 가지가 MY CLUB WAR의 근거가 된다", "interp")
    html('<div class="fx-3 str">' + "".join(f'<div><span>{escape(a)}</span><p>{escape(b)}</p></div>' for a, b in m["strengths3"]) + "</div>")
    with st.expander("PC방 순위 4개 시점 · 경쟁작 차이 · 자료 원문 (조사기관이 달라 하나의 추세로 잇지 않음)"):
        table(["시점", "순위", "점유율", "출처", "참고"],
              [[escape(p["when"]), escape(p["rank"]), escape(p["share"]), src(p["url"], p["src"]), escape(p["note"])] for p in m["points"]])
        table(["게임", "서비스 형태"], [[f"<b>{escape(a)}</b>", escape(b)] for a, b in m["compare"]])
        st.caption(m["compare_note"])

    h("문제 → 근거 → 해결 → 효과: 전략 4개를 한 표로", "mock", num="01", name="핵심 전략 요약")
    table(["전략", "문제", "실제 근거", "해결책", "판단 KPI"], [[f"<b>{escape(a)}</b>", *[escape(x) for x in r]] for a, *r in d["summary4"]],
          cls="ox-mops fx-sum")
    html(f'<div class="ox-purpose"><span>사업PM 결론</span>{escape(d["final_msg"])}</div>')


# ----------------------------------------------------------------------
# 02 BM 강점
def t2(d: dict) -> None:
    bm, mk = d["bm"], d["marketing"]
    h("상품 하나가 아니라 '멤버십 → 페이백 → 한정 상품 → 성장'이 맞물려 반복 구매를 만든다", "real", num="02", name="기존 BM 강점",
      lead="새 BM을 억지로 더하지 않는다 · 확인된 것만 적고 받지 못한 캡처는 '이미지 준비 중'")
    cards = []
    for c in d["bm_cards"]:
        im = slot(c["img"], c["name"])
        tag = '<i class="ok">공식·캡처 확인</i>' if c["status"] == "real" else '<i class="wait">캡처 확인 예정</i>'
        cards.append(f'<div class="fx-bm">{im}<div class="fx-bm-t"><b>{escape(c["name"])}</b>{tag}</div>'
                     f'<p><span>구매 심리</span>{escape(c["psy"])}</p><p><span>사업적 효과</span>{escape(c["effect"])}</p></div>')
    html('<div class="fx-bms">' + "".join(cards) + "</div>")
    h("반복 구매 순환 구조", "interp", lead="구매하지 않으면 혜택을 놓친다고 느끼기 쉬운 구조 · 동시에 결제 피로와 이탈 위험도 함께 커진다")
    n = len(d["bm_cycle"])
    pos = [(50 + 39 * math.sin(2 * math.pi * k / n), 50 - 39 * math.cos(2 * math.pi * k / n)) for k in range(n)]
    html('<div class="fx-cycle">' + "".join(f'<div style="left:{x:.1f}%;top:{y:.1f}%"><em>{k + 1}</em>{escape(s)}</div>'
                                            for k, (s, (x, y)) in enumerate(zip(d["bm_cycle"], pos)))
         + '<span class="fx-cycle-c">다음 달<br>다시</span></div>')
    html(f'<div class="ox-purpose fx-risk"><span>함께 볼 위험</span>{escape(bm["risk"])} · 구단 가치 급락이 겹치면 결제 중단으로 번질 수 있다 (04 탭)</div>')
    with st.expander("BM 상세 · 확인한 내용과 근거 링크"):
        table(["BM", "확인한 내용", "근거"],
              [[f"<b>{escape(c['name'])}</b>", escape(c["fact"]) if c["fact"] else '<span class="ox-pend">캡처 확인 예정</span>',
                src(c["url"], c["src"]) if c["src"] else "—"] for c in d["bm_cards"]], cls="ox-mops")

    ic = mk["icon"]
    h("축구 팬의 관심은 이미 크다 · 과제는 그 관심을 '지속 참여'로 잇는 것", "real", num="02", name="기존 축구 마케팅")
    stats([("약 10만 명", "2025 아이콘매치 이틀 관중", "real"), ("340만 명", "생중계 누적 시청", "real"), ("+47.6%", "월드컵 기간 주간 사용시간", "real")])
    st.caption(f"{ic['title']} · {ic['when']} · 출처 {ic['src']} · 더로그(경향게임스 2026-07-13)")
    html(f'<div class="ox-purpose"><span>→ MY CLUB WAR 근거</span>대형 행사는 이틀, 월드컵은 몇 주 · 실제 구단 팬덤을 8주 시즌 리그로 묶으면 관심이 게임 안 활동으로 이어질 수 있다 (가설)</div>')


# ----------------------------------------------------------------------
# 03 유저 VOC 50
def t3(d: dict) -> None:
    V = d["voc"]
    by = {v["id"]: v for v in V}
    cats = Counter(v["cat"] for v in V)
    tones = Counter(v["tone"] for v in V)
    h(f"VOC {len(V)}건: 불만은 구단 가치·강화에, 만족은 신규 클래스·이적시장·이벤트에 모인다", "real", num="03", name="실제 유저 VOC",
      lead=escape(d["voc_note"]))
    stats([(f"{len(V)}건", "검증한 VOC (원문 링크)", "real"), (f"{tones.get('부정', 0)} · {tones.get('중립', 0)} · {tones.get('긍정', 0)}", "부정 · 중립 · 긍정", "real"),
           (f"{cats.get('키보드·패드 조작', 0) * 100 // len(V)}%", "조작 관련 비중 (반복 댓글 정리 후)", "real")])
    order = [c for c, _ in cats.most_common()]
    tc = {t: Counter(v["cat"] for v in V if v["tone"] == t) for t in ("부정", "중립", "긍정")}
    f = go.Figure([go.Bar(y=order, x=[tc[t].get(c, 0) for c in order], name=t, orientation="h", marker_color=col)
                   for t, col in (("부정", RED), ("중립", GRAY), ("긍정", ACC))])
    f.update_layout(barmode="stack")
    f.update_yaxes(autorange="reversed", automargin=True)
    f.update_xaxes(title="건")
    ox_chart_card(f, key="fcvoc", kind="real", title="주제별 VOC · 빨강 = 부정, 회색 = 중립, 초록 = 긍정",
                  unit="건 · 한 글은 주 분류 1개", kpis=[], analysis="", decision="", basis="", height=300, cols=("주제", "건"), series="방향")
    html('<ol class="ox-ins">' + "".join(f"<li>{escape(x)}</li>" for x in d["voc_insights"]) + "</ol>")
    h("대표 VOC 6건 · 어느 기획으로 이어지는가", "real", lead="부정·중립·긍정을 함께 · 나머지는 아래 전체 목록에서 필터로 확인")
    reps = [d["voc_rep"][i] for i in (0, 2, 4, 5, 6, 7)]
    html('<div class="fx-vocs six">' + "".join(
        f'<div class="t-{ {"부정": "n", "긍정": "p"}.get(by[i]["tone"], "z") }"><span>{escape(by[i]["cat"])} · {escape(by[i]["tone"])}</span>'
        f'<b>{escape(by[i]["summary"])}</b><small>{escape(by[i]["src"])} · {escape(by[i]["date"])} · {src(by[i]["url"], "원문 ↗")}</small>'
        f'<em>→ {escape(by[i]["link"])}</em></div>' for i in reps) + "</div>")
    with st.expander(f"VOC {len(V)}건 전체 · 출처·주제·방향 필터 · 원문 링크"):
        js("fcvoc")
        c1, c2, c3, c4 = st.columns(4)
        s_src = c1.selectbox("출처", ["전체"] + sorted({v["src"] for v in V}), key="fc_voc_src")
        s_cat = c2.selectbox("주제", ["전체"] + order, key="fc_voc_cat")
        s_tone = c3.selectbox("방향", ["전체", "부정", "중립", "긍정"], key="fc_voc_tone")
        q = c4.text_input("검색", key="fc_voc_q")
        rows = [v for v in V if (s_src == "전체" or v["src"] == s_src) and (s_cat == "전체" or v["cat"] == s_cat)
                and (s_tone == "전체" or v["tone"] == s_tone) and (not q.strip() or q.strip().lower() in (v["title"] + v["summary"]).lower())]
        table(["번호", "출처 · 작성일", "제목 (원문 링크)", "요약", "주제", "방향", "연결 기획"],
              [[v["id"], f'{escape(v["src"])}<br><small>{escape(v["date"])}</small>', src(v["url"], v["title"]), escape(v["summary"]),
                escape(v["cat"]), escape(v["tone"]), escape(v["link"])] for v in rows], cls="ox-mops fx-voc")
        js_end()
        st.caption("보조 자료 (50건 미포함): " + " · ".join(t for _, t, _ in d["voc_extra"]) + " · " + d["voc_plan"])


# ----------------------------------------------------------------------
# 04 구단 가치 · CLUB CARE · CLUB REBUILD
def _care_mock(ca: dict, period: str) -> str:
    m = ca["mock"]
    s = m["periods"][period]
    hi = max(s)
    bars = "".join(f'<i style="height:{v / hi * 100:.0f}%"></i>' for v in s)
    tabs = "".join(f'<span class="{"on" if p == period else ""}">{p}</span>' for p in m["periods"])
    pl = "".join(f'<div><b>{escape(n)}</b><em class="{"up" if c.startswith("+") else "dn"}">{escape(c)}</em><small>{escape(w)}</small></div>'
                 for n, c, w in m["players"])
    return mock("CLUB CARE · 구단 가치 대시보드 · 가상 수치",
                f'<div class="fx-care"><div class="fx-care-l"><div class="fx-tabs">{tabs}</div><b>내 구단 가치 · 최근 {period}</b>'
                f'<div class="fx-spark">{bars}</div><small><b class="dn">{m["change"][period]}%</b> · 막대 = 일자별 구단 가치 (조 BP)</small>'
                f'<div class="fx-care-pl">{pl}</div></div><div class="fx-care-r">'
                f'<div><span>휴면 리포트</span><b>{escape(m["dormant"])}</b></div>'
                f'<div><span>주요 시장 변화</span><b>{dots(m["market"])}</b></div>'
                f'<div><span>목표 선수 기준 구매력</span><b class="dn">{escape(m["power"])}</b></div>'
                '<div><span>알림</span><b>동의한 항목만 · 매수·매도 권유 없음</b></div></div></div>')


def _rebuild_mock(rb: dict, opt: str) -> str:
    fm = rb["formation"]
    rows = {"FW": ["LW", "ST", "RW"], "MF": ["CM"], "DF": ["LB", "CB", "RB"], "GK": ["GK"]}
    ps = fm["before"]["players"]
    lines = []
    for grp in ("FW", "MF", "DF", "GK"):
        line = [p for p in ps if p.split()[0] in rows[grp]]
        lines.append('<div class="fx-line">' + "".join(f'<span>{escape(p)}</span>' for p in line) + "</div>")
    pitch = '<div class="fx-pitch">' + "".join(lines) + "</div>"
    a = fm[opt]
    dm = rb["demo"]
    return mock("CLUB REBUILD · BEFORE & AFTER · 가상 사례",
                f'<div class="fx-rb"><div class="fx-rb-v"><div><span>기존 구단 가치</span><b>{dm["before"]}조 BP</b></div>'
                f'<div><span>현재 구단 가치</span><b>{dm["now"]}조 BP</b></div><div><span>하락률</span><b class="dn">{(dm["now"] / dm["before"] - 1) * 100:.0f}%</b></div></div>'
                f'<div class="fx-ba"><div><span>{escape(fm["before"]["name"])}</span>{pitch}</div>'
                f'<div><span>{escape(a["name"])}</span><div class="fx-after"><b>예상 구성 비용 {escape(a["cost"])}</b>'
                + "".join(f"<small>• {escape(x)}</small>" for x in a["change"]) +
                '<small>• 기간제 체험 선수는 거래 불가</small></div>'
                '<div class="fx-rb-m"><span>재건 미션 · 7일</span><div class="ox-bar"><i style="width:57%"></i></div><small>4/7일 진행</small></div></div></div></div>')


def t4(d: dict) -> None:
    h("문제는 시세가 아니라 '투자한 시간과 돈의 가치가 사라졌다'는 박탈감이다", "hypo", num="04", name="구단 가치 하락과 유저 이탈",
      lead="쉬었다 돌아오면 선수단 가치와 경쟁력이 크게 떨어져 있을 수 있다 · " + escape(d["chain_note"]))
    ch = d["chain"]
    html('<div class="fx-chain2">' + "".join(
        f'<div class="{"care" if 1 <= k <= 3 else ("reb" if k >= 4 else "")}"><em>{k + 1}</em>{escape(s)}</div>' for k, s in enumerate(ch))
         + '</div><div class="fx-zone"><span class="care">CLUB CARE · 예방 (2~4단계)</span><span class="reb">CLUB REBUILD · 재건 (5~8단계)</span></div>')
    cv = d["care_vs_rebuild"]
    col = lambda j: "".join(f"<dt>{escape(r[0])}</dt><dd>{escape(r[j])}</dd>" for r in cv[1:] if r[0] != "개입 시점")  # noqa: E731
    when = next(r for r in cv[1:] if r[0] == "개입 시점")
    html('<div class="gb-flow-t fx-cvr-t">CARE는 예방, REBUILD는 회복 · 같은 복귀 이벤트가 아니다 <span class="ox-k mock">기획 시안</span></div>'
         f'<div class="gb-vs fx-cvr2"><div><h5>CLUB CARE<small>{escape(cv[0][1])}</small></h5><span class="when">개입 · {escape(when[1])}</span><dl>{col(1)}</dl></div>'
         f'<i>→</i><div class="b"><h5>CLUB REBUILD<small>{escape(cv[0][2])}</small></h5><span class="when">개입 · {escape(when[2])}</span><dl>{col(2)}</dl></div></div>')
    dv = d["value_demo"]
    xs = [p_[0] for p_ in dv["points"]]
    ys = [p_[1] for p_ in dv["points"]]
    f = go.Figure(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=RED, width=3), marker=dict(size=8), name="구단 가치 (가상)"))
    for p_ in dv["points"]:
        if len(p_) > 2:
            f.add_annotation(x=p_[0], y=p_[1], text=p_[2], showarrow=True, arrowhead=2, ay=-40, font=dict(size=11))
    f.update_yaxes(title="구단 가치 (조 BP)", rangemode="tozero", range=[0, 560])
    ox_chart_card(f, key="fcval", kind="sim", title="가상 사례: 500조 → 200조 BP (−60%)", unit="조 BP · " + dv["label"] + " · 세로축 0부터",
                  kpis=[], analysis="", decision="", basis="", height=300, legend=False, cols=("주차", "구단 가치 (조 BP)"))
    dr = d["drops"]
    with st.expander("실제 관측 사례 · 같은 카드 시세 −64~70% (작성자 캡처 3장)"):
        html(f'<div class="ox-pair">{fig(dr[0]["file"], "시세 그래프 · " + dr[0]["card"])}{fig(dr[1]["file"], "시세 그래프 · " + dr[1]["card"])}</div>')
        table(["카드", "그래프 최고", "최근", "변화"],
              [[escape(x["card"]), f'{x["peak"]:,} BP', f'{x["now"]:,} BP', f'<b>{(x["now"] / x["peak"] - 1) * 100:.0f}%</b>'] for x in dr],
              cls="ox-mops")
        st.caption("같은 카드·같은 강화의 이적시장 그래프 관측값 (2026-11-23 캡처) · 시장 전체 대표 아님")
    with st.expander("BP 실질 구매력 계산기 · 구단 가치가 올라도 목표 선수 기준 구매력은 줄 수 있다 (가상)"):
        p = d["bp_power"]
        js("fcpower")
        c = st.columns(4)
        v = [c[0].number_input("기존 구단 가치 (조 BP)", 0.0, 1e6, float(p["club0"]), key="fc_pw_c0"),
             c[1].number_input("변경 후 구단 가치 (조 BP)", 0.0, 1e6, float(p["club1"]), key="fc_pw_c1"),
             c[2].number_input("기존 목표 선수 가격 (조 BP)", 0.0, 1e6, float(p["target0"]), key="fc_pw_t0"),
             c[3].number_input("변경 후 목표 선수 가격 (조 BP)", 0.0, 1e6, float(p["target1"]), key="fc_pw_t1")]
        r = B.power(*v)
        fmt = lambda x: "—" if x is None else f"{x:+.0f}%"  # noqa: E731
        stats([(fmt(r["nominal"]), "명목 구단 가치 변화", "sim"), (fmt(r["real"]), "목표 선수 기준 구매력 변화", "sim"),
               ("—" if r["p1"] is None else f"{r['p1']:.1f}명분", "지금 구단 가치로 살 수 있는 목표 선수", "sim")])
        js_end()

    ca = d["care"]
    h(f"{ca['name']} · {ca['slogan']}", "mock", num="04", name="개선 기획 A — PREVENTION · 구단 가치 관리",
      lead="선수 1명이 아니라 내 선수단 전체 · 휴면 기간까지 · 운영진 시장 관리와 연결 (가격을 강제로 유지하지 않는다)")
    html(brief4(d, "CLUB CARE"))
    js("fccare")
    per = st.radio("기간", list(ca["mock"]["periods"]), horizontal=True, key="fc_care_p", index=1)
    html(_care_mock(ca, per))
    js_end()
    table(["", "기존 기능 (이적시장·트렌드 센터)", "CLUB CARE"], [[f"<b>{escape(a)}</b>", escape(b), escape(c)] for a, b, c in ca["vs"]], cls="ox-mops")
    st.caption(ca["vs_note"])
    with st.expander("기능 8개 · 운영진 경제 관리 6개 · 원칙 · KPI"):
        html(f'<ul class="ox-facts"><li><b>기능</b> · {dots(ca["features8"])}</li><li><b>운영 시장 관리</b> · {dots(ca["ops"])}</li>'
             f'<li><b>원칙</b> · {dots(ca["rules"])}</li><li><b>KPI</b> · {dots(ca["kpi"])}</li></ul>')

    rb = d["rebuild"]
    h(f"{rb['name']} · {rb['slogan']}", "mock", num="04", name="개선 기획 B — RECOVERY · 구단 재건",
      lead="이미 떠난 유저가 아니라, 급락 뒤 떠나기 전의 유저에게 먼저 다른 선택지를 준다")
    html(brief4(d, "CLUB REBUILD"))
    js("fcrebuild")
    opt = st.radio("재건 방향", ["팀컬러 유지형", "신규 팀컬러 전환형"], horizontal=True, key="fc_rb_opt")
    html(_rebuild_mock(rb, "keep" if opt == "팀컬러 유지형" else "switch"))
    js_end()
    html('<div class="fx-steps">' + "".join(f'<div><em>STEP {k}</em><b>{escape(a)}</b><small>{escape(b)}</small></div>'
                                            for k, (a, b) in enumerate(rb["steps"], 1)) + "</div>")
    ex = rb["exist"]
    html(f'<div class="fx-exist">{fig(rb["exist_img"], "신규/복귀 이벤트 엪온 빌드업")}<div><b>이미 있는 기능과 겹치는 부분</b>'
         + "".join(f'<p><span>{escape(a)}</span>{escape(b)} · {src(u, "공식 ↗")}</p>' for a, b, u in ex)
         + f'<p class="fx-exist-n">→ {escape(rb["exist_note"])}</p></div></div>')
    with st.expander("대상 · 악용·경제 방지 · KPI"):
        html(f'<ul class="ox-facts"><li><b>대상 (기획 기준 · 내부 데이터로 확정)</b> · {dots(rb["target"])}</li>'
             f'<li><b>악용·경제 방지</b> · {dots(rb["guard"])} · 수수료 할인 사용 횟수 제한</li><li><b>KPI</b> · {dots(rb["kpi"])}</li></ul>')


# ----------------------------------------------------------------------
# 05 MY CLUB WAR
def _rival_html(rv: dict, extra: int = 0) -> str:
    pa = rv["pa"]
    return (f'<div class="fx-vs" style="--ca:{rv["ca"]};--cb:{rv["cb"]}"><div class="fx-vs-n">{escape(rv["name"])}</div>'
            f'<div class="fx-vs-row"><div class="a"><i></i><b>{escape(rv["a"])}</b><strong>{pa:.1f}%</strong></div><div class="vs">VS</div>'
            f'<div class="b"><strong>{100 - pa:.1f}%</strong><b>{escape(rv["b"])}</b><i></i></div></div>'
            f'<div class="fx-vs-bar"><span style="width:{pa}%"></span></div>'
            f'<div class="fx-vs-meta"><span>남은 기간 {escape(rv["left"])}</span><span>점수 차 {abs(2 * pa - 100):.1f}%p</span>'
            f'<span>나의 기여 +{180 + extra}점</span></div></div>')


EMB = ["#B91C1C", "#1D4ED8", "#B45309", "#7C3AED", "#0F766E", "#BE185D", "#334155", "#15803D", "#0369A1", "#A16207"]


def league_html(league: list, my_club: str) -> str:
    """팬덤 리그 순위표: 엠블럼 · 1위 트로피 · 내 구단 표시 · 승점 막대 (가상 시즌)."""
    rows = sorted(league, key=lambda r: -(r[1] * 3 + r[2]))
    top = max(w * 3 + dr for _, w, dr, _, _ in rows) or 1
    out = []
    for k, (n, w, dr, l, ch) in enumerate(rows, 1):
        pts = w * 3 + dr
        mv = f'<span class="{"up" if ch > 0 else ("dn" if ch < 0 else "")}">{"▲" if ch > 0 else ("▼" if ch < 0 else "—")}{abs(ch) if ch else ""}</span>'
        cls = " r1" if k == 1 else ""
        cls += " me" if n == my_club else ""
        tag = '<u>MY</u>' if n == my_club else ""
        out.append(f'<div class="fx-lg-r{cls}"><em>{"🏆" if k == 1 else k}</em><b><i style="--c:{EMB[(k - 1) % len(EMB)]}">{escape(n[0])}</i>'
                   f'<span>{escape(n)}{tag}</span></b><span class="g">{w + dr + l}</span><span>{w}</span><span>{dr}</span><span>{l}</span>'
                   f'<strong>{pts}<small style="--w:{pts / top * 100:.0f}%"></small></strong>{mv}</div>')
    return ('<div class="fx-lg"><div class="fx-lg-t">FANDOM LEAGUE<small>시즌 1 · 5주차 · 가상</small></div>'
            '<div class="fx-lg-r hd"><em>#</em><b>구단</b><span class="g">경기</span><span>승</span><span>무</span><span>패</span><strong>승점</strong><span>변동</span></div>'
            + "".join(out) + "</div>")


def me_html(me: dict, missions: list) -> str:
    rk, tot = (me["rank"].replace("구단 내 ", "").split(" / ") + [""])[:2]
    d0, d1 = me["daily"]
    return ('<div class="fx-me"><div class="fx-me-c"><span>MY CONTRIBUTION · ' + escape(me["club"]) + '</span>'
            f'<div class="fx-me-g"><div><b>{me["season"]:,}<small>점</small></b><em>시즌 누적 기여</em></div>'
            f'<div><b>{escape(rk)}</b><em>구단 내 개인 순위 · {escape(tot)}</em></div>'
            f'<div><b>{d0}<small> / {d1}</small></b><em>오늘 기여 / 일일 상한</em><i class="ox-bar"><i style="width:{d0 / d1 * 100:.0f}%"></i></i></div></div>'
            f'<p>{escape(me["need"])} · 보상: {escape(me["reward"])}</p></div>'
            '<div class="fx-me-m"><span>기여 미션 (가상 예시)</span>' + "".join(f"<i>{escape(x)}</i>" for x in missions) + "</div></div>")


def podium_html(res: list, w: int) -> str:
    """경쟁 점수 결과 먼저: 최종 순위 · 점수 막대 · 누적만/평균만 순위 비교 (정적 위젯 JS 와 같은 마크업)."""
    o = sorted(res, key=lambda r: r["rank_score"])
    big = next((r for r in res if r["rank_total"] == 1), None)
    cards = "".join(f'<div class="{"r1" if r["rank_score"] == 1 else ""}"><em>{"🏆 " if r["rank_score"] == 1 else ""}{r["rank_score"]}위</em>'
                    f'<b>{escape(r["name"])}</b><strong>{r["score"]:.1f}</strong><i><span style="width:{min(r["score"], 100):.0f}%"></span></i>'
                    f'<small>누적만 {r["rank_total"]}위 · 평균만 {r["rank_avg"]}위</small></div>' for r in o)
    note = (f'반영 비중 누적 {w} : 평균 {100 - w} · 사람 수가 가장 많은 {escape(big["name"])}(누적 1위)는 최종 {big["rank_score"]}위' if big else "")
    return f'<div class="fx-pod">{cards}</div><p class="fx-pod-n">{note} · <span class="ox-k sim">가정 시뮬레이션</span></p>'


def t5(d: dict) -> None:
    mc = d["mcw"]
    h("MY CLUB WAR · 우리 구단의 자존심을 걸고.", "mock", num="05", name="대표 마케팅 기획 — 실제 구단 팬덤 시즌 리그",
      lead=escape(mc["sub"]) + " · 보상 이벤트가 아니라 '내 구단을 우승시키려고' 참여하는 8주 시즌제 대항전 · " + escape(mc["license"]))
    html(brief4(d, "MY CLUB WAR", "대표 기획 · 기획 시안"))
    names = [r["name"] for r in mc["rivals"]]
    js("fcrival")
    pick = st.radio("라이벌 매치", names, horizontal=True, key="fc_rival")
    rv = next(r for r in mc["rivals"] if r["name"] == pick)
    st.session_state.setdefault("fc_rival_plus", 0)
    html(mock("MY CLUB WAR · 라이벌 매치 · 점수·기간은 가상", '<div class="fx-stadium"><div class="fx-war-h">MY CLUB WAR<small>시즌 1 · 라이벌 위크</small></div>'
              + _rival_html(rv, st.session_state["fc_rival_plus"]) + "</div>", "night"))
    if st.button("라이벌 매치 참여 (콘셉트 · +30점)", key="fc_rival_join"):
        st.session_state["fc_rival_plus"] += 30
        st.rerun()
    js_end()

    un = mc["union"]
    h("이미 있는 '팀컬러 연합 레이스'와 무엇이 다른가 — 공식 자료로 확인", "real",
      lead="기여도 적립·순위 보상은 이미 있는 방식 → 새 기능이라 하지 않고 활용 · 출처 " + " · ".join(src(u, t) for t, u in un["src"]))
    html(f'<div class="fx-union">{fig(un["img"], "팀컬러 연합 레이스 (2026.10.29~11.25)")}<ul class="ox-facts">'
         + "".join(f"<li><b>{escape(a)}</b> · {escape(b)}</li>" for a, b in un["facts"]) + "</ul></div>")
    html('<div class="fx-diff3"><div class="hd"><span></span><b>팀컬러 연합 레이스 (기존)</b><b>MY CLUB WAR</b></div>'
         + "".join(f'<div><span>{escape(a)}</span><p>{escape(b)}</p><p class="new">{escape(c)}</p></div>' for a, b, c in mc["diff3"]) + "</div>")

    h("팬덤 리그 순위표 · 주간 대항전 승 3 · 무 1 · 패 0", "mock", lead=escape(mc["league_note"]))
    me = mc["me"]
    html(league_html(mc["league"], me["club"]))
    h("나의 기여도 · 이기는 것만이 아니라 참여로도 기여한다", "mock", lead=escape(mc["mission_rules"]))
    html(me_html(me, mc["missions"]))

    h("인기 구단이 사람 수만으로 이기지 않게 · 경쟁 점수 시뮬레이터", "sim",
      lead="사람 수(누적)와 1인당 활동(평균)을 함께 본다 · 결과 먼저, 계산식과 가정값은 아래 펼쳐보기")
    fs = d["fandom_sim"]
    js("fcfandom")
    st.session_state.setdefault("fc_fw", fs["w_total"])
    board = st.container()
    with st.expander("가정값 바꾸기 · 계산 과정 · 반영 비중 슬라이더"):
        st.caption("최종 = 정규화 누적 × 규모 비중 + 정규화 평균 × 활동 비중 · 정규화 = 해당 값 ÷ 최고값 × 100 · 기본 30:70은 테스트용 가정")
        w = st.slider("누적 활동 점수 반영 비중 (%) · 평균 비중은 100 − 이 값", 0, 100, key="fc_fw")
        cols = st.columns(3)
        rows_in = []
        for k, (n, ppl, av) in enumerate(fs["rows"]):
            c = cols[k]
            a1 = c.number_input(f"{n} 참여 인원", 0, 10_000_000, int(ppl), step=1000, key=f"fc_fp{k}")
            a2 = c.number_input(f"{n} 1인당 평균 점수", 0.0, 10_000.0, float(av), step=1.0, key=f"fc_fa{k}")
            rows_in.append([n, a1, a2])
        res = B.fandom(rows_in, w)
        table(["팬덤 (가상)", "누적 점수", "정규화 누적", "정규화 평균", f"최종 ({w}:{100 - w})", "누적만 순위", "평균만 순위", "최종 순위"],
              [[escape(r["name"]), f'{r["total"]:,.0f}', f'{r["n_total"]:.1f}', f'{r["n_avg"]:.1f}', f'<b>{r["score"]:.1f}</b>',
                f'{r["rank_total"]}위', f'{r["rank_avg"]}위', f'<b>{r["rank_score"]}위</b>'] for r in res], cls="ox-mops")
        f = go.Figure(go.Bar(x=[r["name"] for r in res], y=[r["score"] for r in res], marker_color=ACC, text=[f'{r["score"]:.1f}' for r in res],
                             textposition="outside", cliponaxis=False))
        f.update_yaxes(title="최종 경쟁 점수", range=[0, 110])
        ox_chart_card(f, key="fcfan", kind="sim", title="최종 경쟁 점수 (0~100)", unit="점 · 가상 팬덤 3개", kpis=[], analysis="", decision="",
                      basis="", height=260, legend=False, cols=("팬덤", "점수"))
    with board:
        html(podium_html(res, w))
    js_end()
    with st.expander("추가 공정 장치 · 운영 규칙"):
        st.caption("추가 공정 장치: 최소 유효 참여 인원 · 소규모 팬덤 평균 변동성 검토 · 다중 계정·반복 참여 방지 · 일일 상한 · 규모별 리그 · 시즌 중 구단 변경 제한 — 실제 데이터 테스트로 조정")

    h("신규 축구 팬 → 장기 유저: 8단계 전환 퍼널", "mock", lead="처음부터 큰돈을 쓰거나 고전력 유저와 바로 부딪히지 않게 · 기간제 체험 선수단")
    html('<div class="fx-funnel8">' + "".join(f'<div style="--w:{96 - k * 8}%"><em>{k + 1}</em>{escape(s)}</div>' for k, s in enumerate(mc["funnel"]))
         + "</div>")
    st.caption("개념도 · 막대 길이는 단계 순서를 나타낼 뿐 실제 전환 비율이 아님 (실제 수치는 07 탭 퍼널 시뮬레이션)")
    html('<div class="fx-3">' + "".join(f'<div><span>{escape(a)}</span><p>{escape(b)}</p></div>' for a, b in mc["targets3"]) + "</div>")
    h("8주 시즌 일정", "mock")
    html('<div class="fx-weeks">' + "".join(f'<div><em>{escape(w_)}</em><span>{escape(t)}</span></div>' for w_, t in mc["weeks"]) + "</div>")
    st.caption("실제 축구 경기 일정 연계 가능성은 검토 사항 · 확정 일정 아님")
    with st.expander("시즌 구성 · 명예의 전당 · 보상 원칙"):
        html('<div class="fx-steps">' + "".join(f'<div><em>{escape(a)}</em><small>{escape(b)}</small></div>' for a, b in mc["season"]) + "</div>")
        html(f'<ul class="ox-facts"><li><b>명예의 전당</b> · {dots(mc["hall"])}</li><li><b>보상</b> · {dots(mc["rewards"])} · {escape(mc["reward_rule"])}</li></ul>')
    with st.expander("구단 대표 크리에이터 대항전 · 외부 마케팅 채널 · 측정 지표"):
        html(f'<ul class="ox-facts"><li><b>콘텐츠</b> · {dots(mc["creator"])}</li><li><b>채널</b> · {dots(mc["channels"])}</li>'
             f'<li><b>측정</b> · {dots(mc["creator_kpi"])}</li><li>{escape(mc["creator_note"])}</li></ul>')
    with st.expander("차별성 상세 비교표 8개 항목 · 아이콘매치와의 관계"):
        table(["비교 항목", "팀컬러 연합 레이스 (기존)", "MY CLUB WAR"], [[f"<b>{escape(a)}</b>", escape(b), escape(c)] for a, b, c in mc["diff"]], cls="ox-mops")
        st.caption(mc["diff_note"])
        table(["", "아이콘매치 (기존)", "MY CLUB WAR"], [[f"<b>{escape(a)}</b>", escape(b), escape(c)] for a, b, c in mc["vs_icon"]], cls="ox-mops")
        st.caption("아이콘매치를 대체하지 않는다 · 이미 확보한 관심을 게임 안 지속 참여로 잇는 추가 전략")
    st.caption("KPI · " + " · ".join(mc["kpi"]) + " · 이벤트 참여 인원이 아니라 가입 → 첫 경기 → D30까지 이어서 평가")


# ----------------------------------------------------------------------
# 06 FAIR PLAY
def t6(d: dict) -> None:
    fp = d["fair"]
    c = fp["controller"]
    h("'패드가 무조건 유리하다'고 단정하지 않는다 — 데이터로 먼저 검증", "hypo", num="06", name="FAIR PLAY PROJECT",
      lead=f"{c['date']} 공식 데이터센터 · 공식경기 1ON1 · 랭킹 1~10,000위 기준 · 전체 유저 비율이나 승률이 아님")
    html(brief4(d, "FAIR PLAY"))
    html(f'<div class="fx-io"><div><i class="kb"></i><b>{c["kb"]}%</b><span>키보드</span></div><div><i class="pad"></i><b>{c["pad"]}%</b><span>패드</span></div></div>')
    html(f'<div class="ox-pair">{slot(fp["slots"][0][0], fp["slots"][0][1])}{slot(fp["slots"][1][0], fp["slots"][1][1])}</div>')
    s = fp["voc_sides"]
    html('<div class="fx-3">'
         f'<div><span>키보드 유저</span>{bullets(s["keyboard"])}</div><div><span>패드 유저</span>{bullets(s["pad"])}</div>'
         f'<div><span>중립 의견</span><p>{escape(s["third"])}</p></div></div>')
    html('<div class="fx-chips">' + "".join(f"<span>{escape(x)}</span>" for x in fp["cats"]) + "</div>")
    st.caption(fp["other"])
    h("검증 → 개선 → 선택 매칭 테스트 · 격차가 확인될 때만 다음 단계", "mock")
    html(flow_html([(escape(a.split(" ", 1)[-1]), escape(b)) for a, b in fp["steps"]], hl=0))
    of = fp["official"]
    html(f'<div class="ox-purpose fx-off"><span>공식 대응 확인</span>{escape(of[0])} · {src(of[1], "공지 ↗")}</div>')
    html(f'<div class="ox-purpose"><span>사업PM 관점</span>{escape(fp["pm"])} · {escape(fp["stop"])}</div>')
    with st.expander("공식 데이터센터 원본 캡처 · KPI"):
        html(fig("controller_share.jpg", "공식 데이터센터 · 컨트롤러 이용 비중"))
        st.caption("KPI · " + " · ".join(fp["kpi"]))


# ----------------------------------------------------------------------
# 07 사업성·실행
def _apply(prefix: str, vals: dict) -> None:
    for k, v in vals.items():
        st.session_state[prefix + k] = v


def _sim_inputs(prefix: str, cfg: dict, title: str = "가정값 바꾸기") -> dict:
    for k, v in cfg["defaults"].items():
        st.session_state.setdefault(prefix + k, v)
    cols = st.columns(len(cfg["presets"]) + 1)
    for i, n in enumerate(cfg["presets"]):
        cols[i].button(n, key=f"{prefix}p{i}", on_click=_apply, args=(prefix, {**cfg["defaults"], **cfg["presets"][n]}), width="stretch")
    cols[-1].button("초기화", key=f"{prefix}reset", on_click=_apply, args=(prefix, dict(cfg["defaults"])), width="stretch")
    with st.expander(title):
        cc = st.columns(3)
        for j, (k, lab, lo, hi, step) in enumerate(cfg["fields"]):
            cast, fm = (float, "%.1f") if k in PCT_KEYS else (int, "%d")
            cc[j % 3].number_input(lab, min_value=cast(lo), max_value=cast(hi), step=cast(step), format=fm, key=prefix + k)
    return {k: st.session_state[prefix + k] for k in cfg["defaults"]}


def keep_html(r: dict) -> str:
    return (f'<div class="ox-res"><div><span>기존 이탈 예상</span><b>{r["lost0"]:,.0f}명</b><small>이탈률 {r["x"]["churn0"]:g}%</small></div>'
            f'<div><span>개선 후 이탈 예상</span><b>{r["lost1"]:,.0f}명</b><small>이탈률 {r["x"]["churn1"]:g}%</small></div>'
            f'<div><span>추가 유지 유저</span><b>{r["kept"]:,.0f}명</b><small>월 매출 보전 {owon(r["monthly"])}</small></div>'
            f'<div class="{"neg" if r["total"] < 0 else "acc"}"><span>{r["x"]["months"]:g}개월 누적 매출 보전</span><b>{owon(r["total"])}</b>'
            '<small>순이익 아님 · 운영비 미차감</small></div></div>'
            '<p class="ox-note">계산: 추가 유지 = 결제 유저 × (기존 이탈률 − 개선 후 이탈률) · 월 보전 = 추가 유지 × 월평균 결제 · 누적 = 월 보전 × 기간 · 이탈률이 오히려 오르면 음수로 표시</p>')


def funnel_html(fr: dict) -> str:
    def w(x):
        return "—" if x is None else (owon(x) if abs(x) >= 1e4 else f"{x:,.0f}원")
    ratio = "—" if fr["ratio"] is None else f"{fr['ratio'] * 100:.0f}%"
    bep = "—" if fr["bep_pur"] is None else f"{fr['bep_pur']:.1f}%"
    sign = "neg" if fr["profit"] < 0 else "acc"
    return (f'<div class="fx-funnel"><span>방문 {fr["visits"]:,.0f}</span><i>→</i><span>가입 {fr["signups"]:,.0f}</span><i>→</i>'
            f'<span>D7 {fr["d7"]:,.0f}</span><i>→</i><span>D30 {fr["d30"]:,.0f}</span></div>'
            f'<div class="ox-res"><div><span>총 캠페인 비용</span><b>{owon(fr["cost"])}</b><small>CPA {w(fr["cpa"])} · D30 1명당 {w(fr["cost_d30"])}</small></div>'
            f'<div><span>D30 잔존 1명 LTV (매출 기준)</span><b>{w(fr["ltv"])}</b><small>결제율 × 월 결제액 × {fr["x"]["months"]:g}개월</small></div>'
            f'<div><span>LTV 합계 ÷ 비용</span><b>{ratio}</b><small>기대 매출 {owon(fr["revenue"])}</small></div>'
            f'<div class="{sign}"><span>반영 비용 차감 후</span><b>{owon(fr["profit"])}</b><small>손익분기 결제율 {bep} · 순이익 아님</small></div></div>'
            '<p class="ox-note">신규 유저 마케팅은 첫 몇 달 안에 비용을 회수하기 어렵다 → 판단 기준은 허용 가능한 CPA와 D30 잔존 · 라이선스·개발비는 미확정이라 기본 0원</p>')


def t7(d: dict) -> None:
    S = d["sims"]
    h("기존 결제 유저 500명을 지키면 3개월 매출 7,500만 원이 보전된다 (가상)", "sim", num="07", name="사업성 시뮬레이션",
      lead=escape(S["keep"]["note"]))
    js("fckeep")
    box = st.container()
    r = B.keep(S["keep"], _sim_inputs("fk_", S["keep"]))
    with box:
        html(keep_html(r))
    js_end()

    h("MY CLUB WAR: 도달 100만 → 가입 1만 → D30 1,500명 · 비용 8개 항목으로 본 사업성", "sim", lead=escape(S["funnel"]["note"]))
    js("fcfunnel")
    box = st.container()
    fr = B.funnel(S["funnel"], _sim_inputs("ff_", S["funnel"], "가정값 바꾸기 · 퍼널 5개 · 결제 3개 · 비용 8개 항목"))
    with box:
        html(funnel_html(fr))
    names = list(S["funnel"]["presets"])
    sc = [B.funnel(S["funnel"], {**fr["x"], **{k: v for k, v in {**S["funnel"]["defaults"], **S["funnel"]["presets"][n]}.items()
                                                 if k in ("visit", "signup", "d7", "d30")}}) for n in names]
    f = go.Figure([go.Bar(x=names, y=[s["revenue"] / 1e4 for s in sc], name="기대 매출 (D30 잔존 × LTV)", marker_color=ACC,
                          text=[owon(s["revenue"]) for s in sc], textposition="outside", cliponaxis=False),
                   go.Bar(x=names, y=[s["cost"] / 1e4 for s in sc], name="총 캠페인 비용", marker_color=GRAY,
                          text=[owon(s["cost"]) for s in sc], textposition="outside", cliponaxis=False)])
    f.update_layout(barmode="group")
    f.update_yaxes(title="만 원", tickformat=",", rangemode="tozero")
    ox_chart_card(f, key="fcfun", kind="sim", title="보수적 · 기준 · 낙관적: 기대 매출 vs 총 캠페인 비용",
                  unit="만 원 · 초록 = 기대 매출, 회색 = 비용 · 방문·가입·잔존율만 바꿈", kpis=[], analysis="", decision="", basis="",
                  height=320, cols=("시나리오", "만 원"), series="항목")
    js_end()

    h("전략별 KPI · 측정 대상 · 기간 · 계산 방식 · 성공 기준", "mock")
    table(["전략", "핵심 KPI", "측정 대상", "기간", "계산 방식", "성공 판단"], [[f"<b>{escape(a)}</b>", *[escape(x) for x in r_]] for a, *r_ in d["kpis"]],
          cls="ox-mops")
    pr = d["priority"]
    h("실행 우선순위 · CARE로 빠르게 검증하고 MY CLUB WAR로 키운다", "interp", lead=escape(pr["note"]))
    table(["전략", *pr["criteria"]], [[f"<b>{escape(a)}</b>", *[escape(x) for x in r_]] for a, *r_ in pr["rows"]], cls="ox-mops")
    h("로드맵 · 다음 단계로 가는 조건과 멈추는 조건", "mock", lead="기획 단계 로드맵 · 실제 개발 일정 아님")
    html('<div class="fx-road">' + "".join(f'<div><em>{escape(a)}</em><b>{escape(b)}</b><p><span>확대</span>{escape(c)}</p><p><span>중단·축소</span>{escape(e)}</p></div>'
                                           for a, b, c, e in d["roadmap"]) + "</div>")
    html(f'<div class="ox-purpose"><span>최종 결론</span>{escape(d["conclusion"])}<br><b>{escape(d["final_msg"])}</b></div>')
