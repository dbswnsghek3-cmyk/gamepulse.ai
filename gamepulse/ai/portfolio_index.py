"""PM 어시스턴트용 검색(Retrieval) 인덱스 — 4개 게임 분석 데이터(JSON)에서만 답을 찾는다.

- 생성형 AI 가 아니다: 질문을 키워드로 나눠 아래 '항목(Entry)' 과 겹치는 정도로 점수를 매기고, 점수가 가장 높은 항목의 원문을 그대로 보여 준다.
- 항목의 문장은 모두 data/<game>/*.json 에 이미 있는 분석 내용 → 새로운 수치·사실을 만들지 않는다.
- 맞는 항목이 없으면 NOT_FOUND 를 돌려준다.
- 나중에 LLM 을 붙일 때: search() 결과(Entry 목록)를 근거 컨텍스트로 넘기면 된다 (RAG). ai/llm.py 의 구현체가 이 모듈을 재사용하도록 설계.
"""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from gamepulse.ai.base import ChatMessage, PMChatbot

DATA = Path(__file__).resolve().parents[2] / "data"
NOT_FOUND = "현재 분석 자료에서 확인되지 않습니다."
OTHER_GAMES = ("발로란트", "롤", "리그 오브 레전드", "리그오브레전드", "lol", "메이플", "로스트아크", "로아", "원신", "마인크래프트", "배틀필드",
               "서든", "카트라이더", "메이플스토리", "디아블로", "스타크래프트", "세븐나이츠", "리니지", "나혼렙", "몬길")
STATIC_BASE = "https://dbswnsghek3-cmyk.github.io/gamepulse.ai/"
STATIC_FILE = {"overwatch": "overwatch.html", "pubg": "pubg.html", "fconline": "fconline.html", "dnf": "dnf.html"}
NAMES = {"overwatch": "오버워치", "pubg": "PUBG: NEW START", "fconline": "FC 온라인", "dnf": "던전앤파이터"}
TAB_NAMES = {
    "overwatch": {"01": "개요·핵심 문제", "02": "게임 화면·VOC", "03": "PROJECT RE:START", "04": "기존 스킨 BM", "05": "신규 BM 제안", "06": "KPI·사업성", "07": "최종 판단"},
    "pubg": {"01": "문제·결론", "02": "실제 유저 근거", "03": "원인 가설", "04": "해결책 데모", "05": "KPI·A/B 테스트", "06": "실행·사업 판단"},
    "fconline": {"01": "개요·시장", "02": "BM 강점", "03": "유저 VOC 50", "04": "구단 가치", "05": "MY CLUB WAR", "06": "FAIR PLAY", "07": "사업성·실행"},
    "dnf": {"01": "문제 정의", "02": "유저 의견·한계", "03": "원인", "04": "개선안", "05": "시뮬레이터·KPI", "06": "로드맵·판단"},
}
GAME_ALIASES = {
    "overwatch": ["오버워치", "옵치", "overwatch", "ow2", "ow"],
    "pubg": ["배그", "배틀그라운드", "pubg", "펍지", "new start"],
    "fconline": ["fc온라인", "fc 온라인", "fconline", "피파", "fc"],
    "dnf": ["던파", "던전앤파이터", "dnf", "던전"],
}
# 질문 의도 → 우선 볼 항목 종류
INTENTS = {
    "kpi": ["kpi", "지표", "잔존", "d7", "d30", "측정", "성과", "a/b", "ab", "실험", "테스트"],
    "cause": ["원인", "가설", "왜"],
    "strategy": ["전략", "개선", "해결", "제안", "방안", "기획", "아이디어", "어떻게", "접근"],
    "evidence": ["근거", "의견", "댓글", "유저", "리뷰", "목소리", "한계", "출처"],
    "plan": ["예산", "비용", "로드맵", "일정", "리스크", "부작용", "가드레일", "판단", "우선순위", "실행", "결론", "bm", "과금"],
    "problem": ["문제", "불만", "요약", "핵심", "개요", "정리", "이탈", "적응"],
    "priority": ["우선", "먼저", "가장", "1순위", "첫 번째"],
}
SYN = {"힘들": ["어려"], "어렵": ["어려"], "광고비": ["예산"], "돈": ["비용"], "짜증": ["불만"], "접": ["이탈"], "떠나": ["이탈"],
       "접는": ["떠나", "이탈"], "랜덤": ["확률", "운에"], "늘려": ["확대", "전액"], "늘리": ["확대", "전액"], "대응": ["재참여", "분석"],
       "떨어": ["하락"], "적응": ["어려"], "잔존율": ["d7", "잔존"], "논란": ["비판", "논란"], "개발진": ["개발사"], "운영진": ["개발사"], "대처": ["대응"], "접근": ["전략", "개선"], "달라지": ["격차", "갈리"], "bm": ["bm", "과금", "매출"], "과금": ["bm", "매출"], "가챠": ["확률", "bm"], "부작용": ["리스크", "위험"]}
TAB_OF_KIND = {"problem": "01", "evidence": "02", "cause": "03", "strategy": "04", "kpi": "05", "plan": "06", "priority": "06"}
STOP = {"알려줘", "알려", "정리해줘", "뭐야", "무엇", "어떻게", "있어", "대해", "관련", "주세요", "은", "는", "이", "가", "의", "좀"}


@dataclass
class Entry:
    game: str
    kind: str                  # problem / evidence / cause / strategy / kpi / plan
    title: str
    summary: str
    evidence: list[str] = field(default_factory=list)
    strategy: list[str] = field(default_factory=list)
    kpi: list[str] = field(default_factory=list)
    tab: str = "01"
    extra: str = ""            # 검색에만 쓰는 추가 텍스트
    problem: str = ""          # 문제 정의 (비어 있으면 게임 공통 문제 정의)
    sources: list[tuple[str, str]] = field(default_factory=list)   # (제목, URL)

    @property
    def text(self) -> str:
        return " ".join([self.title, self.summary, *self.evidence, *self.strategy, *self.kpi, self.extra]).lower()

    def links(self) -> tuple[str, str]:
        label = f"{NAMES[self.game]} › {self.tab} {TAB_NAMES[self.game].get(self.tab, '')}"
        return label, f"?page={self.game}&tab={self.tab}"

    def static_url(self) -> str:
        return f"{STATIC_BASE}{STATIC_FILE[self.game]}"


def _load(p: str) -> dict:
    return json.loads((DATA / p).read_text(encoding="utf-8"))


def _clean(s: object) -> str:
    return re.sub(r"\*\*", "", str(s)).strip()


def _overwatch() -> list[Entry]:
    d = _load("overwatch/restart.json")
    s = d["summary"]
    out = [Entry("overwatch", "problem", s["headline"], s["lead"], [s.get("limit", "")], [s["conclusion"]],
                 [k["name"] for k in d["kpi_defs"][:3]], "01")]
    out.append(Entry("overwatch", "cause", "이탈 원인 흐름 (가설)",
                     " → ".join(f["step"] for f in d["problem"]["flow"]),
                     [f"{f['step']}: {f['desc']} · 근거 {f['basis']}" for f in d["problem"]["flow"]],
                     [], [f["check"] for f in d["problem"]["flow"]], "02"))
    for st_ in d["strategies"]:
        out.append(Entry("overwatch", "strategy", f"{st_['key']}. {st_['name']}", st_["tagline"],
                         [f"대상: {st_['target']}", f"기존 기능과 차이: {st_.get('vs_existing', '')}"],
                         [st_.get("hypothesis", ""), st_.get("effect", "")], list(st_.get("kpis", [])), "03",
                         " ".join(map(str, st_.get("flow", [])))))
    out.append(Entry("overwatch", "kpi", "KPI 정의", "주요·보조·가드레일 지표와 판단 규칙",
                     [f"{k['name']} ({k['role']}) · 분모: {k['denominator']}" for k in d["kpi_defs"]],
                     [f"{r['result']}: {r['rule']}" for r in d["decision_rules"]], [k["name"] for k in d["kpi_defs"]], "06",
                     d["experiment"].get("note", "")))
    out.append(Entry("overwatch", "evidence", "실제 근거와 한계", s.get("limit", ""),
                     [_clean(o.get("quote") or o.get("text") or o) for o in d.get("rep_opinions", [])[:3] if isinstance(o, dict)],
                     [], [], "02"))
    pri = {x["key"]: x for x in d["strategies"]}
    out.append(Entry("overwatch", "priority", "우선 실행: A 복귀 브리핑", s["conclusion"],
                     [f"{k} {pri[k]['name']}: {pri[k].get('priority_reason', '')}" for k in ("A", "C", "B") if k in pri],
                     [f"1단계 A {pri['A']['name']} — {pri['A']['tagline']}", "2단계 C 첫 10경기 미션 → 3단계 B 학습 카드 (수동형)"],
                     list(pri["A"].get("kpis", [])), "07", "우선 먼저 순서 1순위 실행"))
    out.append(Entry("overwatch", "plan", "실행 범위 · 리스크", "MVP 단계와 리스크 대응",
                     [f"리스크: {r['risk']} → {r['response']}" for r in d["risks"]], list(d["mvp"]["in"]),
                     [], "07", "예산 비용 일정 담당 " + " ".join(o["team"] for o in d["pilot"].get("owners", []))))
    bz = _load("overwatch/business.json")   # 06 기존 스킨 BM(캡처 사실) · 07 YOUR HERO · 08 YOUR CHOICE (사용자 기획안)
    ex, yh, yc = bz["existing_bm"], bz["your_hero"], bz["your_choice"]
    out.append(Entry("overwatch", "bm", "기존 스킨 BM: 영웅별 스킨 수 차이 · 고정형 묶음 · 신화 스킨 단계 해금",
                     "키리코 스킨 11종 vs 메르시 25종 · 묶음 상품 15개 6,900 코인 · 신화 스킨 50→10→10→10 프리즘 (작성자 캡처)",
                     [f"{p['name']}: {p['price']} · {p['unlock']}" for p in ex["products"]], [], [], "04",
                     "BM 과금 상품 스킨 신화 배틀패스 코인 프리즘 상점 묶음 패키지"))
    out.append(Entry("overwatch", "bm", f"신규 BM ① {yh['title']} {yh['slogan']}", yh["purpose"],
                     [f"{s_['t']}: {s_['d']}" for s_ in yh["steps"]], list(yh["effects"]), list(yh["kpis"]), "05",
                     "YOUR HERO 유저 참여형 스킨 제작 투표 BM 신규"))
    out.append(Entry("overwatch", "bm", f"신규 BM ② {yc['title']} {yc['slogan']}", yc["purpose"],
                     [f"{t['name']}: 할인 {t['disc']}% · 예시 가격 {yc['base_price'] * t['n'] * (100 - t['disc']) // 100:,}원" for t in yc["tiers"]]
                     + [yc["price_note"]], list(yc["effects"]), list(yc["kpis"]), "05",
                     "YOUR CHOICE 선택형 스킨 패키지 할인 BM 신규 가격"))
    return out


def _pubg() -> list[Entry]:
    d = _load("pubg/newstart.json")
    c = d["cover"]
    out = [Entry("pubg", "problem", c["subtitle"], c["question"], [f"동시접속 최고 {d['peak']['display']} ({d['peak']['date']} · {d['peak']['source']})"],
                 [f"{t['key']}. {t['name']} — {t['question']}" for t in d["tracks"]], [t["kpi"] for t in d["tracks"]], "01")]
    out.append(Entry("pubg", "cause", "휴면 유저 복귀 장벽 (가설)", "복귀를 막는 장벽 4가지",
                     [f"{b['title']}: {b['line']}" for b in d["return_barriers"]],
                     [b.get("pm", "") for b in d["return_barriers"]], [], "03"))
    ta = next(t for t in d["tracks"] if t["key"] == "A")
    pa = [x for x in d["proposals"] if x["track"] == "A"]
    out.append(Entry("pubg", "cause", "신규 유저가 첫 실전 직후 떠나는 이유 (가설)", f"{ta['question']} — {ta['sub']}",
                     [f"{x['key']}: {x['problem']}" for x in pa],
                     [f"{x['key']} {x['name'].split(' · ')[0]}: {x['diff']}" for x in pa],
                     [k[0] for k in d["kpis"]["A"][:3]], "03", "신규 이탈 접는 빨리 떠나 첫 경기 실력 격차 숙련"))
    camp = d["campaign"]
    for p in d["proposals"]:
        ads = [f"광고 {a['no']}: {a['title']}" for a in camp["ads"]] if p["key"] == "B1" else []
        out.append(Entry("pubg", "strategy", f"{p['key']}. {p['name']}", p["problem"],
                         [f"기존: {p['existing']}"] + ([f"대상: {camp['target']}"] if ads else []),
                         [f"차별점: {p['diff']}", f"우선순위: {p['decision']}", d["mvp_reason"].get(p["key"], "")] + ads,
                         [], "04", f"{p.get('data', '')} {p.get('risk', '')} {'광고 지하철 캠페인 ' + camp['why'] if ads else ''}"))
    cost = d["experiment"]["cost"]
    dig_w = next(w for n, _, w in camp["channels"] if "디지털" in n)
    dig = camp["budget"] * dig_w / 100
    land = cost["B1_effort"] * cost["monthly_cost_per_person"]
    man = lambda v: (f"{v / 1e8:g}억 원" if v >= 1e8 and v % 1e8 == 0 else f"{v / 1e4:,.0f}만 원")  # noqa: E731
    out.append(Entry("pubg", "plan", "B1 광고 예산: 1억 원 전액 대신 디지털 파일럿",
                     "PUBG의 ARPU·LTV를 공개 자료로 확인하지 못해 광고 1억 원의 수익성을 판단할 수 없다 → 전액 집행 보류",
                     [f"기존 제안: 광고 {man(camp['budget'])} (디지털 {dig_w}% · 옥외 · 콘텐츠) + 랜딩 제작 {cost['B1_effort']:g}인월 (가정)",
                      "옥외·콘텐츠 광고는 무작위 배정이 안 돼 홀드아웃 대비 순증 복귀를 측정할 수 없다",
                      "손익분기: 순증 복귀자 1명의 기대 매출이 1인당 획득 비용 이상이어야 함 → LTV 미확인"],
                     [f"디지털 리타깃팅 파일럿 {man(dig + land)} = 디지털 {man(dig)} + 랜딩·UTM {man(land)} (가정)",
                      "휴면 리스트를 광고 3종 + 대조군으로 무작위 배정 → 소재별 순증 측정",
                      "확대: 홀드아웃 대비 유의한 순증 + 재정착 1인당 비용 ≤ 내부 LTV 기준 · 중단: 모든 소재가 차이 없음 또는 신고율 악화"],
                     ["순증 D30 재정착 유저당 비용", "복귀 로그인 전환율", "복귀 첫 경기 완료율", "D7·D30"], "05",
                     "1억 억 예산 광고비 바로 전액 집행 손익분기 LTV 파일럿 5,600 이유"))
    out.append(Entry("pubg", "priority", "우선 실행: A1 NEXT MATCH COACH", "신규 유저가 첫 실전 직후 떠나는 지점에 바로 닿는 개선부터",
                     [f"{k}: {d['mvp_reason'].get(k, '')}" for k in ("A1", "B1")],
                     [f"{p['key']} {p['name'].split(' · ')[0]}: {p['decision']}" for p in d["proposals"]][:4],
                     [k[0] for k in d["kpis"]["A"][:3]], "06", "우선 먼저 순서 1순위 MVP"))
    out.append(Entry("pubg", "plan", "실행 · 사업 판단 · 리스크", "우선순위와 리스크 대응",
                     [f"리스크: {r['risk']} → {r['response']}" for r in d["risks"]],
                     [f"{p['key']} {p['name'].split(' · ')[0]}: {p['decision']}" for p in d["proposals"]], [], "06",
                     "예산 비용 손익 시나리오 사업성 파일럿"))
    out.append(Entry("pubg", "kpi", "KPI 정의", "트랙별 주요·보조·가드레일 지표",
                     [f"[{t}] {k[0]} ({k[1]}) · {k[3]}" for t, ks in d["kpis"].items() for k in ks], [],
                     [k[0] for ks in d["kpis"].values() for k in ks], "05"))
    return out


def _fconline() -> list[Entry]:
    """FC 온라인 (2026-11 개편 · data/fconline/fc2.json)."""
    d = _load("fconline/fc2.json")
    m, bm, ca, rb, mc, fp = d["market"], d["bm"], d["care"], d["rebuild"], d["mcw"], d["fair"]
    out = [Entry("fconline", "problem", "FC 온라인 핵심 문제와 전략 4개", d["cover"]["subtitle"],
                 [" → ".join(d["chain"]), d["chain_note"]], [f"{a}: {b}" for a, b in d["final"]] + [d["final_msg"]],
                 [k[1] for k in d["kpis"]], "01", "대표 문제 구단 가치 이탈 전략 요약")]
    out.append(Entry("fconline", "evidence", "시장 경쟁력 · PC방 순위", m["caution"],
                     [f"{p_['when']} {p_['rank']} {p_['share']} ({p_['src']})" for p_ in m["points"]], [f"{a}: {b}" for a, b in m["strengths"]], [],
                     "01", "PC방 점유율 순위 월드컵 시장 경쟁"))
    out.append(Entry("fconline", "bm", "기존 BM 강점", bm["insight"],
                     [f"{b['name']}: {b['fact'] or '캡처 확인 필요'}" for b in bm["items"]], [bm["risk"]], [], "02",
                     "BM 멤버십 페이백 버닝 강화 이적시장 시즌 패스 과금"))
    out.append(Entry("fconline", "evidence", f"유저 VOC {len(d['voc'])}건", d["voc_note"],
                     [f"{v['date']} {v['title']} — {v['summary']}" for v in d["voc"][:12]], [], [], "03", "VOC 유저 의견 커뮤니티 인벤"))
    out.append(Entry("fconline", "strategy", f"{ca['name']} · {ca['slogan']}", ca["existing"],
                     [f"{a}: {b}" for a, b in ca["features"]], list(ca["rules"]), list(ca["kpi"]), "04", "구단 가치 관리 리포트 알림 CARE"))
    out.append(Entry("fconline", "strategy", f"{rb['name']} · {rb['slogan']}", "구단 가치 급락 유저에게 인생 강화·이탈 외의 선택지",
                     [f"{a}: {b}" for a, b in rb["steps"]], list(rb["guard"]), list(rb["kpi"]), "04", "재건 REBUILD 강화 실패 급락 복귀"))
    out.append(Entry("fconline", "marketing", f"{mc['name']} · {mc['slogan']}", mc["license"],
                     [f"{a}: {b}" for a, b in mc["steps"]], list(mc["fair"]) + list(mc["external"]), list(mc["kpi"]), "05",
                     "마케팅 팬덤 구단 대항전 아이콘매치 인플루언서 신규 유저"))
    out.append(Entry("fconline", "strategy", f"{fp['name']} · 키보드와 패드", fp["other"],
                     [f"키보드 {fp['controller']['kb']}% · 패드 {fp['controller']['pad']}% ({fp['controller']['date']} 상위 1만 1ON1)"] + [f"{a}: {b}" for a, b in fp["steps"]],
                     [fp["stop"]], list(fp["kpi"]), "06", "키보드 패드 조작 분리 매칭 공정"))
    out.append(Entry("fconline", "kpi", "KPI · 사업성 시뮬레이션", d["sims"]["keep"]["note"],
                     [f"{k[0]}: {k[1]} · 성공 {k[4]}" for k in d["kpis"]], [f"{r_[0]} → {r_[1]}" for r_ in d["roadmap"]], [k[1] for k in d["kpis"]], "07",
                     "KPI 시뮬레이션 이탈률 매출 보전 CPA LTV 로드맵 우선순위"))
    return out


def _dnf() -> list[Entry]:
    d = _load("dnf/dnf.json")
    i = d["intro"]
    ops_all = d.get("key_opinions", [])
    op_line = lambda o: f"유저 의견 {o['no']} ({o['date']}) {o['summary']} — 원문: “{o['quotes'][0][0]}”"  # noqa: E731
    out = [Entry("dnf", "problem", "던전앤파이터 핵심 문제", f"{d['cover']['title']} {d['cover']['title2']}",
                 [f"{s[0]}: {s[1]} ({s[2]})" for s in i["season"]],
                 [f"{p[0]}. {p[1]} — {p[2]} ({p[3]})" for p in d["problems"]], [], "01", i["line"] + " " + i["question"])]
    prob = {p[0]: f"{p[1]} {p[2]}" for p in d["problems"]}
    for s in d["solutions"]:
        ops = [op_line(o) + f" → {o['pm']}" for o in ops_all if o["sol"] == s["k"]]
        out.append(Entry("dnf", "strategy", f"{s['k']}. {_clean(s['name'])}", _clean(s["p"]), ops or [f"문제 {s['k']}: {prob.get(s['k'], '')}"],
                         [_clean(s["c"])], [_clean(s.get("v", "")) or next((k[1] for k in d["kpis"] if k[0] == s["k"]), "")], "04",
                         _clean(s.get("r", "")) + " " + prob.get(s["k"], "")))
    upd = next((o for o in d["official"] if "2928057" in o["url"]), None)
    pb = next(x for x in d["problems"] if x[0] == "B")
    out.append(Entry("dnf", "cause", "랜덤 보상이 성취감 문제가 되는 이유 (가설)", pb[2],
                     ([f"공식 (2026-07-29 · 퍼스트서버): {upd['fact']}"] if upd else []) + [op_line(o) for o in ops_all if o["sol"] == "B"],
                     ["확률 보상의 재미는 유지하고, 목표를 정해 운이 나쁜 클리어도 진척으로 쌓이게 → B 지정 장비 진척 게이지 (04 탭)"],
                     [k[1] for k in d.get("kpi_main", [])][:3], "03", "랜덤 확률 운 운에 따라 달라 갈리 격차 왜 문제 성취감 노력"))
    out.append(Entry("dnf", "cause", "미카엘라 하드 레이드 보상 논란 (2026)", "하드·일반 이상 난이도의 보상이 시간·난이도 대비 약하다는 유저 비판 → 개발사가 보상 부족을 인정",
                     [op_line(o) for o in ops_all if o["no"] in ("②", "③")] + [f"{a}: {b}" for a, b, _ in d["dev_response"][:1]],
                     [d["dev_gap"], "→ B 지정 장비 진척 게이지로 '반복 클리어 → 예측 가능한 목표' 연결 (04 탭)"],
                     [k[1] for k in d.get("kpi_main", [])][:3], "02", "미카엘라 레이드 하드 보상 논란 비판 왜"))
    ro = d.get("reward_obs")
    if ro:
        out.append(Entry("dnf", "evidence", "미카엘라 하드 클리어와 실제 보상 (영상 확인)",
                         "하드모드 정화 성공 · 클리어 타임 29분 26초 · 클리어 보상과 입찰 전리품 화면을 영상에서 확인",
                         ["클리어 보상 (캐릭터 1명): " + " · ".join(ro["items"]), ro["auction"], ro["official"]],
                         [ro["pm"], "→ B 지정 장비 진척 게이지로 '반복 클리어 → 예측 가능한 목표' 연결 (04 탭)"],
                         [k[1] for k in d.get("kpi_main", [])][:3], "02", "클리어 보상 결과 실제 화면 영상 전투 하드 레이드 빛망울 입찰 전리품 업그레이드"))
        out[-1].sources = [("유튜브 · 하드 미카엘라 클리어 (2026-08-09)", d["media"]["clear"]["url"]),
                           ("공식 7/29 업데이트 (퍼스트서버)", "https://df.nexon.com/community/news/update/2928057")]
    out.append(Entry("dnf", "evidence", "개발사의 실제 대응 (2026-10)", "10/27 라이브에서 하드 보상 부족을 인정하고, 10/29부터 8주간 특별 경매를 임시 조치로 운영",
                     [f"{a}: {b}" for a, b, _ in d["dev_response"]],
                     [d["dev_gap"], "GamePulse AI 제안은 이 대응을 대체하지 않고 보완: 입찰 없는 본인 귀속 목표 · 확률·경매 유지"],
                     [k[1] for k in d.get("kpi_main", [])][:3], "02", "개발사 대응 개발진 디렉터 특별 경매 공지 조치"))
    out[-1].sources = [(f"{a.split(' · ')[0]} {a.split(' · ')[1] if ' · ' in a else ''}".strip(), u) for a, _, u in d["dev_response"]]
    out.append(Entry("dnf", "strategy", "기존 보장 장치와 B 지정 장비 진척 게이지의 차이",
                     "기존 경매·상점 재화·기대 배율은 확률 결과나 입찰에 달려 있음 · '목표 지정 + 이번 클리어의 불운 반영'은 확인되지 않음",
                     [f"{a}: {b}" for a, b, _, _ in d["gap"]],
                     [f"{a} → {c} ({e})" for a, _, c, e in d["gap"][:3]] + [f"{x[0]}: {x[1]} — {x[2]}" for x in d["alternatives"][1:]],
                     [f"{k[1]} — {k[2]}" for k in d.get("kpi_main", [])], "04", "기존 보장 시스템 차이 중복 다른 점 네 제안"))
    v = _load("dnf/voc.json")
    vi, vc, vs = v["items"], v["categories"], v["sources"]
    vlink = lambda x: (f"{vs[x['src']][0]} ({x['date']})")  # noqa: E731
    by = lambda c: [x for x in vi if x["cat"] == c]  # noqa: E731
    n_yt = sum(x["src"].startswith("YT") for x in vi)
    n_kk = sum(x["src"] == "KAKAO" for x in vi)
    order = v["core_cats"] + v["sub_cats"] + [v["positive_cat"]]
    out.append(Entry("dnf", "evidence", f"던파 유저 의견 전수 (VOC {len(vi)}건)",
                     f"원본 캡처 {v['capture']['original_files']}장 + 2026 공식 게시판 글 {v['board']['posts']}개 → 중복 제외 유효 VOC {len(vi)}건 "
                     f"(유튜브 댓글 {n_yt} · 공식 게시판 {len(vi) - n_yt - n_kk} · 지인 1명 {n_kk}) · 이전 사이트 반영 {sum(x['before'] for x in vi)}건 → 전체 목록화",
                     [f"{vc[str(c)]} {len(by(c))}건 — 예: {by(c)[0]['summary']}" for c in order if by(c)],
                     ["핵심 범주(보상 체감·확률 불확실성·반복 동기·난이도 차이) → 지정 장비 진척 게이지",
                      f"분석 범위 밖 {sum(x['cat'] not in order for x in vi)}건 (운영·디렉터 평가 등) · 영상 주제에 따른 편향 있음 · 건수는 표본 내 분포일 뿐 전체 비율 아님"],
                     [k[1] for k in d.get("kpi_main", [])][:3], "02", "유저 의견 총 몇 건 지적 문제 voc 전수 범주 불만 의견들"))
    out[-1].sources = [(vs[k][0], vs[k][1]) for k in ("A", "D", "E") ]
    c4 = by(4)
    out.append(Entry("dnf", "cause", "난이도별 보상 차이 · 하드 진입 효율 (유저 의견)",
                     "일반·하드의 보상 차이가 작아 상위 난이도로 갈 이유가 약하다는 의견이 많다 · 반대로 하드 경매·원하는 아이템 획득 경험을 이유로 갈 만하다는 의견도 있다",
                     [f"{x['summary']} — {vlink(x)}" for x in c4 if x["src"] in ("A", "B", "C", "E", "F2")][:6],
                     ["공식 7/29: 하드는 경매가 확률적으로 진행 · 재료 구성이 난이도별로 다름", "→ 지정 장비 진척 게이지에서 하드 진척 가중치를 실험 변수로 두고 일반↔하드 이동 비율로 검증"],
                     ["일반↔하드 이동 비율", "하드 레이드 재도전율", "클리어 후 보상 만족도"], "02",
                     "일반 하드 난이도 보상 차이 진입 효율 비용 투자 싱글 매칭 갈 이유"))
    out[-1].sources = [(vs[k][0], vs[k][1]) for k in ("A", "B", "C")]
    pos = [x for x in vi if x["stance"] == "긍정" or x["cat"] == v["positive_cat"]]
    out.append(Entry("dnf", "evidence", "던파 유저의 긍정적인 반응 · 반대 의견", "레이드 전투·난이도 자체는 재미있다는 평가가 있다 → 문제는 '레이드가 재미없다'가 아니라 전투 성취감과 장기 성장·보상 체감 사이의 간극",
                     [f"{x['summary']} — {vlink(x)}" for x in pos] + ["2026-08-12 질문 글도 레이드 자체는 호평 (공식 게시판)"],
                     ["전투 경험은 유지하고 보상·성장 체감만 보완 → 지정 장비 진척 게이지"], [], "02",
                     "긍정 반응 좋은 평가 재미 호평 반대 의견 장점"))
    out[-1].sources = [(vs["D"][0], vs["D"][1]), (vs["A"][0], vs["A"][1])]
    c6 = by(6)
    out.append(Entry("dnf", "cause", "후발 유저의 레이드 진입 장벽 (보조 분석)",
                     "하드 파티 모집 기준(명성·스펙)이 높아 후발·복귀 유저가 진입을 고민한다는 질문과 정보성 답변이 있다",
                     [f"{x['summary']} — {vlink(x)}" for x in c6][:6],
                     ["현재 개선안(지정 장비 진척 게이지)은 진입 장벽을 직접 해결하지 않음 → 보조 분석으로만 다룸",
                      "유저들이 제시한 방법: 일반 파티로 숙련도를 올린 뒤 하드 진입 (2026-11-17 댓글) · 새 기능을 추가로 제안하지 않음"],
                     ["일반↔하드 이동 비율 (관찰 지표)", "하드 레이드 재도전율"], "02",
                     "후발 유저 진입 장벽 스펙 컷 파티 흑아 명성 복귀 해결"))
    out[-1].sources = [(vs["E"][0], vs["E"][1]), (vs["D"][0], vs["D"][1])]
    out.append(Entry("dnf", "kpi", "실제 이탈 데이터 없이 던파 문제를 검증하는 방법",
                     "VOC와 공식 자료로 가설을 세웠고, 효과는 로그 확인 → 소규모 A/B → 확대·롤백 순서로 검증한다",
                     [f"{r[0]} {r[1]}: {r[2]}" for r in d["roadmap"]] + list(d["experiment"][:3]),
                     ["VOC 102건은 문제를 찾는 출발점 · 이탈률·불만 비율은 단정하지 않음"],
                     [k[1] for k in d.get("kpi_main", [])], "06", "실제 이탈 데이터 없이 검증 방법 어떻게 검증 로그 실험"))
    out.append(Entry("dnf", "priority", "우선 실행: B 지정 장비 진척 게이지 소규모 파일럿", d["decision"],
                     [f"{r[0]} {r[1]}: {r[2]}" for r in d["roadmap"]][:3],
                     [d["decision"]], [f"{k[1]}" for k in d.get("kpi_main", [])], "06", "우선 먼저 순서 1순위"))
    out.append(Entry("dnf", "kpi", "KPI · 실험", "개선안별 측정 지표와 실험 설계", list(d["experiment"]), [],
                     [f"{k[1]} ({k[0]})" for k in d.get("kpi_main", [])], "05"))
    out.append(Entry("dnf", "evidence", "근거의 범위와 한계", "2026 공식 게시판 글 3건과 공식 발표 · 정성 근거", list(d["limits"]), [], [], "02"))
    out.append(Entry("dnf", "plan", "로드맵 · 판단 · 예산", d["decision"],
                     ["예산(인월): " + " · ".join(f"{c[0]} {c[1]}" for c in d["cost"]["items"]) + f" × 월 {d['cost']['monthly'] // 10000}만 원"]
                     + [f"리스크: {r[0]} → {r[1]}" for r in d["risks"]],
                     [" · ".join(map(str, r)) for r in d["roadmap"]], [], "06", "예산 비용 일정 리스크 로드맵"))
    return out


def _game_defaults() -> dict[str, dict]:
    """게임별 공통 문제 정의 · 기본 근거 · 공식 출처 (모두 data/*.json 원문)."""
    ow, pb = _load("overwatch/restart.json"), _load("pubg/newstart.json")
    fc, dn = _load("fconline/fc.json"), _load("dnf/dnf.json")
    fc2 = _load("fconline/fc2.json")
    src = lambda xs, t="title": [(f"{x.get(t) or x.get('src')} ({x['date']})", x["url"]) for x in xs if x.get("url")][:3]  # noqa: E731
    return {
        "overwatch": {"problem": f"{ow['summary']['headline']} — {ow['summary']['lead']}",
                      "evidence": [f"공식: {o['title']} ({o['date']}) — {o['fact']}" for o in ow["official"][:2]],
                      "sources": src(ow["official"])},
        "pubg": {"problem": f"{pb['cover']['question']} ({pb['cover']['subtitle']})",
                 "evidence": [f"{b['title']}: {b['line']}" for b in pb["return_barriers"][:2]] + [f"공식: {o['title']} ({o['date']})" for o in pb["official"][:1]],
                 "sources": src(pb["official"])},
        "fconline": {"problem": fc2["cover"]["subtitle"],
                     "evidence": [f"PC방 {p_['when']} {p_['rank']} {p_['share']} ({p_['src']})" for p_ in fc2["market"]["points"][-2:]] + [fc2["voc_note"]],
                     "sources": [(f"{p_['src']}", p_["url"]) for p_ in fc2["market"]["points"] if p_["url"]][:3]},
        "dnf": {"problem": dn["intro"]["question"],
                "evidence": [f"유저 의견 {o['no']} ({o['date']}) {o['theme']} — {o['pm']}" for o in dn.get("key_opinions", [])[:3]],
                "sources": [(f"{o['src']} ({o['date']})", o["url"]) for o in dn["official"] if o["date"].startswith("2026-")][-3:]},
    }


@lru_cache(maxsize=1)
def build_index() -> tuple[Entry, ...]:
    entries: list[Entry] = []
    for fn in (_overwatch, _pubg, _fconline, _dnf):
        entries.extend(fn())
    gd = _game_defaults()
    for e in entries:
        g = gd[e.game]
        if not e.problem:
            e.problem = e.summary if e.kind == "strategy" else g["problem"]
        if not e.evidence:
            e.evidence = list(g["evidence"])
        if not e.sources:
            e.sources = list(g["sources"])
    for e in entries:  # 빈 문자열 정리
        e.evidence = [x for x in e.evidence if str(x).strip()]
        e.strategy = [x for x in e.strategy if str(x).strip()]
        e.kpi = [x for x in e.kpi if str(x).strip()]
    return tuple(entries)


def _alias_hit(ql: str, a: str) -> bool:
    if re.fullmatch(r"[a-z0-9 ]+", a):      # 영문 별칭은 단어 단위 (예: 'how' 안의 'ow' 는 무시)
        return re.search(rf"(?<![a-z]){re.escape(a)}(?![a-z])", ql) is not None
    return a in ql


def _fuzzy_alias(ql: str) -> list[str]:
    """띄어쓰기를 지운 문자열 · 오타(예: 오버위치)로도 게임을 찾는다."""
    ns = re.sub(r"\s+", "", ql)
    found = [g for g, al in GAME_ALIASES.items() if any(len(a) >= 3 and a.replace(" ", "") in ns for a in al)]
    if found:
        return found
    flat = {a: g for g, al in GAME_ALIASES.items() for a in al if len(a) >= 3 and not re.fullmatch(r"[a-z0-9 ]+", a)}
    for tok in re.findall(r"[가-힣]{3,}", ql):
        m = difflib.get_close_matches(tok[: max(3, len(tok) - 1)], list(flat), n=1, cutoff=0.75) or difflib.get_close_matches(tok, list(flat), n=1, cutoff=0.75)
        if m:
            found.append(flat[m[0]])
    return list(dict.fromkeys(found))


def detect_games(q: str) -> list[str]:
    ql = q.lower()
    hit = [g for g, al in GAME_ALIASES.items() if any(_alias_hit(ql, a) for a in al)]
    return hit or _fuzzy_alias(ql)


def infer_game(q: str) -> str | None:
    """게임 이름이 없을 때: 질문 단어 중 한 게임의 자료에만 있는 단어가 있으면 그 게임."""
    by_game = {g: " ".join(e.text for e in build_index() if e.game == g) for g in NAMES}
    owned: dict[str, list[str]] = {}
    for t in _terms(q):
        owners = [g for g, txt in by_game.items() if t in txt]
        if len(owners) == 1:
            owned.setdefault(owners[0], []).append(t)
    if len(owned) != 1:
        return None
    g, ts = next(iter(owned.items()))
    domain = {"하드", "레이드", "던전", "강화", "구단", "패드", "광고", "영웅"}
    return g if len(ts) >= 2 or any(len(t) >= 3 or t in domain for t in ts) else None   # '설정' 같은 흔한 2글자 단어 하나로는 추론하지 않음


def detect_kinds(q: str) -> list[str]:
    ql = q.lower()
    kinds = [k for k, words in INTENTS.items() if any(w in ql for w in words)]
    weak = not any(w in ql for w in ("문제", "불만", "이탈", "적응", "개요"))
    if "problem" in kinds and len(kinds) > 1 and weak:
        kinds.remove("problem")
    if "problem" in kinds and "cause" in kinds:          # '왜 문제야' → 원인 항목 우선
        kinds.remove("problem")
    if "problem" in kinds and "strategy" in kinds and any(w in ql for w in ("어떻게", "해결", "접근", "방법")):
        kinds.remove("problem")                           # '문제는 어떻게 접근해?' → 전략 항목 우선
    return kinds


@lru_cache(maxsize=1)
def _vocab() -> list[str]:
    return sorted({w for e in build_index() for w in re.findall(r"[가-힣]{2,}", e.text)})


def _terms(q: str) -> list[str]:
    ql = q.lower()
    for al in GAME_ALIASES.values():
        for a in sorted(al, key=len, reverse=True):
            if _alias_hit(ql, a):
                ql = re.sub(rf"(?<![a-z]){re.escape(a)}(?![a-z])", " ", ql) if re.fullmatch(r"[a-z0-9 ]+", a) else ql.replace(a, " ")
    toks = re.findall(r"[0-9a-z가-힣/]+", ql)
    corpus = " ".join(e.text for e in build_index())
    out = []
    for t in toks:
        if t.startswith("운") and len(t) <= 4:          # '운이라·운에' → 확률·불운 (한 글자 단어 보완)
            out += ["확률", "불운"]
        st_ = re.sub(r"(은|는|이|가|을|를|의|에|로|으로|와|과|도|만|에서|해줘|알려줘|줘)$", "", t)
        t = st_ if len(st_) >= 2 or t not in corpus else t   # '성과'처럼 떼면 한 글자가 되는 단어는 그대로
        if re.fullmatch(r"[a-z0-9/]+", t):
            if t not in corpus:                         # 영문은 자르지 않음 · 자료에 없는 단어는 버림
                continue
        else:
            if len(t) >= 3 and t not in corpus:         # 오타 교정 (자료에 있는 가까운 단어)
                m = difflib.get_close_matches(t, _vocab(), n=1, cutoff=0.8)
                if m:
                    t = m[0]
            while len(t) > 2 and t not in corpus:      # '복귀하면 → 복귀' 처럼 어미를 줄여 가며 자료에 있는 형태 찾기
                t = t[:-1]
        if len(t) >= 2 and t not in STOP:
            out += [t] + SYN.get(t, [])
    return list(dict.fromkeys(out))


NUM_Q = re.compile(r"몇\s*(퍼센트|%|명|개|회|원)|얼마|수치|매출|확률이\s*몇|비율이\s*몇")
GENERIC = {"몇", "퍼센트", "얼마", "얼마야", "수치", "숫자", "정도", "실제", "대략", "현재", "최근"}


def _missing_metric(q: str, game: str | None) -> str:
    """수치를 묻는데 질문의 핵심 단어가 해당 게임 자료에 아예 없으면 그 단어를 돌려준다 (없으면 '')."""
    if not NUM_Q.search(q):
        return ""
    games = [game] if game else detect_games(q)
    pool = " ".join(e.text for e in build_index() if not games or e.game in games)
    ql = q.lower()
    for al in GAME_ALIASES.values():
        for a in sorted(al, key=len, reverse=True):
            if _alias_hit(ql, a):
                ql = ql.replace(a, " ")
    for t in re.findall(r"[가-힣a-z]+", ql):
        t = re.sub(r"(은|는|이|가|을|를|의|에|로|으로|와|과|도|만|에서|이야|야|인가|인지|일까)$", "", t)
        if len(t) >= 2 and t not in GENERIC and t not in STOP and t not in pool:
            return t
    return ""


def search(q: str, game: str | None = None, k: int = 3) -> list[tuple[float, Entry]]:
    games = [game] if game else detect_games(q)
    kinds = detect_kinds(q)
    terms = _terms(q)
    pool = [e for e in build_index() if not games or e.game in games]
    # 드문 단어(해당 범위에서 2개 항목 이하에만 나오는 단어)는 질문의 핵심일 가능성이 높아 2배
    w = {t: (2.0 if sum(t in e.text for e in pool) <= 2 else 1.0) for t in terms}
    scored = []
    for e in pool:
        s = 0.0
        if e.kind in kinds:
            s += 2.0
        s += sum(w[t] for t in terms if t in e.text)
        s += 0.8 * sum(1 for t in terms if t in e.title.lower())   # 제목과 많이 겹칠수록 가산
        if s > 0:
            scored.append((s, e))
    scored.sort(key=lambda x: -x[0])
    # 게임만 지정되고 의도·키워드가 없으면 '문제 요약' 항목을 보여 준다
    if not scored and games and not terms:
        scored = [(1.0, e) for e in build_index() if e.game in games and e.kind == "problem"]
    # 키워드만 맞고 의도·게임이 모두 없으면 근거가 약하다 → 2개 이상 일치만 인정
    if not games and not kinds:
        scored = [x for x in scored if x[0] >= 2.0]
    return scored[:k]


@lru_cache(maxsize=1)
def _qa() -> list[dict]:
    return _load("assistant/qa.json")["items"]


@lru_cache(maxsize=1)
def _costs() -> dict[str, float]:
    """제안별 공수(인월) · 각 게임 JSON에서 계산 (가정값)."""
    ow, pb, fc, dn = _load("overwatch/restart.json"), _load("pubg/newstart.json"), _load("fconline/fc.json"), _load("dnf/dnf.json")
    c: dict[str, float] = {f"ow:{x['key']}": float(x["effort"]) for x in ow["rice"]["items"]}
    pc = pb["experiment"]["cost"]
    c["pubg:A1"], c["pubg:B1"] = float(pc["A1_effort"]), float(pc["B1_effort"])
    dig_w = next(w for n, _, w in pb["campaign"]["channels"] if "디지털" in n)
    c["won:pubg:B1pilot"] = pb["campaign"]["budget"] * dig_w / 100 + pc["B1_effort"] * pc["monthly_cost_per_person"]
    for name, mm, *_ in fc["cost"]["items"]:
        if name.startswith("A1"):
            c["fc:A1"] = float(mm)
        if name.startswith("A2"):
            c["fc:A2"] = float(mm)
    for name, mm in dn["cost"]["items"]:
        if name.startswith("B "):
            c["dnf:B"] = float(mm)
    return c


def _man(v: float) -> str:
    return f"{v / 1e8:g}억 원" if v >= 1e8 and v % 1e7 == 0 else f"약 {v / 1e4:,.0f}만 원"


def _fill(text: str) -> str:
    c, mon = _costs(), 6_000_000

    def cost(m):
        k = m.group(1)
        if k == "pubg:B1pilot":
            return f"{_man(c['won:pubg:B1pilot'])} (가정)"
        return f"{c[k]:g}인월 · {_man(c[k] * mon)} (가정)"

    def total(m):
        return f"{_man(sum(c[k.strip()] for k in m.group(1).split(',')) * mon)} (가정)"
    text = re.sub(r"\{cost:([a-z]+:[A-Za-z0-9]+)\}", cost, text)
    return re.sub(r"\{sum:([^}]+)\}", total, text)


def qa_match(q: str) -> dict | None:
    """게임 이름이 없는 비교·우선순위 질문을 qa.json 에서 찾는다 (긴 핵심어 1점 · 짧은 핵심어 0.5점)."""
    ns = re.sub(r"\s+", "", q.lower())
    best, top = None, 0.0
    for it in _qa():
        sc = sum((1.0 if len(k.replace(" ", "")) >= 3 else 0.5) for k in it["keys"] if k.replace(" ", "").lower() in ns)
        if sc > top:
            best, top = it, sc
    return best if top >= 1 else None


def qa_md(it: dict) -> str:
    link = lambda a, pg, tb: f"[{a}](?page={pg}{'&tab=' + tb if tb else ''})"  # noqa: E731
    parts = [f"#### {it['cat']} · {it['q']}", f"**핵심 결론** — {_fill(it['conclusion'])}",
             "**문제와 근거**\n" + "\n".join(f"- {_fill(x)}" for x in it["points"]),
             "**사업PM 개선 전략**\n" + "\n".join(f"- {_fill(x)}" for x in it["strategy"])]
    if it.get("kpi"):
        parts.append("**핵심 KPI** (목표·가정 · 실측 아님)\n" + "\n".join(f"- {x}" for x in it["kpi"]))
    parts.append("**관련 분석 페이지 · 출처**\n" + " · ".join(link(*x) for x in it["links"]) + f"\n\n_{it['note']}_")
    parts.append("_포트폴리오 기반 검색형 답변 · 4개 게임 분석 자료에서 정리했으며 새로운 사실을 만들지 않습니다._")
    return "\n\n".join(parts)


def answer_md(q: str, game: str | None = None, datalab: dict | None = None) -> str:
    """검색 결과를 '핵심 결론 → 문제와 근거 → 사업PM 개선 전략 → 핵심 KPI → 관련 페이지' 마크다운으로 (원문 그대로)."""
    gs = detect_games(q)
    if not game and len(gs) >= 2 and any(w in q for w in ("달라", "다른", "차이", "비교", "vs", "공통")):
        return _multi_md(q, gs)
    if not game and not detect_games(q):
        it = qa_match(q)
        if it:
            return qa_md(it)
    if not game and not detect_games(q) and (any(w in q for w in ("공통", "전체", "모든 게임", "비교", "4개", "네 게임", "4 게임", "각 게임"))
                                             or "priority" in detect_kinds(q)):
        return _cross_md(q)
    if not game and not detect_games(q) and any(o in q.lower() for o in OTHER_GAMES):
        return (f"**{NOT_FOUND}** 이 포트폴리오는 오버워치 · PUBG · FC 온라인 · 던전앤파이터 4개 게임만 분석했습니다. "
                "다른 게임에 대한 수치나 의견은 만들지 않습니다.")
    if not game and not detect_games(q):
        game = infer_game(q)
    miss = _missing_metric(q, game)
    if miss:
        return (f"**{NOT_FOUND}** 분석 자료에 '{miss}' 수치가 없습니다. 근거 없는 수치는 만들지 않습니다.\n\n"
                "공개 자료로 확인한 수치와 가정값만 각 게임 페이지에 표시되어 있습니다.")
    hits = search(q, game)
    if hits and not game and not detect_games(q):
        top_s = hits[0][0]
        gs = list(dict.fromkeys(e.game for sc, e in hits if sc >= top_s - 1))
        if len(gs) > 1:
            cands = " · ".join(f"[{NAMES[g]}](?page={g})" for g in gs)
            return (f"**어느 게임에 대한 질문인지 확인이 필요합니다.** 비슷하게 맞는 자료가 여러 게임에 있습니다: {cands}\n\n"
                    "질문에 게임 이름(오버워치·배그·FC·던파)을 넣거나 위에서 게임을 선택해 주세요. 4개 게임을 비교하려면 '4개 게임 공통 …'으로 물어보세요.")
    if not hits:
        return f"**{NOT_FOUND}**\n\n질문에 게임 이름(오버워치·배그·FC·던파)과 알고 싶은 항목(문제·근거·전략·KPI·예산)을 함께 넣어 보세요."
    top = hits[0][1]
    label, href = top.links()
    if top.kind == "strategy" and re.match(r"^[A-D]\d?(-\d)?\. ", top.title):
        concl = f"{top.summary} → **{top.title}**"
    elif top.kind == "strategy":
        concl = top.summary
    elif top.kind == "problem":
        concl = top.problem
    elif top.kind == "kpi":
        concl = "핵심 KPI: " + " · ".join(top.kpi[:3]) + " (목표·가정)"
    else:
        concl = top.summary
    parts = [f"#### {NAMES[top.game]} · {top.title}", f"**핵심 결론** — {concl}"]
    parts.append("**문제와 근거**\n" + "\n".join(f"- {x}" for x in top.evidence[:3]))
    strat = top.strategy[:3] or [top.summary]
    parts.append("**사업PM 개선 전략**\n" + "\n".join(f"- {x}" for x in strat))
    if top.kpi:
        parts.append("**핵심 KPI** (목표·가정 · 실측 아님)\n" + "\n".join(f"- {x}" for x in top.kpi[:4]))
    src = [f"- 분석 페이지: [{label}]({href}) · [정적 페이지]({top.static_url()})"] + [f"- 출처: [{t}]({u})" for t, u in top.sources[:3]]
    parts.append("**관련 분석 페이지 · 출처**\n" + "\n".join(src))
    if len(hits) > 1:
        parts.append("관련 항목: " + " · ".join(f"[{e.title}]({e.links()[1]})" for _, e in hits[1:]))
    parts.append("_포트폴리오 기반 검색형 답변 · 분석 자료 원문을 그대로 보여 주며 새로운 사실을 만들지 않습니다._")
    return "\n\n".join(parts)


def _multi_md(q: str, gs: list[str]) -> str:
    """두 게임 이상 비교: 게임마다 가장 관련 높은 항목 + 문제 정의 (원문)."""
    parts = [f"#### {' vs '.join(NAMES[g] for g in gs)} 비교", "**핵심 결론** — 게임마다 불만의 대상과 원인이 다르다 · 아래는 각 게임 분석 자료 원문"]
    for g in gs:
        hits = search(q, g, k=1)
        e = hits[0][1] if hits else next(x for x in build_index() if x.game == g and x.kind == "problem")
        prob = next((x.problem for x in build_index() if x.game == g and x.kind == "problem"), "")
        body = "\n".join(f"- {x}" for x in (e.evidence[:2] + e.strategy[:1]))
        parts.append(f"**{NAMES[g]}** — {prob}\n- 관련 항목: {e.title}\n{body}\n- [{e.links()[0]}]({e.links()[1]})")
    parts.append("_포트폴리오 기반 검색형 답변 · 각 게임 분석 자료 원문 · 두 게임의 불만 규모를 수치로 비교하지 않음_")
    return "\n\n".join(parts)


def _cross_md(q: str) -> str:
    """게임 공통 질문: 게임마다 가장 관련 높은 항목 1개씩 요약 (같은 형식)."""
    kinds = detect_kinds(q) or ["problem"]
    if "priority" in kinds:     # '가장 먼저 할 일' 질문은 우선순위 항목만 본다
        kinds = ["priority"]
    ko = {"kpi": "KPI", "cause": "원인", "strategy": "개선 전략", "evidence": "근거", "plan": "실행·예산", "problem": "핵심 문제", "priority": "우선 실행안과 이유"}
    parts = [f"#### 4개 게임 비교 · {' · '.join(ko.get(k, k) for k in kinds)}"]
    for g in NAMES:
        same = [(0, e) for e in build_index() if e.game == g and e.kind == kinds[0]][:1]
        hits = same if kinds[0] in ("priority", "problem") else (search(q, g, k=1) or same)
        if not hits:
            parts.append(f"- **{NAMES[g]}** — {NOT_FOUND}")
            continue
        e = hits[0][1]
        if e.kind == "problem":
            pk = next((x.kpi for x in build_index() if x.game == g and x.kind == "priority"), e.kpi)
            first = e.strategy[:2] + ([f"KPI: {' · '.join(pk[:3])} (목표·가정)"] if pk else [])
        elif e.kind == "priority":
            first = e.strategy[:1] + [f"이유: {x}" for x in e.evidence[:1]] + ([f"KPI: {' · '.join(e.kpi[:3])}"] if e.kpi else [])
        else:
            first = (e.kpi or e.strategy or e.evidence or [""])[:3]
        body = "\n".join(f"- {x}" for x in first if x)
        parts.append(f"**{NAMES[g]} · {e.title}** — {e.summary}\n{body}\n- [{e.links()[0]}]({e.links()[1]})")
    parts.append("_검색 기반 답변 · 게임별 분석 자료의 원문을 모아 보여 줍니다._")
    return "\n\n".join(parts)


class PortfolioAssistant(PMChatbot):
    """규칙·검색 기반 어시스턴트 (생성형 AI 아님)."""

    name = "retrieval"

    def __init__(self, datalab: dict | None = None):
        self.datalab = datalab

    def reply(self, messages: list[ChatMessage], game_id: str | None = None) -> str:
        q = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return answer_md(q, game_id, self.datalab)
