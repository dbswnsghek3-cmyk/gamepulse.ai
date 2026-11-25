"""오버워치 사업 효과 시뮬레이터 — 성장형 스킨 + RE:START 잔존 개선 (분기 기준 · 모든 입력은 기획 가정).

정적 사이트의 JavaScript 시뮬레이터(scripts/ow_static_demos.py)는 이 파일과 같은 순서·같은 식으로 계산한다.

계산 순서 (분기 = 91일)
  1 예상 구매 유저        = 노출 유저 × 구매 전환율
  2 성장형 스킨 총매출    = 구매 유저 × 판매 가격
  3 기존 상품 매출 잠식액 = 총매출 × 잠식률
  4 순증 상품 매출        = 총매출 − 잠식액
  5 순증 활성 유저        = 유입 × D30 개선폭 + 유입 × (D7 개선폭 − D30 개선폭) × (30 ÷ 91)
                            · D30 잔존 유저는 D7 잔존 유저에 포함되므로 D7·D30을 더하지 않는다 (D30 개선폭 ≤ D7 개선폭으로 보정)
                            · D7까지만 남은 유저는 분기 91일 중 약 30일만 활성으로 본다
  6 잔존 추가 매출        = 순증 활성 유저 × PUR × ARPPU(분기)  ← 스킨 구매와 별도 (스킨 매출과 합산하지 않고 따로 계산 후 더함)
  7 수수료 차감 후 순증 매출 = (4 + 6) × (1 − 수수료율)   · 수수료는 유저 결제액(스킨 순증 매출 + 잔존 추가 매출)에만 적용
  8 총비용                = 개발 인월 × 인월당 비용 + 마케팅비 + 기타 운영비
  9 예상 사업 이익        = 7 − 8
 10 손익분기 구매 전환율  = (총비용 − 잔존 추가 매출 × (1 − 수수료)) ÷ (노출 × 가격 × (1 − 잠식률) × (1 − 수수료))
 11 손익분기 구매 유저    = 노출 유저 × 손익분기 전환율
 12 ROI                   = 이익 ÷ 총비용
"""

from __future__ import annotations

import math

DAYS, D7_DAYS = 91, 30


def fields(sim: dict) -> dict:
    return {f["key"]: f for f in sim["fields"]}


def preset(sim: dict, name: str) -> dict:
    return {**sim["defaults"], **sim["presets"].get(name, {})}


def clamp(sim: dict, x: dict) -> dict:
    """빈 값·음수·범위 밖 값은 허용 범위로 고친다 (0 입력 허용)."""
    out = {}
    for k, f in fields(sim).items():
        try:
            v = float(x.get(k, sim["defaults"][k]))
        except (TypeError, ValueError):
            v = float(sim["defaults"][k])
        if math.isnan(v):
            v = float(sim["defaults"][k])
        out[k] = min(max(v, f["min"]), f["max"])
    out["d30_uplift"] = min(out["d30_uplift"], out["d7_uplift"])
    return out


def simulate(sim: dict, x: dict) -> dict:
    x = clamp(sim, x)
    days, d7_days = sim.get("period_days", DAYS), sim.get("d7_only_days", D7_DAYS)
    fee = x["fee"] / 100
    buyers = x["exposed"] * x["conv"] / 100
    gross = buyers * x["price"]
    cannib = gross * x["cannib"] / 100
    skin_net = gross - cannib
    ret30 = x["inflow"] * x["d30_uplift"] / 100
    ret7_only = x["inflow"] * (x["d7_uplift"] - x["d30_uplift"]) / 100
    active = ret30 + ret7_only * d7_days / days
    ret_rev = active * x["pur"] / 100 * x["arppu"]
    pre_fee = skin_net + ret_rev
    fee_amt = pre_fee * fee
    net = pre_fee - fee_amt
    dev = x["dev_mm"] * x["mm_cost"]
    cost = dev + x["marketing"] + x["other_cost"]
    profit = net - cost

    per_pt = x["exposed"] / 100 * x["price"] * (1 - x["cannib"] / 100) * (1 - fee)   # 전환율 1%p 당 이익 증가
    need = cost - ret_rev * (1 - fee)                                                 # 스킨으로 메워야 할 금액
    if need <= 0:
        bep, bep_state = 0.0, "already"          # 스킨 판매 없이도 손익분기
    elif per_pt <= 0:
        bep, bep_state = None, "impossible"      # 노출·가격이 0이거나 잠식·수수료 100%
    else:
        bep = need / per_pt
        bep_state = "ok" if bep <= 100 else "impossible"
    bep_buyers = math.ceil(x["exposed"] * bep / 100) if bep is not None and bep_state != "impossible" else None
    roi = profit / cost * 100 if cost > 0 else None
    return {"x": x, "buyers": buyers, "gross": gross, "cannib": cannib, "skin_net": skin_net, "ret30": ret30,
            "ret7_only": ret7_only, "active": active, "ret_rev": ret_rev, "pre_fee": pre_fee, "fee": fee_amt, "net": net,
            "dev": dev, "marketing": x["marketing"], "other": x["other_cost"], "cost": cost, "profit": profit,
            "bep": bep, "bep_state": bep_state, "bep_buyers": bep_buyers, "roi": roi, "verdict": verdict(x["conv"], profit, bep, bep_state)}


def verdict(conv: float, profit: float, bep: float | None, state: str) -> str:
    """profit(흑자 확대 검토) · near(손익분기 근접) · loss(적자) — 현재 전환율 ÷ 손익분기 전환율로 판정."""
    if state == "already":
        return "profit"
    if state == "impossible" or not bep:
        return "loss"
    r = conv / bep
    if r >= 1.2:
        return "profit"
    if r >= 0.8:
        return "near"
    return "loss"


VERDICT_TEXT = {
    "loss": ("예상 적자", "비용 절감과 소규모 파일럿을 먼저 검토한다"),
    "near": ("손익분기 근접", "구매 전환율 검증을 우선한다"),
    "profit": ("예상 흑자", "단계적 확대를 검토한다"),
}
GUARD_TEXT = "흑자가 예상되더라도 게임플레이 보호 지표와 기존 상품 매출 잠식 여부를 검증한 뒤 확대한다."


def profit_curve(sim: dict, x: dict, n: int = 41) -> tuple[list[float], list[float]]:
    """구매 전환율(0 ~ 상한)에 따른 이익 · 상한은 손익분기의 2배와 현재값의 2배 중 큰 값 (최소 5%)."""
    r = simulate(sim, x)
    hi = max(5.0, 2 * r["x"]["conv"], 2 * (r["bep"] or 0) if r["bep_state"] == "ok" else 0)
    hi = min(hi, 100.0)
    xs = [hi * i / (n - 1) for i in range(n)]
    return xs, [simulate(sim, {**x, "conv": c})["profit"] for c in xs]
