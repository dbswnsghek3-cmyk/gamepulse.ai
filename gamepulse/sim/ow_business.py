"""오버워치 사업 효과 시뮬레이션 (보수적·기본·낙관적) — 모든 입력은 data/overwatch/business.json 의 기획 가정.

연결 구조
  RE:START  : 순증 D7 잔존 → 분기 활성 유지 → 결제율(PUR) × ARPPU → 순증 매출
  성장형 스킨: 노출 유저 × 구매 전환율 × 판매가 → 단순 매출 − 기존 스킨 잠식 → 순증 매출
  공통       : 순증 매출 − 결제·플랫폼 수수료 = 순매출 · 순매출 − (개발 + 마케팅) = 분기 이익
  손익분기   : 성장형 스킨 비용(개발 + 마케팅) ÷ 구매자 1명당 순공헌 = 필요 구매자 수

자연 복귀 유저는 A/B 대조군과의 차이(ITT)만 순증으로 세므로 이미 빠져 있다.
"""

from __future__ import annotations

import math


def run(sim: dict, added_d7_base: float) -> list[dict]:
    """시나리오별 결과 dict 목록 (보수적 → 낙관적)."""
    r, s, c = sim["restart"], sim["skin"], sim["cost"]
    fee = sim["platform_fee"] / 100
    mc = c["monthly_cost_per_person"]
    restart_cost = c["restart_effort"] * mc
    skin_cost = c["skin_effort"] * mc + c["marketing"]
    out = []
    for i, name in enumerate(sim["scenarios"]):
        added = added_d7_base * r["added_d7_scale"][i]
        active = added * r["keep_rate"][i] / 100
        payers = active * r["pur"][i] / 100
        rs_rev = payers * r["arppu"][i]

        buyers = s["exposed_users"] * s["conversion"][i] / 100
        sk_gross = buyers * s["price"]
        sk_cannib = sk_gross * s["cannibalization"][i] / 100
        sk_rev = sk_gross - sk_cannib

        net_rev = (rs_rev + sk_rev) * (1 - fee)
        cost = restart_cost + skin_cost
        per_buyer = s["price"] * (1 - s["cannibalization"][i] / 100) * (1 - fee)
        bep_buyers = math.ceil(skin_cost / per_buyer) if per_buyer > 0 else None
        out.append({
            "name": name, "added_d7": added, "active": active, "payers": payers, "restart_rev": rs_rev,
            "buyers": buyers, "skin_gross": sk_gross, "skin_cannib": sk_cannib, "skin_rev": sk_rev,
            "gross": rs_rev + sk_gross, "net_new": rs_rev + sk_rev, "fee": (rs_rev + sk_rev) * fee, "net_rev": net_rev,
            "restart_cost": restart_cost, "skin_cost": skin_cost, "cost": cost, "profit": net_rev - cost,
            "per_buyer": per_buyer, "bep_buyers": bep_buyers,
            "bep_conv": bep_buyers / s["exposed_users"] * 100 if bep_buyers else None,
        })
    return out
