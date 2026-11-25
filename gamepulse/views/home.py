"""홈 · 개요 — 프로젝트 소개 · 4개 게임 핵심 문제와 바로가기 · 사업PM 어시스턴트 소개."""

from __future__ import annotations

import base64
import io
import json
from functools import lru_cache
from html import escape
from pathlib import Path

import streamlit as st

from gamepulse.config import APP_NAME
from gamepulse.ui.components import card, grid, hero, html, section

ROOT = Path(__file__).resolve().parents[2]


def _go(page: str) -> None:
    st.session_state["page"] = page
    st.query_params["page"] = page


@lru_cache(maxsize=8)
def _thumb(rel: str, mtime: float, png: bool, blur: tuple = ()) -> str:
    """대표 이미지 썸네일(base64) · 원본은 건드리지 않는다."""
    from PIL import Image, ImageFilter

    with Image.open(ROOT / rel) as src:
        im = src.convert("RGBA" if png else "RGB")
    for x0, y0, x1, y1 in blur:  # 다른 플레이어 닉네임 가림 (오버워치 manifest 기준)
        region = im.crop((x0, y0, x1, y1))
        im.paste(region.resize((max(1, (x1 - x0) // 10), max(1, (y1 - y0) // 10))).resize(region.size).filter(ImageFilter.GaussianBlur(3)), (x0, y0))
    w = 420 if png else 720
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG" if png else "JPEG", **({"optimize": True} if png else {"quality": 80, "optimize": True}))
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _ow_image() -> tuple[str, tuple]:
    from gamepulse.data.overwatch_images import all_status
    stt = all_status().get("returning_menu")
    if stt is None or not stt.ok:
        return "", ()
    return str(Path(stt.path).resolve().relative_to(ROOT)).replace("\\", "/"), tuple(tuple(int(v) for v in b) for b in stt.slot.get("blur", []))


def _games() -> list[dict]:
    load = lambda p: json.loads((ROOT / "data" / p).read_text(encoding="utf-8"))  # noqa: E731
    ow, pb, fc, dn = load("overwatch/restart.json"), load("pubg/newstart.json"), load("fconline/fc.json"), load("dnf/dnf.json")
    ow_img, ow_blur = _ow_image()
    return [
        {"id": "overwatch", "name": "오버워치", "proj": "PROJECT RE:START", "img": ow_img, "png": False, "blur": ow_blur,
         "credit": "실제 게임 화면 · 작성자 캡처", "problem": "신규·복귀 유저의 학습 부담 · 영웅별 스킨 상품 차이와 고정형 묶음의 선택권 한계",
         "answer": "복귀율: PROJECT RE:START (복귀 브리핑 → 첫 10경기 미션 → 전투 학습 카드) · 매출: YOUR HERO · YOUR CHOICE",
         "kpi": "복귀 D7 잔존율 · 패키지 구매 전환율 · 평균 결제 금액"},
        {"id": "fconline", "name": "FC 온라인", "proj": "축구 게임인가, 주식 게임인가?", "img": "assets/fconline/main_screen.jpg", "png": False, "blur": (),
         "credit": "실제 게임 메인 화면 · 작성자 캡처", "problem": "구단 가치 급락과 강화 실패로 인한 이탈 위험, 그리고 조작 환경의 공정성", "answer": "A 구단 가치 급락 완충 프로그램 · B 강화 실패 후 재기 프로그램 · C 분리 없는 조작 공정성 개선",
         "kpi": "급락 경험 유저 D7 · 강화 실패 후 D7 재접속률"},
        {"id": "pubg", "name": "PUBG", "proj": "NEW START", "img": "assets/pubg/brand/pubg_logo.png", "png": True, "blur": (),
         "credit": "로고 © KRAFTON", "problem": pb["cover"]["copy"], "answer": "A1 경기별 코칭으로 신규 정착 + B1 복귀 광고 «다시 낙하할 시간»은 디지털 파일럿부터",
         "kpi": "신규 D7 · 순증 D30 재정착 유저당 비용"},
        {"id": "dnf", "name": "던전앤파이터", "proj": "시즌의 가치 회복", "img": dn["cover"]["logo"] if "/" in dn["cover"]["logo"] else f"assets/dnf/{dn['cover']['logo']}",
         "png": True, "blur": (), "credit": "로고 © NEOPLE", "problem": "고난도 던전을 클리어해도 보상이 운에 갈려 성장이 쌓이지 않는다",
         "answer": "B 지정 장비 진척 게이지: 목표를 정하고 기대 미만 클리어도 진척으로 쌓이게 (확률·경매 유지) · 소규모 파일럿", "kpi": "주간 고난도 재도전율 · 목표 획득 전 이탈률 · 재화 공급 ±5%"},
    ]


def render() -> None:
    hero("Game Business PM Portfolio", APP_NAME, "실제 유저 의견과 공식 자료로 게임의 사업 문제를 정의하고, 실행 가능한 개선안 · KPI · 실험으로 연결한 사업PM 포트폴리오",
         "불만을 '가설'로, 가설을 '실험 가능한 전략'과 'KPI'로.")

    section("4개 게임 · 핵심 문제와 대표 전략", "게임마다 문제 → 근거 → 원인 → 개선안 → KPI → 실행 판단 (01~06 탭)")
    games = _games()
    for i, g in enumerate(games):
        if i % 2 == 0:   # 두 개씩 한 줄 → 모바일·정적 화면에서도 메뉴 순서(오버워치 → FC → PUBG → 던파) 유지
            cols = st.columns(2)
        with cols[i % 2]:
            src = ""
            if g["img"] and (ROOT / g["img"]).exists():
                p = ROOT / g["img"]
                b64 = _thumb(g["img"], p.stat().st_mtime, g["png"], g["blur"])
                src = (f'<div class="hm-img{" logo" if g["png"] else ""} {g["id"]}"><img src="data:image/{"png" if g["png"] else "jpeg"};base64,{b64}" '
                       f'alt="{escape(g["name"])} 대표 이미지"><span>{escape(g["credit"])}</span></div>')
            html(f'<div class="hm-game">{src}<div class="hm-body"><div class="hm-k">{escape(g["name"])} · {escape(g["proj"])}</div>'
                 f'<h4>{escape(g["problem"])}</h4><p><b>대표 전략</b> {escape(g["answer"])}</p>'
                 f'<p class="kpi"><b>핵심 KPI</b> {escape(g["kpi"])} <em>(목표·가정)</em></p></div></div>')
            st.button(f"{g['name']} 분석 보기 →", key=f"go_{g['id']}", on_click=_go, args=(g["id"],), use_container_width=True)

    section("사업PM 어시스턴트", "4개 게임 분석 내용을 질문으로 빠르게 찾습니다.")
    grid([card("포트폴리오 기반 검색형 PM 어시스턴트",
               "게임별 자주 묻는 질문을 누르거나 직접 질문하면 핵심 결론 → 문제와 근거 → 사업PM 개선 전략 → 핵심 KPI → 관련 페이지 순서로 답합니다.",
               meta="생성형 AI API 미연결 · 사이트 분석 자료 원문만 검색 · 자료에 없으면 '현재 분석 자료에서 확인되지 않습니다'")])
    st.button("사업PM 어시스턴트 열기 →", key="go_assistant", on_click=_go, args=("assistant",), use_container_width=True)

    section("분석 프레임워크", "4개 게임 모두 같은 6단계 구조 (각 게임 페이지의 01~06 탭)")
    grid([
        card("01 문제 정의", "누가, 어디서, 왜 불편한가를 한 문장으로"),
        card("02 근거", "실제 유저 의견 · 공식 자료 · 게임 화면 (출처·한계 표시)"),
        card("03 원인 가설", "불만과 원인의 연결은 가설로 두고 검증 데이터를 명시"),
        card("04 개선안", "기존 시스템과 겹치지 않는 차별화 + 부작용"),
        card("05 KPI · 실험", "주요 · 보조 · 가드레일 지표와 A/B 설계"),
        card("06 실행 판단", "우선순위 · 예산 · 리스크 · 확대/중단 조건"),
    ])
