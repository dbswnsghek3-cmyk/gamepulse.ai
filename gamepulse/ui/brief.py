"""가독성 공통 부품 (2026-11-26 · 오버워치·FC 온라인·PUBG 전용 · gb-* 클래스).

- brief_html: 대표 기획 첫머리 4칸 — 무엇이 문제인가 → 왜 해결해야 하나 → 어떻게 해결하나 → 기대 사업 효과
- flow_html: 단계 흐름도 (번호 · 제목 · 한 줄 설명 · 화살표)
- chips_html: 짧은 항목 묶음 (효과·KPI 등 목록을 한눈에)
색은 페이지 테마 변수(--g-acc · --g-ink)를 쓰므로 게임별 색이 자동 적용된다. 던전앤파이터 페이지는 이 모듈을 쓰지 않는다.
"""
from __future__ import annotations

from html import escape

Q4 = ("무엇이 문제인가", "왜 해결해야 하나", "어떻게 해결하나", "기대 사업 효과")


def brief_html(problem: str, why: str, how: str, effect: str, *, name: str = "", tag: str = "") -> str:
    """대표 기획 4칸 요약. 인자는 이미 안전한 HTML(짧은 문장 · <b> 허용)."""
    head = ""
    if name:
        t = f'<span class="gb-tag">{escape(tag)}</span>' if tag else ""
        head = f'<div class="gb-brief-h"><b>{escape(name)}</b> 한눈에 보기{t}</div>'
    cells = "".join(f'<div class="gb-q{i}"><span>{q}</span><p>{v}</p></div>'
                    for i, (q, v) in enumerate(zip(Q4, (problem, why, how, effect)), 1))
    return f'<div class="gb-brief">{head}<div class="gb-brief-g">{cells}</div></div>'


def flow_html(steps: list[tuple[str, str]], *, title: str = "", cls: str = "", hl: int | None = None) -> str:
    """단계 흐름도: steps = [(제목, 한 줄 설명), ...] · hl = 강조할 단계(0부터)."""
    t = f'<div class="gb-flow-t">{title}</div>' if title else ""
    items = "".join(f'<li class="{"on" if i == hl else ""}"><em>{i + 1}</em><b>{a}</b>{f"<small>{b}</small>" if b else ""}</li>'
                    for i, (a, b) in enumerate(steps))
    return f'<div class="gb-flow {cls}">{t}<ol>{items}</ol></div>'


def chips_html(label: str, items: list[str], cls: str = "") -> str:
    return (f'<div class="gb-chips {cls}"><span>{escape(label)}</span>'
            + "".join(f"<i>{escape(x)}</i>" for x in items) + "</div>")
