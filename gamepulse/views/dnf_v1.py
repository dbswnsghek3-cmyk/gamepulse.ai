"""던전앤파이터 — 어려운 던전을 클리어했는데, 왜 성장했다는 느낌이 없을까? (사업PM 포트폴리오 · 01~06 탭)

- 01 문제 정의 (게임 소개 · 2026 시즌 상황 · 핵심 질문) · 02 유저 의견·검증 한계 · 03 원인 (현상 → 근거 → 체감 → 가설)
  · 04 개선안 (A 성장 가치 · B 지정 장비 진척 게이지 · C 다음 시즌 기대) · 05 시뮬레이터·KPI·실험 · 06 실행 로드맵·사업적 판단
- 사실·가설·시안: data/dnf/dnf.json · 계산: gamepulse/sim/dnf_sim.py (정적 페이지 JS 와 같은 난수열·같은 식)
- 근거 원본: DNF_GamePulse_OneShot/01_original_evidence (공개 금지 · .gitignore) → 공개용은 assets/dnf/evidence (아이디·아바타 블러, 문구 원문 그대로)
- 친구 카톡은 개인정보가 있어 이미지를 공개하지 않고 원문 문구만 인용 · 1명의 정성 인터뷰로만 표시
- 디자인은 FC 온라인 컴포넌트 재사용 · 표지는 던파 전용 빨간색 + 로고
"""

from __future__ import annotations

import base64
import json
from html import escape
from pathlib import Path

import streamlit as st
from PIL import Image

from gamepulse.data.overwatch_images import web_jpeg_b64
from gamepulse.sim import dnf_sim as D
from gamepulse.ui.components import html
from gamepulse.ui.gallery import gallery_html, pair_html
from gamepulse.views.fconline import conclude, lead, sol_card, tr, won
from gamepulse.views.overwatch import b_hypo, b_interp, b_mock, b_real, b_sim, badge_legend, head, link, sub, table

ROOT = Path(__file__).resolve().parents[2]
DATA, ASSETS = ROOT / "data" / "dnf", ROOT / "assets" / "dnf"
SECTIONS = [("01", "문제 정의"), ("02", "유저 의견·한계"), ("03", "원인"), ("04", "개선안"), ("05", "시뮬레이터·KPI"), ("06", "로드맵·판단")]
TAB_LABELS = [f"{n} {t}" for n, t in SECTIONS]
TAB_KEY = "df_tab"


@st.cache_data(show_spinner=False)
def load() -> dict:
    return json.loads((DATA / "dnf.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def load_voc() -> dict:
    return json.loads((DATA / "voc.json").read_text(encoding="utf-8"))


def voc_block(d: dict) -> None:
    """VOC 전수: 출처별 건수 → 범주별 건수·성향·대표 의견 → 반대 의견 → 전체 목록 (모두 voc.json 에서 계산)."""
    v = load_voc()
    items, cats, src = v["items"], v["categories"], v["sources"]
    n_yt = sum(x["src"].startswith("YT") for x in items)
    n_kk = sum(x["src"] == "KAKAO" for x in items)
    n_bd = len(items) - n_yt - n_kk
    cap = v["capture"]
    sub("④ 유저 의견 전수 · 범주별 (중복 제외 · 작성자 비공개)", b_real())
    html('<div class="df-vocsum">'
         f'<div><span>원본 캡처</span><b>{cap["original_files"]}장</b><small>VOC 캡처 {cap["voc_files"]} · 그래프 {cap["chart_files"]} (2차 자료)</small></div>'
         f'<div><span>중복 제외 유효 VOC</span><b>{len(items)}건</b><small>유튜브 댓글 {n_yt} · 공식 게시판 {n_bd} (글 {v["board"]["posts"]}개) · 지인 1명 {n_kk}</small></div>'
         f'<div><span>이전 사이트 반영</span><b>{sum(x["before"] for x in items)}건</b><small>→ 이번에 전체 {len(items)}건을 목록화 · 신규 {sum(not x["before"] for x in items)}건</small></div></div>')
    link_of = lambda x: link(src[x["src"]][1], src[x["src"]][0]) if src[x["src"]][1] else escape(src[x["src"]][0])  # noqa: E731
    order = v["core_cats"] + v["sub_cats"] + [v["positive_cat"]]
    rows = []
    for c in order:
        xs = [x for x in items if x["cat"] == c]
        st_ = " · ".join(f"{k} {sum(x['stance'] == k for x in xs)}" for k in ("부정", "질문", "제안", "중립", "긍정") if any(x["stance"] == k for x in xs))
        rep_ = next((x for x in xs if x["src"] in ("A", "B", "C", "D", "E", "F1", "F2")), xs[0] if xs else None)
        role = "핵심 → 지정 장비 진척 게이지" if c in v["core_cats"] else ("보조 분석" if c in v["sub_cats"] else "반대·긍정 의견")
        rows.append([f"<b>{escape(cats[str(c)])}</b><br><small>{role}</small>", f"<b>{len(xs)}</b>", escape(st_),
                     (f"{escape(rep_['summary'])}<br><small>{escape(rep_['date'])} · {link_of(rep_)}</small>" if rep_ else "—")])
    table(["분석 범주", "건수", "성향", "대표 의견 (요약 · 출처)"], rows)
    other = [x for x in items if x["cat"] not in order]
    st.caption(f"분석 범위 밖 {len(other)}건 (운영·디렉터·회사 평가 {sum(x['cat'] == 8 for x in other)} · 골드·경제 {sum(x['cat'] == 9 for x in other)} · "
               f"스토리·콘텐츠 방향 {sum(x['cat'] == 10 for x in other)}) · 유튜브 영상 1·3이 '던파 위기' 주제라 운영 비판이 많은 편향이 있음 · "
               "건수는 수집 표본 안의 분포일 뿐 전체 이용자 비율이 아님")
    pos = [x for x in items if x["stance"] == "긍정" or x["cat"] == v["positive_cat"]]
    html('<div class="df-pos"><b>긍정·반대 의견도 함께</b>' + "".join(
        f'<span>{escape(x["summary"])} <small>{escape(x["date"])} · {link_of(x)}</small></span>' for x in pos) + "</div>")
    with st.expander(f"자세히 보기 · VOC 전체 목록 {len(items)}건 (출처·날짜·성향·범주)"):
        table(["번호", "출처", "위치", "날짜", "성향", "범주", "요약"],
              [[x["id"], link_of(x), escape(x["where"]), escape(x["date"]), escape(x["stance"]), escape(cats[str(x["cat"])]), escape(x["summary"])] for x in items])
        st.caption(v["_note"] + " · " + cap["note"] + " · " + v["board"]["excluded"])


@st.cache_data(show_spinner=False)
def _img(rel: str, mtime: float) -> str:
    return web_jpeg_b64(str(ASSETS / rel), max_w=1400)


@st.cache_data(show_spinner=False)
def _png(rel: str, mtime: float) -> str:
    return base64.b64encode((ASSETS / rel).read_bytes()).decode()


def gallery(key: str, items: list[list[str]], folder: str = "evidence") -> None:
    slides = []
    for f, cap, credit in items:
        p = ASSETS / folder / f
        if p.is_file():
            slides.append((f'<img src="data:image/jpeg;base64,{_img(f"{folder}/{f}", p.stat().st_mtime)}" alt="{escape(cap)}" loading="lazy">', cap, credit))
    out = gallery_html(key, slides)
    if out:
        html(out)


def _tab_from_query() -> str:
    q = str(st.query_params.get("tab", ""))
    return next((lab for lab in TAB_LABELS if lab.startswith(q.zfill(2)[:2])), TAB_LABELS[0]) if q else TAB_LABELS[0]


def _sync_tab_param() -> None:
    st.query_params["page"] = "dnf"
    st.query_params["tab"] = str(st.session_state.get(TAB_KEY, TAB_LABELS[0]))[:2]


def tab_nav() -> int:
    if st.session_state.get(TAB_KEY) not in TAB_LABELS:
        st.session_state[TAB_KEY] = _tab_from_query()
    sel = st.radio("섹션 선택", TAB_LABELS, key=TAB_KEY, horizontal=True, label_visibility="collapsed", on_change=_sync_tab_param)
    return TAB_LABELS.index(sel)


def anchor(k: str) -> None:
    html(f'<div class="fc-anchor" data-k="{k}"></div>')


def vlink(d: dict, v: str, extra: str = "") -> str:
    name, _, url = d["videos"][v]
    return link(url, f"{name} ↗") + (f" · {escape(extra)}" if extra else "")


def render() -> None:
    d = load()
    cv = d["cover"]
    lp = ASSETS / cv["logo"]
    logo = (f'<img class="df-logo" src="data:image/png;base64,{_png(cv["logo"], lp.stat().st_mtime)}" alt="던전앤파이터 로고">'
            if lp.is_file() else "")
    html('<div class="gp-ow-page"></div>')
    html(f'<div class="fc-hero solo dnf"><div class="df-hero-in"><div class="fc-hero-t"><div class="k">{escape(cv["kicker"])}</div>'
         f'<div class="q" role="heading" aria-level="1">{escape(cv["title"])}<br>{escape(cv["title2"])}</div>'
         f'<div class="s">{escape(cv["subtitle"])}</div></div>{logo}</div><div class="df-credit">{escape(cv["logo_credit"])}</div></div>')
    i = tab_nav()
    badge_legend()
    html(f'<div class="ow-pane-mark" data-tab="{SECTIONS[i][0]}"></div>')
    [s1, s2, s3, s4, s5, s6][i](d)
    st.caption(f"{d['disclaimer']} · 자료 확인일 {d['checked_at']}")


# ======================================================================
def fig(im: dict, cls: str = "") -> None:
    """공식 이미지 1장을 크게 (최대 1100px) · 출처 링크."""
    p = ASSETS / im["file"]
    if not p.is_file():
        html(f'<div class="df-wait">실제 화면 확보 필요 · {link(im["url"], "공식 자료 ↗")}</div>')
        return
    html(f'<figure class="df-fig {cls}"><img src="data:image/jpeg;base64,{_img(im["file"], p.stat().st_mtime)}" alt="{escape(im["cap"])}">'
         f'<figcaption><b>{escape(im["cap"])}</b> · {link(im["url"], im["credit"] + " ↗")}</figcaption></figure>')


def s1(d: dict) -> None:
    it = d["intro"]
    fig(d["hero_img"], "hero")
    html('<div class="df-points six">' + "".join(f'<div class="{c}"><span>{escape(k)}</span><b>{escape(v)}</b></div>' for k, v, c in d["cover"]["points"]) + "</div>")
    html(f'<div class="fc-intro dnf"><b>던전앤파이터란?</b><p>{escape(it["line"])}</p></div>')
    html('<div class="fc-evs">' + "".join(
        f'<div class="fc-ev off"><span class="t">{escape(k)} · 공식·보도</span><b>{escape(v)}</b><small>{link(u, s + " ↗")}</small></div>'
        for k, v, s, u in it["season"]) + "</div>")
    html(f'<div class="fc-pm"><span>핵심 질문</span><b>{escape(it["question"])}</b></div>')
    head("문제: 클리어는 했는데 성장이 쌓이지 않는다", "세 문제 모두 가설 · 근거(2026)는 02 탭", b_hypo())
    html('<div class="fc-why">' + "".join(
        f'<div><span>{escape(k)} · {escape(n)}</span><b>{escape(p)}</b><small>{escape(s)}</small></div>' for k, n, p, s in d["problems"]) + "</div>")


def s2(d: dict) -> None:
    m = d["media"]
    head("근거 (2026): 전투 → 클리어 → 실제 보상 → 유저 의견 → 개발사 대응", "실제 플레이는 제3자 유튜브 영상 캡처·원본 링크 · 유저 주장과 공식 발표를 구분", b_real())
    sub("① 고난도 레이드 전투 → 클리어 후 보상 결과 · 실제 화면 2장 (클릭하면 크게 보기)", b_real())
    c = m["clear"]
    slides, ratios = [], []
    for f, cap, credit in m["shots"]:
        p = ASSETS / f
        if p.is_file():
            with Image.open(p) as im:
                ratios.append(im.width / im.height)
            slides.append((f'<img src="data:image/jpeg;base64,{_img(f, p.stat().st_mtime)}" alt="{escape(cap)}" loading="lazy">', cap, credit))
    html(pair_html("dfscene", slides, ratios))
    html('<div class="df-pairmsg"><b>높은 난이도의 레이드를 극복한 성취감이, 확률에 좌우되는 보상 결과에 따라 약해질 수 있다.</b>'
         '<small>전투 화면만으로 보상 불만이 입증되지는 않음 → 아래 보상 관찰·유저 의견(VOC)·개발사 대응으로 확인 (가설)</small></div>')
    html(f'<div class="df-ytcap"><b>{escape(c["title"])}</b> · 유튜브 · 2026-08-09 업로드 · 30:26 · {link(m["video_url"], "원본 영상 ↗")}'
         '<br>제3자 유저 영상의 캡처 (본인·GamePulse AI 플레이 아님) · 유튜브 재생 UI는 잘라내고 캐릭터 닉네임만 가림 · 게임 장면·보상 내용은 원본 그대로 · '
         '한 번의 클리어 영상으로 전체 유저의 경험을 단정하지 않음</div>')
    sub("② 클리어 · ③ 실제 보상 (영상 화면을 직접 확인한 내용)", b_real())
    r = d["reward_obs"]
    html('<div class="df-reward"><div class="h"><b>하드모드 정화 성공 · 클리어 타임 29분 26초</b><small>영상 29:59</small></div>'
         '<ul>' + "".join(f"<li>{escape(x)}</li>" for x in r["items"]) + f'</ul><small>{escape(r["note"])}</small>'
         f'<p>{escape(r["auction"])}</p><p class="off"><span>공식 기준</span>{escape(r["official"])}</p>'
         f'<div class="pm"><span>사업PM 해석</span>{escape(r["pm"])}</div></div>')
    with st.expander("자세히 보기 · 다른 영상·공식 프리뷰·공략 링크"):
        html('<div class="df-media">' + "".join(f'<div><span>{escape(k)}</span><b>{link(u, t + " ↗")}</b><small>{escape(n)}</small></div>' for k, t, u, n in m["links"]) + "</div>")
    voc_block(d)
    sub("핵심 원문 발췌 · 지정 장비 진척 게이지와 직접 연결되는 2026 의견", b_real())
    html(f'<div class="fc-cav">{escape(d["opinion_scope"])}</div>')
    cards = []
    for o in d["key_opinions"]:
        q = o["quotes"][0][0]
        cards.append(f'<div class="df-op {o["sol"].lower()}"><div class="h"><span class="no">{o["no"]}</span><b>{escape(o["theme"])}</b>'
                     f'<span class="to">→ 개선안 {o["sol"]}</span></div>'
                     f'<div class="sm"><span>유저 의견 요약</span>{escape(o["summary"])}</div>'
                     f'<div class="q"><q>{escape(q)}</q><small>원문 발췌 · {escape(o["date"])} · {link(o["url"], o["title"] + " ↗")}</small></div>'
                     f'<div class="ev"><span>확인된 근거</span>{escape(o["evidence"])}</div>'
                     f'<div class="pm"><span>사업PM 해석</span>{escape(o["pm"])}</div></div>')
    html('<div class="df-ops">' + "".join(cards) + "</div>")
    sub("⑤ 개발사 대응 · 공식 발표와 보도", b_real())
    html('<div class="fc-evs">' + "".join(f'<div class="fc-ev off"><span class="t">{escape(a)}</span><b>{escape(b)}</b><small>{link(u, "원문 ↗")}</small></div>'
                                          for a, b, u in d["dev_response"]) + "</div>")
    html(f'<div class="df-gapnote"><b>남은 문제</b> {escape(d["dev_gap"])} → 기존 시스템과 다른 개선안은 04 탭 · KPI는 05 탭</div>')
    conclude("유저 의견은 문제를 찾는 출발점 · 효과 판단은 로그와 실험(05 탭)으로 한다.")
    with st.expander("자세히 보기 · 보조 자료 (이전 유튜브 댓글 캡처·지인 인터뷰 · 작성 시점이 2026 근거보다 불명확) · 검증 한계"):
        gallery("dfev", d["evidence_images"])
        f = d["friend"]
        st.markdown(f"**지인 인터뷰 · {f['label']}**")
        table(["상황", "원문", "해석 (분석자)"], [[escape(a), f"<b>“{escape(b)}”</b>", escape(c)] for a, b, c in f["items"]])
        st.caption(f["note"])
        st.markdown("**보조 배경 자료 (영상 제작자 2차 자료 · 원자료 미확인)**")
        gallery("dfsec", d["secondary"])
        st.markdown("\n".join(f"- {x}" for x in d["limits"]))


def _chain(rows: list[tuple[str, str, str]]) -> None:
    """원인 → 기존 시스템의 한계 → 차별화 → 검증: 한 줄씩 (카드 나열 대신)."""
    html('<ol class="df-chain">' + "".join(f'<li><span>{escape(k)}</span><p>{escape(t)} <small>{escape(src)}</small></p></li>' for k, t, src in rows) + "</ol>")


def s3(d: dict) -> None:
    head("원인: 운이 나쁜 클리어는 '쌓이는 것'이 없고, 다음 시즌을 기다릴 이유가 약하다", "원인 → 기존 시스템의 한계 → 차별화 → 검증", b_hypo())
    lead("B", "고난도 보상과 성취감 (핵심)", "구조는 공식 사실 · 체감과 이탈은 가설")
    fig(d["reward_img"], "sm")
    _chain([("원인", "상급 던전은 주 2개 클리어 보상 · 보상은 기대 배율에 따른 확률 → 클리어해도 결과가 운에 갈린다", "공식 가이드"),
            ("기존 한계", "기대 배율은 '평균'을 올릴 뿐, 이번 클리어의 운 나쁜 결과는 보정하지 않는다 · 조율의 경계는 별도 재료가 필요", "공식 가이드 · 분석자 비교"),
            ("체감", "일반 이상 난이도는 시간 대비 보상 차이가 작다는 비판 (2026-10-21 · 유저 의견 ③)", "유저 의견 · 정성"),
            ("검증", "불운한 클리어가 반복된 계정의 다음 주 재도전율이 낮은가 → 로그로 확인 (가설)", "검증 필요")])
    lead("A", "시즌 성장 가치", "시즌제 자체가 아니라 '받은 성장의 수명'")
    fig(d["equip_img"])
    _chain([("원인", "시즌마다 최상위 장비가 바뀐다 · 유일 장비는 다음 시즌에도 위상 유지 예고", "공식 · 방송 보도"),
            ("기존 한계", "무기고·통합 변환은 장비·세트를 보존하지만, '내 시즌을 돌아보고 다음 목표를 정하는' 화면은 확인 못함", "공식 · 분석자 비교"),
            ("체감", "새 시즌도 같은 확률 파밍이 반복된다는 우려 (2026-03-12 · 유저 의견 ①)", "유저 의견 · 정성"),
            ("검증", "시즌 전환 후 복귀 계정의 D7·D30과 첫 목표 달성률 비교 (가설)", "검증 필요")])
    lead("C", "목표 획득 시점 예측", "확률 보상 구조상 '언제 얻는지'를 알 수 없음")
    _chain([("원인", "레이드·상급 던전 보상과 하드 경매가 모두 확률로 결정 (공식 공지·가이드)", "공식"),
            ("기존 한계", "특별 경매도 '등장'만 100% · 낙찰은 입찰 경쟁 · 8주 임시 조치", "공식 공지"),
            ("검증", "목표를 지정한 계정의 '목표 획득 전 이탈률'을 대조군과 비교 (가설)", "검증 필요")])
    with st.expander("자세히 보기 · 확인한 공식 자료"):
        table(["날짜", "자료", "확인한 사실"], [[escape(o["date"]), link(o["url"], o["src"]), escape(o["fact"])] for o in d["official"]], badge_html=b_real())


def s4(d: dict) -> None:
    head("개선안: 확률은 그대로, 성장과 기대는 쌓이게", "기존 공식 장치와 겹치지 않는 부분만 (기획 시안)", b_mock())
    sub("기존 장치 → 남는 문제 → 추가 제안 → 효과·부작용", b_interp())
    table(["현재 게임의 장치 (공식)", "현재 장치로 남는 문제", "GamePulse AI 추가 제안", "기대 효과 / 부작용·대응"],
          [[f"<b>{escape(a)}</b>", escape(b), f"<b>{escape(c)}</b>", escape(e)] for a, b, c, e in d["gap"]])
    html('<div class="fc-sols">' + "".join(sol_card(x, x["k"].lower()) for x in d["solutions"][:2]) + "</div>")
    html('<div class="fc-sols one">' + sol_card(d["solutions"][2], "c") + "</div>")
    sub("지정 장비 진척 게이지 · 화면 시안", b_mock())
    im = d["proposal_img"]
    pp = ASSETS / im["file"]
    if pp.is_file():
        html(f'<figure class="df-fig sm2"><img src="data:image/png;base64,{_png(im["file"], pp.stat().st_mtime)}" alt="{escape(im["cap"])}">'
             f'<figcaption><b>{escape(im["cap"])}</b> · GamePulse AI 제작</figcaption></figure>')
    sub("검토한 대안과 판단", b_interp())
    table(["판단", "대안", "이유"], [[f"<b>{escape(a)}</b>", escape(b), escape(c)] for a, b, c in d["alternatives"]])
    with st.expander("자세히 보기 · 기존 공식 장치와 중복 확인"):
        fig(d["convert_img"], "sm")
        table(["기존 장치", "하는 일", "B 지정 장비 진척 게이지와의 차이"], [[f"<b>{escape(a)}</b>", escape(b), escape(c)] for a, b, c in d["existing"]], badge_html=b_real())
    conclude("운의 재미는 남기고, 플레이한 만큼의 성취는 반드시 쌓이게 한다.")


def sim_html(r: dict, note: str) -> str:
    A, B, C = r["A"], r["B"], r["C"]

    def f(x):
        return f"{x:,.1f}"

    def row(n, a, b, c, better_low=False):
        def cell(v):
            d = v - a
            cls = "up" if (d < 0 if better_low else d > 0) else ("dn" if abs(d) > 1e-9 else "")
            return f'<td class="{cls}"><b>{f(v)}</b> <small>({d:+,.1f})</small></td>'
        return f"<tr><td>{n}</td><td>{f(a)}</td>{cell(b)}{cell(c)}</tr>"
    sup = lambda v: f'<b class="{"dn" if abs(v) > 5 else "up"}">{v:+.1f}%</b>'  # noqa: E731
    return (f'<div class="fc-demo"><h4>현행 vs B 지정 장비 진척 게이지 (제안) vs 천장 (비교) {b_sim()}</h4><div class="fc-cmp"><table>'
            '<tr><th>지표 (이용자 2,000명 · 가정)</th><th>현행</th><th>B 지정 장비 진척 게이지</th><th>천장 (비교)</th></tr>'
            + row("하위 10% 누적 보상", A["p10"], B["p10"], C["p10"]) + row("최저 누적 보상", A["min"], B["min"], C["min"])
            + row("평균 총보상", A["mean"], B["mean"], C["mean"]) + row("보상 편차 (표준편차)", A["sd"], B["sd"], C["sd"], True)
            + row("현행 평균 이상 도달 비율 (%)", r["reach_a"], r["reach_b"], r["reach_c"])
            + f'<tr><td>보상 재화 공급량 변화</td><td>—</td><td>{sup(r["supply_b"])}</td><td>{sup(r["supply_c"])}</td></tr>'
            + f'<tr><td>고배율 보상 크기 (×)</td><td>{r["mult"]:g}</td><td><b>{r["jack_b"]:.1f}</b></td><td><b>{r["jack_c"]:.1f}</b></td></tr>'
            + '</table></div>'
            f'<div class="fc-act">{_insight(r)}</div>'
            f'<div class="src">{escape(note)}</div></div>')


def _insight(r: dict) -> str:
    A, B, C = r["A"], r["B"], r["C"]
    if B["p10"] < A["p10"]:
        return "<b>B도 하위 10%가 줄어듦</b> · 이 설정은 개선안으로 쓰지 않는다"
    msg = (f"<b>B 지정 장비 진척 게이지</b> · 하위 10% {A['p10']:.1f} → {B['p10']:.1f} · 공급 {r['supply_b']:+.1f}% · 고배율 ×{r['jack_b']:.1f} "
           + ("→ 가드레일(±5%) 안에서 운이 나쁜 구간만 보완" if abs(r["supply_b"]) <= 5 else "→ 공급이 가드레일(±5%)을 넘음: K를 늘리거나 공급 중립을 켠다"))
    if abs(r["supply_c"]) > 5:
        msg += f"<br><b>천장 (반례)</b> · 공급 {r['supply_c']:+.1f}% → 재화 공급 과열"
    elif r["jack_c"] < r["mult"] * 0.8:
        msg += f"<br><b>천장 (반례)</b> · 공급을 맞추려면 고배율이 ×{r['mult']:g} → ×{r['jack_c']:.1f}로 줄어 확률 보상의 설렘이 크게 약해짐"
    return msg


def s5(d: dict) -> None:
    head("시뮬레이터·KPI: 운이 나쁜 구간이 얼마나 줄어드는지 본다", "모든 수치는 가정 · 실제 던파 확률이 아님", b_mock())
    sub("대표 KPI 4개", b_mock())
    html('<div class="df-kpi">' + "".join(f'<div><span>{escape(t)}</span><b>{escape(n)}</b><small>{escape(x)}</small></div>' for t, n, x in d["kpi_main"]) + "</div>")
    html('<div class="fc-cav">' + " · ".join(escape(x) for x in d["experiment"] if x.startswith(("성공", "롤백"))) + " (기준값은 제안 · 파일럿 전 합의)</div>")
    sub("B 지정 장비 진척 게이지 시뮬레이션 · 천장 방식과 비교", b_sim())
    c1, c2 = st.columns([1, 1.6], gap="medium")
    with c1:
        anchor("d1")
        n = st.slider("주간 클리어 누적 횟수", 10, 200, 50, 5, key="df_n")
        p = st.slider("기대 이상 결과 확률 (% · 가정)", 1, 30, 5, key="df_p")
        m = st.slider("기대 이상 결과의 보상 배율 (× · 가정)", 2, 20, 10, key="df_m")
        k = st.slider("게이지 칸 수 K: 기대 미만 클리어 K번마다 1회 하한 보장 (0 = 없음)", 0, 50, 10, 5, key="df_k")
        neutral = st.checkbox("공급 중립 (고배율 보상 크기를 줄여 평균을 현행과 같게)", False, key="df_neu")
    r = D.simulate(n, p / 100, m, k, neutral)
    with c2:
        html(sim_html(r, d["sim_note"]))
        if k:
            html(f'<div class="fc-cav"><b>예측 가능한 상한</b> 목표 1회까지 최대 <b>기대 미만 클리어 {k}번</b> (설계값 K · 공식 확률이 없어 평균 횟수는 계산하지 않음)</div>')
    st.caption(d["kpi_note"])
    with st.expander("자세히 보기 · 개선안별 전체 KPI · 실험 설계 (대조군·실험군 · 성공·롤백 기준)", expanded=False):
        table(["개선안", "KPI"], [[tr(a), escape(b)] for a, b in d["kpis"]])
        st.markdown("\n".join(f"- {x}" for x in d["experiment"]))
        st.caption("이전 버전의 '평균 공급을 맞추려고 모든 이용자 보상을 일괄 축소'하는 방식은 하위 10%를 59.0 → 56.4로 낮춰 폐기 · "
                   "공급 중립은 고배율 보상 크기만 조정하도록 바꿈")


def s6(d: dict) -> None:
    c = d["cost"]
    eff = sum(x[1] for x in c["items"])
    head(f"사업적 판단: {d['decision']}", "실제 매출·잔존 자료가 없어 효과를 확정하지 않는다", b_mock())
    sub("실행 로드맵", b_mock())
    html('<ol class="fc-order">' + "".join(f'<li class="c"><span>{escape(w)}</span><b>{escape(k)}</b><small>{escape(x)}</small></li>'
                                           for w, k, x in d["roadmap"]) + "</ol>")
    sub("대표 전략 한눈에 · B 지정 장비 진척 게이지", b_mock())
    table(["단계", "내용"], [
        ["<b>문제</b>", "어려운 던전·레이드를 클리어해도 결과가 운에 갈려 노력이 체감되지 않는다 (가설)"],
        ["<b>근거</b>", "공식: 미카엘라 하드 경매 확률 진행(7/29) · 하드 보상 부족 인정·특별 경매 임시 조치(10/27·10/29) · 유저: 2026 공식 게시판 글 ②·③"],
        ["<b>해결책</b>", "목표 1개 지정 → 기대 미만 클리어마다 진척 +1 → K칸이면 지정 목표 1회 (하한 수준) · 확률·고배율·경매 유지 · 교환 불가 · 천장·상점형은 제외"],
        ["<b>비용</b>", f"{eff:g}인월 × {c['monthly'] / 1e4:,.0f}만 원 = <b>{won(eff * c['monthly'])}</b> (전체 · 가정)"],
        ["<b>KPI</b>", "주간 고난도 재도전율 · 보상 만족도 · 하위 10% 누적 보상 · 가드레일: 재화 공급량 ±5%"],
        ["<b>실험</b>", "계정 10% 무작위 · 명성 구간 층화 · 롤백 기준 사전 합의"],
        ["<b>사업적 판단</b>", f"<b>{escape(d['decision'])}</b>"]])
    with st.expander("자세히 보기 · 예산 (인월 시나리오) · 리스크와 대응"):
        table(["항목", "공수", "금액"], [[escape(a), f"{b:g}인월", won(b * c["monthly"])] for a, b in c["items"]]
              + [["<b>합계</b>", f"<b>{eff:g}인월</b>", f"<b>{won(eff * c['monthly'])}</b>"]], badge_html=b_sim())
        table(["리스크", "대응"], [[escape(a), f"<b>{escape(b)}</b>"] for a, b in d["risks"]], badge_html=b_interp())
