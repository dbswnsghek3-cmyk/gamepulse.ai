"""사업PM 어시스턴트 — 포트폴리오 기반 검색형 PM 어시스턴트 (생성형 AI 아님).

gamepulse/ai/portfolio_index.py 가 4개 게임 분석 자료(JSON)에서 질문과 맞는 항목을 찾아
'문제 정의 → 근거 → 개선 전략 → KPI → 출처' 순서로 원문을 보여 준다.
맞는 항목이 없으면 '현재 분석 자료에서 확인되지 않습니다' 라고 답한다.
"""

from __future__ import annotations

import streamlit as st

from gamepulse.ai.base import ChatMessage
from gamepulse.ai.factory import current_provider, get_chatbot
from gamepulse.ai.portfolio_index import NAMES
from gamepulse.ai.portfolio_index import _qa as qa_items
from gamepulse.content.games import GAME_ORDER
from gamepulse.ui.components import hero, html, notice

# 게임별 자주 묻는 질문 (누르면 바로 답변)
FAQ = {
    "overwatch": ["오버워치 복귀 유저 문제는?", "오버워치 복귀 브리핑 전략", "오버워치 KPI"],
    "pubg": ["배그 신규 유저 코칭 전략", "배그 복귀 광고 캠페인", "배그 KPI"],
    "fconline": ["FC 구단 가치 하락 해결책", "FC 키보드 패드 조작 개선", "FC 예산과 우선순위"],
    "dnf": ["던파 미카엘라 보상 논란은?", "던파 개발사는 어떤 대응을 했어?", "던파 기존 보장 시스템과 제안의 차이"],
}
COMMON = "4개 게임 공통 KPI 비교"


def _show(content: str, expanded: bool) -> None:
    content = content.replace("~", "\\~")  # '1~2' 가 취소선으로 바뀌는 것 방지
    head, sep, rest = content.partition("\n\n**문제와 근거**")
    st.markdown(head)
    if sep:
        with st.expander("문제와 근거 · 사업PM 개선 전략 · 핵심 KPI · 관련 페이지", expanded=expanded):
            st.markdown(sep.strip() + rest)


def _ask(q: str, game: str | None) -> None:
    st.session_state.chat.append(ChatMessage("user", q))
    st.session_state.chat.append(ChatMessage("assistant", get_chatbot().reply(st.session_state.chat, game)))


def render() -> None:
    hero("Portfolio Search Assistant", "사업PM 어시스턴트",
         "오버워치 · PUBG · FC 온라인 · 던파 분석 자료를 검색해 핵심 결론 → 문제와 근거 → 사업PM 개선 전략 → 핵심 KPI → 관련 페이지 순서로 답합니다.")
    notice(f"**포트폴리오 기반 검색형 PM 어시스턴트**{'' if current_provider() == 'rule' else ' (LLM 설정됨)'} · 생성형 AI API는 연결되어 있지 않습니다 · "
           "사이트의 분석 자료 원문만 보여 주며, 자료에 없으면 '현재 분석 자료에서 확인되지 않습니다', 어느 게임인지 애매하면 확인을 요청합니다.")
    if "chat" not in st.session_state:
        st.session_state.chat = []

    html('<div class="as-label">추천 질문 · 누르면 바로 답변</div>')
    clicked = None
    t_game, t_cmp = st.tabs(["게임별 (문제·전략·KPI)", "비교·우선순위 (비용·매출·예산)"])
    with t_game:
        cols = st.columns(2)
        for i, gid in enumerate(GAME_ORDER):
            with cols[i % 2]:
                html(f'<div class="as-game">{NAMES[gid]}</div>')
                for j, q in enumerate(FAQ[gid]):
                    if st.button(q, key=f"faq_{gid}_{j}", use_container_width=True):
                        clicked = (q, gid)
        if st.button(COMMON, key="faq_common", use_container_width=True):
            clicked = (COMMON, None)
    qa = qa_items()
    with t_cmp:
        cols = st.columns(2)
        for k, it in enumerate([x for x in qa if x["cat"] == "비교·우선순위"]):
            if cols[k % 2].button(it["q"], key=f"qa_{it['id']}", use_container_width=True):
                clicked = (it["q"], None)

    game = st.selectbox("직접 질문할 게임 (선택하지 않으면 질문에서 자동 인식)", [None] + GAME_ORDER,
                        format_func=lambda x: "자동 인식 · 공통 질문" if x is None else NAMES[x], key="as_game")
    prompt = st.chat_input("질문 입력 · 예: 던파 ARAD CARE 골드 영향은?")
    if prompt or clicked:
        q, g = (prompt, game) if prompt else clicked
        _ask(q, g)
        st.rerun()

    n = len(st.session_state.chat)
    for i, m in enumerate(st.session_state.chat):
        with st.chat_message(m.role):
            if m.role == "assistant":
                _show(m.content, expanded=i == n - 1)
            else:
                st.markdown(m.content.replace("~", "\\~"))
    asked = [m.content for m in st.session_state.chat if m.role == "user"]
    if len(asked) > 1:
        with st.expander(f"이전 질문 기록 {len(asked)}개"):
            st.markdown("\n".join(f"{i}. {q}" for i, q in enumerate(asked, 1)))
    if st.session_state.chat and st.button("대화 지우기", key="as_clear"):
        st.session_state.chat = []
        st.rerun()
