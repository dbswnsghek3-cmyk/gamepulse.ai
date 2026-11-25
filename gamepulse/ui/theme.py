"""게임별 테마 색상 (2026-11) — 한 곳에서 관리.

- acc  : 메인 색상 (사용자 지정 HEX · 임의 변경 금지)
- ink  : 흰 배경 위 글자·얇은 선용 (메인 색이 흰 배경에서 대비가 낮을 때만 같은 계열의 진한 색)
- soft : 연한 배경 (강조 영역 바탕)
- on   : 메인 색 위 글자색 (선택된 탭·버튼)

적용 방식
- 화면: app.py 가 게임 페이지마다 <div class="gp-theme" data-game="..."> 표식을 넣고, CSS(theme_css)가 그 페이지에만 변수를 건다.
- 차트: st.plotly_chart 를 감싸 기본 파랑 계열을 해당 게임 메인 색으로 바꾼다 (데이터·구성은 그대로).
- 정적 사이트: export_static 이 같은 THEMES 로 JavaScript 데모 안의 파랑 계열을 바꾼다.
"""

from __future__ import annotations

import re

THEMES = {
    "overwatch": {"acc": "#F99E1A", "ink": "#A35F00", "soft": "#FEF3E2", "on": "#1F2937", "name": "오버워치 2"},
    "fconline": {"acc": "#16A34A", "ink": "#15803D", "soft": "#DCFCE7", "on": "#FFFFFF", "name": "FC 온라인"},
    "pubg": {"acc": "#142D50", "ink": "#142D50", "soft": "#E6ECF5", "on": "#FFFFFF", "name": "PUBG 배틀그라운드"},
    "dnf": {"acc": "#C62828", "ink": "#C62828", "soft": "#FDECEC", "on": "#FFFFFF", "name": "던전앤파이터"},
}
# 차트 기본 파랑(진한) → 메인 색 · 연한 파랑 → soft 계열
_BLUE = {"#2563EB", "#1E5EFF", "#1D4ED8", "#3B82F6", "#4A7DFF", "#1E40AF"}
_SKY = {"#8DB3FF", "#93C5FD", "#BFDBFE", "#60A5FA", "#B9CFFF", "#DCE8FF"}
_SOFT_CHART = {"overwatch": "#FBC774", "fconline": "#86EFAC", "pubg": "#8FA3C2", "dnf": "#EF9A9A"}


def _swap(c, t: dict, game: str):
    if isinstance(c, str):
        u = c.upper()
        if u in _BLUE:
            return t["acc"]
        if u in _SKY:
            return _SOFT_CHART[game]
        return c
    if isinstance(c, (list, tuple)):
        return [_swap(x, t, game) for x in c]
    return c


def recolor(fig, game: str):
    """Plotly 그림의 파랑 계열 색만 게임 메인 색으로 바꾼다 (값·구성은 그대로)."""
    t = THEMES.get(game)
    if t is None:
        return fig
    for tr in fig.data:
        for path in ("marker.color", "line.color", "marker.line.color", "fillcolor",
                     "increasing.marker.color", "decreasing.marker.color", "totals.marker.color"):
            obj, *rest = path.split(".")
            try:
                node = tr
                for p in path.split(".")[:-1]:
                    node = getattr(node, p)
                val = getattr(node, path.split(".")[-1])
            except (AttributeError, ValueError):
                continue
            if val is None:
                continue
            new = _swap(val if not hasattr(val, "tolist") else val.tolist(), t, game)
            if new != val:
                try:
                    node.update({path.split(".")[-1]: new})
                except (ValueError, TypeError):
                    pass
    if fig.layout.colorway:
        fig.update_layout(colorway=_swap(list(fig.layout.colorway), t, game))
    return fig


def install_chart_theme() -> None:
    """st.plotly_chart 를 한 번만 감싼다 · 그릴 때 현재 페이지(session_state['page'])의 테마를 적용."""
    import streamlit as st
    if getattr(st.plotly_chart, "_gp_themed", False):
        return
    orig = st.plotly_chart

    def themed(fig=None, *a, **kw):
        try:
            game = st.session_state.get("page")
            if fig is not None and game in THEMES:
                fig = recolor(fig, game)
        except Exception:   # 테마 적용 실패는 원래 색으로 그대로 그린다
            pass
        return orig(fig, *a, **kw)
    themed._gp_themed = True
    st.plotly_chart = themed


def recolor_scripts(html: str, game: str) -> str:
    """정적 사이트: <script> 안의 파랑 계열 HEX 만 메인 색으로 (본문·데이터 문자열은 건드리지 않음)."""
    t = THEMES.get(game)
    if t is None:
        return html

    def fix(m):
        s = m.group(0)
        for b in _BLUE:
            s = re.sub(b, t["acc"], s, flags=re.I)
        for b in _SKY:
            s = re.sub(b, _SOFT_CHART[game], s, flags=re.I)
        return s
    return re.sub(r"<script\b[^>]*>.*?</script>", fix, html, flags=re.S)


def theme_css() -> str:
    """게임 페이지별 CSS 변수 + 공통 강조 위치 (배경 전체는 칠하지 않음)."""
    out = []
    for g, t in THEMES.items():
        out.append(f':root:has(.gp-theme[data-game="{g}"]) {{ --g-acc: {t["acc"]}; --g-ink: {t["ink"]}; --g-soft: {t["soft"]}; --g-on: {t["on"]}; }}')
    out.append("""
/* 선택된 탭 (정적 탭 · Streamlit 라디오 탭) */
:root:has(.gp-theme) .ow-tabbar button[aria-selected="true"] { background: var(--g-acc) !important; border-color: var(--g-acc) !important; color: var(--g-on) !important; box-shadow: none !important; }
:root:has(.gp-theme) .ow-tabbar button[aria-selected="true"] b { color: var(--g-on) !important; }
:root:has(.gp-theme) .ow-tabbar button b { color: var(--g-ink) !important; }
:root:has(.gp-theme) .ow-tabbar button[aria-selected="true"] b { color: var(--g-on) !important; }
:root:has(.gp-theme) :is(.st-key-pg_tab, .st-key-fc_tab, .st-key-df_tab) label[data-testid="stRadioOption"]:has(input:checked) { background: var(--g-acc) !important; border-color: var(--g-acc) !important; box-shadow: none !important; }
:root:has(.gp-theme) :is(.st-key-pg_tab, .st-key-fc_tab, .st-key-df_tab) label[data-testid="stRadioOption"]:has(input:checked) p { color: var(--g-on) !important; }
/* 제목 · 소제목 · 핵심 수치 · 강조 */
:root:has(.gp-theme) .sx-pane-h { color: var(--g-ink) !important; border-color: var(--g-acc) !important; }
:root:has(.gp-theme) .ow-head h3 { border-left: 4px solid var(--g-acc); padding-left: 0.6rem; }
:root:has(.gp-theme) .ow-sub { color: var(--g-ink) !important; }
:root:has(.gp-theme) .ow-kpi-v, :root:has(.gp-theme) .ow-tile-v { color: var(--g-ink) !important; }
:root:has(.gp-theme) .ow-tile, :root:has(.gp-theme) .ow-kpi { border-top-color: var(--g-acc) !important; }
:root:has(.gp-theme) .ow-conclusion, :root:has(.gp-theme) .owx-int { border-left-color: var(--g-acc) !important; }
:root:has(.gp-theme) .sx-exp > summary .sx-more { color: var(--g-ink) !important; }
:root:has(.gp-theme) .sx-btn { border-color: var(--g-acc) !important; color: var(--g-ink) !important; }
:root:has(.gp-theme) .stButton button[kind="primary"] { background: var(--g-acc) !important; border-color: var(--g-acc) !important; color: var(--g-on) !important; }
:root:has(.gp-theme) .gp-xlinks a { color: var(--g-ink) !important; }
/* 상단 메뉴: 현재 게임 */
:root:has(.gp-theme) .sx-top nav a.on { color: var(--g-ink) !important; background: var(--g-soft) !important; }
/* 홈: 게임 카드별 색 */""")
    for g, t in THEMES.items():
        out.append(f'.hm-game:has(.hm-img.{g}) {{ border-top: 4px solid {t["acc"]} !important; }} '
                   f'.hm-game:has(.hm-img.{g}) .hm-k {{ color: {t["ink"]} !important; }}')
    return "\n".join(out) + "\n"
