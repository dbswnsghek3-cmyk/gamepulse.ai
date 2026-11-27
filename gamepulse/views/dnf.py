"""던전앤파이터 — 노력은 남고, 성취는 이어져야 한다. (사업PM 포트폴리오 · 2026-11-27 개편 · 01~07 탭)

01 시장·서비스 · 02 BM·성장 구조 · 03 유저 VOC · 04 핵심 문제 · 05 개선 전략 3종 · 06 사업성·경제 시뮬 · 07 KPI·로드맵
- 사실·출처: data/dnf/dnf2.json (+ 기존 data/dnf/dnf.json 의 영상·보상 관찰·인터뷰·공식 자료) · VOC: data/dnf/voc.json
- 계산: gamepulse/sim/dnf_biz.py (정적 페이지 JS: scripts/dnf_static_widgets.py 와 같은 식)
- 작성자는 던파를 직접 플레이하지 않았다 · 지인 카톡은 이미지 비공개(이름·프로필 노출) · 원문 문구만 인용
- 이전 6탭 화면은 dnf_v1.py 에 보관
"""

from __future__ import annotations

import base64
import json
from collections import Counter
from html import escape
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from PIL import Image

from gamepulse.data.overwatch_images import web_jpeg_b64
from gamepulse.sim import dnf_biz as B   # gold() 는 ARAD CARE 백업용으로 남김 (archive/dnf_arad_care_backup)
from gamepulse.ui.brief import brief_html, chips_html, flow_html
from gamepulse.ui.components import html
from gamepulse.ui.gallery import gallery_html, pair_html
from gamepulse.views.fconline import _sim_inputs, js, js_end, mock, src
from gamepulse.views.overwatch import h, ox_chart_card, table

ROOT = Path(__file__).resolve().parents[2]
DATA, ASSETS = ROOT / "data" / "dnf", ROOT / "assets" / "dnf"
SECTIONS = [("01", "시장·서비스"), ("02", "BM·성장 구조"), ("03", "유저 VOC"), ("04", "핵심 문제"),
            ("05", "개선 전략 3종"), ("06", "사업성·경제 시뮬"), ("07", "KPI·로드맵")]
TAB_LABELS = [f"{n} {t}" for n, t in SECTIONS]
TAB_KEY = "df_tab"
RED, GRAY, GREEN = "#C62828", "#9CA3AF", "#16A34A"
REP = ["A", "F1", "IV13", "NB09", "IV11", "DC05"]   # 대표 VOC 6건 (출처 키 · 부정·중립·긍정 섞음)


@st.cache_data(show_spinner=False)
def load() -> tuple[dict, dict, dict]:
    return (json.loads((DATA / "dnf2.json").read_text(encoding="utf-8")), json.loads((DATA / "dnf.json").read_text(encoding="utf-8")),
            json.loads((DATA / "voc.json").read_text(encoding="utf-8")))


@st.cache_data(show_spinner=False)
def _img(rel: str, mtime: float) -> str:
    return web_jpeg_b64(str(ASSETS / rel), max_w=1400)


@st.cache_data(show_spinner=False)
def _png(rel: str, mtime: float) -> str:
    return base64.b64encode((ASSETS / rel).read_bytes()).decode()


def fig(im: dict, cls: str = "") -> str:
    p = ASSETS / im["file"]
    if not p.is_file():
        return ""
    return (f'<figure class="df2-fig {cls}"><img src="data:image/jpeg;base64,{_img(im["file"], p.stat().st_mtime)}" alt="{escape(im["cap"])}" loading="lazy">'
            f'<figcaption><b>공식 이미지</b>{escape(im["cap"])} · {src(im["url"], im["credit"])}</figcaption></figure>')


def ofig(im: dict, cls: str = "") -> str:
    """공식·실제 이미지 (확대 가능 · 출처·날짜 표기)."""
    p = ASSETS / im["file"]
    if not p.is_file():
        return ""
    return (f'<figure class="df2-fig {cls}"><details class="ox-zoom"><summary title="클릭하면 크게 보기"><img src="data:image/jpeg;base64,{_img(im["file"], p.stat().st_mtime)}" '
            f'alt="{escape(im["cap"])}" loading="lazy"></summary></details><figcaption><b>공식 자료</b>{escape(im["cap"])} · {src(im["url"], im["credit"])}</figcaption></figure>')


def vcard(f: str, title: str, ch: str, url: str, note: str) -> str:
    p = ASSETS / f
    im = f'<img src="data:image/jpeg;base64,{_img(f, p.stat().st_mtime)}" alt="{escape(title)} 썸네일" loading="lazy">' if p.is_file() else ""
    return (f'<a class="df2-yt" href="{escape(url, quote=True)}" target="_blank" rel="noopener">{im}<b>{escape(title)}</b>'
            f'<small>유튜브 · {escape(ch)} · {escape(note)} · 원본 영상 ↗</small></a>')


def gallery(key: str, items: list, folder: str = "evidence") -> str:
    slides = []
    for f, cap, credit in items:
        p = ASSETS / folder / f
        if p.is_file():
            slides.append((f'<img src="data:image/jpeg;base64,{_img(f"{folder}/{f}", p.stat().st_mtime)}" alt="{escape(cap)}" loading="lazy">', cap, credit))
    return gallery_html(key, slides) or ""


def _tab_from_query() -> str:
    q = str(st.query_params.get("tab", ""))
    return next((lab for lab in TAB_LABELS if lab.startswith(q.zfill(2)[:2])), TAB_LABELS[0]) if q else TAB_LABELS[0]


def _sync_tab_param() -> None:
    st.query_params["page"] = "dnf"
    st.query_params["tab"] = str(st.session_state.get(TAB_KEY, TAB_LABELS[0]))[:2]


def tab_nav() -> int:
    if st.session_state.get(TAB_KEY) not in TAB_LABELS:
        st.session_state[TAB_KEY] = _tab_from_query()
    sel = st.radio("섹션 선택", TAB_LABELS, key=TAB_KEY, horizontal=True, label_visibility="collapsed", on_change=_sync_tab_param)
    return TAB_LABELS.index(sel)


def gfmt(x: float, sign: bool = False) -> str:
    a, s = abs(x), ("−" if x < 0 else ("+" if sign and x > 0 else ""))
    return f"{s}{a / 1e8:,.2f}억 골드" if a >= 1e8 else f"{s}{a / 1e4:,.0f}만 골드"


def render() -> None:
    d, old, _v = load()
    cv = d["cover"]
    lp = ASSETS / "logo.png"
    logo = f'<img class="df-logo" src="data:image/png;base64,{_png("logo.png", lp.stat().st_mtime)}" alt="던전앤파이터 로고">' if lp.is_file() else ""
    html('<div class="gp-ow-page gp-dnf-page"></div>')
    html(f'<div class="df2-hero"><div class="df2-hero-t"><span>{escape(cv["kicker"])}</span><b role="heading" aria-level="1">{escape(cv["title"])}</b>'
         f'<p>{escape(cv["subtitle"])}</p><small>{escape(cv["note"])}</small></div>{logo}</div>')
    html('<div class="df2-w">' + "".join(f'<div style="flex:{w} 1 0"><b>{escape(n)}</b><span>{w}% · {escape(t)}</span></div>' for n, w, t in d["weights"])
         + f'</div><p class="df2-wn">{escape(d["weights_note"])}</p>')
    i = tab_nav()
    html('<div class="ox-legend"><b>실제 자료</b>만 확인된 사실 · 분석자 해석 · 검증 전 가설 · 기획 시안 · 가정 시뮬레이션은 실적이 아님</div>')
    html(f'<div class="ow-pane-mark" data-tab="{SECTIONS[i][0]}"></div>')
    [t1, t2, t3, t4, t5, t6, t7][i](d, old)
    st.caption(f"{old['disclaimer']} · 자료 확인일 {d['checked_at']}")


# ----------------------------------------------------------------------
def t1(d: dict, old: dict) -> None:
    h("시즌 11 천해천 · 최상위 콘텐츠는 확률 보상 · 개발진은 보상 보강 방향을 발표했다", "real", num="01", name="시장 및 서비스 분석",
      lead="2026-11-27 기준 공식 자료·보도로 확인 · 작성자는 직접 플레이하지 않음")
    html(fig(old["hero_img"], "hero"))
    html('<div class="df2-facts">' + "".join(f'<div><span>{escape(k)}</span><b>{escape(v)}</b><small>{escape(n)} · {src(u, s)}</small></div>'
                                             for k, v, n, s, u in d["market"]["facts"]) + "</div>")
    h("던파의 강점 · 오래 사랑받은 이유", "real", lead="공식 자료·보도·유저 글 근거 · 이 강점 위에 기획을 더한다")
    html('<div class="df2-str">' + "".join(f'<div><span>{escape(a)}</span><p>{escape(b)}</p><small>{src(u, c)}</small></div>' for a, b, c, u in d["strengths"]) + "</div>")
    html(f'<div class="ox-purpose"><span>사업PM 해석</span>{escape(d["market"]["pm"])}</div>')


def t2(d: dict, old: dict) -> None:
    h("성장은 '확률 보상 + 일부 교환'으로 돌아가고, 수리비는 골드를 회수하는 장치다", "real", num="02", name="기존 BM 및 성장 구조",
      lead="공식 가이드·공지·보도 기준 · 유료 상품과 게임 내 골드 소비를 나눠 본다")
    html(flow_html([(escape(a), escape(b)) for a, b, _ in d["growth"]], title="고난도 성장 구조 (2026-11) · 보장 문구가 있는 콘텐츠는 확인 못함"))
    html('<div class="df2-pair">' + ofig(d["img"]["mikaela"]) + ofig(d["img"]["nightmare"]) + "</div>")
    table(["콘텐츠", "보상 방식 (공식 · 보도)", "출처"], [[f"<b>{escape(a)}</b>", escape(b), escape(c)] for a, b, c in d["growth"]], cls="ox-mops")
    html(fig(old["reward_img"], "sm"))
    h("BM: 현금 상품과 골드 소비를 구분한다", "interp", lead=escape(d["bm_note"]))
    table(["구분", "결제 수단", "내용", "확인 수준"], [[f"<b>{escape(a)}</b>", escape(b), escape(c), escape(e)] for a, b, c, e in d["bm"]], cls="ox-mops")
    html('<div class="df2-pair">' + ofig(d["img"]["seria"]) + ofig(d["img"]["mileage"]) + "</div>")
    rp = d["repair"]
    h("수리비 · 이미 있었던 개선과 지금의 지원", "real", lead=escape(rp["pm"]))
    html('<div class="df2-tl">' + "".join(f'<div><em>{escape(a)}</em><p>{escape(b)}</p><small>{src(u, s)}</small></div>' for a, b, s, u in rp["facts"]) + "</div>")
    html(f'<div class="ox-purpose fx-risk"><span>확인 못한 것</span>{escape(rp["unverified"])}</div>')


VOC_CH = ["유튜브 댓글", "공식 게시판", "인벤", "디시 던파IP 갤러리"]


def t3(d: dict, old: dict) -> None:
    _d, _o, v = load()
    items = [x for x in v["items"] if x["channel"] != "지인 인터뷰"]
    cats, srcs = v["categories"], v["sources"]
    ch = Counter(x["channel"] for x in items)
    tone = Counter(x["stance"] for x in items)
    h(f"공개 VOC {len(items)}건: 보상·시즌에 대한 아쉬움과 함께 클리어 성취·다음 시즌 기대도 있다", "real", num="03", name="실제 VOC 및 유저 여론",
      lead="원문을 직접 확인한 글·댓글 단위 · 작성자 비공개 · 표본 분포는 전체 이용자 여론이 아님")
    html('<div class="df2-ch">' + "".join(f'<div><b>{ch.get(c, 0)}</b><span>{escape(c)}</span></div>' for c in VOC_CH)
         + '<div class="x"><b>0</b><span>아카라이브 (접근 차단)</span></div></div>')
    order = [c for c, _ in Counter(x["cat"] for x in items).most_common()]
    names = [cats[str(c)] for c in order]
    f = go.Figure([go.Bar(y=names, x=[sum(1 for x in items if x["cat"] == c and x["stance"] == t) for c in order], name=t, orientation="h", marker_color=col)
                   for t, col in (("부정", RED), ("질문", "#F59E0B"), ("제안", "#64748B"), ("중립", GRAY), ("긍정", GREEN))])
    f.update_layout(barmode="stack")
    f.update_yaxes(autorange="reversed", automargin=True)
    f.update_xaxes(title="건")
    ox_chart_card(f, key="dfvoc", kind="real", title=f"주제별 VOC · 부정 {tone['부정']} · 질문 {tone['질문']} · 제안 {tone['제안']} · 중립 {tone['중립']} · 긍정 {tone['긍정']}",
                  unit="건 · 한 의견은 주제 1개", kpis=[], analysis="", decision="", basis="", height=420, cols=("주제", "건"), series="성향")
    by_src = {}
    for x in items:
        by_src.setdefault(x["src"], x)
    reps = [by_src[k] for k in REP if k in by_src]
    html('<div class="gb-flow-t">대표 VOC 6건 · 부정·중립·긍정을 함께</div><div class="fx-vocs six">' + "".join(
        f'<div class="t-{ {"부정": "n", "긍정": "p"}.get(x["stance"], "z") }"><span>{escape(x["channel"])} · {escape(cats[str(x["cat"])])} · {escape(x["stance"])}</span>'
        f'<b>{escape(x["summary"])}</b><small>{escape(x["date"])} · {src(srcs[x["src"]][1], "원문 ↗") if srcs[x["src"]][1] else escape(srcs[x["src"]][0])}</small></div>'
        for x in reps) + "</div>")
    with st.expander(f"VOC {len(items)}건 전체 · 채널·주제·성향 필터 · 원문 링크"):
        js("dfvoc")
        c1, c2, c3 = st.columns(3)
        s_ch = c1.selectbox("채널", ["전체"] + VOC_CH, key="df_voc_ch")
        s_cat = c2.selectbox("주제", ["전체"] + names, key="df_voc_cat")
        s_t = c3.selectbox("성향", ["전체", "부정", "질문", "제안", "중립", "긍정"], key="df_voc_t")
        rows = [x for x in items if (s_ch == "전체" or x["channel"] == s_ch) and (s_cat == "전체" or cats[str(x["cat"])] == s_cat) and (s_t == "전체" or x["stance"] == s_t)]
        table(["번호", "채널 · 날짜", "출처", "요약", "주제", "성향"],
              [[x["id"], f'{escape(x["channel"])}<br><small>{escape(x["date"])}</small>',
                src(srcs[x["src"]][1], srcs[x["src"]][0][:40]) if srcs[x["src"]][1] else escape(srcs[x["src"]][0]),
                escape(x["summary"]), escape(cats[str(x["cat"])]), escape(x["stance"])] for x in rows], cls="ox-mops fx-voc")
        js_end()
        st.caption(f'{v["collect"]["blocked"]} · {v["collect"]["dropped"]} · {v["collect"]["note"]} · 유튜브 댓글 작성일은 캡처(2026-11-23) 화면의 상대 표기')
    fr = old["friend"]
    h("현역 이용자 1명 인터뷰 (카카오톡 · 공개 표본과 별도)", "real", lead="1명의 개인 경험 · 대표 의견이 아님 · 캡처에 이름·프로필이 있어 이미지는 공개하지 않고 원문 문구만 인용")
    table(["질문 상황", "원문", "해석 (분석자)"], [[escape(a), f"<b>“{escape(b)}”</b>", escape(c)] for a, b, c in fr["items"]], cls="ox-mops")
    h("유튜브 댓글 원본 캡처 · 실제 레이드 장면", "real", lead="기존에 받은 댓글 캡처(2026-11-23 · 아이디·아바타 블러) · 제3자 유저 영상 캡처 (본인 플레이 아님)")
    html('<div class="df2-src">' + "".join(f'<a href="{escape(u, quote=True)}" target="_blank" rel="noopener"><span>유튜브 영상 댓글 · 캡처 출처</span><b>{escape(c)} 채널</b><small>원본 영상 ↗</small></a>'
                                          for c, u in d["videos"]) + f'</div><p class="fx-pod-n">{escape(d["video_note"])}</p>')
    html(quotes_html(d["season_quotes"]))
    with st.expander("장문 댓글 원문 전체 (발췌하지 않은 원본 캡처)"):
        html(gallery("dfq", d["season_quotes"]["full"]))
    with st.expander("보상 체감 댓글 원본 캡처"):
        html(gallery("dfev", old["evidence_images"]))
    m = old["media"]
    slides, ratios = [], []
    for fn, cap, credit in m["shots"]:
        p = ASSETS / fn
        if p.is_file():
            with Image.open(p) as im:
                ratios.append(im.width / im.height)
            slides.append((f'<img src="data:image/jpeg;base64,{_img(fn, p.stat().st_mtime)}" alt="{escape(cap)}" loading="lazy">', cap, credit))
    html(pair_html("dfscene", slides, ratios))
    html(f'<p class="fx-pod-n">{escape(m["clear"]["title"])} · {src(m["video_url"], "원본 영상")} · 한 번의 클리어 영상으로 전체 유저의 경험을 단정하지 않음</p>')


def t4(d: dict, old: dict) -> None:
    h("투자 → 보상 편차 → 성취감 저하 → 시즌 불안 → 소통 공백 → 재도전 동기 약화", "hypo", num="04", name="핵심 문제 정의",
      lead="유저 의견과 공식 구조로 만든 가설 흐름 · 모든 유저에게 같은 인과가 생긴다고 단정하지 않는다")
    html(flow_html([(escape(a), escape(b)) for a, b in d["problem_flow"]], hl=2))
    h("문제별 현재 상태 · 이미 개선된 것은 미해결로 쓰지 않는다", "real", lead="과거 · 지속 · 운영진 인지 · 개선 발표 · 개선 적용 · 추가 검증 필요")
    h("운영진이 이미 개선했거나 발표한 것", "real", lead=escape(d["done_note"]))
    html('<div class="df2-done">' + "".join(f'<div><span>✓ {escape(a)}</span><p>{escape(b)}</p></div>' for a, b in d["done_well"]) + "</div>")
    with st.expander("문제별 상태표 · 과거·지속·인지·발표·적용·검증 필요"):
        table(["문제", "발생", "운영진 인지", "개선 상태", "근거"], [[f"<b>{escape(a)}</b>", escape(b), escape(c), escape(e), escape(f)] for a, b, c, e, f in d["status"]],
              cls="ox-mops")
    html('<div class="df2-w big">' + "".join(f'<div style="flex:{w} 1 0"><b>{escape(n)}</b><span>{w}% · {escape(t)}</span></div>' for n, w, t in d["weights"]) + "</div>")
    st.caption(d["weights_note"])


def _ach_ui() -> str:
    cells = "".join(f'<i class="{"on" if k < 14 else ""}"></i>' for k in range(20))
    return mock("PROJECT ACHIEVEMENT · 레이드 클리어 결과 · 가상 기획 UI (실제 던파 화면 아님)", (
        '<div class="df2-ach"><div class="df2-ach-l"><span>무너진 성자 미카엘라 · 하드</span><b>클리어 · 29분 26초</b>'
        '<div class="df2-ach-r"><em>이번 보상</em><p>여명의 빛망울 ×180 · 서약 결정 ×2 <small>(확률 보상 · 기존과 동일)</small></p></div></div>'
        f'<div class="df2-ach-m"><span>누적 진행도 · 목표: 축성 업그레이드 재료</span><div class="df2-cells">{cells}</div>'
        '<b>14 / 20</b><small>다음 확정 보상까지 6회 · 확정 보상은 교환 불가</small>'
        '<div class="df2-rec"><div><em>일반</em><b>9회</b></div><div><em>하드</em><b>5회</b></div><div><em>각인된 악몽</em><b>80%</b></div></div></div></div>'), "night")


def _legacy_ui() -> str:
    return mock("SEASON LEGACY · 나의 시즌 기록 · 가상 기획 UI", (
        '<div class="df2-leg"><div><span>시즌 11 천해천 · 나의 기록</span><b>하드 레이드 클리어 14회</b><small>최고 기록 · 각인된 악몽 상위 30% · 대표 업적 3개</small></div>'
        '<div><span>시즌별 성장 이력</span><p>시즌 10 중천 · 레이드 9회 → 시즌 11 · 14회</p><small>성능이 아니라 기록·칭호로 남김</small></div>'
        '<div class="n"><span>다음 시즌 예고 (던파 페스티벌 공개 후)</span><b>새 지역 · 새 목표 3개</b><small>복귀 유저용 변화 요약 · 준비 현황 체크</small></div></div>'), "night")


def _retrust_ui(rt: dict) -> str:
    stg = rt["stages"]
    rows = "".join(f'<div class="{k}"><span>{escape(a)}</span><b>{escape(b)}</b><em>{escape(c)}</em><small>{escape(e)}</small></div>'
                   for a, b, c, e, k in rt["board"])
    return mock("DNF RE:TRUST · 운영 개선 현황판 · 가상 기획 UI (파란 표시 = 공식 발표 · 회색 = 가상 예시)", (
        f'<div class="df2-rt"><div class="df2-rt-s">{"".join(f"<i>{escape(s)}</i>" for s in stg)}</div><div class="df2-rt-b">{rows}</div></div>'), "night")


def t5(d: dict, old: dict) -> None:
    P = d["plans"]
    a, lg, rt = P["achievement"], P["legacy"], P["retrust"]
    html('<div class="gb-flow-t">3개 전략의 기대 사업 효과 (검증 전 목표) · 작성자 우선순위 50 · 30 · 20</div><div class="df2-eff">'
         + "".join(f'<div><span>{escape(n)}</span><b>{escape(e)}</b><small>{escape(g)}</small></div>' for n, e, g in d["effects"]) + "</div>")
    h(f"{a['name']} · {a['slogan']}", "mock", num="05", name="대표 개선 전략 ① 성취감 · 랜덤 보상 (50%)", lead="랜덤 보상의 재미는 남기고, 노력의 누적을 보이게 한다")
    html(brief_html(*a["brief"], name=a["name"], tag="기획 시안"))
    html(_ach_ui())
    html('<div class="df2-pair">' + ofig(d["img"]["result"]) + vcard(*d["video_official"]) + "</div>")
    table(["기존 장치 (공식·유저 글)", "하는 일", "남는 문제"], [[f"<b>{escape(x)}</b>", escape(y), escape(z)] for x, y, z in a["exist"]], cls="ox-mops")
    html(chips_html("추가 제안", a["new"], "kpi"))
    html(f'<div class="ox-purpose fx-risk"><span>경제 영향</span>{escape(a["risk"])} → 06 탭 시뮬레이터</div>')

    h(f"{lg['name']} · {lg['slogan']}", "mock", num="05", name="대표 개선 전략 ② 시즌 기대 · 성장 가치 (30%)", lead="시즌제는 유지 · 성능이 아니라 기록과 기대를 잇는다")
    html(brief_html(*lg["brief"], name=lg["name"], tag="기획 시안"))
    html(flow_html([(escape(x), escape(y)) for x, y in lg["flow"]], title="시즌 전환 마케팅 흐름", hl=2))
    html(_legacy_ui())
    html(f'<div class="ox-purpose"><span>기존과의 차이</span>{escape(lg["exist"])} · {escape(lg["avoid"])}</div>')
    html(f'<p class="fx-pod-n">근거: 03 탭 장문 댓글 발췌 · {escape(d["season_quotes"]["pm"])}</p>')

    h(f"{rt['name']} · {rt['slogan']}", "mock", num="05", name="대표 개선 전략 ③ 운영 소통 (20%)", lead="방송·개발자 노트의 발표를 진행 상황까지 한곳에")
    html(brief_html(*rt["brief"], name=rt["name"], tag="기획 시안"))
    html(_retrust_ui(rt))
    html(f'<p class="fx-pod-n">{escape(rt["note"])} · {escape(rt["avoid"])}</p>')


def reward_html(r: dict) -> str:
    b, n = r["base"], r["new"]
    sp = "—" if r["supply_pct"] is None else f'{"+" if r["supply_pct"] >= 0 else "−"}{abs(r["supply_pct"]):,.1f}%'
    neg = "neg" if r["supply_pct"] is not None and r["supply_pct"] > 5 else ""
    return (f'<div class="ox-res"><div class="acc"><span>한 번도 못 얻을 확률</span><b>{b["zero"]:,.2f}% → {n["zero"]:,.2f}%</b>'
            f'<small>참여 {r["x"]["users"]:,.0f}명 중 {r["zero_users0"]:,.0f}명 → {r["zero_users"]:,.0f}명</small></div>'
            f'<div><span>1인 평균 획득</span><b>{b["mean"]:,.2f} → {n["mean"]:,.2f}개</b><small>{r["x"]["n"]:,.0f}회 플레이 기준</small></div>'
            f'<div><span>획득 편차 (표준편차)</span><b>{b["sd"]:,.2f} → {n["sd"]:,.2f}</b><small>작을수록 운 차이가 작음</small></div>'
            f'<div class="{neg}"><span>보상 공급 증가</span><b>{sp}</b><small>총 {b["supply"]:,.0f} → {n["supply"]:,.0f}개 · 가드레일 +5%</small></div></div>'
            f'<div class="df2-bars"><div><span>현행 (확률만)</span><i style="width:{min(b["zero"], 100):.1f}%"></i><b>{b["zero"]:,.2f}%</b></div>'
            f'<div class="n"><span>제안 (누적 보장)</span><i style="width:{min(n["zero"], 100):.1f}%"></i><b>{n["zero"]:,.2f}%</b></div><small>막대 = 한 번도 못 얻는 유저 비율</small></div>')


def quotes_html(q: dict) -> str:
    return ('<div class="df2-q"><span>장문 댓글 핵심 3줄 · 원문 발췌</span>' + "".join(f"<p>“{escape(x)}”</p>" for x in q["lines"])
            + f'<small>{escape(q["src"])}</small></div>')


def t6(d: dict, old: dict) -> None:
    S = d["sims"]
    h("누적 보장은 '못 얻는 유저'를 0으로 만들지만 공급은 늘어난다", "sim", num="06", name="사업성 및 게임 경제 시뮬레이션", lead=escape(S["reward"]["note"]))
    js("dfreward")
    box = st.container()
    r = B.reward(S["reward"], _sim_inputs("dr_", S["reward"], "가정값 바꾸기 · 확률 · 플레이 · 보장 횟수 · 확률 상승 · 수량 · 유저 수"))
    with box:
        html(reward_html(r))
    js_end()
    html('<div class="ox-purpose"><span>사업PM 판단</span>확정 보상 공급이 +5%를 넘으면 장비 가치 하락·콘텐츠 소진이 빨라질 수 있다 → K를 늘리거나 확정 보상을 '
         '교환 불가 재료로 제한 · 확률 상승 구간은 보장 직전에만</div>')


def t7(d: dict, old: dict) -> None:
    h(f"판단: {d['decision']}", "mock", num="07", name="KPI 및 실행 로드맵", lead=escape(d["tests_note"]))
    html('<div class="df2-kpi">' + "".join(f'<div><span>{escape(g)}</span>' + "".join(f"<i>{escape(k)}</i>" for k in ks) + "</div>" for g, ks in d["kpis"]) + "</div>")
    table(["기획", "실험 방식", "주요 지표", "부작용 감시"], [[f"<b>{escape(a)}</b>", escape(b), escape(c), escape(e)] for a, b, c, e in d["tests"]], cls="ox-mops")
    html(flow_html([(escape(a), f"{escape(b)} · {escape(c)}") for a, b, c in d["roadmap"]], title="실행 로드맵 (가정 · 실제 일정 아님)", hl=0))
    table(["리스크", "대응"], [[f"<b>{escape(a)}</b>", escape(b)] for a, b in d["risks"]], cls="ox-mops")
    with st.expander("추가로 필요한 실제 자료 · 확보하지 못한 이미지"):
        html("<ul class='ox-facts'>" + "".join(f"<li>{escape(x)}</li>" for x in d["need"]) + "</ul>")
        html("<ul class='ox-facts'>" + "".join(f"<li>이미지 미확보 · {escape(x)}</li>" for x in d["img_missing"]) + "</ul>")
