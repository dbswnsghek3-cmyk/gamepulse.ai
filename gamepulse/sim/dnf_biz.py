"""던전앤파이터 개선 기획 계산 (모두 가상 시뮬레이션 · 실제 던파 확률·수리비 아님) — 정적 사이트 JS(scripts/dnf_static_widgets.py)와 같은 식.

reward : PROJECT ACHIEVEMENT — 기존 확률형 vs 누적 보장(K번째 확정)·확률 상승 · 미획득 확률 · 평균·편차 · 공급 증가율 (정확한 동적 계획법)
gold   : ARAD CARE — 계정 단위 수리 지원 · 상한 · 이용률 · 플레이 증가에 따른 골드 생산·회수 → 순골드 공급 변화
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


def _dist(n: int, p: float, k: int, s: int, step: float) -> tuple[float, float, float]:
    """n회 플레이 · 상태 = 연속 미획득 횟수 · 반환: 평균 획득 횟수, 분산, 0회 확률."""
    cap = k if k > 0 else n + 1          # 상태 수 (보장이 없으면 최대 n)
    pm = [0.0] * cap                     # 상태별 확률
    e1 = [0.0] * cap                     # 상태별 E[획득 수 · 1]
    e2 = [0.0] * cap                     # 상태별 E[획득 수² · 1]
    pm[0] = 1.0
    for _ in range(n):
        np_, n1, n2 = [0.0] * cap, [0.0] * cap, [0.0] * cap
        for j in range(cap):
            if pm[j] == 0.0:
                continue
            q = p + ((j - s + 1) * step if s > 0 and j >= s - 1 else 0.0)
            q = 1.0 if (k > 0 and j == k - 1) else min(max(q, 0.0), 1.0)
            # 성공 → 상태 0 · 획득 +1
            np_[0] += pm[j] * q
            n1[0] += (e1[j] + pm[j]) * q
            n2[0] += (e2[j] + 2 * e1[j] + pm[j]) * q
            if j + 1 < cap:
                np_[j + 1] += pm[j] * (1 - q)
                n1[j + 1] += e1[j] * (1 - q)
                n2[j + 1] += e2[j] * (1 - q)
        pm, e1, e2 = np_, n1, n2
    mean = sum(e1)
    var = max(sum(e2) - mean * mean, 0.0)
    # 0회 확률 = 처음부터 n번 연속 미획득
    zero = 1.0
    for j in range(n):
        q = p + ((j - s + 1) * step if s > 0 and j >= s - 1 else 0.0)
        q = 1.0 if (k > 0 and j == k - 1) else min(max(q, 0.0), 1.0)
        zero *= (1 - q)
    return mean, var, zero


def reward(cfg: dict, x0: dict) -> dict:
    x = _clamp(cfg["fields"], cfg["defaults"], x0)
    n, k, s = (int(math.floor(x[c] + 0.5)) for c in ("n", "k", "s"))   # JS Math.round 와 같게
    p, step = x["p"] / 100, x["step"] / 100
    m0, v0, z0 = _dist(n, p, 0, 0, 0.0)
    m1, v1, z1 = _dist(n, p, k, s, step)
    q, u = x["qty"], x["users"]
    sup0, sup1 = m0 * q * u, m1 * q * u
    return {"x": x, "base": {"mean": m0 * q, "sd": math.sqrt(v0) * q, "zero": z0 * 100, "supply": sup0},
            "new": {"mean": m1 * q, "sd": math.sqrt(v1) * q, "zero": z1 * 100, "supply": sup1},
            "zero_users": z1 * u, "zero_users0": z0 * u, "supply_pct": (sup1 / sup0 - 1) * 100 if sup0 > 0 else None}


def gold(cfg: dict, x0: dict) -> dict:
    x = _clamp(cfg["fields"], cfg["defaults"], x0)
    r0 = x["chars"] * x["rep"]
    save = min(r0 * x["rate"] / 100, x["cap"])
    r1 = r0 - save
    act = x["users"] * x["util"] / 100
    g = x["grow"] / 100
    drop = act * save                    # 서버 골드 회수 감소 (주)
    prod = act * x["prod"] * g           # 플레이 증가 → 추가 골드 생산 (주)
    rec = act * r1 * g                   # 플레이 증가 → 추가 수리(회수) (주)
    net = drop + prod - rec              # 순골드 공급 변화 (+ = 시장에 골드가 더 풀림)
    base = act * x["prod"]
    return {"x": x, "r0": r0, "r1": r1, "save": save, "save_m": save * 4, "act": act, "drop": drop, "prod": prod, "rec": rec,
            "net": net, "net_pct": net / base * 100 if base > 0 else None}
