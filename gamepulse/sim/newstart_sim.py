"""PUBG: NEW START 계산 모듈 (UI 와 분리 · 단위 테스트 가능).

1) 확률형 상자 비용 계산 (독립 시행 + 스크랩 교환 '천장')
   - n회 안에 1번 이상 획득할 확률 = 1 − (1 − p)^n
   - 천장 K = ceil((교환 스크랩 − 보유 스크랩) ÷ 1회당 스크랩)  → K회째에는 교환으로 반드시 확보
   - 기대 개봉 수(천장 포함) = E[min(G, K)] = (1 − (1 − p)^K) ÷ p   (G = 첫 획득까지 시도 수, 기하분포)
   - q% 도달 개봉 수 = min(ceil(ln(1 − q) ÷ ln(1 − p)), K)
   - 비용: 첫 구매는 10회 묶음 할인가, 이후 1회 가격 (cost_of) · 중복 보상 분해·토큰 환급은 반영 안 함
2) 성장형 스킨 재료: 공식 '분해 환급표'를 누적 투입량으로 가정한 추정 (레벨별 필요량은 공식 미공개)
3) 실험 설계: 우월성(두 비율 차이) · 비열등성(한쪽 검정) 표본 수, 배정 주수, 판정 주차
4) BM 시나리오: 방문자 × 전환율 × ARPPU (+ 재구매) — 비관·낙관 범위
"""

from __future__ import annotations

import math
from statistics import NormalDist

from gamepulse.sim.restart_sim import sample_size_two_proportions


# ----------------------------------------------------------------------
# 1) 확률형 상자
def crate_cap(exchange_scrap: int, owned_scrap: int, scrap_per_open: int) -> int | None:
    """스크랩 교환으로 반드시 확보되는 개봉 수 K. 교환 불가(1회당 스크랩 0)면 None."""
    if scrap_per_open <= 0 or exchange_scrap <= 0:
        return None
    return max(0, math.ceil((exchange_scrap - owned_scrap) / scrap_per_open))


def prob_within(n: int, p: float, cap: int | None = None) -> float:
    """n회 이내 확보 확률 (0~1). 천장 K 이상이면 1."""
    if cap is not None and n >= cap:
        return 1.0
    if p <= 0:
        return 0.0
    return 1 - (1 - min(p, 1.0)) ** max(n, 0)


def expected_opens(p: float, cap: int | None = None) -> float:
    """첫 확보까지 기대 개봉 수. 천장이 있으면 E[min(G, K)]."""
    if cap is not None and cap == 0:
        return 0.0
    if p <= 0:
        return float(cap) if cap is not None else math.inf
    if cap is None:
        return 1 / p
    return (1 - (1 - p) ** cap) / p


def opens_for(q: float, p: float, cap: int | None = None) -> int | None:
    """확보 확률 q(0~1)에 도달하는 최소 개봉 수 (천장 반영)."""
    if p <= 0:
        return cap
    n = math.ceil(math.log(1 - q) / math.log(1 - min(p, 0.999999)))
    return min(n, cap) if cap is not None else n


def cost_of(opens: int, price: float, first_n: int = 0, first_price: float = 0) -> float:
    """개봉 수 → 누적 비용. 첫 구매는 first_n회 묶음(first_price)으로 사고, 그 뒤는 1회씩 산다고 가정.
    first_n=0 이면 할인 없음(opens × price). 묶음 중간에 얻어도 묶음 값은 이미 낸 것으로 본다."""
    if first_n <= 0 or opens <= 0:
        return max(opens, 0) * price
    return first_price + max(opens - first_n, 0) * price


def crate_summary(price: float, p_pct: float, scrap_per_open: int, exchange_scrap: int, owned_scrap: int = 0,
                  n: int = 100, first_n: int = 0, first_price: float = 0) -> dict:
    """기대 비용 = E[cost(N)], N = min(G, K).
    할인 없음: price × E[N]
    첫 묶음 할인: first_price + price × (E[N] − E[min(N, first_n)])  (E[min(G, K, m)] = expected_opens(p, min(K, m)))"""
    p = p_pct / 100
    cap = crate_cap(exchange_scrap, owned_scrap, scrap_per_open)
    e_no = 1 / p if p > 0 else math.inf
    e_cap = expected_opens(p, cap)
    o50, o90 = opens_for(0.5, p, cap), opens_for(0.9, p, cap)

    def exp_cost(e_n: float, c: int | None) -> float:
        if first_n <= 0:
            return e_n * price
        m = first_n if c is None else min(c, first_n)
        return (first_price if (c is None or c > 0) else 0) + price * (e_n - expected_opens(p, m))

    def cost(k: int | None) -> float | None:
        return None if k is None else cost_of(k, price, first_n, first_price)

    return {"p": p, "cap": cap, "within_n": prob_within(n, p, cap), "within_n_nocap": prob_within(n, p),
            "exp_opens": e_cap, "exp_cost": exp_cost(e_cap, cap), "exp_cost_nocap": exp_cost(e_no, None),
            "o50": o50, "o90": o90, "c50": cost(o50), "c90": cost(o90), "cap_cost": cost(cap),
            "n_cost": cost(n), "first_n": first_n, "first_price": first_price}


def crate_curve(p_pct: float, cap: int | None, max_n: int) -> list[tuple[int, float, float]]:
    """(개봉 수, 천장 없는 확보 확률 %, 천장 포함 확보 확률 %)."""
    p = p_pct / 100
    return [(n, prob_within(n, p) * 100, prob_within(n, p, cap) * 100) for n in range(0, max_n + 1)]


# ----------------------------------------------------------------------
# 2) 성장형 스킨 재료 (추정)
def upgrade_need(salvage: list[list[int]], cur: int, target: int, polymer: int, schematic: int) -> dict:
    """분해 환급표[level] = 그 레벨까지 누적 투입량이라고 가정해, cur → target 에 필요한 재료와 부족분을 계산."""
    tab = {lv: (pol, sch) for lv, pol, sch in salvage}
    cur, target = max(1, cur), max(1, target)
    if target <= cur:
        return {"polymer": 0, "schematic": 0, "short_polymer": 0, "short_schematic": 0, "steps": []}
    need_p = tab[target][0] - tab[cur][0]
    need_s = tab[target][1] - tab[cur][1]
    steps = [(lv, tab[lv][0] - tab[lv - 1][0], tab[lv][1] - tab[lv - 1][1]) for lv in range(cur + 1, target + 1)]
    return {"polymer": need_p, "schematic": need_s, "short_polymer": max(0, need_p - polymer),
            "short_schematic": max(0, need_s - schematic), "steps": steps}


# ----------------------------------------------------------------------
# 3) 실험 설계
def sample_size_noninferiority(p: float, margin: float, alpha: float = 0.05, power: float = 0.8) -> int | None:
    """비열등성(한쪽 검정, 실제 차이 0 가정) 그룹당 표본. p·margin 은 0~1."""
    if not (0 < p < 1) or margin <= 0:
        return None
    nd = NormalDist()
    za, zb = nd.inv_cdf(1 - alpha), nd.inv_cdf(power)
    return math.ceil((za + zb) ** 2 * 2 * p * (1 - p) / margin ** 2)


def plan(cfg: dict) -> dict:
    """newstart.json 'experiment' → A1(신규 D7)·B1(휴면 복귀) 두 실험의 MDE·표본·배정 주수·판정 주차.
    모든 화면(01·05·06 탭)이 이 값 하나를 공유한다. 수치는 모두 가정값이다."""
    a, r = cfg["A"], cfg["R"]
    alpha, power = cfg["alpha"], cfg["power"]
    mde = a["participation"] / 100 * a["uplift_viewer"]                       # 배정 기준(ITT) 효과
    n_a = sample_size_two_proportions(a["base_d7"] / 100, (a["base_d7"] + mde) / 100, alpha, power)
    wk_a = math.ceil(2 * n_a / a["weekly"])
    m10_mde = a["participation"] / 100 * a["uplift_m10_viewer"]
    # B1: 휴면 계정을 대조군(광고 없음) + 광고 그룹(arms−1개)으로 무작위 배정 → 각 광고 vs 대조군 복귀 로그인율(배정 기준) 비교
    arms = r.get("arms", 2)
    # 광고 (arms−1)개를 각각 대조군과 비교 → Bonferroni 보정 α ÷ (arms−1) 로 그룹당 표본 계산 (화면 설명과 일치)
    n_r = sample_size_two_proportions(r["base_return"] / 100, (r["base_return"] + r["mde"]) / 100, alpha / max(arms - 1, 1), power)  # 그룹당
    wk_r = math.ceil(arms * n_r / r["weekly"])
    win = math.ceil(r["window_days"] / 7)
    r0 = r["start_week"]
    sched = {"a_assign": (1, wk_a), "a_d7": wk_a + 1, "a_d30": math.ceil((wk_a * 7 + 30) / 7),
             "r_assign": (r0, r0 + wk_r - 1)}
    sched["r_return"] = sched["r_assign"][1] + win              # 마지막 배정 + 30일: 복귀율 판정
    sched["r_d30"] = sched["r_return"] + math.ceil(30 / 7)      # 마지막 복귀자 + 30일: 복귀 후 D30
    sched["decision"] = max(sched["a_d30"], sched["r_d30"]) + 1
    q = cfg["quarter_new"]
    added = q * mde / 100
    c = cfg["cost"]
    a1_cost = c["A1_effort"] * c["monthly_cost_per_person"]
    b1_cost = c["B1_effort"] * c["monthly_cost_per_person"] + c.get("B1_ad_budget", 0) + c.get("B1_reward_budget", 0)
    return {"A": {"mde": mde, "n": n_a, "assign_weeks": wk_a, "m10_mde": m10_mde},
            "R": {"mde": r["mde"], "n": n_r, "assign_weeks": wk_r, "arms": arms},
            "sched": sched, "quarter_added_d7": added, "a1_cost": a1_cost,
            "a1_cost_per_added": a1_cost / added if added else float("nan"),
            "practical_min": a.get("practical_min", mde / 2),
            "a1_cost_per_added_practical": a1_cost / (q * a.get("practical_min", mde / 2) / 100),
            "b1_cost": b1_cost,
            "b1_cost_per_added": b1_cost / (n_r * r["mde"] / 100) if n_r else float("nan"),
            "c_cost": c.get("C_effort", 0) * c["monthly_cost_per_person"]}


def return_funnel(cfg: dict) -> list[tuple[str, float]]:
    """B3 30일 재정착 퍼널 (가정 시뮬레이션). 각 단계 = 앞 단계 × 전환율. 반환: [(단계, 발송 대비 %)]."""
    out, v = [], 100.0
    for name, rate in cfg["steps"]:
        v = v * rate / 100
        out.append((name, v))
    return out


# ----------------------------------------------------------------------
# 4) BM 시나리오
def scenario_revenue(visitors: int, conv: float, arppu: float, repurchase: float, rep_ratio: float) -> dict:
    """60일 매출 = 첫 30일(방문자 × 전환율 × ARPPU) + 다음 30일(구매자 × 재구매율 × ARPPU × 재구매 금액 비율)."""
    buyers = visitors * conv / 100
    first = buyers * arppu
    second = buyers * repurchase / 100 * arppu * rep_ratio
    return {"buyers": buyers, "first": first, "second": second, "total": first + second}


def scenarios(cfg: dict) -> list[dict]:
    out = []
    for s in cfg["items"]:
        lo = scenario_revenue(cfg["visitors"], s["conv"][0], s["arppu"][0], s["repurchase"][0], cfg["repurchase_arppu_ratio"])
        hi = scenario_revenue(cfg["visitors"], s["conv"][1], s["arppu"][1], s["repurchase"][1], cfg["repurchase_arppu_ratio"])
        out.append({**s, "low": lo, "high": hi})
    base = out[0]["low"]["total"]
    for s in out:
        s["low_pct"] = (s["low"]["total"] / base - 1) * 100
        s["high_pct"] = (s["high"]["total"] / base - 1) * 100
    return out
