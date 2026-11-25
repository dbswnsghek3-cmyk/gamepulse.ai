"""FC 온라인 — 축구 게임인가, 주식 게임인가? (2026-11 개편 · 7탭 · 가독성 우선)

01 개요·시장 · 02 BM 강점 · 03 유저 VOC 50 · 04 구단 가치 (CLUB CARE · CLUB REBUILD) · 05 MY CLUB WAR · 06 FAIR PLAY · 07 사업성·실행
- 사실·VOC·기획: data/fconline/fc2.json (이전 자료 fc.json 은 보존) · 계산: gamepulse/sim/fc_biz.py (정적 JS 와 같은 식)
- 실제 화면: assets/fconline/*.jpg (작성자 캡처 · 계정 정보 블러) · 기획 화면은 HTML 콘셉트 (실제 게임 화면 아님)
- 정적 사이트: ox-js-start ~ ox-js-end 구역을 scripts/fc_static_widgets.py 의 JS 위젯으로 교체
이전 화면 코드는 fconline_v1.py 에 보관.
"""

from __future__ import annotations

import json
from collections import Counter
from html import escape
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from gamepulse.sim import fc_biz as B
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
ACC, GRAY = "#16A34A", "#9CA3AF"   # FC 온라인 테마 · 비교 기준 (범례와 같은 색)
CAP = "작성자 캡처 · 2026-11-23 · 계정 정보 블러"
PCT_KEYS = {"churn0", "churn1", "visit", "signup", "d7", "d30", "pur"}


@st.cache_data(show_spinner=False)
def load() -> dict:
    return json.loads((DATA / "fc2.json").read_text(encoding="utf-8"))


def fig(name: str, label: str, cap: str = CAP) -> str:
    p = ASSETS / name
    if not p.is_file():
        return ""
    return (f'<figure class="ox-fig real"><details class="ox-zoom"><summary title="클릭하면 크게 보기">'
            f'<img src="data:image/jpeg;base64,{_jpg_b64(str(p), p.stat().st_mtime)}" alt="{escape(label)}" loading="lazy"></summary></details>'
            f'<figcaption><b>실제 게임 화면</b>{escape(label)} · {escape(cap)}</figcaption></figure>')


def src(url: str, text: str) -> str:
    return f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener">{escape(text)}</a>' if url else escape(text)


def mock(tag: str, inner: str, cls: str = "") -> str:
    return f'<div class="fx-mock {cls}"><div class="fx-mock-tag">기획 시안 · 실제 게임 화면 아님 · {escape(tag)}</div>{inner}</div>'


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
    cv = d["cover"]
    img = fig("main_screen.jpg", "FC 온라인 메인 화면")
    html(f'<div class="owx-hero ox-cover fx-cover"><div class="owx-t"><div class="ow-cover-t">{escape(cv["kicker"])}</div>'
         f'<div class="owx-q" role="heading" aria-level="1">{escape(cv["title"])}</div><p class="owx-s">{escape(cv["subtitle"])}</p>'
         '<div class="ox-tracks"><span><b>이탈 방지</b>CLUB CARE · CLUB REBUILD</span><span><b>신규 고객</b>MY CLUB WAR</span>'
         '<span><b>경쟁 환경</b>FAIR PLAY PROJECT</span></div></div>' + (f'<div class="fx-cover-img">{img}</div>' if img else "") + "</div>")
    i = tab_nav()
    ox_badge_legend()
    html(f'<div class="ow-pane-mark" data-tab="{SECTIONS[i][0]}"></div>')
    [t1, t2, t3, t4, t5, t6, t7][i](d)
    st.caption(f"{d['disclaimer']} · 자료 확인일 {d['checked_at']}")


# ----------------------------------------------------------------------
# 01 개요·시장
def t1(d: dict) -> None:
    m = d["market"]
    h("국내 PC방 2위권 축구 게임, 실제 축구 일정이 이용을 끌어올린다", "real", num="01", name="게임 개요 · 시장 경쟁력",
      lead="넥슨 서비스 · EA SPORTS 라이선스 · 실제 선수·구단 IP · 조사 기준일 2026-11-25")
    html('<div class="fx-pts">' + "".join(
        f'<div><span>{escape(p["when"])}</span><b>{escape(p["share"])}</b><em>{escape(p["rank"])}</em>'
        f'<small>{src(p["url"], p["src"])}</small></div>' for p in m["points"]) + "</div>")
    x = [a for a, _ in m["usage"]]
    y = [b for _, b in m["usage"]]
    f = go.Figure(go.Bar(x=x, y=y, marker_color=ACC, text=[f"{v}만" for v in y], textposition="outside", cliponaxis=False))
    f.update_yaxes(title="주간 PC방 사용시간 (만 시간)", rangemode="tozero", range=[0, max(y) * 1.25])
    ox_chart_card(f, key="fcusage", kind="real", title="월드컵(6/11 개막) 기간 주간 사용시간 84만 → 124만 시간",
                  unit="만 시간 · " + m["usage_src"], kpis=[], analysis="", decision="", basis="", height=300, legend=False,
                  cols=("주차", "사용시간 (만 시간)"))
    html('<div class="ox-mcards">' + "".join(f'<div><b>{escape(a)}</b><span>{escape(b)}</span></div>' for a, b in m["strengths"]) + "</div>")
    st.caption(m["caution"])
    with st.expander("경쟁작과의 차이 · 시장 자료 원문"):
        table(["게임", "서비스 형태"], [[f"<b>{escape(a)}</b>", escape(b)] for a, b in m["compare"]])
        st.caption(m["compare_note"])
        table(["시점", "순위", "점유율", "출처", "참고"],
              [[escape(p["when"]), escape(p["rank"]), escape(p["share"]), src(p["url"], p["src"]), escape(p["note"])] for p in m["points"]])

    h("성공한 BM은 지키고, 이탈과 신규 유입을 손본다: 전략 4개", "mock", num="01", name="핵심 전략")
    html('<div class="fx-4">' + "".join(f'<div><em>{escape(n)}</em><span>{escape(g)}</span></div>' for n, g in d["final"]) + "</div>")
    html(f'<div class="ox-purpose"><span>사업PM 결론</span>{escape(d["final_msg"])}</div>')


# ----------------------------------------------------------------------
# 02 BM 강점
def t2(d: dict) -> None:
    bm, mk = d["bm"], d["marketing"]
    h("멤버십 → 페이백 → 이벤트 → 강화가 이어져 반복 결제와 접속을 만든다", "real", num="02", name="기존 BM 강점",
      lead=escape(bm["insight"]))
    html(f'<div class="ox-pair">{fig("burning_week.jpg", "버닝 위크 · PC방·집 접속 보상 + 강화 부스트")}'
         f'{fig("market_trend.jpg", "이적시장 트렌드 센터 · 시세 급상승·최고 거래가")}</div>')
    rows = []
    for b in bm["items"]:
        if b["status"] == "real":
            rows.append([f"<b>{escape(b['name'])}</b>", escape(b["fact"]), escape(b["psy"]), src(b["url"], b["src"])])
        else:
            rows.append([f"<b>{escape(b['name'])}</b>", '<span class="ox-pend">캡처 확인 필요</span>', escape(b["psy"]), "—"])
    table(["BM · 운영", "확인한 내용", "구매·접속 동기", "근거"], rows, cls="ox-mops")
    html(f'<div class="ox-purpose"><span>함께 볼 위험</span>{escape(bm["risk"])}</div>')

    ic = mk["icon"]
    h("아이콘매치는 이틀 10만 관중 · 과제는 관심을 '지속 참여'로 잇는 것", "real", num="02", name="기존 마케팅")
    stats([("약 10만 명", "2025 아이콘매치 이틀 관중", "real"), ("60만 명", "온라인 동시 시청 최고", "real"),
           ("340만 명", "생중계 누적 시청", "real")])
    st.caption(f"{ic['title']} · {ic['when']} · 출처 {ic['src']}")
    html(f'<ul class="ox-facts"><li>{escape(mk["worldcup"])}</li><li>{escape(mk["limit"])}</li><li>{escape(mk["existing_event"])}</li></ul>')


# ----------------------------------------------------------------------
# 03 유저 VOC 50
def t3(d: dict) -> None:
    V = d["voc"]
    cats = Counter(v["cat"] for v in V)
    neg = Counter(v["cat"] for v in V if v["tone"] == "부정")
    order = [c for c, _ in cats.most_common()]
    h(f"VOC {len(V)}건 · 조작 {cats.get('키보드·패드 조작', 0)} · 구단 가치 {cats.get('구단 가치·시세', 0)} · 강화 {cats.get('강화', 0)} · BM {cats.get('BM·과금', 0)}",
      "real", num="03", name="실제 유저 VOC", lead=escape(d["voc_note"]))
    f = go.Figure([go.Bar(y=order, x=[neg.get(c, 0) for c in order], name="부정", orientation="h", marker_color=ACC),
                   go.Bar(y=order, x=[cats[c] - neg.get(c, 0) for c in order], name="중립", orientation="h", marker_color=GRAY)])
    f.update_layout(barmode="stack")
    f.update_yaxes(autorange="reversed", automargin=True)
    f.update_xaxes(title="건")
    ox_chart_card(f, key="fcvoc", kind="real", title="주제별 VOC · 진한 색 = 부정, 회색 = 중립 (긍정으로 분류된 글 0건)",
                  unit="건 · 한 글은 주 분류 1개", kpis=[], analysis="", decision="", basis="", height=320, cols=("주제", "건"), series="방향")
    html('<ol class="ox-ins">'
         '<li><b>구단 가치·강화</b> — 하루 만의 반토막·강화 실패 손실이 "접는다"는 표현과 함께 나온다</li>'
         '<li><b>조작</b> — 키보드 불리 주장과 패드 쪽 반론이 함께 있고, 패스 실수는 입력 습관 문제라는 글도 있다</li>'
         '<li><b>이적시장</b> — 시세 하락을 "팀 맞추기 좋은 때"로 보는 글처럼 거래 자체를 즐기는 유저도 있다</li></ol>')
    js("fcvoc")
    c1, c2 = st.columns(2)
    cat = c1.selectbox("주제", ["전체"] + order, key="fc_voc_cat")
    q = c2.text_input("검색 (제목·요약)", key="fc_voc_q")
    rows = [v for v in V if (cat == "전체" or v["cat"] == cat) and (not q.strip() or q.strip().lower() in (v["title"] + v["summary"]).lower())]
    table(["번호", "출처 · 작성일", "제목 (원문 링크)", "요약", "주제", "방향"],
          [[v["id"], f'{escape(v["src"])}<br><small>{escape(v["date"])}</small>', src(v["url"], v["title"]), escape(v["summary"]),
            escape(v["cat"]), escape(v["tone"])] for v in rows], cls="ox-mops fx-voc")
    js_end()
    st.caption("보조 자료 (50건 미포함): " + " · ".join(t for _, t, _ in d["voc_extra"]) +
               " · 표본에 긍정 분류 글이 없어 만족 유저 의견은 추가 수집이 필요하다")


# ----------------------------------------------------------------------
# 04 구단 가치 · CLUB CARE · CLUB REBUILD
def t4(d: dict) -> None:
    h("가치 급락 → 박탈감 → 인생 강화 → 이탈: VOC로 관찰한 이탈 경로", "hypo", num="04", name="구단 가치 하락과 유저 이탈",
      lead=escape(d["chain_note"]))
    html('<div class="fx-chain">' + '<i>→</i>'.join(f'<span class="{"hot" if k >= 4 else ""}">{escape(s)}</span>'
                                                   for k, s in enumerate(d["chain"])) + "</div>")
    html('<div class="ox-purpose"><span>사업적 의미</span>구단 성장은 핵심 매출 동력이지만, 급락을 겪으면 이탈 동력이 된다 → 신규 시즌 판매를 멈추는 게 아니라 '
         '판매와 고객 유지의 균형을 잡는다.</div>')
    dr = d["drops"]
    html(f'<div class="ox-pair">{fig(dr[0]["file"], "시세 그래프 · " + dr[0]["card"])}{fig(dr[1]["file"], "시세 그래프 · " + dr[1]["card"])}</div>')
    table(["카드", "그래프 최고", "최근", "변화"],
          [[escape(x["card"]), f'{x["peak"]:,} BP', f'{x["now"]:,} BP', f'<b>{(x["now"] / x["peak"] - 1) * 100:.0f}%</b>'] for x in dr],
          cls="ox-mops")
    st.caption("같은 카드·같은 강화의 이적시장 그래프 관측값 (2026-11-23 캡처) · 시장 전체 대표 아님")

    h("구단 가치가 올라도, 목표 선수 기준 구매력은 줄 수 있다", "sim", lead="가상 시뮬레이션 · 명목 구단 가치와 실질 구매력 비교")
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
    h(f"{ca['name']} · {ca['slogan']}", "mock", num="04", name="개선 기획 A — 구단 가치 관리")
    html(mock("CLUB CARE · 구단 가치 리포트",
              '<div class="fx-care"><div class="fx-care-l"><b>내 구단 가치 · 최근 30일</b><div class="fx-spark"><i style="height:90%"></i><i style="height:88%"></i>'
              '<i style="height:86%"></i><i style="height:70%"></i><i style="height:52%"></i><i style="height:50%"></i><i style="height:54%"></i></div>'
              '<small>−42% · 하락 기여 1위 선수 A (같은 선수 신규 시즌 출시)</small></div>'
              '<div class="fx-care-r"><div><span>보유 선수 급락</span><b>선수 A −58% · 선수 B −31%</b></div>'
              '<div><span>시장 변화</span><b>신규 시즌 출시 · 공급 이벤트 진행 중</b></div>'
              '<div><span>목표 선수 기준 구매력</span><b>−50%</b></div><div><span>알림</span><b>동의한 항목만 · 매수·매도 권유 없음</b></div></div></div>'))
    st.caption("화면 속 수치는 기능 설명용 가상 수치")
    html('<div class="ox-mcards">' + "".join(f'<div><b>{escape(a)}</b><span>{escape(b)}</span></div>' for a, b in ca["features"]) + "</div>")
    html(f'<ul class="ox-facts"><li><b>원칙</b> · {dots(ca["rules"])}</li><li>{escape(ca["existing"])}</li><li><b>KPI</b> · {dots(ca["kpi"])}</li></ul>')

    rb = d["rebuild"]
    h(f"{rb['name']} · {rb['slogan']}", "mock", num="04", name="개선 기획 B — 구단 재건",
      lead="이미 떠난 유저가 아니라, 떠나기 전의 활성 유저에게 먼저 다른 선택지를 준다")
    dm = rb["demo"]
    drop = (dm["now"] / dm["before"] - 1) * 100
    html(mock("CLUB REBUILD · 가상 유저 사례",
              f'<div class="fx-rb"><div class="fx-rb-v"><div><span>기존 구단 가치</span><b>{dm["before"]}조 BP</b></div>'
              f'<div><span>현재 구단 가치</span><b>{dm["now"]}조 BP</b></div><div><span>하락률</span><b class="dn">{drop:.0f}%</b></div></div>'
              '<div class="fx-rb-c"><div class="on"><b>팀컬러 유지형</b><small>주전 유지 · 부족 포지션만 보강</small></div>'
              '<div><b>신규 구단 재편형</b><small>현재 자산으로 새 팀컬러 구성</small></div></div>'
              '<div class="fx-rb-m"><span>재건 미션 · 7일</span><div class="ox-bar"><i style="width:57%"></i></div>'
              '<small>4/7일 · 기간제 체험 선수 2명 (거래 불가)</small></div></div>'))
    st.caption("사례 수치(500조 → 200조)와 미션 진행률은 기능 설명용 가상 수치")
    html('<div class="fx-steps">' + "".join(f'<div><em>STEP {k}</em><b>{escape(a)}</b><small>{escape(b)}</small></div>'
                                            for k, (a, b) in enumerate(rb["steps"], 1)) + "</div>")
    html(f'<ul class="ox-facts"><li><b>대상 (기획 기준 · 내부 데이터로 확정)</b> · {dots(rb["target"])}</li>'
         f'<li><b>악용·경제 방지</b> · {dots(rb["guard"])}</li><li><b>KPI</b> · {dots(rb["kpi"])}</li></ul>')


# ----------------------------------------------------------------------
# 05 MY CLUB WAR
def t5(d: dict) -> None:
    mc = d["mcw"]
    h(f"{mc['name']} · {mc['slogan']}", "mock", num="05", name="신규 마케팅 — 구단 팬덤 대항전",
      lead="경기를 하지 않는 축구 팬도 '응원 구단'으로 들어오게 하는 8주 캠페인 · " + escape(mc["license"]))
    rank = B.fandom(mc["fair_demo"])
    rows = "".join(f'<div><b>{r["rank_mixed"]}</b><span>{escape(r["name"])}</span><small>{r["people"]:,}명 · 1인당 {r["avg"]}점</small></div>'
                   for r in sorted(rank, key=lambda r: r["rank_mixed"]))
    html(mock("MY CLUB WAR · 캠페인 화면",
              '<div class="fx-war"><div class="fx-war-h">MY CLUB WAR<small>시즌 1 · 4주차 · 라이벌 매치 주간</small></div>'
              '<div class="fx-war-g"><div><span>나의 구단</span><b>응원 구단 1개 선택</b><small>기간 중 변경 제한</small></div>'
              f'<div><span>실시간 팬덤 순위 (가상)</span><div class="fx-war-r">{rows}</div></div>'
              '<div><span>라이벌 매치</span><b>구단 A vs 구단 B</b><small>이번 주 특별 미션 · 경기 3회</small></div>'
              '<div><span>나의 기여도</span><b>1,240점</b><small>오늘 상한 300점 중 180점</small></div></div></div>', "pitch"))
    html('<div class="fx-steps">' + "".join(f'<div><em>STEP {k}</em><b>{escape(a)}</b><small>{escape(b)}</small></div>'
                                            for k, (a, b) in enumerate(mc["steps"], 1)) + "</div>")
    table(["", "아이콘매치 (기존)", "MY CLUB WAR (제안)"], [[f"<b>{escape(a)}</b>", escape(b), escape(c)] for a, b, c in mc["vs_icon"]],
          cls="ox-mops")
    st.caption("아이콘매치를 대체하지 않고, 이미 확보한 팬덤·인지도를 게임 안 지속 활동으로 잇는 추가 전략 · "
               "이벤트 메뉴의 '팀컬러 연합 레이스'와 규칙이 겹치는지 확인 필요")

    h("인기 구단이 사람 수만으로 이기지 않게: 누적 + 1인당 평균을 함께 본다", "sim", lead="가상 팬덤 3개로 본 점수 방식 비교")
    table(["팬덤 (가상)", "참여 인원", "1인당 평균", "누적 점수 순위", "1인당 평균 순위", "혼합 순위 (50:50)"],
          [[escape(r["name"]), f'{r["people"]:,}명', f'{r["avg"]}점', f'{r["rank_total"]}위', f'{r["rank_avg"]}위', f'<b>{r["rank_mixed"]}위</b>']
           for r in rank], cls="ox-mops")
    html(f'<ul class="ox-facts"><li><b>공정 장치</b> · {dots(mc["fair"])}</li>'
         '<li><b>타깃</b> · ' + " / ".join(f"{a}: {escape(b)}" for a, b in mc["targets"]) + "</li>"
         f'<li><b>외부 유입</b> · {dots(mc["external"])} (인플루언서 협업은 확정 아님)</li></ul>')
    h("8주 실행 일정", "mock")
    html('<div class="ox-gantt">' + "".join(f'<div><em>{escape(w)}</em><b></b><span>{escape(t)}</span></div>' for w, t in mc["weeks"]) + "</div>")
    st.caption("KPI · " + " · ".join(mc["kpi"]))


# ----------------------------------------------------------------------
# 06 FAIR PLAY
def t6(d: dict) -> None:
    fp = d["fair"]
    c = fp["controller"]
    h("'패드가 무조건 유리하다'고 단정하지 않는다 — 데이터로 먼저 검증", "hypo", num="06", name="키보드와 패드 경쟁 환경",
      lead=f"상위 1만 명 공식경기 1ON1 기준 키보드 {c['kb']}% · 패드 {c['pad']}% ({c['date']} 공식 데이터센터 · 전체 유저 비율 아님)")
    html(fig("controller_share.jpg", "공식 데이터센터 · 컨트롤러 이용 비중"))
    s = fp["voc_sides"]
    html('<div class="fx-3">'
         f'<div><span>키보드 쪽</span>{bullets(s["keyboard"])}</div><div><span>패드 쪽</span>{bullets(s["pad"])}</div>'
         f'<div><span>제3의 의견</span><p>{escape(s["third"])}</p></div></div>')
    h(f"{fp['name']} · 검증 → 개선 → 선택 매칭 테스트", "mock")
    html('<div class="fx-steps three">' + "".join(f'<div><em>{escape(a)}</em><small>{escape(b)}</small></div>' for a, b in fp["steps"]) + "</div>")
    html(f'<ul class="ox-facts"><li><b>보류 조건</b> · {escape(fp["stop"])}</li><li>{escape(fp["other"])}</li><li><b>KPI</b> · {dots(fp["kpi"])}</li></ul>')


# ----------------------------------------------------------------------
# 07 사업성·실행
def _apply(prefix: str, vals: dict) -> None:
    for k, v in vals.items():
        st.session_state[prefix + k] = v


def _sim_inputs(prefix: str, cfg: dict) -> dict:
    for k, v in cfg["defaults"].items():
        st.session_state.setdefault(prefix + k, v)
    cols = st.columns(len(cfg["presets"]) + 1)
    for i, n in enumerate(cfg["presets"]):
        cols[i].button(n, key=f"{prefix}p{i}", on_click=_apply, args=(prefix, {**cfg["defaults"], **cfg["presets"][n]}), width="stretch")
    cols[-1].button("초기화", key=f"{prefix}reset", on_click=_apply, args=(prefix, dict(cfg["defaults"])), width="stretch")
    with st.expander("가정값 바꾸기"):
        cc = st.columns(3)
        for j, (k, lab, lo, hi, step) in enumerate(cfg["fields"]):
            if k in PCT_KEYS:
                cast, fm = float, "%.1f"
            else:
                cast, fm = int, "%d"
            cc[j % 3].number_input(lab, min_value=cast(lo), max_value=cast(hi), step=cast(step), format=fm, key=prefix + k)
    return {k: st.session_state[prefix + k] for k in cfg["defaults"]}


def keep_html(r: dict) -> str:
    return (f'<div class="ox-res"><div><span>기존 이탈 예상</span><b>{r["lost0"]:,.0f}명</b><small>이탈률 {r["x"]["churn0"]:g}%</small></div>'
            f'<div><span>개선 후 이탈 예상</span><b>{r["lost1"]:,.0f}명</b><small>이탈률 {r["x"]["churn1"]:g}%</small></div>'
            f'<div><span>추가 유지 유저</span><b>{r["kept"]:,.0f}명</b><small>월 매출 보전 {owon(r["monthly"])}</small></div>'
            f'<div class="acc"><span>{r["x"]["months"]:g}개월 누적 매출 보전</span><b>{owon(r["total"])}</b><small>순이익 아님 · 운영비 미차감</small></div></div>')


def funnel_html(fr: dict) -> str:
    def w(x):
        return "—" if x is None else (owon(x) if abs(x) >= 1e4 else f"{x:,.0f}원")
    ratio = "—" if fr["ratio"] is None else f"{fr['ratio'] * 100:.0f}%"
    bep = "—" if fr["bep_pur"] is None else f"{fr['bep_pur']:.1f}%"
    sign = "neg" if fr["profit"] < 0 else "acc"
    return (f'<div class="fx-funnel"><span>방문 {fr["visits"]:,.0f}</span><i>→</i><span>가입 {fr["signups"]:,.0f}</span><i>→</i>'
            f'<span>D7 {fr["d7"]:,.0f}</span><i>→</i><span>D30 {fr["d30"]:,.0f}</span></div>'
            f'<div class="ox-res"><div><span>신규 가입 CPA</span><b>{w(fr["cpa"])}</b><small>D7 1명당 {w(fr["cost_d7"])} · D30 1명당 {w(fr["cost_d30"])}</small></div>'
            f'<div><span>D30 잔존 1명 LTV</span><b>{w(fr["ltv"])}</b><small>결제율 × 월 결제액 × {fr["x"]["months"]:g}개월</small></div>'
            f'<div><span>기대 매출 ÷ 비용</span><b>{ratio}</b><small>기대 매출 {owon(fr["revenue"])} · 비용 {owon(fr["cost"])}</small></div>'
            f'<div class="{sign}"><span>비용 차감 후</span><b>{owon(fr["profit"])}</b><small>손익분기 결제율 {bep}</small></div></div>'
            '<p class="ox-note">신규 유저 마케팅은 첫 몇 달 안에 비용을 회수하기 어렵다 → 판단 기준은 허용 가능한 CPA(가입자 1명의 기대 매출)와 D30 잔존이다.</p>')


def t7(d: dict) -> None:
    S = d["sims"]
    h("기존 결제 유저를 지키는 것이 가장 확실한 매출이다", "sim", num="07", name="KPI 및 사업성 시뮬레이션", lead=escape(S["keep"]["note"]))
    js("fckeep")
    box = st.container()
    r = B.keep(S["keep"], _sim_inputs("fk_", S["keep"]))
    with box:
        html(keep_html(r))
    js_end()

    h("MY CLUB WAR: 도달 100만 명 → 가입 1만 명 → D30 1,500명", "sim", lead=escape(S["funnel"]["note"]))
    js("fcfunnel")
    box = st.container()
    fr = B.funnel(S["funnel"], _sim_inputs("ff_", S["funnel"]))
    with box:
        html(funnel_html(fr))
    names = list(S["funnel"]["presets"])
    sc = [B.funnel(S["funnel"], {**fr["x"], **{k: v for k, v in {**S["funnel"]["defaults"], **S["funnel"]["presets"][n]}.items()
                                                 if k in ("visit", "signup", "d7", "d30")}}) for n in names]
    f = go.Figure([go.Bar(x=names, y=[s["revenue"] / 1e4 for s in sc], name="기대 매출 (D30 잔존 × LTV)", marker_color=ACC,
                          text=[owon(s["revenue"]) for s in sc], textposition="outside", cliponaxis=False),
                   go.Bar(x=names, y=[s["cost"] / 1e4 for s in sc], name="마케팅 비용", marker_color=GRAY,
                          text=[owon(s["cost"]) for s in sc], textposition="outside", cliponaxis=False)])
    f.update_layout(barmode="group")
    f.update_yaxes(title="만 원", tickformat=",", rangemode="tozero")
    ox_chart_card(f, key="fcfun", kind="sim", title="보수적 · 기준 · 낙관적: 기대 매출 vs 마케팅 비용",
                  unit="만 원 · 진한 색 = 기대 매출, 회색 = 비용 · 방문·가입·잔존율만 바꿈", kpis=[], analysis="", decision="", basis="",
                  height=320, cols=("시나리오", "만 원"), series="항목")
    js_end()

    h("전략별 KPI · 측정 대상 · 기간 · 성공 기준", "mock")
    table(["전략", "핵심 KPI", "측정 대상", "기간", "성공 판단"], [[f"<b>{escape(a)}</b>", *[escape(x) for x in r_]] for a, *r_ in d["kpis"]],
          cls="ox-mops")
    h("실행 로드맵 · 다음 단계로 가는 조건과 멈추는 조건", "mock", lead="기획 단계 로드맵 · 실제 개발 일정 아님")
    table(["단계", "할 일", "확대 조건", "중단·축소 조건"], [[f"<b>{escape(a)}</b>", *[escape(x) for x in r_]] for a, *r_ in d["roadmap"]],
          cls="ox-final")
    html(f'<div class="ox-purpose"><span>최종 메시지</span>{escape(d["final_msg"])}</div>')
