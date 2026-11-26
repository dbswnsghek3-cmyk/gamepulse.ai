"""PUBG: NEW START — 신규 유저 정착(A 55%) · 휴면·복귀 유저 재활성화(B 35%) · BM 신뢰·수익성(C 10%) 사업PM 포트폴리오.

구성 (오버워치 RE:START 와 같은 01~06 탭 · 같은 배지·차트 카드 규칙)
- 01 문제·결론 · 02 실제 유저 근거 · 03 원인 가설 · 04 해결책 데모 · 05 KPI·A/B 테스트 · 06 실행·사업 판단
- 공식 사실·가정값·시연 데이터: data/pubg/newstart.json (계산은 gamepulse/sim/newstart_sim.py 한 곳)
- 실제 유저 의견: 신규·BM = data/pubg/opinions.csv (Steam 리뷰 45건, 원본 그대로 · track 'B'는 BM → 화면에서 TRACK C)
                  휴면·복귀 = data/pubg/opinions_return.csv (Steam 리뷰 21건, 별도 표본)
- 색: TRACK A = 블루, TRACK B = 네이비, TRACK C = 코랄
- 게임 화면은 작성자가 직접 캡처한 assets/pubg/* (다른 플레이어 닉네임 가림 사본)만 표시. 원본은 _originals/ (git 제외).
  newstart.json screens[].ready=true 인 것만 표시, 없으면 '캡처 대기' 자리 (임의 이미지 생성 금지).
- YouTube 댓글은 확보한 원자료가 없어 사용하지 않는다 (추측해서 만들지 않음).
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from gamepulse.data.overwatch_images import web_jpeg_b64
from gamepulse.sim import newstart_sim as S
from gamepulse.ui.brief import brief_html, chips_html, flow_html
from gamepulse.ui.gallery import gallery_html
from gamepulse.ui.components import html
from gamepulse.views.overwatch import (C_CTRL, C_MUTED, C_TREAT, KIND, b_hypo, b_interp, b_mock, b_real, b_sample, b_sim,
                                       badge_legend, chart_card, head, hpair, link, note, pp, sub, table, tiles)

DATA = Path(__file__).resolve().parents[2] / "data" / "pubg"
ASSETS = Path(__file__).resolve().parents[2] / "assets" / "pubg"
C_CORAL, C_NAVY = "#E97870", "#1E3A8A"

SECTIONS = [("01", "문제·결론"), ("02", "실제 유저 근거"), ("03", "원인 가설"), ("04", "해결책 데모"),
            ("05", "KPI·A/B 테스트"), ("06", "실행·사업 판단")]
TAB_LABELS = [f"{n} {t}" for n, t in SECTIONS]
TAB_KEY = "pg_tab"
DEMO_TABS = ["★ 다음 경기 코치", "첫 10경기 로드맵", "매칭 품질 실험", "★ 복귀 캠페인 · 광고 3종",
             "복귀 첫날 · D30", "BM 내부 분석"]
CREDIT = "실제 게임 화면 · 작성자 직접 캡처 (2026-11) · 다른 플레이어 닉네임 가림 · © KRAFTON"


# ----------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load() -> tuple[dict, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict, dict]:
    ns = json.loads((DATA / "newstart.json").read_text(encoding="utf-8"))
    ops = pd.read_csv(DATA / "opinions.csv", dtype=str).fillna("")
    ops["track"] = ops["track"].replace({"B": "C"})          # 원본 파일의 BM 분류(B) → 화면에서는 TRACK C
    ret = pd.read_csv(DATA / "opinions_return.csv", dtype=str).fillna("")
    steam = pd.read_csv(DATA / "steam_monthly.csv")
    pool = json.loads((DATA / "review_pool.json").read_text(encoding="utf-8"))
    rpool = json.loads((DATA / "return_pool.json").read_text(encoding="utf-8"))
    ko = json.loads((DATA / "quote_ko.json").read_text(encoding="utf-8"))   # 외국어 발췌의 한국어 번역 (원문은 CSV 그대로)
    for df in (ops, ret):
        df["quote_ko"] = [ko.get(i, q) for i, q in zip(df["opinion_id"], df["quote_original"])]
    return ns, ops, ret, steam, pool, rpool


def tr(t: str) -> str:
    return {"A": '<span class="pg-tr a">TRACK A</span>', "B": '<span class="pg-tr nv">TRACK B</span>',
            "C": '<span class="pg-tr b">TRACK C</span>'}.get(t, '<span class="pg-tr c">공통</span>')


def _tab_from_query() -> str:
    q = str(st.query_params.get("tab", ""))
    return next((lab for lab in TAB_LABELS if lab.startswith(q.zfill(2)[:2])), TAB_LABELS[0]) if q else TAB_LABELS[0]


def _sync_tab_param() -> None:
    st.query_params["page"] = "pubg"
    st.query_params["tab"] = str(st.session_state.get(TAB_KEY, TAB_LABELS[0]))[:2]


def tab_nav() -> int:
    if st.session_state.get(TAB_KEY) not in TAB_LABELS:
        st.session_state[TAB_KEY] = _tab_from_query()
    sel = st.radio("섹션 선택", TAB_LABELS, key=TAB_KEY, horizontal=True, label_visibility="collapsed", on_change=_sync_tab_param)
    return TAB_LABELS.index(sel)


# ----------------------------------------------------------------------
# 게임 화면
SCREENS: dict[str, dict] = {}   # newstart.json 'screens' (render 에서 채움)


@st.cache_data(show_spinner=False)
def _jpeg_b64(path: str, mtime: float, max_w: int = 1400) -> str:
    return web_jpeg_b64(path, max_w=max_w)


@st.cache_data(show_spinner=False)
def _png_b64(path: str, mtime: float) -> str:
    import base64
    return base64.b64encode(Path(path).read_bytes()).decode()


def _img_src(key: str, max_w: int = 1400) -> str | None:
    sc = SCREENS.get(key, {})
    path = ASSETS / sc.get("file", "-")
    if not (sc.get("ready") and path.is_file()):
        return None
    if sc.get("lossless"):      # 글자가 중요한 작은 캡처(치킨 승리 화면): 원본 PNG 그대로 · 재압축 없음
        return f"data:image/png;base64,{_png_b64(str(path), path.stat().st_mtime)}"
    return f"data:image/jpeg;base64,{_jpeg_b64(str(path), path.stat().st_mtime, max_w)}"


def slot_html(key: str) -> str:
    sc = SCREENS.get(key, {"title": key, "where": "", "file": f"{key}.png"})
    return (f'<div class="pg-slot"><span class="pg-slot-k">실제 게임 화면 · 캡처 대기</span><b>{escape(sc["title"])}</b>'
            f'<small>캡처 위치 · {escape(sc["where"])}</small><small class="f">assets/pubg/{escape(sc["file"])}</small></div>')


def shot(key: str) -> None:
    """오버워치와 같은 '실제 게임 화면' 프레임. 파일이 없으면 캡처 대기 자리만."""
    src = _img_src(key)
    if not src:
        html(slot_html(key))
        return
    t = escape(SCREENS[key].get("title", ""))
    html(f'<figure class="ow-shot"><div class="ow-shot-bar"><span class="ow-shot-tag">실제 게임 화면</span>{t}</div>'
         f'<div class="ow-shot-img"><img src="{src}" alt="{t}" loading="lazy"></div></figure>')


def photo(key: str, caption: str, cls: str = "") -> str:
    """탭의 핵심 메시지를 돕는 사진 (프레임 없이 · 아래 한 줄 설명 + 출처). 파일이 없으면 빈 문자열."""
    src = _img_src(key, 1200)
    if not src:
        return ""
    sc = SCREENS[key]
    alt = escape(sc.get("title", caption))
    credit = escape(sc["credit"]) + " · © KRAFTON" if sc.get("credit") else CREDIT
    cap = f"<b>{escape(caption)}</b>" if caption else ""
    return (f'<figure class="pn-photo {cls}"><img src="{src}" alt="실제 게임 화면: {alt}" loading="lazy">'
            f'<figcaption>{cap}<span>{credit}</span></figcaption></figure>')


def art(ns: dict, key: str, caption: str, cls: str = "") -> str:
    """캠페인·참고 이미지 (게임 캡처가 아닌 것). 원본 비율 · 원본보다 크게 늘리지 않는다 (max-width = 원본 폭)."""
    a = ns["art"].get(key) if key in ns.get("art", {}) else None
    a = a or next(({"file": x["image"], "title": x["title"], "credit": x["label"]} for x in ns["campaign"]["ads"] if x["key"] == key), None)
    path = ASSETS / a["file"] if a else None
    if not (path and path.is_file()):
        return ""
    from PIL import Image
    with Image.open(path) as im:
        w = im.width
    mime = "png" if path.suffix == ".png" else "jpeg"
    cap = f"<b>{escape(caption)}</b>" if caption else ""
    return (f'<figure class="pn-photo pn-art {cls}"><img src="data:image/{mime};base64,{_png_b64(str(path), path.stat().st_mtime)}" '
            f'alt="{escape(a["title"])}" style="max-width:{w}px" loading="lazy"><figcaption>{cap}<span>{escape(a["credit"])}</span></figcaption></figure>')


def compare(real_key: str, real_title: str, mock_title: str, mock_fn) -> None:
    """'실제 화면(왼쪽) ↔ 기획 시안(오른쪽)' 비교 배치."""
    left, right = st.columns([1, 1], gap="medium")
    with left:
        html(f'<div class="ow-colh real">현재 · {escape(real_title)}</div>')
        shot(real_key)
    with right:
        html(f'<div class="ow-colh mock">제안 · {escape(mock_title)} · 실제 게임에 없음</div>')
        mock_fn()


def _flow3(steps: list[tuple[str, str, str]], cls: str = "") -> str:
    """제목 + 한 줄 설명만 있는 3단계 흐름. steps = [(kind, 제목, 한 줄)]."""
    out = []
    for i, (kind, t, d) in enumerate(steps):
        out.append(f'<div class="pg-step {kind}"><div class="n">{"①②③④"[i]} <span class="kb">{KIND[kind]()}</span></div>'
                   f'<b>{escape(t)}</b><small>{escape(d)}</small></div>')
        if i < len(steps) - 1:
            out.append('<div class="pg-arrow">→</div>')
    return f'<div class="pg-flow {cls}">{"".join(out)}</div>'


def _quotes(rows: pd.DataFrame, labels: dict[str, str] | None = None) -> str:
    labels = labels or {}
    return '<div class="pg-quotes">' + "".join(
        f'<div class="ow-quote {"neg" if r.sentiment == "부정" else "pos" if r.sentiment == "긍정" else "neu"}">'
        f'<div class="ow-quote-tag">{escape(labels.get(r.opinion_id, r.category))} · 플레이 {escape(r.hours_on_record)}시간</div>'
        f'<div class="ow-quote-t">{escape(r.summary_ko)}</div><div class="ow-quote-o">“{escape(r.quote_ko)}”</div>'
        + f'<div class="ow-quote-m">Steam 리뷰 · {escape(r.published_date)}'
        + (f' · {escape(r.language)} 원문 번역' if r.quote_ko != r.quote_original else "")
        + f' · {link(r.source_url, "원문 보기")}</div></div>'
        for r in rows.itertuples()) + "</div>"


def _pick(df: pd.DataFrame, ids: list[str]) -> pd.DataFrame:
    ids = [x for x in ids if x in set(df["opinion_id"])]
    return df.set_index("opinion_id").loc[ids].reset_index()


# ----------------------------------------------------------------------
# 첫 화면 (탭 위에 항상 표시)
def _tier(t: dict) -> str:
    """핵심 전략 2개(A1·B1)를 앞세우고 나머지는 후속·보조로 표시."""
    sol = t["solutions"]
    if t["key"] == "C":
        return "보조 · " + " · ".join(escape(s[1]) for s in sol)
    rest = " · ".join(escape(s[1]) for s in sol[1:])
    return f'<b>대표 {escape(sol[0][1])}</b>' + (f" · 후속 {rest}" if rest else "")


def _cover(ns: dict) -> None:
    cv = ns["cover"]
    logo, drop = ASSETS / "brand" / "pubg_logo.png", ASSETS / "drop.png"
    logo_html = (f'<img class="pg-logo" src="data:image/png;base64,{_png_b64(str(logo), logo.stat().st_mtime)}" alt="PUBG: BATTLEGROUNDS 로고">'
                 if logo.is_file() else "")
    pk = ns["peak"]
    bg = f"url(data:image/jpeg;base64,{_jpeg_b64(str(drop), drop.stat().st_mtime, 1600)})" if drop.is_file() else "none"
    html(f'<div class="pn-hero pn-peakhero" style="--bg:{bg}"><div class="pn-hero-t">{logo_html}<div class="pg-cover-k">{escape(cv["title"])}</div>'
         '<div class="pn-big" role="heading" aria-level="1">325만 명</div>'
         '<p class="pn-big-l1">한때 325만 명이 동시에 낙하했던 전장.</p>'
         '<p class="pn-big-l2">이제 중요한 건, 새로운 유저를 정착시키고 떠난 유저를 다시 불러오는 것.</p>'
         f'<p class="pn-big-src">Steam 역대 최고 동시접속 {pk["value"]:,}명 · {escape(pk["date"])} 기록 · '
         '<a href="https://steamdb.info/app/578080/charts/" target="_blank" rel="noopener">SteamDB</a> (Guinness World Records 인용) · '
         '과거 기록이며 현재 이용자·이탈자 수가 아님</p></div></div>')
    tk = ns["tracks"]
    short = {"A": "신규 유저 정착", "B": "휴면 유저 복귀", "C": "BM 정책 검토"}
    bar = "".join(f'<div class="pn-w {t["key"].lower()}" style="flex:{t["weight"]} 1 0"><b>{t["key"]} {t["weight"]}%</b><span>{short[t["key"]]}</span></div>' for t in tk)
    cards = "".join(
        f'<div class="pn-tc {t["key"].lower()}"><div class="pn-tc-k">TRACK {t["key"]} · {escape(t["name"])}</div>'
        f'<b>{escape(t["question"])}</b><small>{_tier(t)}</small></div>' for t in tk)
    html(f'<div class="pn-weights" aria-label="포트폴리오 비중">{bar}</div><div class="pn-tcards">{cards}</div>')


def render() -> None:
    ns, ops, ret, steam, pool, rpool = load()
    SCREENS.clear()
    SCREENS.update({x["key"]: x for x in ns.get("screens", [])})
    plan = S.plan(ns["experiment"])
    html('<div class="gp-ow-page"></div>')
    _cover(ns)
    i = tab_nav()
    badge_legend()
    html(f'<div class="ow-pane-mark" data-tab="{SECTIONS[i][0]}"></div>')   # 정적 보고서 탭 경계 표식
    [lambda: s1(ns, ops, plan), lambda: s2(ns, ops, ret, steam, pool, rpool), lambda: s3(ns, ops, ret, rpool),
     lambda: s4(ns, ops, plan), lambda: s5(ns, plan), lambda: s6(ns, plan)][i]()
    st.caption(f"{ns['disclaimer']} · 자료 확인일 2026-11-26")


GAP_CATS = ["실력 격차·매칭", "봇→실전 전환", "초반 교전·첫 사망"]


def _market(ns: dict) -> None:
    """시장 최신값 3장 (실제 자료) + 한 줄 해석."""
    mk = ns["market"]
    st_, kr = mk["steam"], mk["krafton"]
    html('<div class="pz-mkt">'
         f'<div><span>Steam 동시접속 · 최근 30일 {b_real()}</span><b>평균 {st_["avg30"] / 1e4:.1f}만 명</b>'
         f'<small>30일 최고 {st_["peak30"] / 1e4:.1f}만 · {escape(st_["rank"])} · {link(st_["url"], st_["src"])} {escape(st_["date"])}</small></div>'
         f'<div><span>크래프톤 PC 매출 · 2026 3분기 {b_real()}</span><b>{escape(kr["pc_rev"])} <em>{escape(kr["pc_yoy"])}</em></b>'
         f'<small>{escape(kr["why"])} · {link(kr["url"], kr["src"])}</small></div>'
         f'<div class="i"><span>사업PM 해석 {b_interp()}</span><b>규모는 여전히 상위권</b>'
         f'<small>{escape(kr["franchise"])} · {escape(kr["next"])} → 콘텐츠만으로는 부족, 신규 정착·복귀가 과제</small></div></div>'
         '<div class="pn-cav2">Steam 동시접속 ≠ 전체 플랫폼 이용자 · 배그 단독 매출·이용자 수는 비공개</div>')


def flag_rows(ns: dict, ops: pd.DataFrame, plan: dict) -> dict[str, list]:
    """대표 기획 2개의 문제 → 근거 → 해결 → 효과 (01 탭 카드 · 04 탭 4칸 요약 공통)."""
    a = ops[ops["track"] == "A"]
    gap = int(a["category"].isin(GAP_CATS).sum())
    m14, ex = ns["my14"], ns["experiment"]
    return {
        "coach": [("문제", "훈련은 끝났는데, 첫 실전에서 막혀 떠난다"),
                  ("근거", f"신규 리뷰 {len(a)}건 중 {gap}건이 실전 전환 직후 · 직접 플레이 14경기 평균 {m14['stats'][0][0]} · 생존 {m14['stats'][1][0]}"),
                  ("해결", "경기 후 고칠 행동 1개 → 다음 경기에서 달성했는지 확인 → 성장 기록"),
                  ("효과", f"신규 D7 {ex['A']['base_d7']:.0f}% → {ex['A']['base_d7'] + plan['A']['mde']:.0f}% 목표 (가정 설계 · A/B로 검증)")],
        "camp": [("문제", "떠난 유저에게 다시 할 이유도, 함께할 친구도 없다"),
                 ("근거", "복귀 리뷰 21건 · 추억 6 · 핵·도용 6 · 친구 이탈 3"),
                 ("해결", "친구가 부르는 광고 → 공식 '달라진 점' 랜딩 → 첫날 친구와 3경기"),
                 ("효과", f"복귀율 {ex['R']['base_return']:.1f}% → {ex['R']['base_return'] + plan['R']['mde']:.1f}% · 복귀 후 D30까지 추적 (가정)")]}


def _brief(rows: list, name: str) -> str:
    return brief_html(*[escape(b) for _, b in rows], name=name, tag="대표 기획 · 기획 시안")


def _flag(cls: str, kicker: str, title: str, en: str, rows: list) -> str:
    return (f'<div class="pz-flag {cls}"><div class="pz-flag-k">{escape(kicker)}</div><div class="pz-flag-t">{escape(title)}<small>{escape(en)}</small></div>'
            + "".join(f'<div class="pz-row"><span>{escape(a)}</span><p>{escape(b)}</p></div>' for a, b in rows) + "</div>")


def _journey(ns: dict) -> None:
    """광고 노출 → 복귀 → 친구와 재결합 → D7 → D30 (가정 시뮬레이션 수치 · 배정 대비 %)."""
    jr = ns["campaign"]["journey"]
    fn = S.return_funnel(ns["funnel"])
    vals = [100.0] + [v for _, v in fn]
    cells = []
    for i, ((t, d_), v) in enumerate(zip(jr, vals)):
        cells.append(f'<div style="--h:{max(v, 0.0) ** 0.5 * 10:.1f}%"><em>{i + 1}</em><b>{escape(t)}</b><strong>{v:.2f}%</strong>'.replace(".00%", "%")
                     + f'<small>{escape(d_)}</small><i></i></div>')
    html(f'<div class="pz-jour"><div class="pz-jour-h">복귀 여정 · 광고 배정 100% 기준 {b_sim()}</div><div class="pz-jour-r">{"".join(cells)}</div>'
         '<div class="pz-jour-n">단계별 전환율은 실험으로 측정할 가정값 · 성공 판단은 복귀율만이 아니라 복귀 후 D7·D30까지</div></div>')


def _my14(ns: dict) -> None:
    m = ns["my14"]
    html(f'<div class="pz-my14"><div class="pz-my14-h">직접 플레이한 신규 계정 14경기 {b_real()}</div><div class="g">'
         + "".join(f'<div><b>{escape(v)}</b><span>{escape(l)}</span><small>{escape(c)}</small></div>' for v, l, c in m["stats"])
         + f'</div><p>{escape(m["gap"])}</p><small>{escape(m["src"])}</small></div>')
    html(photo("season_stats", "실제 전적 화면 · 시즌 3 일반 3인칭 솔로"))


# ======================================================================
# 01 문제·결론 — 하나의 결론: A1 먼저, B1 다음, C는 내부 분석
def s1(ns: dict, ops: pd.DataFrame, plan: dict) -> None:
    a = ops[ops["track"] == "A"]
    gap = int(a["category"].isin(GAP_CATS).sum())
    pk = ns["peak"]
    head("결론: 신규는 '다음 경기 행동 1개'로 붙잡고, 떠난 유저는 친구의 한마디로 다시 부른다",
         "코치 먼저 → 복귀 캠페인 → BM은 내부 분석", b_mock())
    _market(ns)
    fr = flag_rows(ns, ops, plan)
    html('<div class="pz-flags">'
         + _flag("a", "대표 기획 ① 신규 유저 정착", "다음 경기 코치", "NEXT MATCH COACH", fr["coach"])
         + _flag("b", "대표 기획 ② 휴면 유저 복귀", "«야, 배그 한 판 할래?»", "복귀 캠페인", fr["camp"])
         + "</div>")
    _journey(ns)
    html('<div class="pn-b1h">복귀 광고 3종 · 대표 «야, 배그 한 판 할래?» · 화살표로 다음 광고</div>')
    html(ad_gallery(ns, "pgad01"))
    html('<div class="pg-subbox c"><span class="pg-tr b">보조</span><b>BM 내부 분석</b> 성장형 스킨의 확률·결과 불만을 줄이면서 매출을 지킬 수 있을까? '
         '→ 유저 화면은 바꾸지 않고 내부 정책 시나리오만 비교 (04 탭)</div>')
    with st.expander("자세히 보기 · 트랙별 근거 · 복귀 장벽 · 판단 근거"):
        html('<div class="pn-duo">' + photo("gameplay", "A · 첫 실전에서 막히는 신규 유저")
             + art(ns, "ghillie", "B · 그때 그 배그를 기억하는 휴면 유저") + '</div>')
        html('<div class="pn-a pn-arow"><div><div class="pn-k">TRACK A · 50% · 신규 유저 정착</div>'
             '<div class="pn-q">첫 치킨을 맛보기도 전에, 왜 떠나는가?</div><div class="pn-sub">훈련은 끝났다. 그런데 실전은 왜 어려울까?</div></div>'
             '<div><ul class="pg-why">'
             f'<li>{b_real()} 기본 훈련·초심자 훈련소는 이미 있다 → 빈 곳은 <b>훈련 이후 첫 실전</b></li>'
             f'<li>{b_real()} 신규 정착 리뷰 {len(a)}건 중 <b>{gap}건</b>이 실력 격차·봇→실전·첫 교전 사망</li></ul>'
             '<div class="pg-chips"><span>다음 경기 코치</span><i>→</i><span>첫 10경기 로드맵</span><i>→</i><span>매칭 품질 실험</span></div></div></div>')
        html('<div class="pn-band" style="grid-template-columns:1fr">'
             '<div class="pn-band-t"><div class="pn-k">TRACK B · 40% · 휴면 유저 복귀</div>'
             '<div class="pn-q">한때 배그를 즐기던 유저는 왜 돌아오지 않을까?</div>'
             '<div class="pn-sub">그때, 우리는 모두 치킨을 꿈꿨다. PC방에서 친구들과 헤드셋을 끼고, 마지막 자기장까지.</div>'
             f'<div class="pn-peak"><b>{escape(pk["display"])}</b><span>Steam 역대 최고 동시접속 {b_real()}</span></div>'
             '<div class="pg-chips nv"><span>복귀 캠페인 «야, 배그 한 판 할래?»</span><i>→</i><span>복귀 첫날 · D30</span></div></div></div>')
        html('<div class="pn-bflow"><div><span>과거의 즐거움</span>친구와 스쿼드</div><i>→</i>'
             '<div class="w"><span>복귀 장벽</span>핵·불법 프로그램 · 실력 격차 · 친구 이탈 · 운영·과금 불신</div><i>→</i>'
             '<div><span>다시 할 이유</span><b>복귀 캠페인</b></div><i>→</i><div><span>실제 재정착</span><b>복귀 첫날 · D7·D30</b></div></div>'
             '<div class="pn-cav2">최고 동접은 과거 규모일 뿐, 이탈 유저 수나 복귀 가능 유저 수가 아니다.</div>')
        html('<div class="pg-subbox c"><span class="pg-tr b">TRACK C · 10%</span><b>BM 신뢰·수익성 관리</b> '
             '과금 불만을 줄이면서 매출을 지킬 수 있을까? → 유저 화면 변경 없이 <b>내부 정책 시나리오</b>만 비교한다.</div>')
        sub("판단 근거 · 실행 순서 · 제외한 아이디어")
        html("<ul class='pg-ul'>"
             f"<li><b>왜 다음 경기 코치가 먼저인가</b> {b_interp()} 이탈 지점(첫 실전 직후)에 바로 닿고, 공개 텔레메트리로 MVP 판정이 가능하며 매칭을 건드리지 않는다.</li>"
             f"<li><b>왜 복귀는 광고 캠페인인가</b> {b_interp()} 휴면 유저는 PUBG를 이미 안다. 필요한 것은 인지도가 아니라 '다시 할 이유'와 '무엇이 달라졌는지'다. "
             "개발 부담이 작고, 휴면 리스트 무작위 배정(홀드아웃 포함)으로 광고 메시지별 효과를 분리할 수 있다.</li>"
             "<li><b>핵 문제</b> 핵에 대한 불신은 복귀 장벽 중 하나다. 광고는 해결을 약속하지 않고, 랜딩에서 공식 대응만 출처와 함께 보여 준 뒤 복귀 후 공정성 신뢰도로 확인한다.</li>"
             f"<li><b>최고 동시접속</b> SteamDB {pk['value']:,}명 (2018-01-13, Guinness 인용) · Steam Charts 3,236,027명 (2018년 1월) → 메인은 '약 325만 명' · 출처 비교는 02 탭</li>"
             f"<li><b>판단 기준</b> {b_mock()} 다음 경기 코치는 신규 D7 (유의성 + 실질 효과 +{plan['practical_min']:.1f}%p + 가드레일), "
             f"복귀 캠페인은 광고 그룹별 복귀 로그인 전환율 (+{plan['R']['mde']:.1f}%p · 가정 설계값)과 복귀 후 D30 → 05 탭</li>"
             "<li><b>실행 순서</b> 1차 다음 경기 코치 → 2차 복귀 캠페인·복귀 첫날 → 3차 첫 10경기 로드맵·매칭 품질 실험 → 4차 BM 내부 분석 (06 탭)</li>"
             "<li><b>제외한 아이디어</b> 단순 초대 보상 이벤트(복귀 캠페인 메인에서 제외) · 무기 숙련도가 이미 있어 무기 성장 칭호 제외 · "
             "이중 가챠는 42.1(2026-06)에 제거된 과거 문제 · 유저에게 총비용을 강제로 보여 주는 화면 (내부 분석 도구로만 유지)</li></ul>")


# ======================================================================
# 02 실제 유저 근거 — 신규·복귀를 별도 표본으로
def s2(ns: dict, ops: pd.DataFrame, ret: pd.DataFrame, steam: pd.DataFrame, pool: dict, rpool: dict) -> None:
    a = ops[ops["track"] == "A"]
    head("근거: 신규는 '첫 실전'에서, 복귀 유저는 '핵·계정·친구'에서 막힌다",
         f"신규·복귀 리뷰를 별도 표본으로 · 대표 의견만 먼저", b_real())

    r_ = ret.groupby("category").size()
    gap_n = int(a["category"].isin(GAP_CATS).sum())
    causes = [("a", f"{gap_n}건", "신규 · 실력 격차와 초기 이탈", "숙련자 로비·봇→실전·첫 교전 사망", f"신규 리뷰 {len(a)}건 중"),
              ("b", f"{int(r_.get('핵·공정성', 0) + r_.get('계정 도용·정지', 0))}건", "복귀 · 핵·불법 프로그램 불신", "핵 경험 · 복귀하니 도용·정지된 계정", f"복귀 리뷰 {len(ret)}건 중"),
              ("b", f"{int(r_.get('숙련도 격차', 0))}건", "복귀 · 매칭·실력 격차", "오랜만에 돌아오니 너무 어렵다", f"복귀 리뷰 {len(ret)}건 중"),
              ("b", f"{int(r_.get('친구·스쿼드', 0))}건", "복귀 · 친구 이탈", "친구가 해야 하는 게임 · 혼자면 재미없다", f"복귀 리뷰 {len(ret)}건 중")]
    html('<div class="pn-cause">' + "".join(
        f'<div class="{c}"><small>{escape(src)}</small><b>{n}</b><strong>{escape(t)}</strong><span>{escape(d)}</span></div>'
        for c, n, t, d, src in causes) + '</div>')
    with st.expander("표본 구성 · 언어·성향 분포 · 원문 재확인"):
        html(f'<div class="pn-cav2"><b>서로 다른 리뷰 {len(set(ops.source_url) | set(ret.source_url))}개</b> (신규·BM {len(ops)}건 + 복귀 {len(ret)}건 · '
        f'같은 리뷰 {len(set(ops.source_url) & set(ret.source_url))}건은 두 표본에 각각 분류)는 직접 고른 선별 사례다 · '
        f'한국어 {int((ops.language == "한국어").sum() + (ret.language == "한국어").sum())}건 · 해외 {int((ops.language != "한국어").sum() + (ret.language != "한국어").sum())}건 · '
        f'긍정 {int((ops.sentiment == "긍정").sum() + (ret.sentiment == "긍정").sum())} · 중립 {int((ops.sentiment == "중립").sum() + (ret.sentiment == "중립").sum())} · '
        f'부정 {int((ops.sentiment == "부정").sum() + (ret.sentiment == "부정").sum())} (비율 조정 없음) · 원문 링크 64개 2026-11-26 재확인 · '
        '전체 유저를 대표하는 표본이 아니며 건수는 비율이 아니다</div>')
    sub("TRACK A · 신규 유저", tr("A"))
    c1, c2 = st.columns([1.35, 1], gap="medium")
    with c1:
        _review_chart(a, pool)
    with c2:
        _my14(ns)
    html(_quotes(_pick(ops, ["A01", "A11"]), {"A01": "실력 격차", "A11": "봇 → 실전 전환"}))   # 대표 2건 · 나머지는 아래 전체 표

    sub("TRACK B · 휴면·복귀 유저", tr("B"))
    c1, c2 = st.columns([1.35, 1], gap="medium")
    with c1:
        _return_chart(ret, rpool)
    with c2:
        kw, n_all = rpool["keyword"], sum(rpool["pool"].values())
        html('<div class="pn-vs">'
             f'<div><span>유저 리뷰 {b_real()}</span><b>{kw["핵·해킹"]:,}건</b><small>최신 리뷰 {n_all:,}건 중 핵·해킹 언급 (키워드 · {kw["핵·해킹"] / n_all * 100:.1f}%)</small></div>'
             f'<div><span>공식 제재 통계 {b_real()}</span><b>약 26만 명</b><small>2025년 DMA 기반 핵 영구 정지 (안티치트 2026 로드맵)</small></div>'
             f'<div><span>공식 도용 피해 기준 {b_real()}</span><b>반기 1회</b><small>2차 비밀번호 계정의 도용 피해 정지 해제 (2026-06-25 개발자 노트)</small></div>'
             '<p><b>핵에 대한 불신은 복귀 장벽 중 하나다.</b> 유저 주장과 공식 통계는 섞지 않고, '
             '공식 대응의 신뢰성과 실제 플레이 경험을 함께 검증한다.</p></div>')
    html(_quotes(_pick(ret, ["R02", "R16", "R06"]), {"R02": "계정 도용·정지", "R16": "친구와 복귀 → 핵", "R06": "긍정 · 다시 돌아오게 된다"}))   # 대표 3건 (부정 2 · 긍정 1)
    note("리뷰는 직접 고른 사례이며 전체 이용자 여론 비율이 아니다.")

    with st.expander(f"자세히 보기 · 의견 6분류 · 신규·BM 리뷰 {len(ops)}건 · 복귀 리뷰 {len(ret)}건 · 게임 화면 {len(SCREENS)}장 · 공식 자료 {len(ns['official'])}건 · 자료 한계"):
        pos = _pick(ret, ["R06", "R12"])
        html('<div class="pn-pos"><b>긍정 경험도 함께</b>' + "".join(
            f'<span>“{escape(r.quote_ko)}” <small>{escape(r.published_date)} · {link(r.source_url, "원문")}</small></span>' for r in pos.itertuples())
             + '</div>')

        c_ = ops[ops["track"] == "C"]
        nb = c_.groupby("category").size()
        html(f'<div class="pg-subbox c"><span class="pg-tr b">TRACK C</span><b>BM 근거 (보조)</b> 리뷰 {len(c_)}건 중 확률·결과 불만 '
             f'{int(nb.get("확률·결과 불만", 0))}건 · 복귀자 과금 불만 1건(R17) · 이중 가챠는 2026-06 이미 제거</div>')
        t = st.tabs(["의견 6분류", f"신규·BM 리뷰 {len(ops)}건", f"복귀 리뷰 {len(ret)}건", f"게임 화면 {len(SCREENS)}장", f"공식 자료 {len(ns['official'])}건",
                     "기존 기능 vs 제안", "최고 동접 출처", "자료 한계"])
        with t[0]:
            _six(ops, ret, rpool)
        t = t[1:]
        with t[0]:
            _review_chart(ops, pool, full=True)
            _table_ops(ops, "pg_op")
        with t[1]:
            _table_ops(ret, "pg_rt")
        with t[2]:
            items = list(SCREENS.values())
            for i in range(0, len(items), 2):
                cols = st.columns(2, gap="medium")
                for col, x in zip(cols, items[i:i + 2]):
                    with col:
                        html(f'<div class="pg-slot-w">{tr(x["track"])}<small>{escape(x["use"])}</small></div>')
                        shot(x["key"])
            st.caption("작성자가 직접 캡처한 최신 한국어 화면 · 다른 플레이어 닉네임은 가린 사본만 공개 · 로고·게임 화면 © KRAFTON")
        with t[3]:
            table(["날짜 · 트랙", "자료", "구분", "확인한 사실", "출처"],
                  [[f"{escape(o['date'])}<br>{tr(o['track'])}", f"<b>{escape(o['title'])}</b>", escape(o.get("kind", "")), escape(o["fact"]),
                    (link(o["url"], o["status"]) if o.get("url") else escape(o["status"]))]
                   for o in sorted(ns["official"], key=lambda o: o["date"], reverse=True)], badge_html=b_real())
            st.caption("과거 자료(2018~2025)는 역사적 변화·과거 불만의 근거로만 쓰고, 2026 현재 상황의 직접 증거로 쓰지 않는다.")
        with t[4]:
            table(["트랙 · 영역", "기존 기능 (실제)", "남은 빈틈", "이번 제안"],
                  [[f"{tr(x['track'])}{escape(x['area'])}", escape(x["existing"]), escape(x["gap"]), f"<b>{escape(x['new'])}</b>"]
                   for x in ns["existing_vs_new"]], badge_html=b_interp())
        with t[5]:
            pk = ns["peak"]
            table(["출처", "최고 동시접속", "날짜", "집계 기준 · 확인 방법"],
                  [[link(u, s), f"<b>{escape(v)}</b>", escape(d), escape(c)] for s, v, d, c, u in pk["sources"]], badge_html=b_real())
            st.caption(f"차이가 나는 이유: {pk['why']} · {pk['note']}")
            _steam_chart(steam, pk)
        with t[6]:
            st.markdown(f"- **신규·BM 표본** {pool['source']} · 한국어 {pool['pool']['한국어']}건({pool['period']['한국어']}) · "
                        f"영어 필터 {pool['pool']['영어 필터']}건({pool['period']['영어 필터']}) 중 {len(ops)}건을 기획자가 직접 읽고 분류 · 원본 파일 그대로 보존\n"
                        f"- **복귀 표본** {rpool['source']} · 한국어 {rpool['pool']['한국어']:,}건({rpool['period']['한국어']}) · "
                        f"영어 {rpool['pool']['영어']:,}건({rpool['period']['영어']}) · {rpool['method']} → {len(ret)}건\n"
                        f"- {rpool['caveat']}\n"
                        "- 두 표본은 수집 시기와 방법이 달라 합산하지 않는다 · 같은 리뷰는 중복 저장하지 않음 (원문 링크 기준)\n"
                        "- Steam 리뷰는 Steam 이용자 중 리뷰를 쓴 사람만 포함 → 전체 이용자 의견 비율이 아니다 (카카오·콘솔 제외)\n"
                        "- **YouTube 댓글**: 참고 영상(‘배그의 치명적인 문제점들에대해 알아보자’)의 댓글 원문을 수집 환경에서 읽지 못해 사용하지 않음 "
                        "→ 사용자 제공 자료가 필요한 항목 (추측으로 만들지 않음) · Reddit은 접근 차단(403), 국내 커뮤니티는 이번 범위 밖\n"
                        "- 욕설·혐오 표현은 발췌에서 제외 · 작성자 이름은 저장하지 않음 (원문 링크만)\n"
                        f"- 최고 동시접속 {ns['peak']['value']:,}명: {ns['peak']['source']} · {ns['peak']['note']}")


def _six(ops: pd.DataFrame, ret: pd.DataFrame, rpool: dict) -> None:
    """요청한 6개 분류로 두 Steam 표본을 다시 묶어 본다 (건수는 표본 안의 사례 수 · 3건 미만은 '표본 부족')."""
    def n(df, cats):
        return int(df["category"].isin(cats).sum())
    c_ = ops[ops["track"] == "C"]
    rows = [
        ("신규 유저 매칭 불만", n(ops, ["봇→실전 전환"]), 0, "봇 위주 경기 뒤 숙련자 로비로 넘어가는 체감"),
        ("숙련자와의 실력 격차", n(ops, ["실력 격차·매칭", "초반 교전·첫 사망"]), n(ret, ["숙련도 격차"]), "수백 레벨 상대 · 첫 교전 전 사망"),
        ("핵·불법 프로그램", 0, n(ret, ["핵·공정성", "계정 도용·정지"]), f"키워드 참고: 최신 {sum(rpool['pool'].values()):,}건 중 {rpool['keyword']['핵·해킹']}건 언급"),
        ("과금·확률형 상품", len(c_), n(ret, ["과금 신뢰"]), "확률·결과 불만이 가장 많음"),
        ("복귀를 망설이는 이유", 0, n(ret, ["친구·스쿼드", "운영 신뢰"]), "친구 부재 · 운영 신뢰 (2026-09 논란 시기 집중)"),
        ("긍정적 경험·향수", int((ops["sentiment"] == "긍정").sum()), n(ret, ["추억·복귀 동기"]), "PC방 친구 · 다시 돌아오게 된다"),
    ]
    table(["분류", "신규·BM 표본", "복귀 표본", "합계", "대표 내용"],
          [[f"<b>{escape(a)}</b>", str(x), str(y), f"<b>{x + y}</b>" + (" · <em>표본 부족</em>" if x + y < 3 else ""), escape(d)]
           for a, x, y, d in rows], badge_html=b_real())
    st.caption("YouTube 댓글은 원문을 확보하지 못해 이 표에 넣지 않았다 · 두 Steam 표본은 수집 시기가 달라 합계는 사례 수 참고용")


def _cat_chart(df: pd.DataFrame, color_fn, title: str, unit: str, key: str, kpis, analysis, decision, basis, height=260) -> None:
    cnt = df.groupby("category").size().reset_index(name="n").sort_values("n", ascending=False)
    fig = go.Figure(go.Bar(y=list(cnt["category"]), x=cnt["n"], orientation="h", marker_color=[color_fn(c) for c in cnt["category"]],
                           text=[f"{n}건" for n in cnt["n"]], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{x}건<extra></extra>"))
    fig.update_yaxes(autorange="reversed", automargin=True, title="")
    fig.update_xaxes(title="리뷰 수 (건)", range=[0, cnt["n"].max() * 1.35], dtick=1, rangemode="tozero")
    chart_card(fig, key=key, kind="real", title=title, unit=unit, kpis=kpis, analysis=analysis, decision=decision,
               basis=basis, height=height, legend=False, cols=("분류", "리뷰 수 (건)"))


def _review_chart(ops: pd.DataFrame, pool: dict, full: bool = False) -> None:
    if full:
        cnt = ops.groupby(["track", "category"]).size().reset_index(name="n").sort_values(["track", "n"], ascending=[True, False])
        colors = [(C_TREAT if c in GAP_CATS else "#93C5FD") if t == "A" else C_CORAL for t, c in zip(cnt["track"], cnt["category"])]
        fig = go.Figure(go.Bar(y=list(cnt["category"]), x=cnt["n"], orientation="h", marker_color=colors, text=[f"{n}건" for n in cnt["n"]],
                               textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x}건<extra></extra>"))
        fig.update_yaxes(autorange="reversed", automargin=True, title="")
        fig.update_xaxes(title="리뷰 수 (건)", range=[0, cnt["n"].max() * 1.35], dtick=1, rangemode="tozero")
        a, c = (ops["track"] == "A").sum(), (ops["track"] == "C").sum()
        chart_card(fig, key="pg_rev_all", kind="real", title=f"신규·BM 리뷰 분류 (직접 분류 {len(ops)}건)", unit="건 · 파랑 = 신규 정착, 코랄 = BM",
                   kpis=[("신규 정착", f"{a}건"), ("BM", f"{c}건"), ("긍정 의견 (반대 사례)", f"{(ops['sentiment'] == '긍정').sum()}건")],
                   analysis="신규 정착은 학습 곡선·실력 격차·봇→실전, BM은 확률 결과가 많다", decision="신규는 실전 전환 구간 · BM은 내부 분석부터",
                   basis=f"최신 리뷰 {sum(pool['pool'].values()):,}건 중 관련 리뷰 직접 분류 · 비율 아님", height=430, legend=False, cols=("분류", "리뷰 수 (건)"))
        return
    gap = int(ops["category"].isin(GAP_CATS).sum())
    _cat_chart(ops, lambda c: C_TREAT if c in GAP_CATS else "#93C5FD", f"신규 정착 리뷰 {len(ops)}건 · 어디서 막히나",
               "건 · 진한 파랑 = 실전 전환 직후", "pg_rev",
               [("실전 전환 직후", f"{gap}건"), ("학습 곡선", f"{int((ops['category'] == '학습 곡선').sum())}건")],
               "숙련자 로비·봇→실전·첫 교전 사망이 실전 전환 직후에 몰린다", "다음 경기 코치는 첫 실전 직후 결과 화면에 둔다",
               "직접 분류 · 사례 수 (비율 아님)")


def _return_chart(ret: pd.DataFrame, rpool: dict) -> None:
    barrier = {"핵·공정성", "계정 도용·정지", "친구·스쿼드", "숙련도 격차", "운영 신뢰", "과금 신뢰"}
    n_bar = int(ret["category"].isin(barrier).sum())
    _cat_chart(ret, lambda c: C_NAVY if c in barrier else "#A5B4FC", f"복귀·휴면 리뷰 {len(ret)}건 · 무엇이 막나",
               "건 · 진한 남색 = 복귀 장벽, 연한 색 = 복귀 동기·추억", "pg_ret",
               [("복귀 장벽", f"{n_bar}건"), ("추억·복귀 동기", f"{len(ret) - n_bar}건")],
               "핵·계정 도용과 친구 이탈이 반복된다 · '친구와 함께'는 장벽이자 복귀 동기",
               "복귀 캠페인은 친구·추억과 출처 있는 변화를 함께 전달 · 복귀 후 공정성 신뢰 측정",
               f"최신 리뷰 {sum(rpool['pool'].values()):,}건 키워드 후보 중 선별 · 사례 수 (비율 아님)", height=280)


def _steam_chart(steam: pd.DataFrame, peak: dict) -> None:
    d = steam.copy()
    d["m"] = pd.to_datetime(d["month"])
    last = d.iloc[-1]
    fig = go.Figure(go.Bar(x=d["m"], y=d["avg_players"], marker_color=C_MUTED, hovertemplate="%{x|%Y-%m} · %{y:,.0f}명<extra></extra>"))
    fig.update_yaxes(title="월평균 동시접속자 (명)", tickformat=",", rangemode="tozero", range=[0, d["avg_players"].max() * 1.15])
    fig.update_xaxes(title="월", tickformat="%y.%m", dtick="M3")
    chart_card(fig, key="pg_steam", kind="real", title="Steam 월평균 동시접속자 (24개월 · 시장 규모 참고)", unit="명",
               kpis=[("역대 최고 (2018-01-13)", f"{peak['value']:,}명"), (f"최근 {last['m']:%y.%m} 월평균", f"{last['avg_players']:,.0f}명")],
               analysis="역대 최고는 동시에 접속한 최대 인원, 월평균은 한 달 평균 · 두 값은 성격이 다르다",
               decision="차이를 '이탈 유저 수'로 계산하지 않음 · 복귀 효과는 휴면 계정 실험으로 측정",
               basis="Steam만 포함 (카카오·콘솔 제외) · Steam Charts · 역대 최고는 SteamDB 기록", height=300, legend=False,
               cols=("월", "월평균 동시접속자 (명)"))


def _table_ops(df: pd.DataFrame, key: str) -> None:
    st.dataframe(df[["opinion_id", "track", "category", "tags", "sentiment", "language", "published_date", "recommended",
                     "hours_on_record", "summary_ko", "quote_ko", "quote_original", "source_url"]]
                 .rename(columns={"opinion_id": "의견 번호", "track": "트랙", "category": "주 분류", "tags": "보조 분류", "sentiment": "방향",
                                  "language": "언어", "published_date": "작성일", "recommended": "추천 여부", "hours_on_record": "플레이 시간",
                                  "summary_ko": "요약", "quote_ko": "발췌 (한국어)", "quote_original": "원문 발췌", "source_url": "원문"}),
                 hide_index=True, key=key, column_config={"원문": st.column_config.LinkColumn("원문", display_text="열기")})


# ======================================================================
# 03 원인 가설
def s3(ns: dict, ops: pd.DataFrame, ret: pd.DataFrame, rpool: dict) -> None:
    n = ops.groupby("category").size()
    r = ret.groupby("category").size()
    head("원인 가설: 세 트랙은 막히는 이유가 다르다", "사실과 가설을 구분 · 인과는 실험으로 판단", b_hypo())
    html(photo("gameplay", "교전 직전 · 바위 하나, 팀원과의 거리 하나에 생존이 갈린다", "strip"))
    sub("TRACK A · 신규 유저", tr("A"))
    html(_flow3([("real", "훈련·봇 경기", "기본 훈련 · 봇이 많은 초반 일반전"),
                 ("interp", "첫 실전 좌절", "숙련자와의 격차 · 첫 교전 전 사망"),
                 ("hypo", "성장 체감 부족", "다음 경기에서 무엇을 할지 모른다")]))
    sub("TRACK B · 휴면·복귀 유저", tr("B"))
    html(_flow3([("real", "즐거웠던 스쿼드", "최고 동접 약 325만 · 'PC방 친구' 추억"),
                 ("interp", "복귀 장벽", "핵·계정 도용 · 친구 이탈 · 숙련도 격차"),
                 ("hypo", "복귀 동기 부족", "돌아올 이유와 함께할 사람이 없다")], "nv"))
    sub("TRACK C · BM (보조)", tr("C"))
    html(_flow3([("real", "확률형 구매", "확률은 게임 안 페이지에서 공개"),
                 ("interp", "기대와 다른 결과", "목표 스킨 대신 다른 보상"),
                 ("hypo", "만족도 저하 가능성", "검증 전 · 내부 데이터로 확인")], "sub"))
    note("서버·운영 논란 같은 다른 원인은 무작위 배정으로 고르게 섞인다 → 기능 효과만 분리된다.")
    with st.expander("자세히 보기 · 복귀 장벽별 근거 판정 · 단계별 근거와 검증 방법 · 다른 원인"):
        table(["복귀 장벽", "복귀 리뷰 근거 (21건 중 · 중복 분류 없음)", "판정"],
              [["실력 격차", f"숙련도 격차 {int(r.get('숙련도 격차', 0))}건", "근거 있음 (소수)"],
               ["불법 프로그램 불신", f"핵·공정성 {int(r.get('핵·공정성', 0))}건 · 계정 도용·정지 {int(r.get('계정 도용·정지', 0))}건", "근거 있음"],
               ["함께하던 친구 이탈", f"친구·스쿼드 {int(r.get('친구·스쿼드', 0))}건", "근거 있음"],
               ["복귀 후 적응 부담", "별도 분류 없음", "<b>가설</b> · 복귀 첫날 설문으로 확인"],
               ["운영·BM 불신", f"운영 신뢰 {int(r.get('운영 신뢰', 0))}건 · 과금 신뢰 {int(r.get('과금 신뢰', 0))}건", "근거 있음"]], badge_html=b_real())
        table(["단계", "구분", "근거", "검증 방법"],
              [[f"{tr('A')}① 훈련·봇 경기", KIND["real"](), "기본 훈련 17챕터 · 초심자 훈련소 14일 (42.2 · 2026-07, 현재) · 일반전 봇 (2020 도입 · 2024 개발자 노트, 과거 자료)", "훈련 완료율 · 경기당 봇 비율"],
               [f"{tr('A')}② 첫 실전 좌절", KIND["interp"](),
                f"리뷰 '실력 격차' {int(n.get('실력 격차·매칭', 0))}건 · '봇→실전' {int(n.get('봇→실전 전환', 0))}건 · '첫 사망' {int(n.get('초반 교전·첫 사망', 0))}건",
                "첫 교전 전 사망률 · 상대 MMR 격차 (매칭 품질 실험)"],
               [f"{tr('A')}③ 성장 체감 부족", KIND["hypo"](), "가설 · 로그 검증 필요", "다음 경기 재참여율 · D7 (다음 경기 코치 A/B)"],
               [f"{tr('B')}① 즐거웠던 스쿼드", KIND["real"](), f"최고 동접 {ns['peak']['value']:,}명 (2018-01-13) · 추억 리뷰 {int(r.get('추억·복귀 동기', 0))}건",
                "휴면 계정의 과거 스쿼드 플레이 비율"],
               [f"{tr('B')}② 복귀 장벽", KIND["interp"](),
                f"핵·공정성 {int(r.get('핵·공정성', 0))} · 계정 도용 {int(r.get('계정 도용·정지', 0))} · 친구 {int(r.get('친구·스쿼드', 0))} · 숙련도 {int(r.get('숙련도 격차', 0))} · 운영 {int(r.get('운영 신뢰', 0))}건",
                "복귀자 첫날 설문 (공정성·재미·난도) · 복귀자 신고율"],
               [f"{tr('B')}③ 복귀 동기 부족", KIND["hypo"](), "가설 · 휴면 계정 로그 검증 필요", "복귀 로그인 전환율 (복귀 캠페인 광고 A/B · 홀드아웃)"],
               [f"{tr('C')}① 확률형 구매", KIND["real"](), "밀수품 상자 · 확률 보기 · 누적 보상 · 스크랩 교환 (공식·캡처)", "상점 방문 → 구매 전환"],
               [f"{tr('C')}② 기대와 다른 결과", KIND["interp"](), f"리뷰 '확률·결과' {int(n.get('확률·결과 불만', 0))}건", "구매 후 문의율"],
               [f"{tr('C')}③ 만족도 저하", KIND["hypo"](), "가설 · 매출·설문 검증 필요", "구매 만족도 설문 · 30일 재구매율"]])
        sub("다른 원인도 함께 확인")
        alts = [("A", "서버·최적화", "튕김·패킷 손실 불만 (분류 제외)", "크래시율과 이탈 비교"),
                ("B", "대회 운영 논란 (2026-09)", "같은 시기 리뷰 집중 · 사실관계 미검증", "논란 전후 휴면 전환율 비교"),
                ("B", "계정 도용·정지 처리", f"'계정 도용·정지' {int(r.get('계정 도용·정지', 0))}건", "복귀 시 로그인 실패·정지 문의율"),
                ("C", "스킨 디자인·콘텐츠 우선순위", f"'콘텐츠 대비 스킨' {int(n.get('콘텐츠 대비 스킨 출시', 0))}건", "상품별 판매·평가")]
        html('<div class="ow-grid2">' + "".join(
            f'<div class="ow-alt"><div class="ow-alt-t">{tr(t)} {escape(c)}</div><div class="ow-alt-n">{escape(e)}</div>'
            f'<div class="ow-alt-c">확인: {escape(k)}</div></div>' for t, c, e, k in alts) + "</div>")


# ======================================================================
# 04 해결책 데모 — 포트폴리오의 중심
def s4(ns: dict, ops: pd.DataFrame, plan: dict) -> None:
    head("해결책: 실제 화면 옆에 제안 시안을 놓고, 직접 눌러 본다",
         "수치는 가상 · 시안은 실제 PUBG에 없음", b_mock())
    fr = flag_rows(ns, ops, plan)
    t = st.tabs(DEMO_TABS)
    with t[0]:
        demo_a1(ns, fr["coach"])
    with t[1]:
        demo_a2(ns)
    with t[2]:
        demo_a3(ns)
    with t[3]:
        demo_b1(ns, fr["camp"])
    with t[4]:
        demo_b2(ns)
    with t[5]:
        demo_c(ns)
    lab = ns["score_labels"]
    with st.expander("자세히 보기 · 후보 6개 비교 · 기존 기능과 중복 확인 · 평가 점수"):
        table(["안", "판단", "문제", "기존 기능", "차이"],
              [[f"<b>{escape(ns['names'].get(p['key'], p['name']))}</b><br><small>{p['key']} · {escape(p['name'])}</small>", f"<b>{escape(p['decision'])}</b>", escape(p["problem"]),
                escape(p["existing"]), escape(p["diff"])] for p in ns["proposals"]], badge_html=b_mock())
        table(["안", *lab.values(), "합계", "필요 데이터", "위험"],
              [[f"<b>{escape(ns['names'].get(p['key'], p['key']))}</b> <small>{p['key']}</small>", *[str(p["scores"][k]) for k in lab], f"<b>{sum(p['scores'].values())}</b>",
                escape(p["data"]), escape(p["risk"])] for p in ns["proposals"]], badge_html=b_interp())


def _pfk(ns: dict, key: str) -> None:
    """개선안 상단 공통 구조: 해결하려는 문제 → 제안 기능 → 검증할 KPI (모두 기획 시안)."""
    p, f, k = ns["pfk"][key]
    html(f'<div class="pn-pfk"><div><span>해결하려는 문제</span><b>{escape(p)}</b></div><i>→</i>'
         f'<div><span>제안 기능 (시안)</span><b>{escape(f)}</b></div><i>→</i><div class="k"><span>검증할 KPI</span><b>{escape(k)}</b></div></div>')


def _lead(track: str, title: str, one: str) -> None:
    html(f'<div class="pn-lead {track.lower()}">{tr(track)}<b>{escape(title)}</b><span>{escape(one)}</span></div>')


def demo_a1(ns: dict, rows: list) -> None:
    _lead("A", "다음 경기 코치 · NEXT MATCH COACH", "경기 결과 → 고칠 행동 1개 → 다음 경기 → 달성 확인 → 성장 기록")
    html(_brief(rows, "다음 경기 코치"))
    c0 = ns["coach"][0]
    html(flow_html([("경기 종료", f"예시 · {escape(c0['scene'])}"), ("문제 확인", escape(c0["improve"])),
                    ("다음 경기 목표", escape(c0["goal"].replace("다음 경기: ", ""))), ("목표 달성", escape(c0["hit"])),
                    ("성장 기록", "달성 1회 추가 → 다음 항목으로")],
                   title=f"NEXT MATCH COACH · 한 경기의 흐름 (예시: {escape(c0['label'])} 상황 · 기획 시안 · 판정 데이터 공개 텔레메트리)", cls="dark", hl=2))
    html(chips_html("검증할 KPI", [x.strip() for x in ns["pfk"]["A1"][2].split("·")], "kpi"))
    co = {c["label"]: c for c in ns["coach"]}

    def mock() -> None:
        lab = st.radio("이번 경기 상황 (예시)", list(co), horizontal=True, key="pg_a1_sit")
        c = co[lab]
        if c["mvp"] == "확장 기능":
            html(f'<div class="pg-demo"><h4>경기 후 코칭 {b_mock()}</h4><div class="src">상황 (예시) · {escape(c["scene"])}</div>'
                 f'<div class="pn-ext"><b>확장 기능 · MVP 제외</b>{escape(c["data"])}</div></div>')
            return
        res = st.radio("다음 경기 결과 (예시)", ["달성", "미달성"], horizontal=True, key="pg_a1_res")
        hit = res == "달성"
        html(f'<div class="pg-demo"><h4>경기 후 코칭 {b_mock()} {b_sample()}</h4>'
             f'<div class="src">상황 (예시) · {escape(c["scene"])}</div>'
             '<ol class="pn-steps">'
             f'<li><span>① 이번 경기 개선 항목</span>{escape(c["improve"])}</li>'
             f'<li class="act"><span>② 다음 경기 목표</span>{escape(c["goal"])}</li>'
             f'<li><span>③ 다음 경기 달성 확인</span>{escape(c["check"])} → <b class="{"ok" if hit else "no"}">{escape(c["hit"] if hit else c["miss"])}</b></li>'
             f'<li><span>④ 성장 기록</span>{"목표 달성 1회 추가 · 다음 항목으로" if hit else "기록 유지 · 같은 목표 재도전"}</li></ol>'
             f'<div class="src">판정 데이터 · {escape(c["data"])} · <b>{escape(c["mvp"])}</b></div></div>')
        st.toggle("코칭 끄기", key="pg_a1_off", help="설정에서 언제든 끄고 켤 수 있다 (기획 시안)")
        if st.session_state.get("pg_a1_off"):
            st.info("코칭을 껐습니다. 결과 화면은 기존과 같습니다. (기획 시안)")
    compare("deathcam", "데스캠 · 과거 장면 재생", "다음 경기 행동 1개", mock)
    html('<div class="pg-diff"><div><span class="pg-tag real">기존 (실제)</span>데스캠·리플레이는 <b>과거 교전</b>을 보여 준다'
         '<small>무엇을 바꿀지, 바꿨는지는 알려 주지 않는다</small></div>'
         '<div><span class="pg-tag mock">제안 (시안)</span>다음 경기 코치는 <b>다음 경기 행동</b>과 달성 여부를 잇는다'
         '<small>MVP는 공개 텔레메트리로 판정되는 차량·팀플레이만 · 엄폐·시야는 확장</small></div></div>')
    sub("이미 있는 기능과 겹치지 않나? · 공식 자료로 확인", b_real())
    with st.expander("기존 기능 7개 비교표 (훈련장·AI 훈련·캐주얼 모드)"):
        table(["기능", "언제", "무엇을", "실전 → 다음 경기 행동 연결", "출처"],
              [[f"<b>{escape(a)}</b>", escape(b), escape(c), f"<b>{escape(d_)}</b>" if d_.startswith("○") else escape(d_), link(u, sr) if u else escape(sr)]
               for a, b, c, d_, sr, u in ns["coach_vs"]], cls="pz-vs")
        note(ns["coach_vs_note"])


def demo_a2(ns: dict) -> None:
    _lead("A", "첫 10경기 로드맵 · FIRST 10 MATCHES", "다음 경기 코치가 한 경기 단위라면, 로드맵은 첫 10경기의 적응 과정을 3단계로 보여 준다")
    _pfk(ns, "A2")
    dm = ns["demo_matches"]
    df = pd.DataFrame(dm["rows"], columns=dm["cols"])
    rm = ns["roadmap"]

    def mock() -> None:
        k = st.select_slider("경기 번호 (예시 계정)", options=list(range(1, 11)), value=5, key="pg_a2_match")
        r, r0 = df.iloc[k - 1], df.iloc[0]
        cur = next(s for s in rm if s["range"][0] <= k <= s["range"][1])
        stages = "".join(f'<div class="{"on" if s is cur else "done" if s["range"][1] < k else ""}"><b>{s["range"][0]}~{s["range"][1]}경기</b>'
                         f'{escape(s["stage"])}</div>' for s in rm)

        def delta(v, v0, unit):
            return "" if k == 1 else f"<em>{'+' if v - v0 > 0 else ''}{v - v0:,.1f}{unit} vs 1경기</em>"
        dist = "—" if pd.isna(r["engage_dist_m"]) else f"{r['engage_dist_m']:.0f}m"
        html(f'<div class="pg-demo"><h4>{k}경기째 · {escape(cur["stage"])} {b_sample()}</h4><div class="pn-stage">{stages}</div>'
             f'<div class="pg-metric"><div><small>생존 시간</small><b>{r["survive_min"]:.1f}분</b>{delta(r["survive_min"], r0["survive_min"], "분")}</div>'
             f'<div><small>첫 교전</small><b>{"참여" if r["engaged"] else "없음"}</b><small>거리 {dist}</small></div>'
             f'<div><small>팀원과 거리</small><b>{r["team_dist_m"]:.0f}m</b>{delta(r["team_dist_m"], r0["team_dist_m"], "m")}</div></div>'
             f'<div class="act">단계 목표 · {escape(cur["goal"])}</div>'
             f'<div class="src">{escape(dm["note"])} · 보상 없음 (초심자 훈련소 미션과 구분) · 구간(1~3 / 4~7 / 8~10)은 기획 가정, 데이터로 조정</div></div>')
    compare("season_stats", "시즌 전적 · '지난 10 매치' 기록", "단계 목표 + 실전 기록", mock)
    if True:
        fig = go.Figure(go.Scatter(x=df["match"], y=df["survive_min"], mode="lines+markers", line=dict(color=C_TREAT, width=3)))
        for s in rm:
            fig.add_vrect(x0=s["range"][0] - 0.5, x1=s["range"][1] + 0.5, fillcolor="#EFF6FF" if s is rm[1] else "#F8FAFC",
                          line_width=0, layer="below", annotation_text=s["stage"], annotation_position="top left")
        fig.update_xaxes(title="경기 번호", dtick=1)
        fig.update_yaxes(title="생존 시간 (분)", rangemode="tozero", range=[0, df["survive_min"].max() * 1.3])
        chart_card(fig, key="pg_demo_a2", kind="sample", title="생존 시간 추이 (예시)", unit="분 · 배경 = 단계", kpis=[],
                   analysis=f"1경기 {df['survive_min'].iloc[0]:.1f} → 10경기 {df['survive_min'].iloc[-1]:.1f}분",
                   decision="구간·목표는 실제 첫 10경기 로그로 조정",
                   basis="예시 데이터 · 실제 계정 기록 아님", height=260, legend=False, cols=("경기 번호", "생존 시간 (분)"))
        st.caption("기존: 초심자 훈련소(14일 미션·보상) · 무기 숙련도(무기별 레벨) · 시즌 전적 '지난 10 매치' → 로드맵은 미션·보상이 아니라 실전 기록을 3단계 목표로 해석")
        if False: st.markdown("- **기존**: 초심자 훈련소(14일 미션·보상) · 무기 숙련도(무기별 레벨) · 시즌 전적 '지난 10 매치'\n"
                    "- **A2 차이**: 미션·보상이 아니라 *실전 기록*을 3단계 목표로 해석 · 첫 10경기에만 표시")


def demo_a3(ns: dict) -> None:
    mq = ns["match_quality"]
    _lead("A", "매칭 품질 실험 · MATCH QUALITY", "새 매칭 알고리즘이 아니라, 운영 정책과 실험 설계")
    _pfk(ns, "A3")
    html('<div class="pg-diff"><div><span class="pg-tag real">이미 있는 정책 (실제 · 과거 자료)</span>일반전 MMR · 신규·미숙련 유저 매칭 구조 개선 · 인원 부족 시 봇'
         '<small>2024 개발자 노트 기준 · 2026 적용 범위는 내부 확인 필요</small></div>'
         f'<div><span class="pg-tag mock">제안 (실험)</span>보호 구간·완화 조건을 대기시간과 함께 실험<small>{escape(mq["experiment"])}</small></div></div>')
    table(["분석", "보는 것", "판단 지표"], [[f"<b>{escape(a)}</b>", escape(b), escape(c)] for a, b, c in mq["analyses"]], badge_html=b_mock())
    note(mq["not"])


def _ad_card(ns: dict, ad: dict) -> str:
    """보조 광고 시안 카드 (짧은 문구 + 이미지만 · 숫자·KPI 없음)."""
    if ad["image"] == "lobby":
        src = _img_src("lobby", 1200)
        img = (f'<div class="pn-ad2"><div class="bubble">{escape(ad["copy"])}</div>'
               f'<img src="{src}" alt="실제 게임 화면: 로비의 빈 스쿼드 자리" loading="lazy"><div class="sub">{escape(ad["sub"])}</div></div>') if src else ""
    else:
        img = art(ns, ad["key"], "")
    return (f'<div class="pn-ad"><div class="pn-ad-h"><span class="no">광고 {ad["no"]}</span><b>{escape(ad["title"])}</b>'
            f'<em>{escape(ad["msg"])}</em></div>{img}<span class="pn-ai">{escape(ad["label"])}</span></div>')


def ad_gallery(ns: dict, key: str = "pgad") -> str:
    """복귀 광고 3종: 대표 광고(길리슈트·3레벨 헬멧) 1장을 크게, 나머지는 좌우 넘기기. 원본 이미지 그대로 · 원본 비율."""
    slides = []
    for ad in ns["campaign"]["ads"]:
        if ad["image"] == "lobby":
            src = _img_src("lobby", 1200)
            if not src:
                continue
            media = (f'<div class="pn-ad2"><div class="bubble">{escape(ad["copy"])}</div>'
                     f'<img src="{src}" alt="광고 2 시안: 로비의 빈 스쿼드 자리" loading="lazy"><div class="sub">{escape(ad["sub"])}</div></div>')
        else:
            path = ASSETS / ad["image"]
            if not path.is_file():
                continue
            mime = "png" if path.suffix == ".png" else "jpeg"
            media = (f'<img src="data:image/{mime};base64,{_png_b64(str(path), path.stat().st_mtime)}" '
                     f'alt="광고 {ad["no"]} 시안: {escape(ad["copy"])}" loading="lazy">')
        slides.append((media, f'광고 {ad["no"]} · {ad["copy"]}', f'{ad["msg"]} · {ad["label"]} · 포트폴리오용 가상 캠페인 (KRAFTON 실제 광고 아님)'))
    return gallery_html(key, slides)


def _poster_mocks(ns: dict) -> str:
    """메인 포스터(광고 1) 하나로 만든 지하철·버스 정류장 목업. 별도 이미지 생성 없이 같은 포스터를 액자에 넣는다."""
    poster = art(ns, "ad1", "")
    qr = ASSETS / "ads" / "qr_ad1_subway.svg"
    qr_html = qr.read_text(encoding="utf-8") if qr.is_file() else ""
    subway = (f'<div class="pn-subway"><div class="pn-subway-top">지하철 스크린도어 광고 (목업)</div><div class="pn-subway-in">{poster}'
              f'<div class="pn-qr">{qr_html}<small>QR → 복귀 랜딩</small></div></div></div>')
    bus = (f'<div class="pn-bus"><div class="roof">BUS STOP · 정류장 광고 (목업)</div><div class="panel">{poster}</div>'
           '<div class="legs"><i></i><i></i></div></div>')
    return f'<div class="pn-mocks"><div class="m1">{subway}</div><div class="m2">{bus}</div></div>'


def _changes(cp: dict) -> str:
    def items(rows, cls, lab):
        return "".join(f'<li><span class="st {cls}">{lab}</span>{escape(t)}<a href="{escape(u, quote=True)}" target="_blank" rel="noopener">{escape(src)}</a></li>'
                       for t, src, u in rows)
    return '<div class="pn-chg">' + "".join(
        f'<div><div class="h">{c["icon"]} {escape(c["title"])}</div><ul>{items(c["applied"], "ok", "적용됨")}'
        f'{items(c["roadmap"], "plan", "개선 예정")}</ul><small>{escape(c["caveat"])}</small></div>'
        for c in cp["changes"]) + "</div>"


def demo_b1(ns: dict, rows: list) -> None:
    cp = ns["campaign"]
    ads = {a["key"]: a for a in cp["ads"]}
    p, f, k = ns["pfk"]["B1"]
    _lead("B", "복귀 캠페인 «야, 배그 한 판 할래?»", "한때 배그를 즐기던 유저는 왜 돌아오지 않을까? → 친구가 부르면 돌아온다")
    html(f'<div class="pz-msg"><span>메인 카피</span><b>«{escape(ads["ad2"]["copy"])}»</b><small>그때 같이 하던 친구에게서 온 한마디 · 친구가 부른다 → 변화 증명 → 함께 복귀</small></div>')
    html(ad_gallery(ns))
    html(_brief(rows, "복귀 캠페인"))
    html('<div class="pn-b1h">광고 노출 → 복귀 → 친구와 재결합 → 장기 정착 — 단계마다 이탈을 측정</div>')
    _journey(ns)
    html('<div class="pn-b1h">광고 3종은 감정·디자인·행동 유도가 다르다</div>')
    html('<div class="pz-ads">' + "".join(
        f'<div class="{a["key"]}"><em>광고 {a["no"]} · {escape(a["type"])}</em><b>«{escape(a["copy"])}»</b>'
        f'<p><span>감정</span>{escape(a["emotion"])}</p><p><span>디자인</span>{escape(a["design"])}</p>'
        f'<p><span>행동 유도</span>{escape(a["cta"])}</p><p><span>노출</span>{escape(a["where"])}</p></div>' for a in cp["ads"]) + "</div>")
    html('<div class="pn-b1h">광고 3의 답 «그래서 뭐가 달라졌냐고?» · 공식 자료로 확인한 변경만</div>')
    html(_changes(cp))
    html(f'<div class="pn-land"><a class="pn-btn" href="{escape(cp["landing"], quote=True)}?src=portfolio" target="_blank" rel="noopener">'
         '복귀 랜딩페이지 데모 열기 →</a><span>클릭 가능한 HTML 데모 · 실제 게임·결제와 연결되지 않음 · 복귀 첫날 경험은 «복귀 첫날 · D30» 탭</span></div>')
    html('<div class="pn-b1h">광고 노출 채널</div>')
    html('<div class="pn-chan">' + "".join(f'<div><b>{escape(n)}</b><span>{escape(r)}</span></div>' for n, r in cp["offline"])
         + f'<p>{b_hypo()} 채널별 효과는 검증할 가설 · QR 유입(src)으로 측정</p></div>')
    html('<div class="pn-b1h">KPI · 예산</div>')
    kf = '<i>→</i>'.join(f'<span>{escape(x)}</span>' for x in cp["kpi_flow"])
    total = cp["budget"] + ns["experiment"]["cost"]["B1_effort"] * ns["experiment"]["cost"]["monthly_cost_per_person"]
    html(f'<div class="pn-cflow">{kf}</div><div class="pn-b1k"><b>KPI</b> {escape(k)} · <b>복귀 캠페인 총액 {won(total)}</b> '
         f'(광고·콘텐츠 파일럿 {won(cp["budget"])} + 랜딩·UTM 제작비) {b_sim()}</div>')
    with st.expander("자세히 보기 · 유입 링크 · 채널 예산 (가정) · 캠페인 흐름"):
        flow = '<i>→</i>'.join(f'<span>{escape(x)}</span>' for x in cp["flow"])
        html(f'<div class="pn-cflow">{flow}</div>')
        table(["광고", "채널", "유입 링크 (실제 주소)"],
              [[escape(a), escape(ch), link(f'{cp["landing"]}?src={src}', f"?src={src}")] for a, ch, src in cp["links"]], badge_html=b_mock())
        bud = cp["budget"]
        table(["채널", "용도", "비중", "파일럿 배분"],
              [[f"<b>{escape(n)}</b>", escape(d), f"{w}%", f"{bud * w / 100 / 1e4:,.0f}만 원"] for n, d, w in cp["channels"]], badge_html=b_sim())
        st.caption(f"광고·콘텐츠 파일럿 {won(bud)} + 추가 제작비(랜딩·UTM) {won(total - bud)} = 복귀 캠페인 총액 {won(total)} (06과 동일) · 가정 · {cp['note']}")


def demo_b2(ns: dict) -> None:
    sq = ns["squad_demo"]
    _lead("B", "복귀 첫 플레이 · D7·D30 재정착", "돌아온 첫날 다시 좌절하지 않게 · 공부가 아니라 친구와 다시 즐길 이유")
    _pfk(ns, "B2")
    names = [f["name"] for f in sq["friends"]]

    def mock() -> None:
        pick = st.multiselect("함께할 친구 (예시 · 친구 목록·초대 링크)", names, default=names[:2], key="pg_b1_f")
        k = st.select_slider("복귀 단계", options=list(range(1, 6)), value=1,
                             format_func=lambda i: f"{i} {sq['steps'][i - 1][0]}", key="pg_b1_step")
        fr = [f for f in sq["friends"] if f["name"] in pick]
        prog = "".join(f'<div class="{"on" if i + 1 == k else "done" if i + 1 < k else ""}"><b>{i + 1}</b>{escape(s[0])}</div>'
                       for i, s in enumerate(sq["steps"]))
        joined = len(fr) if k >= 2 else 0
        squad = "".join(f'<li><b>{escape(f["name"])}</b><small>{escape(f["last"])} · {escape(f["status"])}</small>'
                        f'<em>{"합류" if k >= 2 else "초대 보냄"}</em></li>' for f in fr) or "<li><small>친구를 선택하세요</small></li>"
        games = {1: 0, 2: 0, 3: 1, 4: 3, 5: 3}[k]
        html(f'<div class="pg-demo nv"><h4>WELCOME BACK {b_mock()} {b_sample()}</h4><div class="pn-prog">{prog}</div>'
             f'<div class="act">{escape(sq["steps"][k - 1][1])}</div>'
             f'<ul class="pn-squad"><li><b>나</b><small>휴면 2년 · 복귀</small><em>복귀</em></li>{squad}</ul>'
             f'<div class="pn-goal"><span>첫날 · 함께 3경기</span><div class="bar"><i style="width:{games / 3 * 100:.0f}%"></i></div>'
             f'<b>{games}/3</b></div><div class="src">스쿼드 {1 + joined}/4 · {escape(sq["note"])}</div></div>')
    compare("first_kill", "첫 경기 · 첫 킬 직후", "복귀 첫날 · 친구와 3경기", mock)
    fd = ns["firstday"]
    html('<div class="pn-day">' + "".join(f'<div><span>{escape(a)}</span><b>{escape(b)}</b><small>{escape(c)}</small></div>' for a, b, c in fd)
         + f'</div><div class="pn-daynote">{b_mock()} 첫날 3경기 동안 복귀자 매칭 품질을 따로 점검 · 친구 초대는 기존 기능 그대로</div>')
    fn = ns["funnel"]
    steps = S.return_funnel(fn)
    fig = go.Figure(go.Bar(x=[v for _, v in steps], y=[n for n, _ in steps], orientation="h", marker_color=C_NAVY,
                           text=[f"{v:.2f}%" for _, v in steps], textposition="outside", cliponaxis=False))
    fig.update_yaxes(autorange="reversed", automargin=True, title="")
    fig.update_xaxes(title="광고 배정 대비 (%) · 가정", range=[0, steps[0][1] * 1.35], ticksuffix="%")
    chart_card(fig, key="pg_funnel", kind="sim", title="복귀 첫날 · D30 · 복귀 후 재정착 퍼널 (가정 시뮬레이션)", unit="% · 광고 배정 100% 기준",
               kpis=[("복귀 로그인 (30일 내)", f"{steps[0][1]:.1f}%"), ("복귀 후 D30 잔존", f"{steps[-1][1]:.2f}%")],
               analysis="일회성 접속이 아니라 D30까지 남는 비율이 사업 효과", decision="성공 판단은 복귀율만이 아니라 복귀 후 D30까지 함께 본다",
               basis=fn["note"], height=260, legend=False, cols=("단계", "배정 대비 (%)"))


def demo_c(ns: dict) -> None:
    _lead("C", "보조 사업성 검토 · BM 내부 분석", "A·B 다음 순위 · 사업PM 내부 분석 도구 · 유저 화면 제안이 아님")
    cp = next(x for x in ns["proposals"] if x["key"] == "C")
    rk = next((r for r in ns["risks"] if "BM" in r["risk"]), None)
    kc = ns["kpis"]["C"]
    steps = [("유저 불만", f"{cp['problem']} (Steam 리뷰 · 02 탭)"),
             ("사업 리스크", "불만을 줄이는 변경은 단기 매출을 줄일 수 있다 (상충)" + (f" · {rk['risk']}" if rk else "")),
             ("개선 전략", "새 확률 구조를 만들지 않음 · 기존 스크랩 교환·누적 보상 안에서 재료 지원을 소규모로 먼저 검토"),
             ("실험", "유저 화면 변경 없는 내부 시나리오 비교 + 구매 만족도 설문"),
             ("KPI", " · ".join(f"{k[0]} ({k[1]})" for k in kc)),
             ("중단 기준", next((f"{k[0]} 하락 (가드레일)" for k in kc if k[1] == "가드레일"), "매출 가드레일 악화") + " · 구매 만족도 개선 없음 → 시나리오 중단")]
    html('<ol class="df-chain">' + "".join(f'<li><span>{escape(a)}</span><p>{escape(b)}</p></li>' for a, b in steps) + "</ol>")
    note("천장 유사 구조(스크랩 교환·누적 보상)는 이미 있고 이중 가챠는 제거됐다 → 새 구조를 제안하지 않고, 유저 불만이 확인된 '확률·결과'만 관리 대상으로 둔다.")
    with st.expander("자세히 보기 · 실제 상품 구조 (성장형 스킨 · 공식 자료)"):
        table(["구조", "실제 운영 내용", "판단", "근거"],
              [[f"<b>{escape(a)}</b>", escape(b), escape(c), escape(d)] for a, b, c, d in ns["skin_structure"]], badge_html=b_real())
    bm = ns["bm_sim"]
    box = {}

    def mock() -> None:
        c1, c2 = st.columns(2)
        box["price"] = c1.number_input("1회 가격 (G-Coin · 예시)", 100, 10000, int(bm["price"]), step=100, key="pg_c_price")
        box["prob"] = c2.slider("목표 스킨 확률 (% · 예시)", 0.1, 10.0, float(bm["prob"]), 0.1, key="pg_c_prob")
        box["out"] = st.container()
    compare("contraband_store", "밀수품 상자 구매 화면", "내부 분석 · 목표 스킨 기대 비용", mock)

    with st.expander("자세히 보기 · 스크랩 교환 조건 · 구매 횟수별 확률 곡선 · 계산식"):
        c1, c2, c3, c4 = st.columns(4)
        per = c1.number_input("1회당 스크랩", 0, 100, int(bm["scrap_per_open"]), key="pg_c_spo")
        ex = c2.number_input("교환 필요 스크랩", 0, 20000, int(bm["exchange_scrap"]), step=100, key="pg_c_ex")
        own = c3.number_input("보유 스크랩", 0, 20000, 0, step=100, key="pg_c_own")
        n = c4.slider("구매 횟수", 1, 400, 100, key="pg_c_n")
        d1, d2, _ = st.columns([1, 1, 2])
        fn = d1.number_input("첫 묶음 횟수 (0 = 할인 미적용)", 0, 100, int(bm.get("first_n", 0)), key="pg_c_fn")
        fp = d2.number_input("첫 묶음 가격 (G-Coin)", 0, 100000, int(bm.get("first_price", 0)), step=100, key="pg_c_fp")
        s = S.crate_summary(box["price"], box["prob"], per, ex, own, n, fn, fp)
        cap = s["cap"]
        tiles([(f"{n}회 안에 얻을 확률", f"{s['within_n'] * 100:.1f}%", f"독립 시행 · {n}회 비용 {s['n_cost']:,.0f} G-Coin"),
               ("교환 확정 (천장)", "없음" if cap is None else f"{s['cap_cost']:,.0f}", "" if cap is None else f"{cap}회 · G-Coin"),
               ("교환 없을 때 기대 비용", f"{s['exp_cost_nocap']:,.0f}", "G-Coin · 1 ÷ p 회")])
        mx = max(n, cap or 0, s["o90"] or 0) + 20
        step = max(1, mx // 40)
        curve = [c for c in S.crate_curve(box["prob"], cap, mx) if c[0] % step == 0 or c[0] in (cap, n)]
        fig = go.Figure()
        fig.add_scatter(x=[c[0] for c in curve], y=[c[1] for c in curve], name="교환 없이", line=dict(color=C_CTRL, width=2, dash="dot"))
        fig.add_scatter(x=[c[0] for c in curve], y=[c[2] for c in curve], name="스크랩 교환 포함", line=dict(color=C_CORAL, width=3))
        fig.update_xaxes(title="구매 횟수 (회)", range=[0, mx])
        fig.update_yaxes(title="1번 이상 얻을 확률 (%)", range=[0, 105], ticksuffix="%")
        chart_card(fig, key="pg_demo_c", kind="sim", title="구매 횟수별 획득 확률", unit="% · 코랄 = 교환 포함",
                   kpis=[], analysis=f"{n}회 안에 {s['within_n'] * 100:.1f}%", decision="교환가·재료 지원 시나리오의 비용 변화 비교에 사용 (내부)",
                   basis="P(n회 내) = 1 − (1 − p)^n · 천장 = 교환 스크랩 ÷ 1회당 스크랩", height=280,
                   cols=("구매 횟수 (회)", "획득 확률 (%)"), series="계산")
        st.markdown("- 기대 구매 횟수 = (1 − (1 − p)^K) ÷ p (K = 천장 = 교환 스크랩 ÷ 1회당 스크랩, 교환이 없으면 1 ÷ p)\n"
                    "- 비용 = 첫 구매는 10회 묶음 할인가, 이후 1회 가격 × 추가 횟수 → 기대 비용 = 묶음가 + 1회 가격 × (E[N] − E[min(N, 10)])\n"
                    "- 중복 보상의 분해·토큰 환급은 반영하지 않음 → 실제 부담은 이보다 낮을 수 있다")
        table(["값", "상품", "근거", "검증 상태"], [[f"<b>{escape(a)}</b>", escape(b), escape(c), escape(d)] for a, b, c, d in ns["price_check"]],
              badge_html=b_interp())
    with box["out"]:
        html(f'<div class="pg-demo b"><h4>목표 스킨까지 기대 비용 (내부) {b_sample()} {b_sim()}</h4><div class="pg-metric">'
             f'<div><small>기대 비용 (교환 포함)</small><b class="big">{s["exp_cost"]:,.0f}</b><small>G-Coin · 평균 {s["exp_opens"]:.0f}회</small></div>'
             f'<div><small>50% 확률 도달</small><b>{(s["c50"] or 0):,.0f}</b><small>{s["o50"]}회</small></div>'
             f'<div><small>90% 확률 도달</small><b>{(s["c90"] or 0):,.0f}</b><small>{s["o90"]}회</small></div></div>'
             '<div class="src">가격 200·확률 0.9%·교환가 3,000은 게임 화면 캡처값 (공식 문서 미확인) · 상품별 검증은 아래 펼쳐보기</div></div>')
    _scenario_chart(ns)


def _scenario_chart(ns: dict) -> None:
    sv = S.scenarios(ns["scenarios"])
    fig = go.Figure()
    fig.add_vline(x=0, line_width=2, line_color="#1E293B")
    fig.add_annotation(x=0, y=0.5, yref="paper", text="현행 = 0%", showarrow=False, xanchor="left", xshift=6,
                       font=dict(size=12, color="#1E293B"), bgcolor="rgba(255,255,255,0.9)")
    labs = {"B": "강화 재료 지원", "C": "교환가 인하"}
    for s in sv[1:]:
        col = C_CORAL if s["key"] == "C" else "#F4A79F"
        lo, hi = s["low_pct"], s["high_pct"]
        lab = labs.get(s["key"], s["key"])
        fig.add_trace(go.Scatter(x=[lo, hi], y=[lab, lab], mode="lines+markers+text", line=dict(color=col, width=10),
                                 marker=dict(size=16, color="#FFFFFF", line=dict(color=col, width=3)),
                                 text=[f"{lo:+.0f}%", f"{hi:+.0f}%"], textposition=["middle left", "middle right"],
                                 textfont=dict(size=14, color="#B4433B"), cliponaxis=False, showlegend=False, name=lab,
                                 hovertemplate=f"{s['name']}<br>가정 범위 {lo:+.1f}% ~ {hi:+.1f}%<extra></extra>"))
    fig.update_xaxes(title="현행 대비 60일 매출 변화 (%)", range=[-30, 20], ticksuffix="%", zeroline=False, dtick=10)
    fig.update_yaxes(title="", autorange="reversed", automargin=True)
    b_, c_ = sv[1], sv[2]
    chart_card(fig, key="pg_sim_c", kind="sim", title="C2 · BM 정책별 매출 영향 (가정 시나리오 범위)", unit="% · 선 = 비관 ~ 낙관 가정",
               kpis=[("강화 재료 지원", f"{b_['low_pct']:+.0f}% ~ {b_['high_pct']:+.0f}%"), ("교환가 인하", f"{c_['low_pct']:+.0f}% ~ {c_['high_pct']:+.0f}%")],
               analysis="교환가 인하는 하한이 더 낮다 (고액 결제 감소 가정)",
               decision="결론을 내리지 않음 · 재료 지원을 소규모로 먼저 검토, 구매 만족도 설문을 함께 본다",
               basis="전환율·ARPPU·재구매율 모두 가정값 · 통계적 신뢰구간 아님 · 매출 예측 아님", height=220, legend=False, cols=("정책", "매출 변화 (%)"))
    with st.expander("자세히 보기 · 시나리오 가정값과 산출식"):
        table(["시나리오", "전환율 (%)", "ARPPU (G-Coin)", "재구매율 (%)", "60일 매출 (백만)", "현행 대비"],
              [[f"<b>{s['key']}</b> {escape(s['name'])}", f"{s['conv'][0]}~{s['conv'][1]}", f"{s['arppu'][0]:,}~{s['arppu'][1]:,}",
                f"{s['repurchase'][0]}~{s['repurchase'][1]}", f"{s['low']['total'] / 1e6:,.1f}~{s['high']['total'] / 1e6:,.1f}",
                f"{s['low_pct']:+.1f}%~{s['high_pct']:+.1f}%"] for s in sv], badge_html=b_sim())
        st.caption(f"60일 매출 = 방문자 × 전환율 × ARPPU + 구매자 × 재구매율 × ARPPU × {ns['scenarios']['repurchase_arppu_ratio']} · "
                   f"비관 = 각 범위의 낮은 값, 낙관 = 높은 값 · {ns['scenarios']['note']}")


# ======================================================================
# 05 KPI·A/B 테스트
def s5(ns: dict, plan: dict) -> None:
    ex = ns["experiment"]
    A, R = ex["A"], ex["R"]
    pa, pr, sc = plan["A"], plan["R"], plan["sched"]
    pm = plan["practical_min"]
    cp = ns["campaign"]
    ret_n = (pr["arms"] - 1) * pr["n"] * (R["base_return"] + pr["mde"]) / 100      # 광고 그룹 복귀자 (가정)
    add_n = (pr["arms"] - 1) * pr["n"] * pr["mde"] / 100                            # 대조군 대비 순증 복귀자 (가정)
    head("KPI: 신규 D7 · 복귀율 · 복귀 D30 · 순증 복귀 유저당 비용", "모두 실험 전 가정 · 실제 결과 아님", b_mock())
    html('<div class="pn-k4">'
         f'<div class="a"><span>신규 D7 잔존율</span><b>{A["base_d7"]:.0f}% → {A["base_d7"] + pa["mde"]:.0f}%</b><small>다음 경기 코치 · 가정 설계</small></div>'
         f'<div class="b"><span>복귀율</span><b>{R["base_return"]:.1f}% → {R["base_return"] + pr["mde"]:.1f}%</b><small>광고 vs 대조군 · 가정 설계</small></div>'
         '<div class="b"><span>복귀 D30</span><b>대조군 이상</b><small>자연 복귀자와 비교 · 기준값은 측정</small></div>'
         f'<div class="y"><span>순증 복귀 유저당 비용</span><b>약 {plan["b1_cost"] / add_n / 1e4:,.0f}만 원</b><small>캠페인 총액 ÷ 순증 복귀자 약 {add_n:,.0f}명 · 가정</small></div></div>')
    with st.expander(f"비용 계산 · 일반 복귀 유저당 비용 약 {plan['b1_cost'] / ret_n / 1e4:,.0f}만 원 vs 순증 기준"):
        html(f'<div class="pn-cav2"><b>보조 · 일반 복귀 유저당 비용 약 {plan["b1_cost"] / ret_n / 1e4:,.0f}만 원</b> = 캠페인 총액 {won(plan["b1_cost"])} ÷ 광고 그룹 복귀자 약 {ret_n:,.0f}명 '
             f'(광고 3그룹 × {pr["n"]:,}명 × {R["base_return"] + pr["mde"]:.1f}%) · 순증 기준은 분모가 대조군 대비 늘어난 복귀자 약 {add_n:,.0f}명 '
             f'(× {pr["mde"]:.1f}%p) · 옥외광고 유입은 분모에서 빼 보수적으로 계산 · 모두 가정</div>')
    html(f'<div class="pn-abt"><div class="pn-abt-h">{b_mock()} 복귀 캠페인 광고 A/B 테스트 · 대조군 포함 4그룹</div>'
         '<table><tr><th>그룹</th><th>광고</th><th>가설</th></tr>' + "".join(
             f'<tr><td><b>{escape(g)}</b></td><td>{escape(ad)}</td><td>{escape(h)}</td></tr>' for g, ad, h in cp["abtest"]) + '</table>'
         '<div class="pn-abt-k"><span>주요 KPI</span><b>순증 D30 재정착 유저당 비용</b></div></div>')
    with st.expander("A/B 보조 지표 · 배정 방식"):
        html('<div class="pn-abt-k">보조: CTR · 복귀 로그인 전환율 · 첫 매치 완료율 · D7 · D30 · 스쿼드 재참여율 · 같은 휴면 리스트를 4그룹 무작위 배정(광고별 타깃 동일 · 같은 예산·기간) · 홀드아웃 대비 순증 · 배정된 전원 기준(ITT)</div>')
    dig = cp["budget"] * next(w for n, _, w in cp["channels"] if "디지털" in n) / 100
    land = ex["cost"]["B1_effort"] * ex["cost"]["monthly_cost_per_person"]
    pilot = dig + land
    full_u, pilot_u = plan["b1_cost"] / add_n, pilot / add_n
    sub("복귀 캠페인 사업성 판단 · 결론: 전액 집행 보류 → 디지털 소규모 파일럿", b_sim())
    html(f'<div class="gb-big pz-biz3"><div><em>전액 집행 손익분기 (순증 1인당 기대 매출)</em><b>약 {full_u / 1e4:,.0f}만 원↑</b><small>가정 시뮬레이션</small></div>'
         f'<div><em>공개 자료로 본 수익성</em><b>판단 불가</b><small>PUBG ARPU·LTV 비공개</small></div>'
         f'<div><em>권고</em><b>파일럿 {won(pilot)}</b><small>전액 {won(plan["b1_cost"])}은 보류</small></div></div>')
    with st.expander("손익분기 조건 설명"):
        html(f'<div class="pn-biz"><p><b>손익분기 조건</b> 순증 복귀자 1명이 남은 기간 동안 내는 기대 매출이 <b>약 {full_u / 1e4:,.0f}만 원 이상</b>이어야 전액 집행이 정당화된다. '
             'PUBG의 ARPU·LTV는 공개 자료로 확인하지 못해 <b>수익성은 판단 불가</b> → 1억 원 전액 집행은 보류한다.</p></div>')
    with st.expander(f"파일럿 {won(pilot)} 산출 · 손익분기 기여이익 계산식"):
        html(f'<div class="pn-biz"><p><b>파일럿 {won(pilot)} 산출</b> = 디지털 광고 {won(dig)} (광고 예산 {won(cp["budget"])} × 디지털 비중, 가정) + 랜딩·UTM 제작 '
             f'{ex["cost"]["B1_effort"]:g}인월 × {ex["cost"]["monthly_cost_per_person"] / 1e4:,.0f}만 원 = {won(land)} (가정) · 실제 집행 데이터 아님</p></div>')
        st.caption(f"손익분기 기여이익 = 비용 ÷ (순증 복귀자 × D30 잔존율) · 순증 복귀자 약 {add_n:,.0f}명 = 광고 3그룹 × {pr['n']:,}명 × +{pr['mde']:.1f}%p (무작위 배정이 가능한 디지털 기준 · "
                   "옥외·콘텐츠는 순증 측정이 안 돼 분모를 늘리지 않는 보수적 계산) · D30 20·30·40%는 민감도용 가정 · ARPU·LTV 미확인 → 수익성 판단 불가")
    cont = cp["budget"] * next(w for n, _, w in cp["channels"] if "콘텐츠" in n) / 100
    scen = [("저예산 파일럿", "디지털 리타깃팅 + 랜딩·UTM", pilot, "<b>권고</b>"),
            ("중간 규모", "파일럿 + 랜딩 유입·콘텐츠 홍보", pilot + cont, "파일럿에서 순증·D30 확인 시"),
            ("기존 제안 (전액)", "디지털·옥외·콘텐츠 + 제작", plan["b1_cost"], "보류")]
    table(["시나리오", "구성", "비용", "순증 복귀 1인당", "손익분기 기여이익 (순증 D30 재정착 1인당 · D30 20 / 30 / 40%)", "판단"],
          [[f"<b>{a}</b>", b, won(c), f"약 {c / add_n / 1e4:,.0f}만 원",
            " / ".join(f"{c / add_n / r / 1e4:,.0f}만" for r in (0.2, 0.3, 0.4)), dcs] for a, b, c, dcs in scen], badge_html=b_sim())
    html('<div class="pn-cav2"><b>확대</b> 파일럿에서 소재 1개 이상이 홀드아웃 대비 유의한 순증 + 측정된 재정착 1인당 비용 ≤ 내부 LTV 기준 · '
         '<b>중단</b> 모든 소재가 홀드아웃과 차이 없음 · 또는 복귀자 신고율 악화 · 2주 차 중간 점검에서 차이 없는 소재는 먼저 중단</div>')
    with st.expander("BM 내부 분석 (후속 검토)"):
        note("BM 내부 분석은 후속 정책 검토: 확률형 불만을 줄이는 변경은 단기 매출을 줄일 수 있어 서로 상충 → 매출 효과는 단정하지 않고 내부 데이터로 시나리오만 비교")
        note("BM 내부 분석은 실험 없이 구매 전환율·ARPPU·구매 만족도를 내부 시나리오·설문으로 본다.")

    with st.expander("자세히 보기 · 가정 시뮬레이션 · 판정 기준 · 비용 계산"):
        d30_base, d30_up = A["base_d7"] / 2, pa["mde"] / 2
        cats = ["신규 D7", "신규 D30", "첫 10경기 완료율"]
        before = [A["base_d7"], d30_base, A["base_m10"]]
        after = [A["base_d7"] + pa["mde"], d30_base + d30_up, A["base_m10"] + pa["m10_mde"]]
        fig = hpair(cats, before, after, xtitle="비율 (%)", names=("대조군 (가정)", "실험군 (가정)"), xmax=max(after) * 1.35)
        chart_card(fig, key="pg_sim_a", kind="sim", title="다음 경기 코치 · 대조군 vs 실험군 (가정)", unit="% · 회색 = 대조, 파랑 = 실험",
                   kpis=[("신규 D7 설계 목표", f"{before[0]:.0f}% → <b>{after[0]:.0f}%</b> <em>{pp(pa['mde'])}</em>")],
                   analysis=f"+{pa['mde']:.1f}%p = 코칭 열람률 {A['participation']}% × 열람자 개선 {A['uplift_viewer']:.0f}%p (가정)",
                   decision="유의성·실질 효과·가드레일을 각각 통과해야 확대", basis="설계값 · D30은 D7 효과의 절반 유지 가정",
                   height=280, cols=("지표", "비율 (%)"), series="그룹")
        sub("판정 기준 · 세 가지를 따로 본다", b_mock())
        html('<div class="ow-sig">'
             f'<div><b>① 통계적 유의성</b>코치: D7 차이의 95% 신뢰구간 하한 &gt; 0<br>복귀 캠페인: 광고별 복귀 전환율 차이(대조군 대비) 95% 신뢰구간 하한 &gt; 0 (다중 비교 보정)</div>'
             f'<div><b>② 실질적 사업 효과</b>코치: 점추정 ≥ +{pm:.1f}%p (사전 합의)<br>복귀 캠페인: 복귀 D30이 자연 복귀자보다 낮지 않음 · 복귀 유저당 비용 사전 상한 이하</div>'
             f'<div><b>③ 가드레일</b>하나라도 악화되면 확대하지 않음<br>코치: {escape(" · ".join(A["guardrails"]))}<br>복귀 캠페인: {escape(" · ".join(R["guardrails"]))}</div></div>')
        st.markdown(f"- **참고 · 전체 복귀자 기준** 캠페인 총액 {won(plan['b1_cost'])} ÷ 광고 그룹 복귀자 약 {ret_n:,.0f}명 "
                    f"(광고 3그룹 × {pr['n']:,}명 × {R['base_return'] + pr['mde']:.1f}%) ≈ {plan['b1_cost'] / ret_n / 1e4:,.1f}만 원\n"
                    f"- **순증 복귀 유저당 비용 (위 KPI)** 대조군 대비 순증 복귀자 약 {add_n:,.0f}명 기준 ≈ {plan['b1_cost'] / add_n / 1e4:,.0f}만 원 → 광고가 없어도 돌아왔을 유저를 빼야 하므로 판단은 순증 기준\n"
                    "- 채널별 효율 = 랜딩 방문 → 복귀 로그인 · 지하철·버스 정류장·PC방은 무작위 배정이 불가능해 QR 유입(src)으로만 참고\n"
                    "- 신규 기획 3개는 한 번에 넣지 않는다 → 다음 경기 코치 단독 실험 후 첫 10경기 로드맵은 별도 코호트, 매칭 품질 실험은 서버 단위 실험")
    with st.expander("자세히 보기 · KPI 정의 (분모 · 대상 · 관측 기간)"):
        for t in ("A", "B", "C"):
            table(["지표", "구분", "대상 (분모)", "정의", "관측 기간"],
                  [[f"{tr(t)}<b>{escape(k[0])}</b>", escape(k[1]), escape(k[2]), escape(k[3]), escape(k[4])] for k in ns["kpis"][t]],
                  badge_html=b_mock())
    with st.expander("자세히 보기 · 실험 설계 (표본 · MDE · 기간 · 계산식)"):
        tiles([("다음 경기 코치 · 신규 D7 MDE", f"+{pa['mde']:.1f}%p", f"기준 {A['base_d7']:.0f}% 가정 · 검정력 80%"),
               ("다음 경기 코치 · 표본", f"{pa['n']:,}명 × 2", f"주당 신규 {A['weekly']:,}명 가정 → {pa['assign_weeks']}주"),
               ("복귀 캠페인 · 복귀율 MDE", f"+{pr['mde']:.1f}%p", f"기준 {R['base_return']:.1f}% 가정 · 검정력 80%"),
               ("복귀 캠페인 · 표본", f"{pr['n']:,}명 × {pr['arms']}", f"주당 휴면 {R['weekly']:,}명 가정 → {pr['assign_weeks']}주")])
        table(["실험", "대조군 → 실험군", "배정 · 대상", "주요 지표", "기간"],
              [[f"{tr('A')}<b>다음 경기 코치</b>", f"{escape(A['control'])} → {escape(A['treatment'])}", f"{escape(A['unit'])}<br>{escape(A['segment'])}",
                f"신규 D7 (ITT) · 기준 {A['base_d7']:.0f}% 가정", f"배정 {sc['a_assign'][0]}~{sc['a_assign'][1]}주 · D7 {sc['a_d7']}주 · D30 {sc['a_d30']}주"],
               [f"{tr('B')}<b>복귀 캠페인 «야, 배그 한 판 할래?»</b>", f"{escape(R['control'])} → {escape(R['treatment'])}", f"{escape(R['unit'])}<br>{escape(R['segment'])}",
                f"복귀 로그인 전환율 (ITT) · 기준 {R['base_return']:.1f}% 가정",
                f"배정 {sc['r_assign'][0]}~{sc['r_assign'][1]}주 · 복귀 판정 {sc['r_return']}주 · D30 {sc['r_d30']}주"]], badge_html=b_mock())
        st.markdown(f"- MDE는 표본 크기를 정하는 설계값이다. 성공 조건이 아니므로, MDE보다 작아도 ①을 통과하고 ②(+{pm:.1f}%p) 이상이면 의미 있는 효과로 본다.\n"
                    f"- 코치 MDE(배정 기준) = 코칭 열람률 {A['participation']}% × 열람자 개선 {A['uplift_viewer']}%p = +{pa['mde']:.1f}%p\n"
                    f"- 두 비율 차이 양측 검정 α {ex['alpha']} · 검정력 {ex['power']:.0%} · 배정 주수 = ⌈그룹 수 × 그룹당 표본 ÷ 주당 대상⌉ · 복귀 캠페인은 광고 3개를 대조군과 각각 비교 (Bonferroni 보정)\n"
                    f"- 복귀 캠페인은 코치 실험 배정이 끝난 {R['start_week']}주차부터 시작 · 복귀 판정 = 마지막 배정 + {R['window_days']}일 · 복귀 후 D30 = 그 뒤 30일\n"
                    "- 가정 시뮬레이션(위 차트)과 실제 실험 결과는 다르다 · 실제 결과는 실험 후에만 표시")


# ======================================================================
# 06 실행·사업 판단 — 문제 설명을 반복하지 않음
def s6(ns: dict, plan: dict) -> None:
    sc = plan["sched"]
    pm = plan["practical_min"]
    c = ns["experiment"]["cost"]
    a1c, b1p = c["A1_effort"] * c["monthly_cost_per_person"], ns["campaign"]["budget"] * 0.5 + c["B1_effort"] * c["monthly_cost_per_person"]
    with st.expander("대표 전략 2개 비교표"):
        table(["단계", "다음 경기 코치 (먼저 실행)", "복귀 캠페인 «야, 배그 한 판 할래?»"], [
            ["<b>문제</b>", "첫 실전에서 막혀 떠난다", "떠난 유저에게 다시 할 이유와 달라진 점이 전달되지 않는다"],
            ["<b>근거</b>", "신규 리뷰 26건 중 11건 (실력 격차 5 · 봇→실전 4 · 첫 사망 2)", "복귀 리뷰 21건 (추억 6 · 핵·도용 6 · 친구 3 · 운영·과금 4 · 숙련도 2)"],
            ["<b>해결책</b>", "경기 후 행동 1개 코칭 → 다음 경기 달성 확인 (기본 훈련·훈련소 이후 첫 실전)", "친구가 부르는 광고 3종 + 랜딩 '달라진 점' (공식 변경만) + 첫날 친구와 3경기"],
            ["<b>비용</b>", f"{c['A1_effort']}인월 = <b>{won(a1c)}</b> (가정)", f"파일럿 <b>{won(b1p)}</b> (전액 {won(plan['b1_cost'])}은 보류)"],
            ["<b>KPI</b>", "신규 D7 (ITT)", "순증 D30 재정착 유저당 비용"],
            ["<b>실험</b>", "신규 계정 50:50", "휴면 리스트 4그룹 (홀드아웃 포함)"],
            ["<b>사업적 판단</b>", "<b>소규모 파일럿 → 유의하면 확대</b> · 매칭 변경 없음", "<b>소규모 파일럿</b> · 수익성은 LTV 확인 전 판단 불가"]])
    head(f"실행: 코치 → 복귀 캠페인·복귀 첫날 · 준비 2주 + 운영 {sc['decision']}주 (가정)", "효과 · 난도 · 데이터 접근성으로 우선순위 점검", b_mock())
    order = [("1차", "A", "다음 경기 코치", "신규 코칭 MVP · 공개 텔레메트리로 판정 · 매칭 변경 없음"),
             ("2차", "B", "복귀 캠페인 «야, 배그 한 판 할래?» · 복귀 첫날", "광고 3종 + 랜딩 · 광고 A/B(대조군 포함) · 복귀 첫날 친구와 3경기"),
             ("3차", "A", "첫 10경기 로드맵 · 매칭 품질 실험", "코치 결과 후 · 매칭 실험은 내부 데이터 확인 후"),
             ("4차", "C", "BM 내부 분석", "유저 화면 변경 없는 내부 분석 · 구매 만족도 설문")]
    with st.expander("자세히 보기 · 실행 순서 1~4차"):
        html('<ol class="pn-order">' + "".join(f'<li class="{t.lower()}"><span>{n}</span>{tr(t)}<b>{escape(k)}</b><small>{escape(d)}</small></li>'
                                               for n, t, k, d in order) + "</ol>")
    with st.expander(f"자세히 보기 · 비용 검산 (전체 합계 {won(c['A1_effort'] * c['monthly_cost_per_person'] + c['B1_ad_budget'] + c['B1_effort'] * c['monthly_cost_per_person'] + c['C_effort'] * c['monthly_cost_per_person'])} · 가정) · 성공·수정·중단 조건 · 채널 배분"):
        mp = c["monthly_cost_per_person"]
        a1, land, ad, cc = c["A1_effort"] * mp, c["B1_effort"] * mp, c["B1_ad_budget"], c["C_effort"] * mp
        b1 = ad + land
        assert abs(b1 - plan["b1_cost"]) < 1 and abs(a1 - plan["a1_cost"]) < 1 and abs(cc - plan["c_cost"]) < 1   # 화면 숫자 = 계산 모듈 숫자
        rows = [("다음 경기 코치 개발·운영", f"{c['A1_effort']}인월 × {mp / 1e4:,.0f}만 원", a1, ""),
                ("복귀 캠페인 광고·콘텐츠 (기존 제안 전액)", "디지털 50% · 옥외 30% · 콘텐츠 20% (04와 동일)", ad, ""),
                ("복귀 캠페인 추가 제작비", f"랜딩·UTM {c['B1_effort']}인월 × {mp / 1e4:,.0f}만 원", land, ""),
                ("복귀 캠페인 총액 (기존 제안)", "광고·콘텐츠 + 추가 제작비 · 보류", b1, "sub"),
                ("복귀 캠페인 권고 파일럿", "디지털 리타깃팅 50% + 추가 제작비 (05 사업성 판단)", ad * 0.5 + land, ""),
                ("BM 내부 분석", f"{c['C_effort']}인월 × {mp / 1e4:,.0f}만 원", cc, ""),
                ("전체 합계", "코치 + 캠페인 총액 + BM 분석", a1 + b1 + cc, "tot")]
        html('<div class="gp-table-wrap"><table class="gp-table pn-cost"><tr><th>항목</th><th>산출</th><th>금액</th></tr>' + "".join(
            f'<tr class="{k}"><td>{escape(n)}</td><td>{escape(f)}</td><td><b>{won(v)}</b></td></tr>' for n, f, v, k in rows) + "</table></div>")
        sub("성공 · 수정 · 중단 조건", b_mock())
        table(["결과", "다음 경기 코치", "복귀 캠페인 (+복귀 첫날)"],
              [["<b>확대</b>", "①②③ 모두 통과", "가장 좋은 광고가 ① 통과 + D30·획득 비용 ② + 가드레일 ③ → 그 메시지로 확대"],
               ["<b>수정</b>", f"① 유의 · ② 미달 (+{pm:.1f}%p 미만) → 코칭 항목·위치 수정", "복귀는 늘었지만 D30 낮음 → 복귀 첫날 경험 수정 · 채널 비중 조정"],
               ["<b>연장</b>", "판단 불가 → 1회 재실험", "판단 불가 → 휴면 기준 확대 후 재집행"],
               ["<b>중단</b>", f"효과 상한 &lt; +{pm:.1f}%p · 또는 ③ 악화", "모든 광고가 대조군과 차이 없음 · 또는 복귀자 신고율 악화"]])
        cp = ns["campaign"]
        assert cp["budget"] == ad and sum(w for _, _, w in cp["channels"]) == 100   # 채널 배분 합 = 광고비
        sub(f"기존 제안 복귀 캠페인 광고·콘텐츠 {won(ad)} · 채널 배분 (가정 · 권고는 디지털 파일럿)", b_sim())
        html('<div class="pn-budget">' + "".join(
            f'<div style="flex:{w} 1 0"><b>{w}%</b><span>{escape(n)}</span><small>{cp["budget"] * w / 100 / 1e4:,.0f}만 원</small></div>'
            for n, d, w in cp["channels"]) + f'</div><div class="pn-cav2">파일럿 {won(ad)} 안에서의 배분 · 추가 제작비 {won(land)} 별도 → 캠페인 총액 {won(b1)} · 버스 정류장은 옥외 30% 안에서 검토 · 가정</div>')
    html('<div class="pn-final">' + art(ns, "winner", "첫 치킨의 성취감 · 신규는 처음으로, 복귀 유저는 다시 한 번", "winner") +
         f'<div class="ow-conclusion"><div class="ow-conclusion-k">최종 사업PM 판단 {b_mock()}</div>'
         '<b>신규는 다음 경기 행동으로, 떠난 유저는 다시 낙하할 이유로.</b><br>'
         '다음 경기 코치 먼저 · 복귀 캠페인은 대조군과 비교해 복귀율과 D30을 함께 본다 · 핵 불신은 공정성 신뢰도로 측정 · C는 내부 분석'
         '<div class="pn-next"><b>다음 실험 판단</b> 코치 확대 시 → 첫 10경기 로드맵 별도 코호트 · 복귀 캠페인 확대 시 → 가장 좋은 메시지로 채널 비중 재배분</div></div></div>')
    with st.expander("자세히 보기 · 실행 일정 · 핵심 위험 · 후보 우선순위 점수 · 주차별 일정 · PPT 구성"):
        sub("실행 일정", b_mock())
        weeks = [("준비 (−2~0주)", "코치 판정 규칙·문구 검수 · 광고 3종·랜딩·UTM/QR 점검 · 휴면 대상 추출·4그룹 배정"),
                 (f"{sc['a_assign'][0]}~{sc['a_assign'][1]}주", "다음 경기 코치 배정 (신규 50:50)"),
                 (f"{sc['r_assign'][0]}~{sc['r_assign'][1]}주", f"복귀 캠페인 광고 집행 (휴면 4그룹 · 지하철·버스 정류장·PC방 병행) · {sc['a_d7']}주 코치 D7 판정"),
                 (f"{sc['r_assign'][1] + 1}~{sc['decision']}주", f"{sc['a_d30']}주 코치 D30 · {sc['r_return']}주 캠페인 복귀 로그인율 · {sc['r_d30']}주 캠페인 D30 · {sc['decision']}주 확대·수정·중단")]
        html('<div class="ow-timeline pg-tl">' + "".join(
            f'<div class="ow-tl"><div class="ow-tl-d">{escape(p)}</div><div class="ow-tl-b">{escape(w)}</div></div>' for p, w in weeks) + "</div>")
        sub("핵심 위험", b_interp())
        table(["위험", "대응"], [[escape(r["risk"]), escape(r["response"])] for r in ns["risks"]])
        lab = ns["score_labels"]
        table(["안", *lab.values(), "합계", "판단", "이유"],
              [[f"<b>{escape(ns['names'].get(p['key'], p['key']))}</b> <small>{p['key']}</small>", *[str(p["scores"][k]) for k in lab], f"<b>{sum(p['scores'].values())}</b>",
                f"<b>{escape(p['decision'])}</b>", escape(ns["mvp_reason"].get(p["key"], p["risk"]))] for p in ns["proposals"]],
              badge_html=b_interp())
        html(gantt(sc))
        html("<ol>" + "".join(f"<li>{escape(x)}</li>" for x in ns["ppt"]) + "</ol>")
    note("한계: 리뷰는 사례이고 기준값은 가정이다. 인과는 실험으로만 판단한다.")


def won(x: float) -> str:
    """원 단위 금액 → '1억 600만 원' · '2,700만 원'."""
    eok, man = int(x // 100_000_000), round((x % 100_000_000) / 10_000)
    if eok and man:
        return f"{eok}억 {man:,}만 원"
    return f"{eok}억 원" if eok else f"{man:,}만 원"


def gantt(sc: dict) -> str:
    W = sc["decision"]
    rows = [("다음 경기 코치 (신규)", {**{w: ("assign", "배정") for w in range(sc["a_assign"][0], sc["a_assign"][1] + 1)},
                                    sc["a_d7"]: ("d7", "D7 판정"), sc["a_d30"]: ("d30", "D30")}),
            ("복귀 캠페인 (휴면)", {**{w: ("assign", "배정") for w in range(sc["r_assign"][0], sc["r_assign"][1] + 1)},
                                    sc["r_return"]: ("d7", "복귀율"), sc["r_d30"]: ("d30", "D30")}),
            ("의사결정", {sc["a_d7"]: ("dec", "코치 1차"), sc["r_return"]: ("dec", "캠페인 1차"), W: ("dec", "최종")})]
    head_ = "".join(f"<th>{w}주</th>" for w in range(1, W + 1))
    body = "".join(f"<tr><th>{escape(n)}</th>" + "".join(
        f'<td class="{c[w][0]}">{escape(c[w][1])}</td>' if w in c else "<td></td>" for w in range(1, W + 1)) + "</tr>" for n, c in rows)
    return f'<div class="gp-table-wrap"><table class="ow-gantt"><tr><th>준비 2주 이후</th>{head_}</tr>{body}</table></div>'
