"""오버워치 페이지 — PROJECT RE:START (채용 담당자가 3~5분 안에 핵심을 보도록 구성).

구성
- 표지: 제목 → 핵심 문제 → 핵심 해결 큰 카드 → 01~06 이동 메뉴 → 최신 영웅 선택 화면(크게)
- 01 문제 정의: 문제 문장 · PM 의사결정 요약 · 근거 3단계(관찰 사실/이용자 의견/검증 전 가설) · 사업PM 관점 중요성
- 02 실제 근거: 게임 화면 · 유저 의견(표본·분류 기준) · 공식 업데이트 · 이용 지표
- 03 원인 가설 · 04 개선안(A·B·C 사양 카드 · 단계적 출시 · 실제 화면 vs 기획 시안)
- 05 KPI·A/B 테스트(정의·단계적 실험·MDE·표본·일정·판단 기준·가정 시뮬레이션) · 06 실행·제안
- 가정값은 data/overwatch/restart.json 'experiment' 한 곳에서 읽어 KPI 목표·표본·시뮬레이션·일정을 일치시킨다.

배지 (텍스트로도 구분): 실제 자료 · 분석자 해석 · 검증 전 가설 · 기획 시안 · 가정 시뮬레이션 · 예시 데이터

이미지 원칙
- 게임 화면은 data/overwatch/image_manifest.json 검증(한국어 UI·최신 패치 이후 촬영·출처·16:9·54명)을
  통과한 파일만 표시한다. 통과 전에는 '최신 한국어 스크린샷 필요' 자리를 보여 준다.
- 실제 화면은 남색 실선 프레임 + '실제 게임 화면' 태그, 기획 시안은 주황 점선 + '기획 시안 · 실제 게임에 없음' 리본.
- 다른 플레이어 닉네임은 manifest 의 blur 영역을 표시할 때만 가린다 (원본 파일은 그대로).
- 캐릭터 그림을 임의로 만들지 않는다. 영웅은 공식 영웅 페이지의 이름으로만 표시한다.
- React DOM 과 충돌하지 않도록 DOM 을 직접 조작하는 스크립트를 쓰지 않는다 (정적 마크업 + Streamlit 위젯만 사용).
"""

from __future__ import annotations

import base64
import math
import os
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from gamepulse.config import COLORS as C
from gamepulse.content.games import GAMES
from gamepulse.data.overwatch_data import (COLLECTED_AT, OPINION_CATEGORIES, STEAM_SOURCE, USER_TYPES, OverwatchDataError,
                                          load_json, load_opinions, load_pcbang, load_steam, load_timeline, opinion_codes)
from gamepulse.data.overwatch_images import all_status, load_manifest, web_jpeg_b64
from gamepulse.sim.restart_sim import (CohortInput, SimInput, experiment_plan, rice_table, run,
                                       sample_size_two_proportions, validate_base)
from gamepulse.ui.charts import PLOTLY_CONFIG, style
from gamepulse.ui.components import badge, html
from gamepulse.views import game_page
from gamepulse.views.deep_dives import DEEP_DIVES

SECTIONS = [("01", "개요·핵심 문제", "섹션 01·02"), ("02", "게임 화면·VOC", "섹션 03·04"),
            ("03", "PROJECT RE:START", "섹션 05"), ("04", "기존 스킨 BM", "섹션 06"),
            ("05", "신규 BM 제안", "섹션 07·08"), ("06", "KPI·사업성", "섹션 09"),
            ("07", "최종 판단", "섹션 10")]
ROOT_DIR = Path(__file__).resolve().parents[2]
TAB_LABELS = [f"{n} {t}" for n, t, _ in SECTIONS]
TAB_KEY = "ow_tab"


def _tab_from_query() -> str:
    q = str(st.query_params.get("tab", ""))
    return next((lab for lab in TAB_LABELS if lab.startswith(q.zfill(2)[:2])), TAB_LABELS[0]) if q else TAB_LABELS[0]


def _sync_tab_param() -> None:
    st.query_params["page"] = "overwatch"
    st.query_params["tab"] = str(st.session_state.get(TAB_KEY, TAB_LABELS[0]))[:2]


def tab_nav() -> int:
    """01~06 탭 전환: 고른 섹션 하나만 그린다 (스크롤 이동 없음). 주소 ?tab=04 로 바로 열 수 있다."""
    if st.session_state.get(TAB_KEY) not in TAB_LABELS:
        st.session_state[TAB_KEY] = _tab_from_query()
    sel = st.radio("섹션 선택", TAB_LABELS, key=TAB_KEY, horizontal=True, label_visibility="collapsed",
                   on_change=_sync_tab_param)
    return TAB_LABELS.index(sel)
LEARNING_CODES = {"영웅·스킬 학습 부담", "상대 영웅 대응 이해 부족", "복귀 적응·변경점 파악", "전투 중 정보 과부하"}


# ----------------------------------------------------------------------
# 표시 헬퍼 · 배지는 색상과 텍스트 모두로 구분
def b_real() -> str:
    return badge("실제 자료", "k-real")


def b_interp() -> str:
    return badge("분석자 해석", "k-interp")


def b_hypo() -> str:
    return badge("검증 전 가설", "k-hypo")


def b_mock() -> str:
    return badge("기획 시안", "k-mock")


def b_sim() -> str:
    return badge("가정 시뮬레이션", "k-sim")


def b_sample() -> str:
    return badge("예시 데이터", "k-sample")


KIND = {"real": b_real, "interp": b_interp, "hypo": b_hypo, "mock": b_mock, "sim": b_sim, "sample": b_sample}


def b_plan() -> str:  # 실행 계획·제안도 실제로 시행된 것이 아니므로 '기획 시안'
    return b_mock()


def section(i: int) -> None:
    n, title, desc = SECTIONS[i]
    html(f'<div class="ow-sec" id="ow-s{n}"><div class="ow-sec-n">{n}</div><div class="ow-sec-t"><h2>{escape(title)}</h2>'
         f'<p>{escape(desc)}</p></div><a class="ow-sec-top" href="#ow-nav" target="_self">↑ 메뉴</a></div>')


def nav() -> None:
    items = "".join(
        f'<a class="ow-nav-i{" hot" if n == "04" else ""}" href="#ow-s{n}" target="_self">'
        f'<b>{n}</b><span>{escape(t)}<small>{escape(d)}</small></span></a>' for n, t, d in SECTIONS)
    html(f'<nav class="ow-nav" id="ow-nav" aria-label="섹션 이동">{items}</nav>')


def badge_legend() -> None:
    """배지 뜻은 한 줄로: '실제 자료'만 사실, 나머지는 해석·가설·제안·가정 계산."""
    html(f'<div class="ow-badges"><span>{b_real()} 만 확인된 사실</span>'
         f'<span>{b_hypo()} {b_mock()} {b_sim()} 은 검증 전 · 실적 아님</span></div>')


def ox_badge_legend() -> None:
    """자료 성격 안내는 페이지에 한 번만 (섹션 제목 옆 작은 글자와 같은 표기)."""
    html('<div class="ox-legend"><b>실제 자료</b>만 확인된 사실 · 분석자 해석 · 검증 전 가설 · 기획 시안 · 가정 시뮬레이션은 실적이 아님</div>')


@st.cache_data(show_spinner=False, max_entries=4)
def _png_b64(path: str, mtime: float) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("ascii")


def link(url: str, text: str) -> str:
    return f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener">{escape(text)}</a>'


def head(title: str, lead: str = "", tag: str = "") -> None:
    p = f"<p>{escape(lead)}</p>" if lead else ""
    html(f'<div class="ow-head"><h3>{escape(title)} {tag}</h3>{p}</div>')


def sub(title: str, tag: str = "") -> None:
    html(f'<div class="ow-sub">{escape(title)} {tag}</div>')


def note(text: str) -> None:
    html(f'<div class="ow-line">{escape(text)}</div>')


def tiles(items: list[tuple[str, str, str]]) -> None:
    html('<div class="ow-tiles">' + "".join(
        f'<div class="ow-tile"><div class="ow-tile-l">{escape(l)}</div><div class="ow-tile-v">{v}</div>'
        f'<div class="ow-tile-s">{s}</div></div>' for l, v, s in items) + "</div>")


def table(headers: list[str], rows: list[list[str]], badge_html: str = "", cls: str = "") -> None:
    """표: 배지를 표 바로 위에 붙이고, 모바일에서는 좌우 스크롤 안내를 보여 준다."""
    if not rows:
        st.info("표시할 자료가 없습니다.")
        return
    th = "".join(f"<th>{escape(h)}</th>" for h in headers)
    # data-label: 모바일에서는 행을 카드로 쌓고 각 칸 앞에 열 이름을 표시 (가로 스크롤·글자 잘림 방지)
    body = "".join("<tr>" + "".join(f'<td data-label="{escape(h, quote=True)}">{c}</td>' for h, c in zip(headers, r)) + "</tr>"
                   for r in rows)
    top = f'<div class="ow-table-b">{badge_html}</div>' if badge_html else ""
    html(f'{top}<div class="gp-table-wrap"><table class="gp-table ow-table {cls}"><tr>{th}</tr>{body}</table></div>')


def bullets(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{escape(x)}</li>" for x in items) + "</ul>"


def legend_bottom(fig: go.Figure, xtitle: bool = True) -> go.Figure:
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.25 if xtitle else -0.12, x=0, title_text=""),
                      margin=dict(b=40))
    return fig


def plot(fig: go.Figure) -> None:
    st.plotly_chart(fig, config=PLOTLY_CONFIG)


# 차트 색상 규칙 (모든 차트 공통)
#   실제 자료 강조 = 파랑 · 실제 자료 보조 = 연회색
#   대조군·도입 전·현재(가정) = 회색 · 실험군·도입 후·적용(가정) = 파랑
C_TREAT, C_CTRL, C_MUTED = "#2563EB", "#94A3B8", "#CBD5E1"


def chart_card(fig: go.Figure, *, key: str, kind: str, title: str, unit: str, kpis: list[tuple[str, str]],
               analysis: str, decision: str, basis: str, height: int = 360, legend: bool = True,
               cols: tuple[str, str] = ("항목", "값"), series: str = "구분") -> None:
    """차트 1개 = 배지·제목·단위 → 핵심 수치 → 차트 → 분석 결과 · 사업PM 의사결정 · 비교 기준.

    kpis 의 값(value)은 HTML 을 허용한다(호출하는 쪽에서 숫자만 넣음).
    cols = (범주 열 이름, 값 열 이름): 정적 보고서의 '차트 데이터 표' 열 제목으로 쓰인다 (layout.meta).
    """
    fig.update_layout(meta={"table": {"category": cols[0], "value": cols[1], "series": series, "title": title}})
    with st.container(border=True, key=f"owc_{key}"):
        chips = "".join(f'<div class="ow-kpi"><div class="ow-kpi-v">{v}</div><div class="ow-kpi-l">{escape(l)}</div></div>'
                        for l, v in kpis)
        html(f'<div class="ow-chart-h"><div class="ow-chart-t">{KIND[kind]()} {escape(title)}</div>'
             f'<div class="ow-chart-u">{escape(unit)}</div></div>' + (f'<div class="ow-kpis">{chips}</div>' if chips else ""))
        style(fig, None, height)
        fig.update_layout(title=None, margin=dict(l=8, r=20, t=44 if legend else 12, b=44),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text="", font=dict(size=12)),
                          showlegend=legend, font=dict(size=13))
        plot(fig)
        # 차트 아래는 '사업PM 판단' 한 줄 + 해석·비교 기준 작은 한 줄 (핵심 수치는 차트 위 칩과 중복되므로 합침)
        html(f'<div class="ow-chart-f2"><div class="pm"><b>사업PM 판단</b><span>{escape(decision)}</span></div></div>'
             f'<div class="ow-chart-b">{escape(analysis)} · 기준: {escape(basis)}</div>')


def ox_chart_card(fig: go.Figure, *, key: str, kind: str, title: str, unit: str, kpis: list[tuple[str, str]],
               analysis: str, decision: str, basis: str, height: int = 360, legend: bool = True,
               cols: tuple[str, str] = ("항목", "값"), series: str = "구분") -> None:
    """차트 1개 = 배지·제목·단위 → 핵심 수치 → 차트 → 분석 결과 · 사업PM 의사결정 · 비교 기준.

    kpis 의 값(value)은 HTML 을 허용한다(호출하는 쪽에서 숫자만 넣음).
    cols = (범주 열 이름, 값 열 이름): 정적 보고서의 '차트 데이터 표' 열 제목으로 쓰인다 (layout.meta).
    """
    fig.update_layout(meta={"table": {"category": cols[0], "value": cols[1], "series": series, "title": title}})
    with st.container(border=True, key=f"owc_{key}"):
        chips = "".join(f'<div class="ow-kpi"><div class="ow-kpi-v">{v}</div><div class="ow-kpi-l">{escape(l)}</div></div>'
                        for l, v in kpis)
        kt = {"real": "실제 자료", "interp": "분석자 해석", "hypo": "검증 전 가설", "mock": "기획 시안", "sim": "가정 시뮬레이션",
              "sample": "예시 데이터"}[kind]
        html(f'<div class="ow-chart-h"><div class="ow-chart-t">{escape(title)} <span class="ox-k {kind}">{kt}</span></div>'
             f'<div class="ow-chart-u">{escape(unit)}</div></div>' + (f'<div class="ow-kpis">{chips}</div>' if chips else ""))
        style(fig, None, height)
        fig.update_layout(title=None, margin=dict(l=8, r=20, t=44 if legend else 12, b=44),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text="", font=dict(size=12)),
                          showlegend=legend, font=dict(size=13))
        plot(fig)
        # 개편: 제목 자체가 결론 → '사업PM 판단' 박스는 decision 이 있을 때만 · 해석·기준은 작은 한 줄
        if decision:
            html(f'<div class="ow-chart-f2"><div class="pm"><b>사업PM 판단</b><span>{escape(decision)}</span></div></div>')
        foot = " · ".join(x for x in [escape(analysis), f"기준: {escape(basis)}" if basis else ""] if x)
        if foot:
            html(f'<div class="ow-chart-b">{foot}</div>')


def pp(x: float, digits: int = 1) -> str:
    """%p 변화 폭 표기 (+/− 부호 포함)."""
    return f"{x:+.{digits}f}%p"


def hpair(cats: list[str], before: list[float], after: list[float], *, xtitle: str, names: tuple[str, str],
          xmax: float | None = None) -> go.Figure:
    """대조군(회색) vs 실험군(파랑) 가로 막대 쌍. 변화 폭은 행 이름에 붙여 모바일에서도 겹치지 않게 한다."""
    labels = [f"{c}  <b>{pp(a - b)}</b>" for c, b, a in zip(cats, before, after)]
    fig = go.Figure()
    fig.add_bar(y=labels, x=before, name=names[0], orientation="h", marker_color=C_CTRL,
                text=[f"{v:.1f}%" for v in before], textposition="outside", cliponaxis=False)
    fig.add_bar(y=labels, x=after, name=names[1], orientation="h", marker_color=C_TREAT,
                text=[f"{v:.1f}%" for v in after], textposition="outside", cliponaxis=False)
    top = xmax if xmax is not None else max(before + after) * 1.25
    fig.update_layout(barmode="group", bargap=0.28, bargroupgap=0.06, uniformtext=dict(minsize=11, mode="show"))
    fig.update_yaxes(autorange="reversed", automargin=True, title="", tickfont=dict(size=13))
    fig.update_xaxes(title=xtitle, range=[0, top], ticksuffix="%", rangemode="tozero")
    return fig


def fmt_int(x) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:,.0f}"


def fmt_won(x) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:,.0f}원"


def pct(x) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.1f}%"


def code_counts(v: pd.DataFrame) -> pd.Series:
    """복수 코딩 집계: 주 분류 + 보조 분류 (합계가 표본 수보다 클 수 있음)."""
    codes = [c for _, r in v.iterrows() for c in opinion_codes(r)]
    return pd.Series(codes, dtype=object).value_counts().reindex(OPINION_CATEGORIES, fill_value=0)


def image_slot(sid: str, statuses: dict) -> None:
    """검증을 통과한 한국어 스크린샷만 표시. 아니면 필요한 이미지를 안내하는 16:9 자리."""
    stt = statuses.get(sid)
    if stt is None:
        return
    if stt.ok:
        st.image(str(stt.path), caption=stt.caption, width="stretch")
        return
    reasons = "".join(f"<li>{escape(r)}</li>" for r in stt.reasons[:4])
    html(f'<div class="ow-slot"><div class="ow-slot-in"><div class="ow-slot-k">최신 한국어 스크린샷 필요</div>'
         f'<div class="ow-slot-t">{escape(stt.slot.get("title", ""))}</div>'
         f'<div class="ow-slot-d">{escape(stt.slot.get("need", ""))}</div>'
         f'<div class="ow-slot-f">assets/overwatch/{escape(stt.slot.get("file", ""))}</div>'
         f'<ul class="ow-slot-r">{reasons}</ul></div></div>')


# ----------------------------------------------------------------------
# 실제 게임 화면 (이미지 중심)
# 표시 박스 좌표는 원본 1920×1080 픽셀 기준. 화면에서 직접 확인한 사실만 적는다 (기획자 관찰).
SHOT_W, SHOT_H = 1920, 1080
SHOT_NOTES: dict[str, dict] = {
    "hero_select": {"label": "영웅 선택 화면 (훈련장)",
        "marks": [("돌격", "", (90, 762, 573, 921), ""), ("공격", "", (597, 762, 1323, 921), ""),
                  ("지원", "", (1344, 762, 1833, 921), "right")],
        "facts": ["영웅 선택 화면 하단에 54명의 초상화가 역할별로 한 번에 나열된다",
                  "초상화에는 이름이 없고, 고른 영웅(시온)만 이름이 표시된다"],
    },
    "match_select": {"label": "영웅 선택 화면 (실제 경기)",
        "marks": [("남은 시간", "0:01", (40, 250, 310, 330), "below"),
                  ("팀 조합", "팀원 영웅이 함께 표시", (262, 487, 1650, 757), ""),
                  ("영웅 설명", "한 줄", (1455, 184, 1868, 224), "right below")],
        "facts": ["실제 경기에서는 '팀 구성까지 남은 시간' 안에 영웅을 골라야 한다 (캡처 시점 0:01)",
                  "고른 영웅의 설명은 우측 상단 한 줄뿐이다 — 정크랫: '적을 처치하면 잠깐 동안 재장전 속도가 증가합니다'",
                  "팀원이 고른 영웅을 보며 조합을 맞춰야 해, 낯선 영웅이 많을수록 판단할 것이 늘어난다"],
    },
    "returning_menu": {"label": "복귀 시 메인 화면",
        "marks": [("이벤트", "군림", (90, 195, 615, 525), ""),
                  ("도전 과제", "", (1482, 120, 1887, 468), "right below"),
                  ("이벤트·패스·상점", "", (102, 780, 1842, 933), "")],
        "facts": ["접속하면 이벤트 '군림' 배너와 이벤트·배틀 패스·상점 카드가 가장 크게 보인다",
                  "우측에는 발굴 입문·일일·주간 도전 과제가 표시된다",
                  "이 화면에는 마지막 접속 이후 바뀐 점(신규 영웅·역할 변경)을 요약한 안내가 따로 보이지 않는다"],
    },
    "skill_detail": {"label": "영웅 정보·스킬 설명",
        "marks": [("무기·궁극기", "", (60, 180, 630, 600), ""), ("기술 3 · 지속 능력", "", (667, 180, 1215, 720), ""),
                  ("특전 4", "2·3레벨 선택", (1275, 180, 1875, 690), "right")],
        "facts": ["영웅 1명 설명에 무기 1 · 궁극기 1 · 기술 3 · 지속 능력 1 · 특전 4, 모두 10개 항목이 있다 (시온 기준)",
                  "54명이면 익힐 항목이 수백 개다. 특전은 경기 중 레벨에 따라 고르는 선택지라 상대 영웅의 변수도 늘어난다",
                  "이 화면은 영웅을 직접 골라 찾아 들어가야 하며, '방금 나를 처치한 기술'을 따로 보여 주지는 않는다"],
    },
    "mission_screen": {"label": "도전 과제 화면",
        "marks": [("안내", "AI 상대·사용자 지정 게임 제외", (60, 326, 740, 372), ""),
                  ("남은 기간", "18일", (1610, 205, 1875, 282), "right"),
                  ("경기 수 과제", "5~20회 · 승리 시 2배", (102, 382, 1827, 660), "right"),
                  ("잠김", "선행 과제 필요", (102, 663, 1827, 938), "below")],
        "facts": ["이벤트 도전 과제 8개가 모두 '게임 N회 완료 (승리 시 진척도 두 배)' 형식이다",
                  "대부분의 도전 과제는 사용자 지정 게임·AI 상대 연습에서 완료할 수 없다고 안내한다",
                  "기술 사용·역할 목표처럼 '배우는 행동'을 기준으로 한 과제는 이 화면에 없다"],
    },
    "combat_scene": {"label": "전투 화면",
        "marks": [("처치 기록", "", (1530, 72, 1892, 160), "right below"),
                  ("처치 알림", "상대 이름만", (870, 750, 1050, 795), "below"),
                  ("내 기술", "", (1505, 915, 1870, 1028), "right")],
        "facts": ["처치되면 화면 가운데에 'OOO에게 죽음' 알림과 우측 상단 처치 기록이 뜬다",
                  "누구에게 당했는지는 보이지만, 어떤 기술에 당했고 어떻게 대응하면 되는지는 이 화면에 없다"],
    },
}


@st.cache_data(show_spinner=False, max_entries=48)
def _b64(path: str, mtime: float, blur: tuple, crop: tuple | None, max_w: int) -> str:
    return web_jpeg_b64(path, blur, crop, max_w)


def _src(stt, max_w: int = 1600) -> str:
    return _b64(str(stt.path), stt.path.stat().st_mtime, tuple(tuple(b) for b in stt.slot.get("blur", [])), None, max_w)


def _pct(v: float, total: int) -> str:
    return f"{v / total * 100:.2f}%"


def shot_html(sid: str, statuses: dict, *, marks: bool = True, facts: bool = True, title: str | None = None,
              lead: str = "", size: str = "", tag: str = "실제 게임 화면", mark_desc: dict | None = None,
              max_w: int = 1600) -> str:
    """검증 통과한 실제 스크린샷을 '실제 게임 화면' 프레임으로 감싼 HTML. 미통과 시 빈 문자열."""
    stt = statuses.get(sid)
    if stt is None or not stt.ok:
        return ""
    note_ = dict(SHOT_NOTES.get(sid, {}))
    if mark_desc:
        note_["marks"] = [(lab, mark_desc.get(lab, desc), box, cls) for lab, desc, box, cls in note_.get("marks", [])]
    boxes = ""
    if marks:
        for i, (lab, desc, (x0, y0, x1, y1), cls) in enumerate(note_.get("marks", []), 1):
            d = f" <b>{escape(desc)}</b>" if desc else ""
            boxes += (f'<div class="ow-mark {cls}" style="left:{_pct(x0, SHOT_W)};top:{_pct(y0, SHOT_H)};'
                      f'width:{_pct(x1 - x0, SHOT_W)};height:{_pct(y1 - y0, SHOT_H)}"><span><i>{i}</i>{escape(lab)}{d}</span></div>')
    # 사진 아래에는 짧은 설명(10~20자)만. 촬영일·출처는 탭 맨 아래 '이미지 출처 및 촬영 정보'에 한 번만 표시한다.
    _FIGS.append((sid, stt))
    num = len(_FIGS)
    title_ = escape(title or stt.slot.get("title", ""))
    cap = f"<figcaption>{lead}</figcaption>" if lead else ""
    return (f'<figure class="ow-shot {size}"><div class="ow-shot-bar"><span class="ow-shot-tag">그림 {num}</span>{title_}</div>'
            f'<div class="ow-shot-img"><img src="data:image/jpeg;base64,{_src(stt, max_w)}" alt="{title_}" loading="lazy">{boxes}</div>'
            f'{cap}</figure>')


_FIGS: list = []   # 현재 탭에 표시된 실제 게임 화면 (그림 번호 · 출처 표기용)


def shot_facts(sids: list[str]) -> None:
    """화면별 관찰 사실(긴 설명)은 펼쳐보기 안에 보존."""
    rows = [(sid, SHOT_NOTES[sid]) for sid in sids if sid in SHOT_NOTES]
    if not rows:
        return
    with st.expander("화면별 관찰 사실 (자세히)"):
        html("".join(f'<div class="ow-facts"><b>{escape(n.get("label", sid))}</b>'
                     + "".join(f"<span>{i}. {escape(lab)}{' · ' + escape(desc) if desc else ''}</span>"
                               for i, (lab, desc, _, _) in enumerate(n.get("marks", []), 1))
                     + bullets(n.get("facts", [])) + "</div>" for sid, n in rows))


def image_credits() -> None:
    """탭 하단에 이미지 출처·촬영 정보를 한 번만. 값이 다른 이미지는 그림 번호별로 나눠 적는다."""
    if not _FIGS:
        return
    groups: dict = {}
    for i, (sid, stt) in enumerate(_FIGS, 1):
        s = stt.slot
        k = (s.get("source") or "-", s.get("captured_at") or "확인 안 됨", s.get("game_version") or "버전 미기재")
        groups.setdefault(k, []).append(i)
    blurred = [i for i, (_, stt) in enumerate(_FIGS, 1) if stt.slot.get("blur")]
    lines = "".join(
        f"<li>그림 {', '.join(map(str, nums))} · {escape(src)} · 촬영 {escape(cap)} (파일 전송 시각 기준) · {escape(ver)} · 한국어 UI</li>"
        for (src, cap, ver), nums in groups.items())
    if blurred:
        lines += f"<li>다른 플레이어 닉네임 가림: 그림 {', '.join(map(str, blurred))}</li>"
    html(f'<details class="ox-credits"><summary>이미지 출처 및 촬영 정보</summary><ul>{lines}</ul></details>')


def shot(sid: str, statuses: dict, **kw) -> None:
    """실제 스크린샷 표시. 검증 전이면 '최신 한국어 스크린샷 필요' 자리."""
    h = shot_html(sid, statuses, **kw)
    if h:
        html(h)
    else:
        image_slot(sid, statuses)


def real_vs_mock_key() -> None:
    html('<div class="ow-key"><span class="k-real">실제 게임 화면 (현재 · 직접 캡처)</span>'
         '<span class="k-mock">기획 시안 (제안 기능 · 실제 게임에 없음)</span></div>')


def col_head(kind: str, text: str) -> None:
    html(f'<div class="ow-colh {kind}">{escape(text)}</div>')


def hero_grid(heroes: dict, cutoff: str | None = None) -> None:
    chips = []
    for h in heroes["heroes"]:
        cls, mark = "", ""
        if h.get("new_2026") and (cutoff is None or h["new_2026"] > cutoff):
            cls, mark = "new", f'<small>{h["new_2026"][5:]}</small>'
        elif h.get("recent_catchup") and cutoff is None:
            cls = "recent"
        if h.get("role_changed") and (cutoff is None or h["role_changed"] > cutoff):
            cls += " changed"
        chips.append(f'<span class="ow-hero {cls}">{escape(h["name"])}{mark}</span>')
    html(f'<div class="ow-heroes">{"".join(chips)}</div>')


# ======================================================================
def _steam_chart(steam: pd.DataFrame) -> None:
    if steam.empty:
        st.info("Steam 자료를 불러오지 못했습니다.")
    else:
        last = steam.iloc[-1]
        d = steam.tail(12).reset_index(drop=True)
        pk = d.loc[d["avg_players"].idxmax()]
        first = d.iloc[0]
        colors = [C_TREAT if m == pk["month"] else C_MUTED for m in d["month"]]
        fig = go.Figure(go.Bar(x=d["month"], y=d["avg_players"], marker_color=colors,
                               text=[f"{v / 1000:,.0f}천" for v in d["avg_players"]], textposition="outside", cliponaxis=False,
                               hovertemplate="%{x|%Y-%m} · 월평균 %{y:,.0f}명<extra></extra>"))
        fig.update_yaxes(title="월평균 동시접속자 (명)", tickformat=",", rangemode="tozero", range=[0, d["avg_players"].max() * 1.18])
        fig.update_xaxes(title="월", tickformat="%y.%m", dtick="M1")
        ox_chart_card(fig, key="steam", kind="real", title="Steam 월평균 동시접속자 (12개월)",
                   unit="명 · 파랑 = 최고치",
                   kpis=[(f"최고 {pk['month']:%Y년 %m월}", f"{pk['avg_players']:,.0f}명"),
                         (f"최근 {last['month']:%Y년 %m월}", f"{last['avg_players']:,.0f}명"),
                         ("최고치 대비 최근", f"{(last['avg_players'] / pk['avg_players'] - 1) * 100:+.0f}%")],
                   analysis=f"{pk['month']:%y.%m} 최고 → 최근 {last['avg_players'] / pk['avg_players'] * 100:.0f}% 수준 · 감소 원인은 이 자료로 알 수 없음",
                   decision="유입 규모 참고용 · 이탈 원인 근거로 쓰지 않음",
                   basis=f"{first['month']:%y.%m}~{last['month']:%y.%m} 같은 출처 · Steam만 포함",
                   height=300, legend=False, cols=("월", "월평균 동시접속자 (명)"))


def _pc_chart(pc: pd.DataFrame) -> None:
    tracker = st.radio("집계원", ["게임트릭스", "더로그"], horizontal=True, key="ow_pc_tracker")
    q = pc[pc["plottable"] & (pc["tracker"] == tracker)]
    if q.empty:
        st.info("선택한 집계원의 자료가 없습니다.")
    else:
        daily, weekly = q[q["granularity"] == "일간"], q[q["granularity"] != "일간"]
        cut = pd.Timestamp("2026-08-12")
        before, after = q[q["period_start"] < cut], q[q["period_start"] >= cut]
        fig = go.Figure()
        fig.add_scatter(x=daily["period_start"], y=daily["share_pct"], mode="markers", name="일간 점유율",
                        marker=dict(size=12, color=[C_CTRL if t < cut else C_TREAT for t in daily["period_start"]],
                                    line=dict(color="white", width=1)),
                        customdata=daily[["rank"]], hovertemplate="%{x|%m-%d} · %{y:.2f}% (%{customdata[0]}위)<extra></extra>")
        for j, r in enumerate(weekly.itertuples()):
            fig.add_scatter(x=[r.period_start, r.period_end], y=[r.share_pct] * 2, mode="lines", name="주간 점유율",
                            line=dict(color=C["sky"], width=8), showlegend=j == 0, legendgroup="w",
                            hovertemplate=f"{r.granularity} · {r.share_pct:.2f}% ({int(r.rank)}위)<extra></extra>")
        fig.add_vline(x=cut, line_dash="dot", line_color=C["navy"])
        fig.add_annotation(x=cut, y=12, text="넥슨 서비스 개시 8/12", showarrow=False, xanchor="left", xshift=4,
                           font=dict(size=11, color=C["navy"]))
        fig.update_yaxes(title="PC방 점유율 (%)", range=[0, 12.5], ticksuffix="%")
        fig.update_xaxes(title="기준일 (2026년)", range=[pd.Timestamp("2026-03-15"), pd.Timestamp("2026-10-31")], tickformat="%m월")
        # 비교 기준: 같은 집계원·같은 단위(일간)의 '서비스 직전 마지막 값' vs '서비스 후 마지막 값'
        db, da = daily[daily["period_start"] < cut], daily[daily["period_start"] >= cut]
        kp, analysis = [], "서비스 전후를 같은 단위(일간)로 비교할 자료가 부족하다."
        if not db.empty and not da.empty:
            b0, a0 = db.sort_values("period_start").iloc[-1], da.sort_values("period_start").iloc[-1]
            diff = a0["share_pct"] - b0["share_pct"]
            kp = [(f"서비스 직전 {b0['period_start']:%m/%d} (일간)", f"{b0['share_pct']:.2f}%"),
                  (f"서비스 후 {a0['period_start']:%m/%d} (일간)", f"{a0['share_pct']:.2f}%"),
                  ("변화 폭 (일간끼리)", f"<b>{pp(diff, 2)}</b>")]
            earlier = before[before["share_pct"] > b0["share_pct"]]
            caveat = (f"{earlier.iloc[0]['period_start']:%m/%d} 값 {earlier.iloc[0]['share_pct']:.1f}%가 더 높음" if not earlier.empty
                      else "이벤트·시즌 겹침")
            analysis = f"일간 {b0['share_pct']:.2f}% → {a0['share_pct']:.2f}% ({pp(diff, 2)}) · {caveat}"
        if not kp:   # 전후 비교가 안 될 때만 기간 최고값을 칩으로 (칩은 최대 3개)
            mx = q.loc[q["share_pct"].idxmax()]
            rk = f" · {int(mx['rank'])}위" if pd.notna(mx["rank"]) else ""
            kp.append((f"기간 최고 {mx['period_start']:%m/%d}{rk}", f"{mx['share_pct']:.1f}%"))
        ox_chart_card(fig, key="pc", kind="real", title=f"한국 PC방 점유율 ({tracker})",
                   unit="% · 회색 = 서비스 전, 파랑 = 후 · 가로선 = 주간",
                   kpis=kp, analysis=analysis,
                   decision="시장 반응 참고 · PC방 연계(D)는 A 검증 후 판단",
                   basis=f"같은 집계원·같은 단위(일간)끼리 비교",
                   height=300, cols=("기준일", "PC방 점유율 (%)"), series="집계 단위")


def _metric_sources(pc: pd.DataFrame) -> None:
    with st.expander("자세히 보기 · 출처와 해석 주의"):
        st.markdown(f"출처: [{STEAM_SOURCE['name']}]({STEAM_SOURCE['url']}) · 확인일 {COLLECTED_AT}")
        st.caption("Battle.net·넥슨 클라이언트·콘솔 이용자는 빠져 있다. 2026년 2월 급증은 시즌 1과 명칭 변경 시기가 겹쳐 원인을 하나로 볼 수 없다.")
    with st.expander("자세히 보기 · 원자료와 집계 기준"):
        st.caption("두 집계원은 표본 PC방이 달라 같은 날에도 순위가 다르다(9/13 더로그 2위, 게임트릭스 5위). PC방 이벤트·신규 시즌이 겹쳐 상승 원인을 단정할 수 없고, 계약 발표 이전 수치는 확보하지 못했다.")
        st.dataframe(
            pc[["tracker", "period_start", "granularity", "rank", "share_pct", "source_publisher", "source_url", "status"]]
            .rename(columns={"tracker": "집계원", "period_start": "기준일", "granularity": "단위", "rank": "순위",
                             "share_pct": "점유율(%)", "source_publisher": "보도 매체", "source_url": "원문", "status": "상태"}),
            hide_index=True, column_config={"원문": st.column_config.LinkColumn("원문", display_text="열기"),
                                            "기준일": st.column_config.DateColumn(format="YYYY-MM-DD")})


def _opinion_chart(v: pd.DataFrame) -> None:
    cnt = code_counts(v)
    learn = int(sum(bool(set(opinion_codes(r)) & LEARNING_CODES) for _, r in v.iterrows()))
    top_cat, top_n = cnt.idxmax(), int(cnt.max())
    colors = [C_TREAT if c in LEARNING_CODES else C_MUTED for c in cnt.index]
    fig = go.Figure(go.Bar(y=cnt.index, x=cnt.values, orientation="h", marker_color=colors, text=[f"{x}건" for x in cnt.values],
                           textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x}건<extra></extra>"))
    fig.update_yaxes(autorange="reversed", automargin=True, title="")
    fig.update_xaxes(title="언급 수 (건)", range=[0, max(cnt.max(), 1) * 1.3 + 1], rangemode="tozero")
    ox_chart_card(fig, key="op", kind="real",
               title=f"1위 '{top_cat}' {top_n}건 · 반대 사례(긍정적 학습 경험) {int(cnt.get('긍정적인 학습 경험', 0))}건도 함께 집계",
               unit="건 · 한 의견이 여러 유형에 걸치면 각각 셈 · 파랑 = 학습·적응 관련", kpis=[],
               analysis=f"학습·적응 관련 의견 {learn}/{len(v)}건 · 매칭 {int(cnt.get('매칭·실력 차이', 0))}건·비매너도 함께 추적",
               decision="", basis="", height=380, legend=False, cols=("문제 유형", "언급 수 (건)"))


def _opinion_card(r) -> str:
    tone = {"부정": "neg", "중립": "neu", "긍정": "pos"}.get(r["sentiment"], "neu")
    plat = "인벤" if "인벤" in r["platform"] else ("디시인사이드" if "디시" in r["platform"] else "블리자드 포럼")
    tags = " · ".join(opinion_codes(r))
    return (f'<div class="ow-quote {tone}"><div class="ow-quote-tag">{escape(r["sentiment"])} · {escape(r["user_type"])} · {escape(tags)}</div>'
            f'<div class="ow-quote-t">{escape(r["summary_ko"])}</div>'
            f'<div class="ow-quote-o">“{escape(r["quote_original"])}”</div>'
            f'<div class="ow-quote-m">{plat} · {escape(r["published_date"])} · {link(r["source_url"], "원문 보기")}</div></div>')


def _sample_card(v, plat, utype, n_ko, n_en) -> None:
    html('<div class="ow-sample"><div class="ow-sample-h">표본과 분류 기준</div><div class="ow-sample-g">'
         f'<div><b>표본 구성</b>{bullets([" · ".join(f"{k} {n}" for k, n in plat.items()), " · ".join(f"{k} {n}" for k, n in utype.items()), f"한국어 {n_ko} · 영어 {n_en}"])}</div>'
         '<div><b>중복 제거·검증</b>' + bullets(["원문 링크를 열어 내용을 직접 확인한 글만 '검증 완료'",
                                              "같은 작성자로 추정되는 글은 1건만 집계",
                                              "주제와 무관하거나 원문을 확인할 수 없는 글은 제외 (아래 목록)"]) + '</div>'
         '<div><b>분류 방법</b>' + bullets(["기획자가 직접 분류 (AI 자동 분류 아님)",
                                          "주 분류 1개 + 보조 분류 복수 → 합계가 의견 수보다 많음",
                                          "긍정·중립 의견과 반대 사례도 그대로 포함"]) + '</div>'
         f'<div><b>해석 한계 {b_interp()}</b>' + bullets(["자발적 게시글이라 전체 이용자를 대표하는 통계 표본이 아니다",
                                                       "불편을 겪은 사람의 글이 더 많을 수 있다",
                                                       "언급 수는 '문제의 존재'를 보여 줄 뿐 '비율'이나 '이탈 원인'을 뜻하지 않는다"]) + '</div>'
         '</div></div>')


LAST_ACCESS = {"2026년 1월 (시즌 1 이전)": "2026-01-31", "2026년 7월": "2026-07-31", "2026년 9월": "2026-09-30"}


def _a_reset() -> None:
    st.session_state["ow_a_step"] = 0


def _a_set(step: int) -> None:
    st.session_state["ow_a_step"] = step


def _proto_a(heroes: dict, tl: pd.DataFrame, statuses: dict) -> None:
    html('<div class="ox-demo-h"><b>A · 놓친 변경점만 3분 요약</b>'
         '<span>지금은 웹 공지 기사 속 일괄 요약 → 접속 즉시 <em>내 마지막 접속일 기준</em>으로 놓친 것만</span></div>')
    left, right = st.columns([1, 1], gap="medium")
    with left:
        col_head("real", "현재 · 접속하면 보이는 메인 화면")
        shot("returning_menu", statuses, facts=False, max_w=1200,
             lead="변경점 안내가 보이지 않음")
    with right:
        col_head("mock", "제안 · 접속 직후 복귀 브리핑")
        _proto_a_body(heroes, tl)


def _proto_a_body(heroes: dict, tl: pd.DataFrame) -> None:
    last = st.radio("예시 계정의 마지막 접속 시점", list(LAST_ACCESS), horizontal=True, key="ow_a_last", on_change=_a_reset)
    cutoff = LAST_ACCESS[last]
    new = [h for h in heroes["heroes"] if h.get("new_2026") and h["new_2026"] > cutoff]
    changed = [h for h in heroes["heroes"] if h.get("role_changed") and h["role_changed"] > cutoff]
    sys_rows = tl[tl["date"].notna() & (tl["type"] == "시스템") & tl["status"].str.startswith("공식") & (tl["date"] > pd.Timestamp(cutoff))]
    sys_rows = sys_rows.sort_values("date")
    total = len(new) + len(changed) + len(sys_rows)
    step = st.session_state.get("ow_a_step", 0)

    html(f'<div class="ow-proto coral"><div class="ow-proto-bar"><span>RE:START 복귀 브리핑</span>{b_mock()}</div>'
         f'<div class="ow-proto-h">다시 오신 것을 환영합니다</div>'
         f'<div class="ow-proto-s">마지막 접속 이후 <b>{total}개</b>가 바뀌었습니다 · 예상 3분</div>'
         f'<div class="ow-proto-chips"><span>신규 영웅 {len(new)}</span><span>바뀐 영웅 {len(changed)}</span><span>새 시스템 {len(sys_rows)}</span></div></div>')

    if step == 0:
        c1, c2 = st.columns(2)
        c1.button("3분 요약 보기", key="ow_a_start", type="primary", on_click=_a_set, args=(1,), width="stretch")
        c2.button("나중에 보기", key="ow_a_later", on_click=_a_set, args=(-1,), width="stretch")
    elif step == -1:
        st.info("메뉴 > 복귀 브리핑에서 언제든 다시 볼 수 있습니다. (기획 시안)")
        st.button("다시 열기", key="ow_a_reopen", on_click=_a_set, args=(0,))
    else:
        cards = {
            1: ("1/3 · 새로 나온 영웅", "".join(f'<span class="ow-hero new">{escape(h["name"])}<small>{h["new_2026"][5:]}</small></span>' for h in new)
                or "<p>이 기간에 새로 나온 영웅이 없습니다.</p>"),
            2: ("2/3 · 바뀐 영웅", "".join(f'<span class="ow-hero changed">{escape(h["name"])} · 공격 → 지원</span>' for h in changed)
                or "<p>역할이 바뀐 영웅이 없습니다.</p>"),
            3: ("3/3 · 새 시스템", "<ul>" + "".join(f"<li><b>{r.date:%m-%d}</b> {escape(r.title)}</li>" for r in sys_rows.itertuples()) + "</ul>"
                if len(sys_rows) else "<p>새 시스템 변경이 없습니다.</p>"),
        }
        if step <= 3:
            title, body = cards[step]
            html(f'<div class="ow-proto-card mock coral"><div class="ow-proto-card-t">{title}</div><div class="ow-heroes small">{body}</div>'
                 f'<div class="ow-proto-card-s">출처: 공식 패치노트·공식 영웅 페이지</div></div>')
            c1, c2, c3 = st.columns(3)
            c1.button("이전", key="ow_a_prev", on_click=_a_set, args=(max(step - 1, 0),), width="stretch")
            c2.button("다음" if step < 3 else "완료", key="ow_a_next", type="primary", on_click=_a_set, args=(step + 1,), width="stretch")
            c3.button("건너뛰기", key="ow_a_skip", on_click=_a_set, args=(-1,), width="stretch")
        else:
            st.success("브리핑 완료 · 이제 빠른 대전으로 감각을 되찾아 보세요. (기획 시안)")
            st.button("처음으로", key="ow_a_restart", on_click=_a_set, args=(0,))


def _proto_b(heroes: dict, statuses: dict) -> None:
    html('<div class="ox-demo-h"><b>B · 어려웠던 상대 대응 카드 (수동형 MVP)</b>'
         '<span>지금은 스킬에 마우스를 올려 키워드만 확인 → 경기 후 <em>어려웠던 상대를 골라</em> 핵심 기술·대처법 확인</span></div>')
    left, right = st.columns([1, 1], gap="medium")
    with left:
        col_head("real", "현재 · 처치당한 직후 전투 화면")
        shot("combat_scene", statuses, facts=False, max_w=1200,
             lead="상대 이름만 표시, 대응법 없음")
    with right:
        col_head("mock", "제안 · 경기 직후 전투 학습 카드 (수동형)")
        _proto_b_body(heroes)
    st.caption("MVP 제외: '나를 처치한 기술' 자동 표시는 블리자드와 데이터 범위·정확도 확인 후 결정 · 카드 내용의 출처 화면(영웅 상세)은 02 탭 상세 보기")


def _proto_b_body(heroes: dict) -> None:
    sk = {s["hero"]: s for s in heroes.get("skills_verified", [])}
    if not sk:
        st.info("스킬 자료가 없습니다.")
        return
    c1, c2 = st.columns(2)
    hero = c1.selectbox("어려웠던 상대 영웅 (유저가 선택)", list(sk), key="ow_b_hero")
    skill = c2.selectbox("확인할 기술", sk[hero]["skills"], key="ow_b_skill")
    html(f'<div class="ow-proto dark"><div class="ow-proto-bar"><span>전투 학습 카드 · 수동형</span>{b_mock()}</div>'
         f'<div class="ow-proto-s">선택한 상대 <b>{escape(hero)}</b> · 핵심 기술 1개와 대처 선택지</div>'
         f'<div class="ow-skill"><div class="ow-skill-icon">스킬<br>이미지<br>자리</div><div>'
         f'<div class="ow-skill-n">{escape(skill)}</div>'
         f'<div class="ow-skill-d">기술 특징 · 공식 영웅 페이지 설명 연동 예정 <small>(검증 전 미입력)</small></div>'
         f'<div class="ow-skill-tip">대응 예시 · 혼자 정면으로 맞서지 말고 아군 근처에서 싸우기 <small>(예시 문구 · 게임 디자인 검수 필요)</small></div>'
         f'</div></div><div class="ow-proto-card-s">기술 이름: {link(sk[hero]["source"], "공식 패치노트")} 표기</div></div>')
    c1, c2 = st.columns(2)
    if c1.button("연습해 보기", key="ow_b_practice", type="primary", width="stretch"):
        st.info("연습장으로 이동해 이 기술을 상대해 보는 흐름입니다. 실제 게임 연동은 블리자드 개발 협업이 필요합니다. (기획 시안)")
    if c2.button("다시 보지 않기", key="ow_b_off", width="stretch"):
        st.info("설정에서 카드 표시를 끄거나 하루 표시 횟수를 줄일 수 있습니다. (기획 시안)")


# (경기 구간, 학습 목표, [(미션, 학습 확인 방법)])  · 'N판 플레이' 같은 횟수 조건은 쓰지 않는다
MISSIONS = [
    (1, 3, "역할·기술 이해", [("주력 영웅의 기술 3개를 한 경기 안에서 모두 사용", "경기 후 기술 한 줄 요약 카드 확인"),
                         ("역할 목표 1회 달성 (예: 돌격 거점 진입 · 지원 아군 치유)", "역할 패시브 설명 확인")]),
    (4, 6, "상대 대응", [("어려웠던 상대 1명을 학습 카드(B)로 확인", "대처 선택지 중 1개 고르기"),
                      ("같은 상대를 다시 만난 경기에서 직전보다 오래 생존", "경기 후 결과 비교 표시")]),
    (7, 10, "팀 플레이", [("아군과 함께 목표 지점에 진입", "팀 목표 설명 확인"),
                       ("아군 요청(핑)에 맞춰 위치·역할 조정 1회", "요청 응답 기록 확인")]),
]
MISSION_RULES = ["'N판 플레이' 같은 횟수 조건 없음 · 승패와 무관", "미션마다 학습 목표와 확인 방법을 1:1로 연결",
                 "같은 행동 보상은 하루 1회 · 보상은 외형 위주", "언제든 끄기 · 다시 켜기"]


def _proto_c(statuses: dict) -> None:
    html('<div class="ox-demo-h"><b>C · 첫 10경기 학습 미션</b>'
         '<span>지금은 \'N경기 완료\' 횟수형 과제 → 영웅 선택은 그대로, <em>배우는 행동</em>으로 채우는 선택형 미션</span></div>')
    left, right = st.columns([1, 1], gap="medium")
    with left:
        col_head("real", "현재 · 이벤트 도전 과제 화면")
        shot("mission_screen", statuses, facts=False, max_w=1200,
             lead="과제 = 경기 횟수, 학습 과제 없음")
    with right:
        col_head("mock", "제안 · 첫 10경기 학습 미션")
        _proto_c_body()
    st.caption("설계 원칙 · " + " · ".join(MISSION_RULES))


def _proto_c_body() -> None:
    c1, c2 = st.columns([3, 1])
    n = c1.slider("진행한 경기 수 (예시)", 0, 10, 4, key="ow_c_n")
    off = c2.toggle("미션 끄기", key="ow_c_off")
    if off:
        st.info("미션을 껐습니다. 언제든 다시 켤 수 있고 알림 빈도도 조절할 수 있습니다. (기획 시안)")
        return
    segs = "".join(f'<span class="{"on" if i <= n else ""}">{i}</span>' for i in range(1, 11))
    blocks = []
    for a, b, name, items in MISSIONS:
        done = n >= b
        active = a <= n + 1 <= b and not done
        state = "완료" if done else ("진행 중" if active else "대기")
        cls = "done" if done else ("active" if active else "")
        blocks.append(f'<div class="ow-mission {cls}"><div class="ow-mission-h">{a}~{b}경기 · 학습 목표: {escape(name)}<span>{state}</span></div>'
                      + "".join(f'<div class="ow-mission-i">{"✓" if done else "○"} {escape(x)}<small>확인: {escape(c)}</small></div>'
                                for x, c in items) + "</div>")
    html(f'<div class="ow-proto narrow"><div class="ow-proto-bar"><span>첫 10경기 학습 미션</span>{b_mock()}</div>'
         f'<div class="ow-progress">{segs}</div><div class="ow-grid3">{"".join(blocks)}</div>'
         f'<div class="ow-proto-card-s">보상 예시: 외형 아이템 (확정 아님 · 경쟁 밸런스에 영향 없는 보상만 검토)</div></div>')


def _timeline(plan: dict) -> str:
    """주차별 실험 일정표 (배정 · D7 판정 · D30 확인)."""
    sc = plan["sched"]
    W = sc["decision"]
    rows = [
        ("실험 1 · A (복귀)", {**{w: ("assign", "배정") for w in range(sc["e1_assign"][0], sc["e1_assign"][1] + 1)},
                             sc["e1_d7"]: ("d7", "D7 판정"), sc["e1_d30"]: ("d30", "D30 확인")}),
        ("실험 2 · C (신규)", {**{w: ("assign", "배정") for w in range(sc["e2_assign"][0], sc["e2_assign"][1] + 1)},
                             sc["e2_d7"]: ("d7", "D7 판정"), sc["e2_m10"]: ("m10", "10경기"), sc["e2_d30"]: ("d30", "D30 확인")}),
        ("실험 3 · B 수동형", {w: ("small", "사용성") for w in range(sc["e3"][0], sc["e3"][1] + 1)}),
        ("의사결정", {sc["e1_d7"]: ("dec", "A 1차"), sc["e1_d30"]: ("dec", "A 확정"), W: ("dec", "최종")}),
    ]
    head_ = "".join(f"<th>{w}주</th>" for w in range(1, W + 1))
    body = "".join(f"<tr><th>{escape(n)}</th>" + "".join(
        f'<td class="{cells[w][0]}">{escape(cells[w][1])}</td>' if w in cells else "<td></td>" for w in range(1, W + 1)) + "</tr>"
        for n, cells in rows)
    return f'<div class="gp-table-wrap"><table class="ow-gantt"><tr><th>준비 2주 이후</th>{head_}</tr>{body}</table></div>'


# ======================================================================
# 7탭 개편 (가독성 우선) — 섹션마다 '결론 제목 → 대표 데이터·이미지 1개 → 짧은 설명 → 상세 보기'
# 원본 의견·자료·계산은 삭제하지 않고 상세 보기(펼치기)로 옮겼다.
KIND_TXT = {"real": "실제 자료", "interp": "분석자 해석", "hypo": "검증 전 가설", "mock": "기획 시안", "sim": "가정 시뮬레이션",
            "plan": "기획 확정안", "pending": "작업 중"}


def stats(items: list[tuple[str, str, str]]) -> None:
    """대표 숫자 최대 3~4개: (값 HTML, 설명, 자료 성격)."""
    html('<div class="ox-stats">' + "".join(
        f'<div><b>{v}</b><span>{escape(l)}</span><small>{KIND_TXT.get(k, k)}</small></div>' for v, l, k in items) + "</div>")


def chips_flow(items: list[str], cls: str = "") -> str:
    return f'<div class="ox-flow {cls}">' + '<i>→</i>'.join(f"<span>{escape(x)}</span>" for x in items) + "</div>"


def won(x: float) -> str:
    """원 단위를 억·만 원으로 짧게."""
    a = abs(x)
    s = "−" if x < 0 else ""
    if a >= 1e8:
        return f"{s}{a / 1e8:,.2f}억 원"
    return f"{s}{a / 1e4:,.0f}만 원"


def _learn(v: pd.DataFrame) -> int:
    return int(sum(bool(set(opinion_codes(r)) & LEARNING_CODES) for _, r in v.iterrows()))


def _opinions_all(rs: dict, ops: pd.DataFrame) -> None:
    """의견 전체(필터·페이지·검색 표) + 표본 기준 + 한계 · 펼치기 안에서만 표시 (중첩 펼치기 없음)."""
    v, other = ops[ops["verified"]], ops[~ops["verified"]]
    n_ko, n_en = int((v["language"] == "한국어").sum()), int((v["language"] == "영어").sum())
    plat = v["platform"].map(lambda p: "인벤" if "인벤" in p else ("디시인사이드" if "디시" in p else "블리자드 포럼")).value_counts()
    c1, c2 = st.columns(2)
    n_rep = int(v["opinion_id"].isin(rs["rep_opinions"]).sum())
    rep_label = f"대표 의견 {n_rep}건"
    view = c1.selectbox("보기", [rep_label] + OPINION_CATEGORIES, key="ow_op_view")
    tone = c2.selectbox("의견 방향", ["전체", "부정", "중립", "긍정"], key="ow_op_tone")
    q = v[v["opinion_id"].isin(rs["rep_opinions"])] if view == rep_label else v[v.apply(lambda r: view in opinion_codes(r), axis=1)]
    if tone != "전체":
        q = q[q["sentiment"] == tone]
    q = q.sort_values("published_date", ascending=False)
    per = 4
    pages = max(1, math.ceil(len(q) / per))
    page = st.number_input(f"페이지 (총 {pages}쪽 · {len(q)}건)", 1, pages, 1, key=f"ow_op_page_{view}_{tone}") if pages > 1 else 1
    chunk = q.iloc[(page - 1) * per: page * per]
    if chunk.empty:
        st.info("조건에 맞는 의견이 없습니다.")
    else:
        html(f'<div class="ow-grid2">{"".join(_opinion_card(r) for _, r in chunk.iterrows())}</div>')
    kw = st.text_input("전체 표 검색어 (요약·원문 발췌)", key="ow_f_kw")
    t = v
    if kw.strip():
        k = kw.strip()
        t = t[t["summary_ko"].str.contains(k, case=False, regex=False) | t["quote_original"].str.contains(k, case=False, regex=False)]
    st.dataframe(
        t[["opinion_id", "platform", "published_date", "user_type", "sentiment", "issue_category", "issue_tags",
           "summary_ko", "quote_original", "source_url", "collected_date"]]
        .rename(columns={"opinion_id": "의견 번호", "platform": "플랫폼", "published_date": "작성일", "user_type": "유형",
                         "sentiment": "방향", "issue_category": "주 분류", "issue_tags": "보조 분류", "summary_ko": "요약",
                         "quote_original": "원문 발췌", "source_url": "원문", "collected_date": "확인일"}),
        hide_index=True, column_config={"원문": st.column_config.LinkColumn("원문", display_text="열기")})
    tiles([("검증 완료 의견", f"{len(v)}건", f"한국어 {n_ko} · 영어 {n_en}"),
           ("부정 · 중립 · 긍정", " · ".join(str(int((v['sentiment'] == s).sum())) for s in ["부정", "중립", "긍정"]), "기획자 분류"),
           ("미검증·제외", f"{len(other)}건", "Reddit·유튜브 미확인, 중복·주제 무관")])
    _sample_card(v, plat, v["user_type"].value_counts(), n_ko, n_en)
    plats = " · ".join(f"{k} {n}" for k, n in v["platform"].value_counts().items())
    st.markdown("**표본의 한계 · 수집 방법**\n"
                "- 자발적 게시글이라 불편을 겪은 사람의 글이 많을 수 있다. 전체 이용자 설문이 아니다.\n"
                "- 분류와 의견 방향은 AI 모델이 아닌 기획자가 판단했다. 유형은 작성자가 밝힌 경우만 표시하고 나머지는 '미상'이다.\n"
                "- 같은 작성자로 추정되는 글은 1건만 셌다. 닉네임을 저장하지 않아 다른 글이 같은 사람일 가능성은 남아 있다.\n"
                "- Reddit은 수집 환경에서 접근이 차단됐고, 유튜브는 댓글을 불러올 수 없어 0건이다.\n"
                f"- 플랫폼: {plats} · 작성일 {v['published_date'].min()} ~ {v['published_date'].max()} · 확인일 {v['collected_date'].min()} ~ {v['collected_date'].max()}\n"
                "- 검색 키워드 목록: **수집 기준 미기록** → 다음 수집부터 키워드·기간·플랫폼을 먼저 고정하고 무작위 표본 추출 + 2인 분류 일치율 기록")
    for r in other.itertuples():
        src = "원문 삭제됨 (링크 없음)" if "원문 삭제" in r.verification_status else f"[{r.source_url}]({r.source_url})"
        st.markdown(f"- `{r.opinion_id}` {r.platform} · {src} — {r.verification_status} · {r.note}")


def _cause_detail(p: dict, v: pd.DataFrame, cnt: pd.Series) -> None:
    steps = []
    for i, f in enumerate(p["flow"]):
        codes = set(f.get("codes", []))
        n = sum(bool(set(opinion_codes(r)) & codes) for _, r in v.iterrows()) if codes else 0
        ev = f"{escape(f['basis'])}" + (f" · 관련 의견 {n}건" if n else "")
        steps.append(f'<div class="ow-step {f.get("kind", "hypo")}"><div class="ow-step-n">{i + 1} {KIND[f.get("kind", "hypo")]()}</div>'
                     f'<div class="ow-step-t">{escape(f["step"])}</div><div class="ow-step-d">{escape(f["desc"])}</div>'
                     f'<div class="ow-step-b">근거 · {ev}</div><div class="ow-step-c">검증 · {escape(f.get("check", ""))}</div></div>')
        if i < len(p["flow"]) - 1:
            steps.append('<div class="ow-step-a">→</div>')
    html(f'<div class="ow-flow">{"".join(steps)}</div>')
    note(p["verify"])
    note("A/B 테스트는 무작위 배정이라 매칭·비매너 같은 다른 원인이 두 그룹에 고르게 섞인다 → 기능 효과만 분리된다.")
    cards = []
    for a in p["alternatives"]:
        n = (f"관련 의견 {len(a['ids'])}건" if a.get("ids") else
             (f"관련 의견 {int(cnt.get(a['category'], 0))}건" if a.get("category") else "관련 의견 없음"))
        cards.append(f'<div class="ow-alt"><div class="ow-alt-t">{escape(a["cause"])}</div><div class="ow-alt-n">{n}</div>'
                     f'<div class="ow-alt-d">{escape(a["evidence"])}</div><div class="ow-alt-c">확인: {escape(a["check"])}</div></div>')
    html(f'<div class="ow-grid3">{"".join(cards)}</div>')


def _screens_detail(heroes: dict, statuses: dict) -> None:
    """03 데모에 쓰지 않는 화면(실제 경기 영웅 선택·스킬 설명) + 영웅 목록 · 화면별 관찰 사실."""
    shot("match_select", statuses, size="wide", lead="제한 시간 안에 영웅 선택")
    shot("skill_detail", statuses, size="wide", lead="영웅 1명 = 설명 10개")
    st.caption("파란 상자·번호는 설명용 표시이며 화면은 수정하지 않았습니다.")
    rows = [(sid, SHOT_NOTES[sid]) for sid in ["hero_select", "match_select", "returning_menu", "skill_detail", "mission_screen", "combat_scene"]]
    html("".join(f'<div class="ow-facts"><b>{escape(n.get("label", sid))}</b>' + bullets(n.get("facts", [])) + "</div>" for sid, n in rows))
    n_all = len(heroes["heroes"])
    tiles([("공식 영웅 수", f"{n_all}명", f'{link(heroes["source"], "공식 영웅 페이지")} · {heroes["checked_at"]} 기준'),
           ("2026년 신규 영웅", f"{sum(1 for x in heroes['heroes'] if x.get('new_2026'))}명", "공식 패치노트"),
           ("블리자드 복귀 요약의 '최근 영웅'", f"{sum(1 for x in heroes['heroes'] if x.get('recent_catchup'))}명", "시즌 1 공지 기사")])
    hero_grid(heroes)
    html('<div class="ow-legend"><span class="ow-hero new">2026 신규</span><span class="ow-hero recent">복귀 요약 소개</span>'
         '<span class="ow-hero changed">역할 변경</span><span class="ow-legend-t">영웅 수가 늘었다는 사실만으로 이탈 원인을 단정하지 않습니다.</span></div>')


def _official_detail(rs: dict, kp: dict) -> None:
    html('<div class="ow-timeline">' + "".join(
        f'<div class="ow-tl"><div class="ow-tl-d">{escape(o["date"])}</div><div class="ow-tl-t">{escape(o["title"])}</div>'
        f'<div class="ow-tl-b">{escape(o["fact"])}</div><div class="ow-tl-s">{link(o["url"], "공식 원문")}</div></div>'
        for o in rs["official"]) + "</div>")
    note("RE:START는 기존 지원을 대체하지 않고 보완한다.")
    table(["기능", "한계 또는 확인이 필요한 부분"], [[escape(o["title"]), escape(o["limit"])] for o in rs["official"]])
    st.markdown("**역할 구분** — 넥슨: 한국 PC 버전(Steam 제외) 퍼블리싱·라이브 운영·PC방 / 블리자드: 게임 개발·글로벌 운영·Steam·콘솔")
    src = {x["id"]: x for x in kp["sources"]}
    table(["항목", "확인 내용", "출처"],
          [[escape(i["topic"]), escape(i["official"]), " · ".join(link(src[k]["url"], src[k]["kind"]) for k in i["source_ids"])]
           for i in kp["items"]])
    st.caption(f"블리자드 공식 사이트·언론 보도 기준 · 확인일 {COLLECTED_AT}")


# ----------------------------------------------------------------------
# 03 개선 전략 (A·B·C 데모)
def _strategy_tables(rs: dict, ops: pd.DataFrame) -> None:
    opmap = ops[ops["verified"]].set_index("opinion_id")
    for s in rs["strategies"]:
        st.markdown(f"**전략 {s['key']} · {s['name']}** {'' if s['core'] else '(추가 검토)'}")
        rows = [["대상 유저", escape(s["target"])], ["진입 시점", escape(s["entry"])],
                ["작동 흐름", bullets(s["flow"])], ["기존 기능과 차이", escape(s["vs_existing"])],
                ["유저 선택권", escape(s["control"])], ["검증할 가설", escape(s["hypothesis"])],
                ["기대 효과", escape(s["effect"])], ["개발 난이도", escape(s["difficulty"])],
                ["운영 비용", escape(s["op_cost"])], ["예상 부작용", bullets(s["side_effects"])],
                ["대응", bullets(s["responses"])], ["우선순위 이유", escape(s["priority_reason"])],
                ["핵심 KPI", escape(" · ".join(s["kpis"]))]]
        if s.get("owner"):
            rows.insert(0, ["담당", escape(s["owner"])])
        refs = [f'{link(opmap.loc[o, "source_url"], o)} {escape(opmap.loc[o, "summary_ko"][:40])}…' for o in s["from_opinions"] if o in opmap.index]
        rows.append(["근거 의견", "<br>".join(refs) if refs else "—"])
        table(["항목", "내용"], rows)


def _priority_detail(rs: dict, plan: dict) -> None:
    rc = rs["rice"]
    items = pd.DataFrame(rice_table(rc["items"], plan["quarter"]["reach"])).sort_values("score", ascending=False)
    name = {s["key"]: s["name"] for s in rs["strategies"]}
    items["label"] = items["key"] + " " + items["key"].map(name)
    top = items.iloc[0]
    fig = go.Figure(go.Bar(y=items["label"], x=items["score"], orientation="h",
                           marker_color=[C_TREAT if k == top["key"] else C_MUTED for k in items["key"]],
                           text=items["score"].round(0).astype(int).map("{:,}점".format), textposition="outside", cliponaxis=False))
    fig.update_yaxes(autorange="reversed", automargin=True, title="")
    fig.update_xaxes(title="RICE 점수 (점)", range=[0, items["score"].max() * 1.3], rangemode="tozero")
    ox_chart_card(fig, key="rice", kind="sim", title=f"RICE 1위는 {top['label']} ({top['score']:,.0f}점) → A → C → B 순서, D는 보류",
               unit="점 · 도달×영향×확신÷노력 · 파랑 = 1순위", kpis=[], analysis="", decision="",
               basis="도달 = 분기 유입 × 참여율 · 06과 같은 가정값", height=300, legend=False, cols=("전략", "RICE 점수 (점)"))
    st.caption(f"{rc['formula']} · {rc['notes']}")
    table(["전략", "도달 (분기·명)", "영향", "확신", "노력 (인월)", "점수", "근거"],
          [[escape(x.label), f"{x.reach:,.0f}<br><small>{escape(x.reach_basis)}</small>", str(x.impact), str(x.confidence),
            str(x.effort), f"<b>{x.score:,.0f}</b>", escape(x.why)] for x in items.itertuples()])
    cmp_ = rs["comparison"]
    df = pd.DataFrame(cmp_["criteria"])
    fig = go.Figure()
    fig.add_bar(y=df["name"], x=df["restart"], name="RE:START (제안)", orientation="h", marker_color=C_TREAT,
                text=[f"{v}점" for v in df["restart"]], textposition="outside", cliponaxis=False)
    fig.add_bar(y=df["name"], x=df["alt"], name=f"{cmp_['alt_name']} (대안)", orientation="h", marker_color=C_CTRL,
                text=[f"{v}점" for v in df["alt"]], textposition="outside", cliponaxis=False)
    fig.update_layout(barmode="group")
    fig.update_yaxes(autorange="reversed", automargin=True, title="")
    fig.update_xaxes(range=[0, 5.8], dtick=1, title="유리함 (점)")
    tot_r, tot_a = int(df["restart"].sum()), int(df["alt"].sum())
    ox_chart_card(fig, key="cmp", kind="interp", title=f"RE:START {tot_r}점 vs {cmp_['alt_name']} {tot_a}점 → 선택 자유를 지키는 안",
               unit="1~5점 · 높을수록 유리 · 파랑 = 제안안", kpis=[], analysis="", decision="",
               basis="같은 5개 기준·같은 척도 · 정성 평가", height=380, cols=("평가 기준", "점수 (1~5점)"), series="안")
    st.caption(cmp_["alt_desc"] + " · " + cmp_["note"])
    table(["기준", "RE:START", cmp_["alt_name"], "근거"],
          [[escape(c["name"]), str(c["restart"]), str(c["alt"]), escape(c["why"])] for c in cmp_["criteria"]])


# ----------------------------------------------------------------------
# 04 BM 분석 및 개선
def _kpi_detail(rs: dict, plan: dict) -> None:
    ab, ex = rs["ab_test"], rs["experiment"]
    seg, sc, m10 = plan["seg"], plan["sched"], plan["m10"]
    r, nw = seg["복귀"], seg["신규"]
    tgt = {"MDE": lambda k: (f"+{r['mde']['D7']:.1f}%p (기준 {r['base']['D7']:.0f}% 가정)" if "복귀" in k["name"]
                             else f"+{nw['mde']['D7']:.1f}%p (기준 {nw['base']['D7']:.0f}% 가정)"),
           "MDE30": lambda k: f"+{r['mde']['D30']:.1f}%p (배정 기준)",
           "M10": lambda k: f"+{m10['mde']:.1f}%p (기준 {m10['base']:.1f}% 가정)"}
    st.markdown("**실험은 기능 1개씩** — 실험 1 A 복귀 브리핑(복귀 D7) → 실험 2 C 첫 10경기 미션(신규 D7) → 실험 3 B 사용성")
    exp_rows = []
    for e in ex["experiments"]:
        if e["id"] == "1":
            size = f"+{r['mde']['D7']:.1f}%p ({r['base']['D7']:.0f}→{r['base']['D7'] + r['mde']['D7']:.0f}%) · 그룹당 {r['n']:,}명"
            when = f"배정 {sc['e1_assign'][0]}~{sc['e1_assign'][1]}주 · D7 {sc['e1_d7']}주 · D30 {sc['e1_d30']}주"
        elif e["id"] == "2":
            size = f"+{nw['mde']['D7']:.1f}%p ({nw['base']['D7']:.0f}→{nw['base']['D7'] + nw['mde']['D7']:.0f}%) · 그룹당 {nw['n']:,}명"
            when = f"배정 {sc['e2_assign'][0]}~{sc['e2_assign'][1]}주 · D7 {sc['e2_d7']}주 · D30 {sc['e2_d30']}주"
        elif e["id"] == "3":
            size, when = "잔존 효과 판단 안 함", f"{sc['e3'][0]}~{sc['e3'][1]}주"
        else:
            size, when = "실험 1·3 결과 후 별도 산정", "조건 충족 시"
        exp_rows.append([f"<b>실험 {e['id']}</b><br>{escape(e['name'])}<br><small>{escape(e['why'])}</small>",
                         f"{escape(e['segment'])}<br><small>배정 {escape(e['split'])}</small>",
                         f"<b>{escape(e['primary'])}</b><br><small>보조: {escape(e['secondary'])}</small>", escape(size), escape(when)])
    table(["실험 · 이유", "대상 · 배정", "주요 지표 (1개)", "MDE · 필요 표본 (가정)", "일정 (주차)"], exp_rows)
    note(f"기능을 묶으면 효과를 구분할 수 없어 1개씩 실험한다 · α {ex['alpha']} · 검정력 {ex['power']:.0%} · 배정 기준(ITT)")
    html('<div class="ow-defbox"><div><b>D7 잔존율</b> Day 7 <u>당일</u> 접속 (11/1 복귀 → 11/8)</div>'
         '<div><b>7일 내 재방문율</b> Day 1~7 중 <u>하루라도</u> 접속</div>'
         '<div class="ow-defbox-n">재방문율은 항상 D7 이상이라 섞어 비교하지 않는다. 주요 지표는 D7.</div></div>')
    table(["지표 · 역할", "계산 (분자 ÷ 분모)", "측정 시점", "목표 (MDE)"],
          [[f"<b>{escape(k['name'])}</b><span class='ow-tag'>{escape(k['role'])}</span><br><small>{escape(k['target_users'])}</small>",
            f"<span class='ow-num'>{escape(k['numerator'])}</span><span class='ow-den'>÷ {escape(k['denominator'])}</span>",
            escape(k["timing"]), f"<b>{escape(tgt[k['target']](k) if k['target'] in tgt else k['target'])}</b>"]
           for k in rs["kpi_defs"]], cls="ow-kpi-table")
    table(["구분", "지표", "확인 가능 여부"],
          [["실제 자료", "Steam 동시접속자 · 한국 PC방 점유율", "공개 자료 (Steam 한정 · 한국 PC방 표본)"],
           ["내부 데이터 필요", "DAU · D7 · D30 · 경기 완료율", "넥슨·블리자드 로그 필요 · 기준값은 모두 가정"]])
    tiles([("복귀 D7 표본 (실험 1)", f"{r['n']:,}명 × 2", f"주당 유입 {r['weekly']:,.0f}명 가정 → 배정 {r['assign_weeks']}주"),
           ("신규 D7 표본 (실험 2)", f"{nw['n']:,}명 × 2", f"주당 유입 {nw['weekly']:,.0f}명 가정 → 배정 {nw['assign_weeks']}주"),
           ("검정 조건", f"α {ex['alpha']} · 검정력 {ex['power']:.0%}", "양측 두 비율 차이 검정 · 배정 기준(ITT)")])
    html(_timeline(plan))
    html('<div class="ow-sig">'
         '<div><b>통계적 유의성</b>효과 추정치의 95% 신뢰구간 하한이 0보다 큰가 → 우연이 아닐 가능성</div>'
         f'<div><b>사업적 효과</b>점추정이 MDE(+{r["mde"]["D7"]:.1f}%p) 이상인가, 개발·운영비 대비 추가 잔존 인원이 충분한가</div>'
         '<div><b>판단</b>둘 다 충족하고 안전 지표가 나빠지지 않을 때만 확대. 유의하지만 작으면 조건부 확대</div></div>')
    note("보수적 기준: 실제 효과가 정확히 MDE면 확대 확률은 약 50%다. 효과 없는 기능을 넓히는 오판을 줄이는 쪽을 택했다.")
    table(["결과", "판단 기준"], [[f"<b>{escape(d['result'])}</b>", escape(d["rule"])] for d in rs["decision_rules"]])
    st.markdown(f"**측정 방법** — {ab['method']}  \n**배정** — {ab['unit']}  \n**즉시 중단** — {ab['stop_rule']}")
    st.markdown("**표본 계산기** · 기본값은 실험 1(복귀 D7)")
    c1, c2, c3 = st.columns(3)
    base = c1.number_input("대조군 D7 (%, 가정)", 1.0, 99.0, float(r["base"]["D7"]), step=1.0, key="ab_base")
    mde = c2.number_input("MDE · 배정 기준 (%p)", 0.1, 30.0, float(round(r["mde"]["D7"], 2)), step=0.1, key="ab_mde")
    part = c3.slider("기능 참여율 (%, 가정)", 1, 100, int(r["participation"]), key="ab_part")
    c1, c2, c3 = st.columns(3)
    alpha = c1.selectbox("유의수준", [0.01, 0.05, 0.10], index=1, key="ab_alpha")
    power = c2.selectbox("검정력", [0.8, 0.9], index=0, key="ab_power")
    weekly = c3.number_input("주당 유입 (명, 가정)", 100, 10_000_000, int(r["weekly"]), step=1000, key="ab_weekly")
    n_itt = sample_size_two_proportions(base / 100, min(base + mde, 99.9) / 100, alpha, power)
    tiles([("참여자 기준 필요 개선 폭", f"+{mde / part * 100:.1f}%p", "MDE ÷ 참여율"),
           ("그룹당 필요 표본", "—" if n_itt is None else f"{n_itt:,}명", "두 비율 차이 검정"),
           ("배정 기간", "—" if n_itt is None else f"{math.ceil(2 * n_itt / weekly)}주", "두 그룹 합 ÷ 주당 유입")])


def _sim_inputs(rs: dict) -> dict:
    ex = rs["experiment"]
    coh, fn, upd, ld0 = ex["cohorts"], ex["funnel"], ex["uplift"], ex["leading"]
    c1, c2 = st.columns(2)
    n_new = c1.number_input("신규 코호트 (명)", 0, 10_000_000, int(coh["신규"]["size"]), step=1000, key="rs_n_new")
    n_ret = c2.number_input("복귀 코호트 (명)", 0, 10_000_000, int(coh["복귀"]["size"]), step=1000, key="rs_n_ret")
    c1, c2 = st.columns(2)
    b_new = {d: c1.number_input(f"신규 {d} (%)", 0.0, 100.0, float(coh["신규"]["base"][d]), step=1.0, key=f"rs_new_{d}") for d in ("D1", "D7", "D30")}
    b_ret = {d: c2.number_input(f"복귀 {d} (%)", 0.0, 100.0, float(coh["복귀"]["base"][d]), step=1.0, key=f"rs_ret_{d}") for d in ("D1", "D7", "D30")}
    c1, c2 = st.columns(2)
    p_new = c1.slider("신규 미션 참여율 (%)", 0, 100, int(coh["신규"]["participation"]), key="rs_p_new")
    p_ret = c2.slider("복귀 브리핑 시작률 (%)", 0, 100, int(coh["복귀"]["participation"]), key="rs_p_ret")
    c1, c2, c3 = st.columns(3)
    uplift = {"D1": c1.slider("개선 폭 D1 (%p)", 0.0, 20.0, float(upd["D1"]), 0.5, key="rs_u1"),
              "D7": c2.slider("개선 폭 D7 (%p)", 0.0, 20.0, float(upd["D7"]), 0.5, key="rs_u7"),
              "D30": c3.slider("개선 폭 D30 (%p)", 0.0, 20.0, float(upd["D30"]), 0.5, key="rs_u30")}
    c1, c2, c3 = st.columns(3)
    f_first = c1.slider("접속 → 첫 경기 (%)", 0, 100, int(fn["first"]), key="rs_f1")
    f_3 = c2.slider("첫 경기 → 3경기 (%)", 0, 100, int(fn["m3"]), key="rs_f3")
    f_10 = c3.slider("3경기 → 10경기 (%)", 0, 100, int(fn["m10"]), key="rs_f10")
    c1, c2 = st.columns(2)
    fu3 = c1.slider("참여자 3경기 개선 (%p)", 0.0, 30.0, float(fn["up3"]), 0.5, key="rs_fu3")
    fu10 = c2.slider("참여자 10경기 개선 (%p)", 0.0, 30.0, float(fn["up10"]), 0.5, key="rs_fu10")
    c1, c2 = st.columns(2)
    base_dau = c1.number_input("코호트 외 활성 유저 (명/일)", 0, 100_000_000, 100_000, step=10_000, key="rs_bd")
    act = c2.slider("잔존 유저 일일 접속 확률 (%)", 1, 100, 50, key="rs_act")
    c1, c2 = st.columns(2)
    arrive = c1.slider("유입 기간 (일)", 1, 60, 14, key="rs_arr")
    horizon = c2.slider("관측 기간 (일)", 30, 180, 90, step=10, key="rs_hz")
    st.caption("퍼널은 KPI '첫 10경기 완료율'과 같이 신규 코호트만으로 계산합니다. PC방(D)·이벤트 비용은 MVP 제외라 기본값으로 고정합니다.")
    return dict(n_new=n_new, n_ret=n_ret, b_new=b_new, b_ret=b_ret, p_new=p_new, p_ret=p_ret, uplift=uplift,
                f_first=f_first, f_3=f_3, f_10=f_10, fu3=fu3, fu10=fu10, base_dau=base_dau, act=act, arrive=arrive,
                horizon=horizon, d7_of_10=int(fn["d7_of_10"]), ld=ld0, mcost=int(ex["cost"]["monthly_cost_per_person"]),
                effort=float(sum(x["effort"] for x in rs["rice"]["items"] if x["key"] in ("A", "B", "C"))))


def _sim_results(rs: dict, plan: dict, x: dict) -> None:
    errs = [f"신규: {e}" for e in validate_base(x["b_new"])] + [f"복귀: {e}" for e in validate_base(x["b_ret"])]
    if errs:
        for e in errs:
            st.error(e)
        st.info("설정에서 D1 ≥ D7 ≥ D30 이 되도록 고쳐 주세요.")
        return
    ld = x["ld"]
    inp = SimInput(
        cohorts=[CohortInput("신규", int(x["n_new"]), x["b_new"], x["p_new"]), CohortInput("복귀", int(x["n_ret"]), x["b_ret"], x["p_ret"])],
        uplift=x["uplift"], funnel_first=x["f_first"], funnel_3=x["f_3"], funnel_10=x["f_10"], funnel_d7_of_10=x["d7_of_10"],
        funnel_uplift_3=x["fu3"], funnel_uplift_10=x["fu10"], briefing_completion=int(ld["briefing_completion"]), card_usage=int(ld["card_usage"]),
        pc_reach=int(ld["pc_reach"]), pc_participation=int(ld["pc_participation"]), pc_completion=int(ld["pc_completion"]),
        pc_revisit=int(ld["pc_revisit"]), pc_companion=int(ld["pc_companion"]), reward_cost=3000, event_fixed_cost=20_000_000,
        headcount=x["effort"], months=1.0, monthly_cost_per_person=x["mcost"],
        base_dau=x["base_dau"], active_prob=x["act"], arrival_days=x["arrive"], horizon=x["horizon"], funnel_cohort="신규")
    res = run(inp)
    r, f = res.retention, res.funnel
    total, f_total = x["n_new"] + x["n_ret"], x["n_new"]
    for w in res.warnings:
        st.warning(w)

    def rate(day, col):
        return r.loc[r["day"] == day, col].sum() / total * 100 if total else float("nan")
    cats, before, after = [], [], []
    for d in ["D7", "D30"]:
        for coh in ["복귀", "신규"]:
            row = r[(r["cohort"] == coh) & (r["day"] == d)].iloc[0]
            cats.append(f"{coh} {d}")
            before.append(row["base_rate"])
            after.append(row["new_rate"])
        cats.append(f"전체 {d}")
        before.append(rate(d, "base_users"))
        after.append(rate(d, "new_users"))
    fig = hpair(cats, before, after, xtitle="잔존율 (%)", names=("도입 전 · 대조군 (가정 기준값)", "도입 후 · 실험군 (가정)"))
    ri = cats.index("복귀 D7")
    ox_chart_card(fig, key="sim", kind="sim", title=f"복귀 D7 {before[ri]:.1f}% → {after[ri]:.1f}% (참여율 × 개선 폭)",
               unit="% · 회색 = 대조군, 파랑 = 실험군 · 이름 옆 = 변화 폭", kpis=[], analysis="", decision="",
               basis="같은 코호트 전후 · 전체 = 인원 가중 평균", height=520, cols=("코호트 · 지표", "잔존율 (%)"), series="그룹")
    m10_b = f.loc[3, "base"] / f_total * 100 if f_total else float("nan")
    m10_n = f.loc[3, "improved"] / f_total * 100 if f_total else float("nan")
    keep = f["stage"] != "D7 재접속(10경기 완료자 중)"
    fv = f[keep].reset_index(drop=True)
    fb = (fv["base"] / f_total * 100).tolist() if f_total else [0] * len(fv)
    fn_ = (fv["improved"] / f_total * 100).tolist() if f_total else [0] * len(fv)
    fig = hpair(list(fv["stage"]), fb, fn_, xtitle="접속 대비 (%)", names=("도입 전 · 대조군 (가정)", "도입 후 · 실험군 (가정)"), xmax=118)
    ox_chart_card(fig, key="funnel", kind="sim", title=f"신규 10경기 완료 {m10_b:.1f}% → {m10_n:.1f}% · 완료율만 오르고 D7이 그대로면 미션 수정",
               unit="신규 접속 대비 % · 회색 = 대조군, 파랑 = 실험군", kpis=[], analysis="", decision="",
               basis=f"신규 {f_total:,}명(가정) · KPI와 같은 대상", height=400, cols=("단계", "신규 접속 대비 (%)"), series="그룹")
    dd = res.dau.pivot(index="day", columns="scenario", values="dau")
    dau_b, dau_n = dd.iloc[-1]["현재 가정"], dd.iloc[-1]["RE:START 적용 가정"]
    fig = go.Figure()
    cur, app = res.dau[res.dau["scenario"] == "현재 가정"], res.dau[res.dau["scenario"] != "현재 가정"]
    fig.add_scatter(x=cur["day"], y=cur["dau"], name="현재 · 대조군 (가정)", line=dict(color=C_CTRL, width=3))
    fig.add_scatter(x=app["day"], y=app["dau"], name="RE:START 적용 · 실험군 (가정)", line=dict(color=C_TREAT, width=2, dash="dot"))
    fig.update_yaxes(title="DAU (명)", tickformat=",", rangemode="tozero", range=[0, res.dau["dau"].max() * 1.1])
    fig.update_xaxes(title="코호트 유입 시작 후 경과일 (일)")
    ox_chart_card(fig, key="dau", kind="sim", title=f"{x['horizon']}일차 DAU 차이 {dau_n - dau_b:+,.0f}명 → DAU 대신 코호트 잔존율로 판단",
               unit="명/일 · 세로축 0부터", kpis=[], analysis="", decision="",
               basis="잔존 곡선만 다르게 적용 · Steam과 무관", height=400, cols=("경과일 (일)", "DAU (명)"), series="시나리오")
    st.markdown("**KPI 연결 구조 (가설)**")
    table(["개선 방향", "전략", "확인할 지표"],
          [[escape(k["lever"]), escape(k["strategies"]), escape(" · ".join(k["leading"]))] for k in rs["kpi_chain"]])
    st.markdown("**계산식** — 개선 후 잔존율 = 기존 잔존율 + 참여율 × 개선 폭 (D1 ≥ D7 ≥ D30 보정) · 전체 잔존율 = 인원 가중 평균 · "
                "적응 퍼널 = 이전 단계 × 전환율 (신규 코호트만) · DAU = 코호트 외 활성 유저 + Σ 일별 유입 × 잔존 곡선 × 일일 접속 확률 · "
                "기존 유저는 실험 대상이 아니며 불만·신고율로만 관찰")


# ----------------------------------------------------------------------
# 07 최종 실행 계획
def _cost_detail(rs: dict, plan: dict, ops: pd.DataFrame) -> None:
    sc, seg = plan["sched"], plan["seg"]["복귀"]
    mc = rs["experiment"]["cost"]["monthly_cost_per_person"]
    eff = {x["key"]: x["effort"] for x in rs["rice"]["items"]}
    add = plan["quarter"]["added_d7"]
    cost = {k: eff[k] * mc for k in eff}
    v = ops[ops["verified"]]
    ret = v[v["user_type"] == "복귀"]
    table(["단계", "A 복귀 브리핑 (먼저 실행)"], [
        ["<b>문제</b>", "복귀 후 바뀐 영웅·규칙을 모른 채 첫 주에 막힌다 (이탈 원인은 가설 · 매칭·실력·팀원 요인도 함께 확인)"],
        ["<b>근거</b>", f"검증 의견 {len(v)}건 중 학습·적응 {_learn(v)}건 · 복귀 유저 {len(ret)}건 중 {_learn(ret)}건 · 공식 복귀 요약과 방향이 같음"],
        ["<b>해결책</b>", "접속 직후 놓친 변경점 3개 요약 (영웅·밸런스·매칭은 바꾸지 않음)"],
        ["<b>비용</b>", f"{eff['A']}인월 × {mc / 1e4:,.0f}만 원 = <b>{cost['A'] / 1e4:,.0f}만 원</b> (일회성 · 가정) · 유지보수 별도"],
        ["<b>KPI</b>", f"복귀 D7 (ITT) · 목표 +{seg['mde']['D7']:.1f}%p (목표값 · 실적 아님) · 보조: 브리핑 완료율 · 첫 10경기 완료율 · D30"],
        ["<b>실험</b>", f"복귀 계정 50:50 · 그룹당 {seg['n']:,}명 · {sc['e1_d7']}주차 D7 판정 (주당 유입 가정 기준)"],
        ["<b>사업적 판단</b>", "<b>소규모 파일럿 → 유의하면 확대</b> · 개발비가 가장 작고 실패해도 손실이 작다"]])
    rice = pd.DataFrame(rice_table(rs["rice"]["items"], plan["quarter"]["reach"])).sort_values("score", ascending=False)
    sname = {s["key"]: s for s in rs["strategies"]}
    order = {"A": "1순위 · 먼저", "C": "2순위", "B": "3순위 · 수동형부터", "D": "보류"}
    table(["순서", "개선안", "RICE", "이유", "구현 난이도"],
          [[f"<b>{order.get(x.key, '')}</b>", f"{x.key} {escape(sname[x.key]['name'])}", f"{x.score:,.0f}점",
            escape(x.why), escape(sname[x.key].get("feasibility", ""))] for x in rice.itertuples()])
    table(["개선안", "공수", "개발·운영 비용", "기대 효과 (가정)", "추가 D7 1명당"], [
        ["<b>A</b> 복귀 브리핑", f"{eff['A']}인월", f"<b>{cost['A'] / 1e4:,.0f}만 원</b>", f"분기 추가 복귀 D7 약 {add['A']:,.0f}명", f"약 {cost['A'] / add['A']:,.0f}원"],
        ["<b>C</b> 첫 10경기 미션", f"{eff['C']}인월", f"<b>{cost['C'] / 1e4:,.0f}만 원</b>", f"분기 추가 신규 D7 약 {add['C']:,.0f}명", f"약 {cost['C'] / add['C']:,.0f}원"],
        ["<b>B</b> 전투 학습 카드", f"{eff['B']}인월", f"<b>{cost['B'] / 1e4:,.0f}만 원</b>", "사용성 검증 · 잔존 효과는 판단 안 함", "—"],
        ["<b>A~C 합계</b>", f"{eff['A'] + eff['B'] + eff['C']}인월", f"<b>{(cost['A'] + cost['B'] + cost['C']) / 1e4:,.0f}만 원</b>",
         f"D(보류) {eff['D']}인월 · {cost['D'] / 1e4:,.0f}만 원은 합계 제외", ""]])
    st.caption(f"비용 = 공수 × 1인 월 {mc / 1e4:,.0f}만 원 (가정) · 1명당 비용은 A 단독(약 {cost['A'] / add['A']:,.0f}원)과 A~C 합계 기준이 다르다 · 매출 연결은 06 탭")


def _failure_detail(rs: dict, plan: dict) -> None:
    seg, add, mc = plan["seg"], plan["quarter"]["added_d7"], rs["experiment"]["cost"]["monthly_cost_per_person"]
    eff = {x["key"]: x["effort"] for x in rs["rice"]["items"]}
    q_in = plan["quarter"]["inflow"]
    st.markdown(
        f"- **추가 복귀 D7 약 {add['A']:,.0f}명** = 분기({plan['quarter']['weeks']}주) 복귀 유입 {q_in['복귀']:,.0f}명 × 복귀 D7 MDE +{seg['복귀']['mde']['D7']:.1f}%p (ITT · 가정)\n"
        f"- **A 비용 {eff['A'] * mc / 1e4:,.0f}만 원** = {eff['A']}인월 × {mc / 1e4:,.0f}만 원 (개발·QA 인건비 가정 · 실제 견적 아님) · 유지보수·콘텐츠 갱신 비용은 **미포함**\n"
        "- **D7 +2.0%p는 실험 목표**이지 달성한 성과가 아니다 · 모집단·기준 잔존율은 파일럿 전 과거 로그로 다시 정한다\n"
        f"- **일정 민감도** 그룹당 {seg['복귀']['n']:,}명 × 2 필요 · 주당 복귀 유입 {seg['복귀']['weekly']:,.0f}명(가정)이면 배정 {seg['복귀']['assign_weeks']}주 → "
        f"{plan['sched']['e1_d7']}주차 D7 판정 · 주당 3,000명이면 배정 {math.ceil(2 * seg['복귀']['n'] / 3000)}주\n"
        "- 추가 D7 유저당 비용은 이미 들어온 복귀 유저를 더 남기는 비용이다 · 새 유저 획득 비용(CAC)과 비교하지 않는다")
    table(["구분", "운영상 정의 (실험용 · 실제 데이터 아님)"],
          [["<b>복귀 유저</b>", "90일 이상 미접속 후 재접속 · 같은 계정의 과거 플레이 이력 있음 · 신규 가입 계정 제외"],
           ["<b>세그먼트</b>", "미접속 기간 (90~180일 / 180일+) × 과거 경쟁전 경험 (있음 / 없음) → 층화 무작위 배정"],
           ["<b>오염 방지</b>", "계정 단위 배정 · 실험 기간 중 그룹 고정 · 같은 기간 대조군과만 비교 (전후 비교 금지)"]])
    table(["D7이 개선되지 않았을 때", "확인 지표", "결정"],
          [["브리핑을 보지 않음", "브리핑 시작률", "<b>수정</b> · 진입 위치·문구 실험 후 재실험"],
           ["끝까지 보지 않음", "완료율 · 이탈 지점", "<b>수정</b> · 길이 축소 (핵심 3개)"],
           ["봤지만 이해 못 함", "이해 확인 1문항 · 문의율", "<b>수정</b> · 표현·예시 교체"],
           ["이해했지만 적응으로 안 이어짐", "첫 10경기 완료율 · 30분 내 다음 경기", "<b>중단</b> 검토 · 정보 부족이 원인이 아님 → C 미션으로 넘김"]])


def _ops_detail(rs: dict) -> None:
    mv, pl = rs["mvp"], rs["pilot"]
    html(f'<div class="ow-grid2"><div class="ow-card plain"><div class="ow-card-k">MVP 포함</div>{bullets(mv["in"])}</div>'
         f'<div class="ow-card plain"><div class="ow-card-k">이번에는 제외 · 별도 검토</div>{bullets(mv["out"])}</div></div>')
    table(["제약·리스크", "대응"], [[escape(x["risk"]), escape(x["response"])] for x in rs["risks"]])
    table(["담당", "역할"], [[escape(o["team"]), escape(o["role"])] for o in pl["owners"]])
    st.markdown("**필요한 이벤트 로그** · " + " · ".join(pl["logs"]))
    st.markdown("**출시 전 점검** · " + " · ".join(pl["checklist"]))
    st.markdown("**롤백 기준** · " + " · ".join(pl["rollback"]))




def biz_result_html(r: dict, vt: dict, guard: str) -> str:
    bep = (f"{r['bep']:.1f}%" if r["bep_state"] == "ok" else ("0%" if r["bep_state"] == "already" else "달성 불가"))
    if r["bep_state"] == "ok":
        bep_sub = f"구매 유저 {r['bep_buyers']:,}명 필요"
    elif r["bep_state"] == "already":
        bep_sub = "스킨 판매 없이도 손익분기"
    else:
        bep_sub = "현재 노출·가격·수수료로는 100%여도 미달"
    roi = "—" if r["roi"] is None else f"{r['roi']:+.0f}%"
    t, d = vt[r["verdict"]]
    sign = "neg" if r["profit"] < 0 else "pos"
    return (f'<div class="ox-res"><div><span>예상 구매 유저</span><b>{r["buyers"]:,.0f}명</b><small>노출 × 구매 전환율</small></div>'
            f'<div><span>순증 매출 (수수료 차감 후)</span><b>{won(r["net"])}</b><small>스킨 {won(r["skin_net"])} + 잔존 {won(r["ret_rev"])} (차감 전)</small></div>'
            f'<div class="{sign}"><span>예상 사업 이익</span><b>{won(r["profit"])}</b><small>ROI {roi} · 총비용 {won(r["cost"])}</small></div>'
            f'<div><span>손익분기 구매 전환율</span><b>{bep}</b><small>{bep_sub}</small></div></div>'
            f'<div class="ox-verdict {r["verdict"]}"><b>{t}</b> → {d}<small>{guard}</small></div>')


def biz_steps(r: dict) -> list[list[str]]:
    x = r["x"]
    return [
        ["1 예상 구매 유저", "노출 유저 × 구매 전환율", f"{r['buyers']:,.0f}명"],
        ["2 신규 스킨 총매출", "구매 유저 × 판매 가격", won(r["gross"])],
        ["3 기존 상품 매출 잠식액", "총매출 × 잠식률", won(-r["cannib"])],
        ["4 순증 상품 매출", "2 − 3", won(r["skin_net"])],
        ["5 순증 활성 유저", f"유입 × D30 개선폭 + 유입 × (D7 − D30 개선폭) × 30/91", f"{r['active']:,.0f}명"],
        ["6 잔존 추가 매출", "5 × PUR × ARPPU (분기)", won(r["ret_rev"])],
        ["7 수수료", f"(4 + 6) × {x['fee']:g}%", won(-r["fee"])],
        ["8 수수료 차감 후 순증 매출", "4 + 6 − 7", won(r["net"])],
        ["9 총비용", "개발 인월 × 인월당 비용 + 마케팅 + 기타", won(-r["cost"])],
        ["10 예상 사업 이익", "8 − 9", f"<b>{won(r['profit'])}</b>"],
        ["11 손익분기 구매 전환율", "(총비용 − 잔존 매출 × (1 − 수수료)) ÷ (노출 × 가격 × (1 − 잠식률) × (1 − 수수료))",
         f"{r['bep']:.2f}%" if r["bep_state"] == "ok" else ("0%" if r["bep_state"] == "already" else "달성 불가")],
        ["12 ROI", "이익 ÷ 총비용", "—" if r["roi"] is None else f"{r['roi']:+.1f}%"],
    ]


C_LOSS = "#DC2626"


def _biz_charts(sim: dict, r: dict) -> None:
    from gamepulse.sim.ow_business import preset, profit_curve, simulate
    x = r["x"]
    xs, ys = profit_curve(sim, x)
    fig = go.Figure()
    ys = [y / 1e4 for y in ys]
    fig.add_scatter(x=xs, y=[y if y >= 0 else None for y in ys], mode="lines", line=dict(color=C_TREAT, width=3), name="이익", connectgaps=False)
    fig.add_scatter(x=xs, y=[y if y < 0 else None for y in ys], mode="lines", line=dict(color=C_LOSS, width=3), name="손실", connectgaps=False)
    fig.add_hline(y=0, line_color="#9CA3AF", line_width=1)
    if r["bep_state"] == "ok":
        fig.add_vline(x=r["bep"], line_dash="dot", line_color="#1F2937")
        fig.add_annotation(x=r["bep"], y=0, text=f"손익분기 {r['bep']:.1f}%", showarrow=False, yshift=14, xanchor="left", xshift=4)
    fig.add_scatter(x=[x["conv"]], y=[r["profit"] / 1e4], mode="markers", marker=dict(size=12, color=C_TREAT if r["profit"] >= 0 else C_LOSS,
                    line=dict(color="white", width=2)), name="현재 입력")
    fig.update_xaxes(title="구매 전환율 (%)", ticksuffix="%")
    fig.update_yaxes(title="분기 이익 (만 원)", tickformat=",")
    ox_chart_card(fig, key="bzcurve", kind="sim", title="구매 전환율에 따른 분기 이익 · 점선 = 손익분기",
               unit="만 원 · 파랑 = 이익, 빨강 = 손실", kpis=[], analysis="", decision="", basis="", height=340,
               cols=("구매 전환율 (%)", "분기 이익 (만 원)"), series="구분")
    names = list(sim["presets"])
    keys = sorted({k for n in names for k in sim["presets"][n]})
    sc = [simulate(sim, {**x, **{k: preset(sim, n)[k] for k in keys}}) for n in names]
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        fig = go.Figure(go.Bar(x=names, y=[s["profit"] / 1e4 for s in sc], marker_color=[C_TREAT if s["profit"] >= 0 else C_LOSS for s in sc],
                               text=[won(s["profit"]) for s in sc], textposition="outside", cliponaxis=False))
        fig.add_hline(y=0, line_color="#9CA3AF", line_width=1)
        fig.update_yaxes(title="분기 이익 (만 원)", tickformat=",")
        ox_chart_card(fig, key="bzscen", kind="sim", title="보수적 · 기본 · 낙관적 시나리오 이익",
                   unit="만 원 · 전환율·잠식률·잔존 개선·PUR·ARPPU만 바꾸고 나머지는 현재 입력", kpis=[], analysis="", decision="",
                   basis="", height=320, legend=False, cols=("시나리오", "분기 이익 (만 원)"))
    with c2:
        steps = [("스킨 총매출", r["gross"], "relative"), ("잠식", -r["cannib"], "relative"), ("잔존 매출", r["ret_rev"], "relative"),
                 ("수수료", -r["fee"], "relative"), ("개발비", -r["dev"], "relative"), ("마케팅", -r["marketing"], "relative"),
                 ("기타", -r["other"], "relative"), ("이익", r["profit"], "total")]
        fig = go.Figure(go.Waterfall(x=[s[0] for s in steps], y=[s[1] / 1e4 for s in steps], measure=[s[2] for s in steps],
                                     increasing=dict(marker=dict(color=C_TREAT)), decreasing=dict(marker=dict(color=C_CTRL)),
                                     totals=dict(marker=dict(color=C_TREAT if r["profit"] >= 0 else C_LOSS)),
                                     text=[won(s[1]) for s in steps], textposition="outside", connector=dict(line=dict(color="#E5E7EB"))))
        fig.update_yaxes(title="만 원", tickformat=",")
        ox_chart_card(fig, key="bzwf", kind="sim", title="총매출에서 이익까지 차감 구조",
                   unit="만 원 · 파랑 = 더함, 회색 = 뺌", kpis=[], analysis="", decision="", basis="", height=320, legend=False,
                   cols=("항목", "금액 (만 원)"))


# ======================================================================
# 2026-11 최종 구성: 10개 섹션을 7개 탭에 순서대로 배치
#   01 개요·핵심 문제(01·02) · 02 게임 화면·VOC(03·04) · 03 RE:START(05) · 04 기존 스킨 BM(06)
#   05 신규 BM(07·08) · 06 KPI·사업성(09) · 07 최종 판단(10)
def h(title: str, kind: str = "", lead: str = "", num: str = "", name: str = "") -> None:
    """결론형 섹션 제목 · num/name 이 있으면 '01 서비스 및 분석 개요' 번호 줄을 위에 붙인다."""
    k = f'<span class="ox-k {kind}">{KIND_TXT[kind]}</span>' if kind else ""
    p = f"<p>{lead}</p>" if lead else ""
    n = f'<div class="ox-secn"><b>{num}</b>{escape(name)}</div>' if num else ""
    html(f'<div class="ox-h{" n" if num else ""}">{n}<h3>{escape(title)}</h3>{k}{p}</div>')


@st.cache_data(show_spinner=False, max_entries=24)
def _jpg_b64(path: str, mtime: float) -> str:
    """사용자가 준 캡처를 크기·비율 그대로 JPEG 로 (자르거나 늘리지 않음)."""
    import io

    from PIL import Image
    with Image.open(path) as im:
        rgb = im.convert("RGB")
    buf = io.BytesIO()
    rgb.save(buf, "JPEG", quality=86, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _fig(bz: dict, key: str, cap: str = "") -> str:
    """클릭하면 원본 크기로 커지는 이미지 · 실제 화면과 기획 시안을 캡션 첫 단어로 구분."""
    s = bz["shots"][key]
    p = ROOT_DIR / s["file"]
    if not p.is_file():
        return ""
    real = s["kind"] == "real"
    tag = "실제 게임 화면" if real else "자체 제작 기획 시안"
    src = "작성자 캡처 · 2026 시즌 5" if real else "실제 게임에 없음"
    extra = f" · {escape(cap)}" if cap else ""
    return (f'<figure class="ox-fig {"real" if real else "plan"}"><details class="ox-zoom"><summary title="클릭하면 크게 보기">'
            f'<img src="data:image/jpeg;base64,{_jpg_b64(str(p), p.stat().st_mtime)}" alt="{escape(s["label"])}" loading="lazy"></summary></details>'
            f'<figcaption><b>{tag}</b>{escape(s["label"])} · {src}{extra}</figcaption></figure>')


def _pair(a: str, b: str) -> None:
    html(f'<div class="ox-pair">{a}{b}</div>')


def _facts(items: list[str]) -> str:
    return '<ul class="ox-facts">' + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


def _biz_base(bz: dict) -> dict:
    from gamepulse.sim.ow_business import preset, simulate
    sim = bz["simulation"]
    return simulate(sim, preset(sim, "기본"))


def _pkg_base(bz: dict) -> dict:
    from gamepulse.sim.ow_business import package_sim
    c = bz["your_choice"]
    return package_sim(c, c["sim"]["defaults"])


def summary_rows(rs: dict, ops: pd.DataFrame, plan: dict, bz: dict) -> list[tuple[str, str]]:
    """한눈에 보기 · 홈 비교표와 같은 항목."""
    v = ops[ops["verified"]]
    b, pk = _biz_base(bz), _pkg_base(bz)
    mde = plan["seg"]["복귀"]["mde"]["D7"]
    bep = f"신규 스킨 손익분기 전환율 {b['bep']:.1f}%" if b["bep_state"] == "ok" else "신규 스킨 손익분기 불가 조건"
    return [
        ("핵심 문제", "① 신규·복귀 유저의 학습 부담 ② 영웅별 스킨 상품 수 차이와 고정형 묶음의 선택권 한계"),
        ("주요 근거", f"유저 의견 {len(v)}건 중 {_learn(v)}건 학습·적응 어려움 · 공식 영웅 54명 · 캡처: 키리코 스킨 11종 vs 메르시 25종"),
        ("복귀율 전략", "PROJECT RE:START: 복귀 브리핑 → 첫 10경기 미션 → 전투 학습 카드"),
        ("매출 전략", "YOUR HERO (유저 참여형 스킨 제작) · YOUR CHOICE (선택형 스킨 패키지)"),
        ("마케팅", "별도 캠페인 미정 · YOUR HERO 투표가 유저 참여 창구"),
        ("핵심 KPI", f"복귀 D7 +{mde:.1f}%p · 패키지 구매 전환율 · 평균 결제 금액 · 개별 스킨 매출 잠식"),
        ("예상 사업 효과", f"YOUR CHOICE 예시 입력 기준 매출 {pk['diff_pct']:+.0f}% · {bep} (모두 가정)"),
        ("주요 리스크", "학습 부담과 이탈의 인과는 미검증 · 할인 패키지의 개별 스킨 매출 잠식"),
    ]


# ======================================================================
def render() -> None:
    g = GAMES["overwatch"]
    try:
        kp, rs, heroes = load_json("korea_publishing.json"), load_json("restart.json"), load_json("heroes.json")
        bz = load_json("business.json")
        steam, pc, ops, tl = load_steam(), load_pcbang(), load_opinions(), load_timeline()
    except OverwatchDataError as e:
        st.error(f"오버워치 자료를 불러오지 못했습니다: {e}")
        return
    statuses = all_status(load_manifest())

    html('<div class="gp-ow-page"></div>')  # 오버워치 전용 CSS 범위 표식 (포인트 컬러 #F99E1A)
    plan = experiment_plan(rs["experiment"])
    _cover(bz, heroes)

    i = tab_nav()
    ox_badge_legend()
    html(f'<div class="ow-pane-mark" data-tab="{SECTIONS[i][0]}"></div>')  # 정적 보고서가 탭 경계를 찾는 표식
    _FIGS.clear()
    [lambda: _t1_overview(rs, ops, plan, bz, heroes),
     lambda: _t2_screens_voc(rs, kp, steam, pc, ops, heroes, statuses, bz),
     lambda: _t3_restart(rs, ops, heroes, tl, statuses, plan),
     lambda: _t4_skin_bm(bz),
     lambda: _t5_new_bm(bz),
     lambda: _t6_business(rs, plan, bz),
     lambda: _t7_plan(rs, g, statuses, plan, ops, bz)][i]()
    image_credits()


def _cover(bz: dict, heroes: dict) -> None:
    """첫 화면: 로고 · 분석 주제 두 가지 (복귀율 전략 / 매출 전략을 구분)."""
    lg = ROOT_DIR / bz["shots"]["logo"]["file"]
    logo = (f'<img class="owx-logo" src="data:image/png;base64,{_png_b64(str(lg), lg.stat().st_mtime)}" alt="오버워치 로고">'
            if lg.is_file() else "")
    html(f'<div class="owx-hero ox-cover">{logo}<div class="owx-t"><div class="ow-cover-t">OVERWATCH · 사업PM 분석</div>'
         '<div class="owx-q" role="heading" aria-level="1">진입장벽은 낮추고,<br>스킨 선택권은 넓힌다</div>'
         '<div class="ox-tracks"><span><b>복귀율</b>신규·복귀 유저 진입장벽 → PROJECT RE:START</span>'
         '<span><b>매출</b>스킨 중심 BM → YOUR HERO · YOUR CHOICE</span></div></div></div>')


# ----------------------------------------------------------------------
# 탭 01 · 섹션 01 서비스 및 분석 개요 · 02 핵심 문제 정의
def _t1_overview(rs: dict, ops: pd.DataFrame, plan: dict, bz: dict, heroes: dict) -> None:
    v = ops[ops["verified"]]
    n_new = sum(1 for x in heroes["heroes"] if x.get("new_2026"))
    h("두 문제를 따로 본다: 복귀율은 진입장벽, 매출은 스킨 상품 구성", "", num="01", name="서비스 및 분석 개요",
      lead="블리자드 개발 · 한국 PC(Steam 제외)는 2026-08-12부터 넥슨이 퍼블리싱 (2026-03-30 계약 발표) · 공식 영웅 54명 (2026-11-19 확인)")
    stats([(f"{len(v)}건", "검증한 유저 의견 (인벤·디시·블리자드 포럼)", "real"),
           (f"{len(rs['official'])}건", "확인한 공식 업데이트", "real"),
           ("13장", "작성자 게임 캡처 (영웅·상점·스킨·전투)", "real")])
    table(["구분", "문제", "제안", "판단 지표"], [
        ["<b>복귀율</b>", "신규·복귀 유저의 학습 부담", "PROJECT RE:START", f"복귀 D7 잔존율 (목표 +{plan['seg']['복귀']['mde']['D7']:.1f}%p)"],
        ["<b>매출</b>", "영웅별 상품 차이 · 고정형 묶음", "YOUR HERO · YOUR CHOICE", "패키지 구매 전환율 · 평균 결제 금액"],
    ], cls="ox-two")
    st.caption("두 전략은 목표 지표가 달라 따로 실험하고 따로 판단한다.")

    h(f"배울 것은 계속 늘고, 스킨 상품은 영웅·구성에 따라 고를 폭이 다르다", "", num="02", name="핵심 문제 정의")
    html('<div class="ox-prob">'
         '<div><span>① 신규·복귀 유저 진입장벽</span>' + _facts([
             f"공식 영웅 <b>54명</b> · 2026년 신규 <b>{n_new}명</b>",
             "영웅 1명 설명 <b>10개</b> (무기·궁극기·기술 3·지속 능력·특전 4 · 시온 기준)",
             f"유저 의견 {len(v)}건 중 <b>{_learn(v)}건</b>이 학습·적응 어려움",
             "복귀 시 메인 화면에 변경점 요약 없음"]) +
         '<small>학습 부담이 실제 이탈로 이어지는지는 내부 로그와 A/B 테스트로 확인해야 한다.</small></div>'
         '<div><span>② 스킨 중심 BM</span>' + _facts([
             "영웅별 스킨 수 표기: 키리코 <b>11종</b> · 메르시 <b>25종</b>",
             "상점 추천 묶음: 15개 고정 구성 <b>6,900 코인</b> (정가 9,500 · 27% 할인)",
             "신화 스킨은 프리즘 <b>50 → 10 → 10 → 10</b> 단계 해금 (로드호그·우양 동일)",
             "개별 스킨 가격 300 · 1,000 · 1,900 코인 (키리코 목록)"]) +
         '<small>유저가 원하는 영웅과 판매 상품이 어긋나는지는 영웅별 플레이·구매 데이터로 확인해야 한다.</small></div></div>')
    with st.expander("한눈에 보기 · 8개 항목 요약"):
        html('<div class="ox-sumt">' + "".join(f"<div><span>{escape(k)}</span><p>{escape(t)}</p></div>"
                                                for k, t in summary_rows(rs, ops, plan, bz)) + "</div>")


# ----------------------------------------------------------------------
# 탭 02 · 섹션 03 실제 게임 화면 기반 분석 · 04 유저 의견 및 VOC 분석
def _t2_screens_voc(rs: dict, kp: dict, steam: pd.DataFrame, pc: pd.DataFrame, ops: pd.DataFrame, heroes: dict,
                    statuses: dict, bz: dict) -> None:
    h("영웅 54명이 한 화면에, 이름과 설명은 고른 영웅만 보인다", "real", num="03", name="실제 게임 화면 기반 분석")
    html(_fig(bz, "hero_roster"))
    html(_facts(["돌격 15 · 공격 23 · 지원 16 = 54명 (공식 영웅 페이지 수와 같음)",
                 "초상화에는 이름이 없고, 고른 영웅(오리사)만 이름·역할 특성·소개가 보인다",
                 "영웅마다 레벨 표시(오리사 1레벨)가 따로 있다"]))
    with st.expander(f"다른 실제 화면 · 영웅 선택(실전)·스킬 설명 · 공식 영웅 {len(heroes['heroes'])}명 목록"):
        _screens_detail(heroes, statuses)

    v = ops[ops["verified"]]
    other = ops[~ops["verified"]]
    plat = v["platform"].map(lambda p: "인벤" if "인벤" in p else ("디시인사이드" if "디시" in p else "블리자드 포럼")).value_counts()
    reddit = int(other["verification_status"].str.contains("Reddit").sum())
    h(f"유저 의견 {len(v)}건 중 {_learn(v)}건이 '바뀐 것을 따라잡기 어렵다'", "real", num="04", name="유저 의견 및 VOC 분석",
      lead=(f"원문을 직접 확인한 {len(v)}건 (기준 50건 충족) · " + " · ".join(f"{k} {n}" for k, n in plat.items())
            + f" · 제외·대기 {len(other)}건 (Reddit {reddit}건은 수집 환경 접근 차단) · 한 의견이 여러 유형에 걸치면 각각 집계"))
    _opinion_chart(v)
    rep = v[v["opinion_id"].isin(rs["rep_opinions"]) & (v["sentiment"] != "긍정")].sort_values("published_date", ascending=False).head(2)
    if not rep.empty:
        html(f'<div class="ow-grid2">{"".join(_opinion_card(r) for _, r in rep.iterrows())}</div>')
    p = rs["problem"]
    html('<div class="ox-cause">' + '<i>→</i>'.join(
        f'<div class="{f.get("kind", "hypo")}"><small>{KIND_TXT[f.get("kind", "hypo")]}</small><b>{escape(f["step"])}</b></div>'
        for f in p["flow"]) + "</div>")
    st.caption("정보 과부하·전투 이해 실패는 의견으로 확인 · 반복 패배와 이탈의 연결은 아직 확인하지 않음")
    with st.expander(f"유저 의견 {len(v)}건 전체 · 원문 링크 · 검색 · 표본과 분류 기준"):
        _opinions_all(rs, ops)
    with st.expander(f"원인 {len(p['flow'])}단계 근거·검증 지표 · 다른 원인 {len(p['alternatives'])}가지"):
        _cause_detail(p, v, code_counts(v))
    with st.expander(f"블리자드 기존 지원 {len(rs['official'])}건 · 넥슨 퍼블리싱 범위"):
        _official_detail(rs, kp)
    with st.expander("시장 지표 (Steam 동시접속 · 한국 PC방 점유율) · 원자료 — 복귀 이탈과 인과 연결 안 함"):
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            _steam_chart(steam)
        with c2:
            _pc_chart(pc)
        _metric_sources(pc)


# ----------------------------------------------------------------------
# 탭 03 · 섹션 05 PROJECT RE:START
def _t3_restart(rs: dict, ops: pd.DataFrame, heroes: dict, tl: pd.DataFrame, statuses: dict, plan: dict) -> None:
    v = ops[ops["verified"]]
    cc = code_counts(v)
    h("신규와 복귀를 나눠, 지금 필요한 정보만 먼저 보여 준다", "mock", num="05", name="신규·복귀 유저 개선 전략 — PROJECT RE:START",
      lead="영웅·밸런스·매칭은 바꾸지 않는다 · 모든 안내는 끌 수 있다 · 기대 효과는 검증 전")
    rows = [
        ("신규·복귀 구분 적응 경로", "신규와 복귀 유저가 같은 첫 화면에서 시작 (복귀 메인 화면에 변경점 안내 없음)",
         "접속 이력으로 신규·복귀를 나눠 첫 안내를 다르게", "90일 이상 미접속 = 복귀 → A · 신규 → C · 둘 다 끄기 가능",
         "필요 없는 안내를 줄이고 필요한 정보부터", "경로별 D7 잔존율 · 안내 끄기 비율"),
        ("A 복귀 브리핑", "무엇이 바뀌었는지 모른 채 경기 시작", "마지막 접속일 이후 바뀐 영웅·시스템만 3분 요약",
         "접속 직후 1회 · 3단계 카드 · 메뉴에서 다시 보기", "첫 경기 전 변경점 인지", "복귀 D7 (주요) · 브리핑 완료율"),
        ("기존 플레이 영웅 기반 추천", "하던 영웅이 바뀌었거나 새 영웅을 모른다", "과거 주로 한 역할·영웅 기준으로 비슷한 영웅 1~2명 추천",
         "브리핑 마지막 단계에 노출 · 연습장 바로가기", "새 영웅을 시도할 출발점", "추천 영웅 플레이율 · 첫 3경기 내 이탈"),
        ("B 전투 학습 카드", "왜 졌는지, 상대 기술에 어떻게 대응할지 모른다", "경기 후 어려웠던 상대를 골라 핵심 기술·대처법 확인",
         "유저가 직접 고르는 수동형 MVP · 하루 표시 횟수 조절", "같은 상대에게 반복되는 패배 감소", "카드 사용률 · 재대결 생존 시간"),
        ("C 첫 10경기 학습 미션", "무엇부터 익힐지 모른다 · 현재 과제는 'N경기 완료' 횟수형", "역할·기술 → 상대 대응 → 팀 플레이 순서의 미션",
         "1~3·4~6·7~10경기 단계 · 승패 무관 · 외형 보상만", "학습 순서가 생겨 초반 적응", "신규 D7 (주요) · 10경기 완료율"),
        ("복귀 초기 부담 완화", f"복귀 직후 변경점과 실력 격차가 한꺼번에 (매칭·실력 차이 의견 {int(cc.get('매칭·실력 차이', 0))}건)",
         "복귀 유저도 C 미션을 선택 참여 · 브리핑·카드·미션 모두 선택형", "강제 노출 없음 · 영웅·밸런스·매칭 변경 없음",
         "첫 주 부담 완화", "복귀 첫 3경기 이탈 · 미션 끄기 비율"),
    ]
    table(["전략", "문제", "개선 방안", "운영 방식", "기대 효과 (검증 전)", "측정 KPI"],
          [[f"<b>{escape(a)}</b>", *[escape(x) for x in r]] for a, *r in rows], cls="ox-strat6")
    st.caption("A·B·C는 기존 시안 · '구분 적응 경로'와 '기존 플레이 영웅 기반 추천', '복귀 초기 부담 완화'는 A·C 운영 방식을 구체화한 항목")
    t = st.tabs(["A 복귀 브리핑", "C 첫 10경기 미션", "B 전투 학습 카드"])
    with t[0]:
        _proto_a(heroes, tl, statuses)
    with t[1]:
        _proto_c(statuses)
    with t[2]:
        _proto_b(heroes, statuses)
    with st.expander("전략 A~D 상세 · 대상 · 작동 흐름 · 부작용 · 근거 의견"):
        _strategy_tables(rs, ops)
    with st.expander("우선순위 근거 · RICE 점수 · 대안(영웅 선택 제한안) 비교"):
        _priority_detail(rs, plan)


# ----------------------------------------------------------------------
# 탭 04 · 섹션 06 기존 스킨 BM 분석
def _t4_skin_bm(bz: dict) -> None:
    ex = bz["existing_bm"]
    h("영웅마다 스킨 수가 다르고, 묶음 상품은 구성이 고정돼 있다", "real", num="06", name="기존 스킨 BM 분석",
      lead=escape(bz["capture_note"]) + " · 원화 가격은 캡처에 없어 코인·프리즘 단위로만 적는다")
    _pair(_fig(bz, "battle_pass"), _fig(bz, "store_main"))
    html(_facts(["배틀 패스: '프리미엄으로 업그레이드해 즉시 3개의 보상을 잠금 해제' 문구 · 보상마다 잠금 표시와 숫자(14·12·8)",
                 "상점 추천: 묶음 상품 15개를 한 번에 6,900 코인 (정가 9,500 · 27% 할인) · 구성은 고를 수 없음 · 새로고침 6일 남음",
                 "상점 탭: 추천 · 할인 중 · 신화 · 시즌 · 재출시 패스 · 이스포츠 · 맞춤 추천"]))

    h("같은 화면에서도 영웅별 스킨 수와 가격대가 다르다", "real")
    _pair(_fig(bz, "kiriko_skins"), _fig(bz, "mercy_skins"))
    table(["", "키리코", "메르시"], [
        ["스킨 수 표기", "<b>1/11</b>", "<b>15/25</b>"],
        ["목록에 보이는 가격", "1,900 코인 4종 · 1,000 코인 1종 · 300 코인 4종 · 프리즘 1종(신화)", "보이는 항목에 가격 표기 없음"],
        ["획득 경로 문구", "점쟁이(전설): 전리품 상자로 잠금 해제", "용기수(전설): 가끔 상점에서 획득 가능"],
    ], cls="ox-cmp")
    st.caption("출시 시기가 다른 영웅이라 스킨 수 차이에는 출시 기간 영향이 섞여 있다 · 일부 1,900 항목은 다른 코인 아이콘으로 표기")

    h("신화 스킨은 이미 '단계별 해금' 구조다: 50 → 10 → 10 → 10 프리즘", "real")
    _pair(_fig(bz, "mythic_roadhog"), _fig(bz, "mythic_wuyang"))
    html(_facts(["로드호그 '과거의 기사'와 우양 '용의 협객' 모두 4단계 · 1레벨 50, 2~4레벨 각 10 = 총 80 프리즘",
                 "단계마다 추가: 1레벨 기술 시각 효과·마스크/머리카락·색상 → 2레벨 마스크/머리카락 2종 → 3레벨 색상 2종 → 4레벨 스킨 시각 효과",
                 "'모든 레벨 잠금 해제' 버튼으로 한 번에 구매 가능"]))
    html('<div class="ox-purpose"><span>BM 판단</span>신화 스킨이 이미 단계 해금 구조라 이전에 검토한 \'성장형 스킨\'은 겹쳐 제외했다. '
         '대신 <b>상품이 적은 영웅의 수요 확인(YOUR HERO)</b>과 <b>고정형 묶음의 선택권 보완(YOUR CHOICE)</b>을 제안한다.</div>')
    with st.expander("판매 상품 8종 정리 · 캡처에서 확인한 내용만"):
        table(["상품", "판매 방식", "가격", "구성·해금 구조", "근거 화면"],
              [[f"<b>{escape(p['name'])}</b>", escape(p["sale"]), escape(p["price"]), escape(p["unlock"]), escape(p["source"])]
               for p in ex["products"]], cls="ox-bmt")
        st.caption(ex["note"])


# ----------------------------------------------------------------------
# 탭 05 · 섹션 07 YOUR HERO · 08 YOUR CHOICE
def _bm_block(bz: dict, key: str, img: str, num: str) -> None:
    b = bz[key]
    h(f"{b['title']} {b['slogan']}", "mock", num=num, name=f"신규 BM 제안 — {b['title'].rstrip('.')}", lead=escape(b["kind"]))
    html(f'<div class="ox-bm">{_fig(bz, img, b.get("image_note", ""))}</div>')
    html(f'<div class="ox-purpose"><span>기획 목적</span>{escape(b["purpose"])}</div>')


def _t5_new_bm(bz: dict) -> None:
    hero, ch = bz["your_hero"], bz["your_choice"]
    _bm_block(bz, "your_hero", "your_hero", "07")
    html('<div class="ox-cols3">'
         '<div><b>운영 구조</b><ol>' + "".join(f"<li><em>{escape(s['t'])}</em> {escape(s['d'])}</li>" for s in hero["steps"]) + "</ol></div>"
         f'<div><b>기대 효과</b>{bullets(hero["effects"])}</div><div><b>측정 KPI</b>{bullets(hero["kpis"])}</div></div>')

    from gamepulse.sim.ow_business import tier_prices
    _bm_block(bz, "your_choice", "your_choice", "08")
    prices = tier_prices(ch)
    table(["구분", "할인율", "예시 가격", "정가 합계 대비"],
          [[f"<b>{escape(t['name'])}</b>", f"{t['disc']}%" if t["disc"] else "없음", f"<b>{p:,}원</b>",
            f"{t['n'] * ch['base_price']:,}원 − {t['n'] * ch['base_price'] - p:,}원" if t["disc"] else "—"]
           for t, p in zip(ch["tiers"], prices)], cls="ox-price")
    st.caption(f"{ch['price_note']} · 가격 = 기본 {ch['base_price']:,}원 × 스킨 수 × (1 − 할인율)")
    html('<div class="ox-cols3">'
         f'<div><b>운영 방식</b>{bullets(ch["ops"])}</div><div><b>기대 효과</b>{bullets(ch["effects"])}</div>'
         f'<div><b>측정 KPI</b>{bullets(ch["kpis"])}</div></div>')


# ----------------------------------------------------------------------
# 탭 06 · 섹션 09 KPI 및 사업성 시뮬레이션
SIM_KEYS = "bz_"
PKG_KEYS = "pk_"


def _sim_apply(values: dict, prefix: str = SIM_KEYS) -> None:
    for k, v in values.items():
        st.session_state[prefix + k] = v


def _t6_business(rs: dict, plan: dict, bz: dict) -> None:
    seg = plan["seg"]
    rr, nw = seg["복귀"], seg["신규"]
    h("복귀율과 매출은 지표를 나눠서 판단한다", "mock", num="09", name="KPI 및 사업성 시뮬레이션")
    table(["트랙", "지표", "기준", "판단"], [
        ["<b>복귀율</b> · RE:START A", "복귀 D7 잔존율", f"{rr['base']['D7']:.0f}% → {rr['base']['D7'] + rr['mde']['D7']:.0f}% (목표·가정 +{rr['mde']['D7']:.1f}%p)", "95% 신뢰구간 하한 &gt; 0 이고 목표 이상이면 확대"],
        ["<b>복귀율</b> · RE:START C", "신규 D7 잔존율", f"{nw['base']['D7']:.0f}% → {nw['base']['D7'] + nw['mde']['D7']:.0f}% (목표·가정 +{nw['mde']['D7']:.1f}%p)", "A 결과 후 실험 2로 판정"],
        ["<b>매출</b> · YOUR CHOICE", "패키지 구매 전환율 · 평균 결제 금액", "판매 테스트에서 측정 (목표값 미정)", "개별 스킨 잠식을 빼고도 순증일 때 확대"],
        ["<b>매출</b> · YOUR HERO", "투표 참여율 · 참여 유저 구매 전환율", "투표 파일럿에서 측정 (목표값 미정)", "제작 비용 대비 예상 수익이 남을 때 제작"],
    ], cls="ox-kpit")
    _pkg_sim(bz)
    _biz_sim(bz)
    with st.expander("A/B 실험 설계 · KPI 정의 10개 · 표본·일정 · 판단 기준"):
        _kpi_detail(rs, plan)
    res_box = st.expander("잔존율 시뮬레이션 결과 · D7·D30 · 첫 10경기 퍼널 · DAU (가정)")
    with st.expander("잔존율 시뮬레이션 설정 (가정값)"):
        inputs = _sim_inputs(rs)
    with res_box:
        _sim_results(rs, plan, inputs)


def pkg_result_html(r: dict) -> str:
    if not r["ok"]:
        return (f'<div class="ox-verdict loss"><b>구매 비중 합계 {r["share_total"]:g}%</b> → 100%가 되도록 고쳐 주세요'
                '<small>개별 · 3개 · 5개 패키지 비중의 합이 100%일 때만 계산합니다.</small></div>')
    pct = "—" if r["diff_pct"] is None else f"{r['diff_pct']:+.1f}%"
    sign = "neg" if r["diff"] < 0 else "pos"
    disc = "—" if r["disc_pct"] is None else f"{r['disc_pct']:.1f}%"
    return (f'<div class="ox-res"><div><span>예상 구매자</span><b>{r["buyers"]:,.0f}명</b><small>노출 × 개선 후 전환율</small></div>'
            f'<div><span>평균 결제 금액</span><b>{r["avg"]:,.0f}원</b><small>구매 비중 × 패키지 가격</small></div>'
            f'<div><span>예상 매출</span><b>{won(r["rev1"])}</b><small>기존 {won(r["rev0"])}</small></div>'
            f'<div class="{sign}"><span>기존 대비 증감</span><b>{won(r["diff"])}</b><small>증감률 {pct}</small></div></div>'
            f'<p class="ox-note">할인으로 덜 받는 금액 {won(r["discount"])} (정가 기준 매출의 {disc}) · 판매 스킨 {r["skins"]:,.0f}개 · '
            '기존 매출은 구매자가 개별 스킨 1개를 산다고 가정했다. 이미 여러 개를 개별로 사던 유저가 패키지로 옮기면 1인당 결제액은 오히려 줄 수 있다.</p>')


def _pkg_sim(bz: dict) -> None:
    from gamepulse.sim.ow_business import package_sim
    ch = bz["your_choice"]
    s = ch["sim"]
    for k, v in s["defaults"].items():
        st.session_state.setdefault(PKG_KEYS + k, v)
    h("YOUR CHOICE 시뮬레이터: 전환율과 패키지 비중이 매출을 바꾼다", "sim", escape(s["note"]))
    html('<div class="ox-js-start" data-demo="pkg"></div>')
    box = st.container()
    cols = st.columns(3)
    for j, f in enumerate(s["fields"]):
        fmt = "%.1f" if f["step"] < 1 else "%d"
        cast = float if f["step"] < 1 else int
        cols[j % 3].number_input(f"{f['label']} ({f['unit']})", min_value=cast(f["min"]), max_value=cast(f["max"]),
                                 step=cast(f["step"]), format=fmt, key=PKG_KEYS + f["key"])
    st.button("초기화", key="pk_reset", on_click=_sim_apply, args=(dict(s["defaults"]), PKG_KEYS))
    r = package_sim(ch, {k: st.session_state[PKG_KEYS + k] for k in s["defaults"]})
    with box:
        html(pkg_result_html(r))
    html('<div class="ox-js-end"></div>')


def _biz_sim(bz: dict) -> None:
    from gamepulse.sim.ow_business import GUARD_TEXT, VERDICT_TEXT, fields, preset, simulate
    sim = bz["simulation"]
    fs = fields(sim)
    for k, v in sim["defaults"].items():
        st.session_state.setdefault(SIM_KEYS + k, v)
    h("신규 스킨 + RE:START 손익: 구매 전환율이 손익을 가른다", "sim", escape(sim["note"]) + " · 신규 스킨은 YOUR HERO 출시 스킨 기준")
    html('<div class="ox-js-start" data-demo="biz"></div>')
    result_box = st.container()
    cols = st.columns(4)
    for i, name in enumerate(sim["presets"]):
        cols[i].button(name, key=f"bz_preset_{i}", on_click=_sim_apply, args=(preset(sim, name),), width="stretch")
    cols[3].button("초기화", key="bz_reset", on_click=_sim_apply, args=(dict(sim["defaults"]),), width="stretch")

    def num(f, col):
        fmt = "%.1f" if f["step"] < 1 else "%d"
        cast = float if f["step"] < 1 else int
        hi = cast(f["max"])
        if f["key"] == "d30_uplift":            # D30 개선폭 ≤ D7 개선폭
            hi = cast(st.session_state[SIM_KEYS + "d7_uplift"])
            st.session_state[SIM_KEYS + "d30_uplift"] = min(st.session_state[SIM_KEYS + "d30_uplift"], hi)
        col.number_input(f"{f['label']} ({f['unit']})", min_value=cast(f["min"]), max_value=hi, step=cast(f["step"]),
                         format=fmt, key=SIM_KEYS + f["key"], help=f["help"])
    basic = [f for f in sim["fields"] if f.get("basic")]
    for f, col in zip(basic, st.columns(len(basic))):
        num(f, col)
    with st.expander("고급 설정 · 잠식률 · 잔존율 개선폭 · PUR · ARPPU · 수수료 · 개발비 · 기타 운영비"):
        adv = [f for f in sim["fields"] if not f.get("basic")]
        for j in range(0, len(adv), 3):
            for f, col in zip(adv[j:j + 3], st.columns(3)):
                num(f, col)
    r = simulate(sim, {k: st.session_state[SIM_KEYS + k] for k in fs})
    with result_box:
        html(biz_result_html(r, VERDICT_TEXT, GUARD_TEXT))
    _biz_charts(sim, r)
    with st.expander("계산 순서 · 공식 · 현재 값"):
        table(["단계", "계산", "현재 값"], biz_steps(r))
        st.markdown("- 기간: 매출·ARPPU·비용 모두 **분기(91일)** 기준\n"
                    "- 수수료는 유저 결제액(스킨 순증 매출 + 잔존 추가 매출)에만 적용하고, 비용에는 적용하지 않는다\n"
                    "- 잔존 추가 매출은 스킨 매출과 따로 계산한다 (스킨 구매 여부와 무관한 RE:START 잔존 효과)\n"
                    "- D30 잔존 유저는 D7 잔존 유저에 포함되므로 D7·D30을 더하지 않는다 · D7까지만 남은 유저는 분기 중 30일만 활성으로 본다\n"
                    "- 손익분기 구매 전환율은 위 이익 계산식에서 이익 = 0 이 되는 전환율을 직접 푼 값이다")
    html('<div class="ox-js-end"></div>')
    with st.expander("가정값 출처 · 기본 · 보수적 · 낙관적"):
        names = list(sim["presets"])
        table(["변수", *names, "설명"],
              [[f"{escape(f['label'])} ({escape(f['unit'])})", *[f"{preset(sim, n)[f['key']]:,}" for n in names], escape(f["help"])]
               for f in sim["fields"]])


# ----------------------------------------------------------------------
# 탭 07 · 섹션 10 최종 인사이트 및 실행 판단
def _t7_plan(rs: dict, g: dict, statuses: dict, plan: dict, ops: pd.DataFrame, bz: dict) -> None:
    sc = plan["sched"]
    r = plan["seg"]["복귀"]
    v = ops[ops["verified"]]
    b = _biz_base(bz)
    h("복귀율은 A 파일럿부터, 매출은 제작비가 없는 YOUR CHOICE 테스트부터", "mock", num="10",
      name="최종 인사이트 및 사업PM 관점의 실행 판단")
    html('<ol class="ox-ins">'
         f'<li><b>진입장벽은 확인됐고, 이탈과의 연결은 아직이다.</b> 의견 {len(v)}건 중 {_learn(v)}건과 실제 화면이 학습 부담을 보여 주지만 '
         '이탈 원인인지는 로그와 A/B 테스트로 확인한다.</li>'
         '<li><b>스킨 상품 구성 차이는 화면으로 확인됐다.</b> 키리코 11종과 메르시 25종, 15개 고정 묶음은 사실이고, '
         '유저 선호와 어긋나는지는 영웅별 플레이·구매 데이터로 확인한다.</li>'
         f'<li><b>제작비가 드는 상품은 수요 확인이 먼저다.</b> 가정 기준 신규 스킨 손익분기 전환율은 '
         + (f"{b['bep']:.1f}%" if b["bep_state"] == "ok" else "달성 불가") +
         '로 높다. 그래서 YOUR HERO는 투표로 수요를 본 뒤 제작하고, 기존 스킨을 쓰는 YOUR CHOICE를 먼저 시험한다.</li></ol>')
    table(["트랙", "먼저 할 일", "확대 · 중단 기준"], [
        ["<b>복귀율</b>", f"A 복귀 브리핑 {sc['decision'] + 2}주 파일럿 (복귀 유저 50:50)", f"복귀 D7 +{r['mde']['D7']:.1f}%p 이상 유의 → C·B 확대 · 미달 시 수정 후 재실험"],
        ["<b>매출 ①</b>", "YOUR CHOICE 소규모 판매 테스트 (기존 스킨 대상 · 할인율 비교)", "패키지 전환율·평균 결제 금액 상승, 개별 스킨 잠식 제외 후 순증 → 확대"],
        ["<b>매출 ②</b>", "YOUR HERO 투표 파일럿 (제작 전)", "투표 참여율·영웅별 선호 확인 → 제작 비용 대비 수익이 남는 영웅만 제작"],
    ], cls="ox-two")
    h(f"RE:START 파일럿 일정 · 준비 2주 + 운영 {sc['decision']}주")
    weeks = [("준비", "-2~0주", "이벤트 로그 · 실험 배정 · 기능 스위치 · CS 문구"),
             ("실험 1", f"{sc['e1_assign'][0]}~{sc['e1_assign'][1]}주", "A 복귀 브리핑 배정 (복귀 유저 50:50)"),
             ("실험 2", f"{sc['e2_assign'][0]}~{sc['e2_assign'][1]}주", f"C 학습 미션 배정 · {sc['e1_d7']}주차 A의 D7 1차 판정"),
             ("실험 3", f"{sc['e3'][0]}~{sc['e3'][1]}주", f"B 수동형 사용성 · {sc['e1_d30']}주차 A의 D30 → 확대 확정"),
             ("결정", f"{sc['decision']}주", "C의 D30 확인 · 확대·수정·중단 최종 결정")]
    html('<div class="ox-gantt">' + "".join(f'<div><em>{escape(a)}</em><b>{escape(w)}</b><span>{escape(t)}</span></div>'
                                            for a, w, t in weeks) + "</div>")
    st.caption("YOUR CHOICE·YOUR HERO 일정은 기획 확정 후 정한다.")
    with st.expander("RE:START 확대 · 수정 · 중단 기준 (4단계)"):
        table(["결과", "기준"], [[f"<b>{escape(d['result'])}</b>", escape(d["rule"])] for d in rs["decision_rules"]])
    with st.expander("대표 전략 A 요약 · 우선순위 · 개발·운영 비용 검산"):
        _cost_detail(rs, plan, ops)
    with st.expander("복귀 유저 정의 · 실패 대응 · 일정 민감도"):
        _failure_detail(rs, plan)
    with st.expander("MVP 범위 · 현실적인 제약과 대응 · 담당 · 이벤트 로그 · 롤백 기준"):
        _ops_detail(rs)
    with st.expander("한계 · 고지"):
        note(rs["summary"]["limit"])
        st.caption(f"{rs['cover']['footnote']} · {rs['disclaimer']} · YOUR HERO·YOUR CHOICE와 가격은 자체 기획 시안 · 자료 확인일 {COLLECTED_AT}")

    if os.getenv("GAMEPULSE_SHOW_ARCHIVE") != "1":   # v0.1 예시 분석은 로컬 보관함에서만 (archive/README.md)
        return
    with st.expander("보관함 · v0.1 분석 (가상 예시 데이터 · 비공개)"):
        t = st.tabs(["문제 정의", "불만 유형(가상)", "원인 가설", "개선 전략", "KPI", "심층 분석"])
        with t[0]:
            game_page._problem(g)
        with t[1]:
            game_page._complaints(g)
        with t[2]:
            game_page._hypotheses(g)
        with t[3]:
            game_page._strategies(g)
        with t[4]:
            game_page._kpis(g)
        with t[5]:
            DEEP_DIVES["overwatch"]()
