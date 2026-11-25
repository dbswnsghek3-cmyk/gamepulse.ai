"""FC 온라인 사업성 계산 (모두 가상 시뮬레이션 · 실제 내부 데이터 아님) — 정적 사이트 JS(scripts/fc_static_widgets.py)와 같은 식.

keep   : 기존 결제 유저 이탈 방지 → 매출 보전 (순이익 아님)
funnel : MY CLUB WAR 마케팅 퍼널 → CPA · 잔존 유저당 비용 · LTV · 비용 차감 후 사업성
power  : BP 실질 구매력 (명목 구단 가치 vs 목표 선수 가격)
fandom : 팬덤 점수 — 누적 · 1인당 평균 · 혼합 점수 순위 비교
"""

from __future__ import annotations

import math


def _clamp(fields: list, defaults: dict, x0: dict) -> dict:
    x = {}
    for k, _lab, lo, hi, _st in fields:
        try:
            v = float(x0.get(k, defaults[k]))
        except (TypeError, ValueError):
            v = float(defaults[k])
        if math.isnan(v):
            v = float(defaults[k])
        x[k] = min(max(v, lo), hi)
    return x


def keep(cfg: dict, x0: dict) -> dict:
    x = _clamp(cfg["fields"], cfg["defaults"], x0)
    lost0 = x["payers"] * x["churn0"] / 100
    lost1 = x["payers"] * x["churn1"] / 100
    kept = lost0 - lost1
    monthly = kept * x["arppu"]
    return {"x": x, "lost0": lost0, "lost1": lost1, "kept": kept, "monthly": monthly, "total": monthly * x["months"]}


def funnel(cfg: dict, x0: dict) -> dict:
    x = _clamp(cfg["fields"], cfg["defaults"], x0)
    x["d30"] = min(x["d30"], x["d7"])                      # 같은 가입자 집단: D30 잔존 ≤ D7 잔존
    visits = x["reach"] * x["visit"] / 100
    signups = visits * x["signup"] / 100
    d7 = signups * x["d7"] / 100
    d30 = signups * x["d30"] / 100
    ltv = x["pur"] / 100 * x["arppu"] * x["months"]        # D30 잔존 유저 1명의 기간 기대 매출
    revenue = d30 * ltv
    cost = x["cost"]
    per = lambda n: cost / n if n > 0 else None           # noqa: E731
    bep_pur = (cost / (d30 * x["arppu"] * x["months"]) * 100) if d30 * x["arppu"] * x["months"] > 0 else None
    return {"x": x, "visits": visits, "signups": signups, "d7": d7, "d30": d30, "ltv": ltv, "revenue": revenue, "cost": cost,
            "profit": revenue - cost, "cpa": per(signups), "cost_d7": per(d7), "cost_d30": per(d30),
            "rev_per_signup": revenue / signups if signups > 0 else None,
            "ratio": revenue / cost if cost > 0 else None, "bep_pur": bep_pur}


def power(club0: float, club1: float, target0: float, target1: float) -> dict:
    nominal = (club1 / club0 - 1) * 100 if club0 > 0 else None
    p0 = club0 / target0 if target0 > 0 else None
    p1 = club1 / target1 if target1 > 0 else None
    real = (p1 / p0 - 1) * 100 if p0 and p1 is not None else None
    return {"nominal": nominal, "p0": p0, "p1": p1, "real": real}


def fandom(rows: list, w_avg: float = 0.5) -> list[dict]:
    """rows = [[이름, 참여 인원, 1인당 평균 점수]] · 혼합 = (누적/최대누적)×(1−w) + (평균/최대평균)×w."""
    out = [{"name": n, "people": p, "avg": a, "total": p * a} for n, p, a in rows]
    mt, ma = max(r["total"] for r in out) or 1, max(r["avg"] for r in out) or 1
    for r in out:
        r["mixed"] = (r["total"] / mt) * (1 - w_avg) + (r["avg"] / ma) * w_avg
    for key in ("total", "avg", "mixed"):
        for i, r in enumerate(sorted(out, key=lambda r: -r[key]), 1):
            r["rank_" + key] = i
    return out
