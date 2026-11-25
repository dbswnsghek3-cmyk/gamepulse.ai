"""2026-11 개편 CSS (가독성 우선 · 게임별 포인트 컬러) — styles.CSS 끝에 붙는다.

공통: 배경 #FFFFFF · 본문 #1F2937 · 구분선 #E5E7EB · 차트는 기존 파랑 유지.
포인트 컬러는 제목 표식 · 섹션 번호 · 활성 탭 · 핵심 강조에만. 흰 배경 위 글자는 대비 확보용 진한 톤을 쓴다.
현재는 오버워치(#F99E1A · 글자용 #A35F00)만 적용 · 나머지 게임은 확인 후 같은 규칙으로 확장.
"""

OW_REDESIGN_CSS = """
:root { --ow-acc: #F99E1A; --ow-ink: #A35F00; --ox-text: #1F2937; --ox-line: #E5E7EB; --ox-muted: #6B7280; }
body:has(.gp-ow-page), .stApp:has(.gp-ow-page), .stApp:has(.gp-ow-page) [data-testid="stAppViewContainer"],
.stApp:has(.gp-ow-page) [data-testid="stMain"] { background: #FFFFFF !important; }
body:has(.gp-ow-page) .sx-exp, .stApp:has(.gp-ow-page) [data-testid="stExpander"] details { background: #FFFFFF !important; border-color: var(--ox-line) !important; }

/* 첫 화면: 장식 없이 질문 + 실제 화면 */
.owx-hero { background: #FFFFFF !important; border: 0 !important; border-radius: 0 !important; padding: 0.4rem 0 1.2rem !important;
  border-bottom: 1px solid var(--ox-line) !important; margin-bottom: 1rem !important; }
.owx-hero .ow-cover-t { color: var(--ow-ink) !important; font-weight: 800; letter-spacing: 0.08em; font-size: 0.9rem; }
.owx-q { color: var(--ox-text) !important; font-weight: 800 !important; }
.owx-s { color: var(--ox-muted) !important; font-size: 1.02rem !important; }
.owx-img img { box-shadow: none !important; border: 1px solid var(--ox-line); border-radius: 10px !important; }

/* 탭: 활성 탭만 포인트 컬러 */
body:has(.gp-ow-page) .ow-tabbar { display: flex !important; flex-wrap: wrap; gap: 0.4rem !important; }
body:has(.gp-ow-page) .ow-tabbar button { flex: 1 1 auto; min-height: 2.7rem !important; padding: 0.5rem 0.9rem !important; border-radius: 8px !important;
  background: #FFFFFF !important; border: 1px solid var(--ox-line) !important; color: var(--ox-text) !important; box-shadow: none !important; white-space: nowrap; }
body:has(.gp-ow-page) .ow-tabbar button b { color: var(--ow-ink) !important; }
body:has(.gp-ow-page) .ow-tabbar button[aria-selected="true"] { background: var(--ow-acc) !important; border-color: var(--ow-acc) !important; color: var(--ox-text) !important; }
body:has(.gp-ow-page) .ow-tabbar button[aria-selected="true"] b { color: var(--ox-text) !important; }
.st-key-ow_tab [data-testid="stRadioGroup"] { grid-template-columns: repeat(4, minmax(0, 1fr)) !important; gap: 0.4rem !important; }
.st-key-ow_tab label[data-testid="stRadioOption"] { min-height: 2.7rem !important; padding: 0.5rem 0.8rem !important; border-radius: 8px !important; box-shadow: none !important; }
.st-key-ow_tab label[data-testid="stRadioOption"]:has(input:checked), .st-key-ow_tab label[data-testid="stRadioOption"][data-selected] {
  background: var(--ow-acc) !important; border-color: var(--ow-acc) !important; box-shadow: none !important; }
.st-key-ow_tab label[data-testid="stRadioOption"]:has(input:checked) p { color: var(--ox-text) !important; }
body:has(.gp-ow-page) .sx-pane-h { color: var(--ox-text) !important; border: 0 !important; }

/* 섹션 제목 = 결론 한 문장 · 포인트 컬러 짧은 막대 */
.ox-h { margin: 2.6rem 0 0.9rem; }
.ox-h::before { content: ""; display: block; width: 28px; height: 4px; border-radius: 2px; background: var(--ow-acc); margin-bottom: 0.65rem; }
.ox-h h3 { display: inline; margin: 0; padding: 0; font-size: 1.42rem; line-height: 1.45; font-weight: 800; letter-spacing: -0.02em; color: var(--ox-text) !important; }
.ox-h p { margin: 0.45rem 0 0; color: var(--ox-muted); font-size: 0.94rem; line-height: 1.65; max-width: 54rem; }
.ox-k { display: inline-block; margin-left: 0.55rem; font-size: 0.76rem; font-weight: 700; color: var(--ox-muted); vertical-align: 0.15em; white-space: nowrap; letter-spacing: 0; }
.ox-k::before { content: ""; display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #9CA3AF; margin-right: 0.3rem; vertical-align: 0.12em; }
.ox-k.real::before { background: #2563EB; } .ox-k.pending::before { background: var(--ow-acc); }
.ox-legend { font-size: 0.8rem; color: var(--ox-muted); margin: 0.3rem 0 0.6rem; } .ox-legend b { color: var(--ox-text); }

/* 01 핵심 요약 */
.ox-path { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border-top: 1px solid var(--ox-line); border-bottom: 1px solid var(--ox-line); margin: 0 0 1.8rem; }
.ox-path > div { padding: 1.1rem 1rem; border-left: 1px solid var(--ox-line); display: flex; flex-direction: column; gap: 0.35rem; }
.ox-path > div:first-child { border-left: 0; padding-left: 0; }
.ox-path span { font-size: 0.76rem; font-weight: 800; color: var(--ow-ink); letter-spacing: 0.04em; }
.ox-path b { font-size: 1.04rem; line-height: 1.45; color: var(--ox-text); }
.ox-path small { font-size: 0.84rem; color: var(--ox-muted); line-height: 1.5; }
.ox-path em, .ox-stats em, .ox-demo-h em { font-style: normal; color: var(--ow-ink); font-weight: 800; }
.ox-sumt > div { display: grid; grid-template-columns: 8.5rem minmax(0, 1fr); gap: 1rem; padding: 0.72rem 0; border-bottom: 1px solid var(--ox-line); }
.ox-sumt span { font-size: 0.86rem; font-weight: 700; color: var(--ox-muted); }
.ox-sumt p { margin: 0; font-size: 0.97rem; line-height: 1.55; color: var(--ox-text); }

/* 대표 숫자 */
.ox-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr)); gap: 1.4rem; margin: 0.3rem 0 1.4rem; }
.ox-stats > div { display: flex; flex-direction: column; gap: 0.15rem; }
.ox-stats b { font-size: 1.75rem; font-weight: 800; letter-spacing: -0.02em; color: var(--ox-text); line-height: 1.2; }
.ox-stats span { font-size: 0.9rem; color: var(--ox-text); } .ox-stats small { font-size: 0.76rem; color: var(--ox-muted); }

/* 02 원인 흐름 */
.ox-cause { display: flex; align-items: center; gap: 0.45rem; flex-wrap: wrap; margin: 0.2rem 0 0.6rem; }
.ox-cause > div { flex: 1 1 9rem; border: 1px solid var(--ox-line); border-radius: 10px; padding: 0.65rem 0.8rem; display: flex; flex-direction: column; gap: 0.15rem; }
.ox-cause > div.real { border-color: #BFDBFE; } .ox-cause small { font-size: 0.74rem; color: var(--ox-muted); font-weight: 700; }
.ox-cause b { font-size: 0.98rem; color: var(--ox-text); } .ox-cause > i { font-style: normal; color: var(--ow-acc); font-weight: 900; }

/* 03 전략 3개 · 데모 머리말 */
.ox-strats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.4rem; margin: 0.2rem 0 1.6rem; }
.ox-strats > div { display: flex; flex-direction: column; gap: 0.25rem; }
.ox-strats em { font-style: normal; font-size: 1.6rem; font-weight: 900; color: var(--ow-acc); line-height: 1; }
.ox-strats b { font-size: 1.08rem; color: var(--ox-text); } .ox-strats p { margin: 0; font-size: 0.95rem; color: var(--ox-text); line-height: 1.5; }
.ox-strats small { font-size: 0.8rem; color: var(--ox-muted); }
.ox-demo-h { margin: 0.8rem 0 0.9rem; } .ox-demo-h b { display: block; font-size: 1.1rem; color: var(--ox-text); margin-bottom: 0.2rem; }
.ox-demo-h span { font-size: 0.92rem; color: var(--ox-muted); line-height: 1.55; }

/* 04 BM */
.ox-pend { display: inline-block; font-size: 0.76rem; font-weight: 700; color: #92400E; background: #FEF3C7; border-radius: 4px; padding: 1px 7px; }
.ox-lv { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 0.6rem; margin: 0.6rem 0 0.3rem; }
.ox-lv > div { border-top: 4px solid rgba(249, 158, 26, calc(0.25 + var(--i) * 0.1875)); padding: 0.7rem 0.1rem 0; display: flex; flex-direction: column; gap: 0.2rem; }
.ox-lv em { font-style: normal; font-size: 0.82rem; font-weight: 800; color: var(--ow-ink); }
.ox-lv b { font-size: 0.98rem; color: var(--ox-text); line-height: 1.4; } .ox-lv small { font-size: 0.82rem; color: var(--ox-muted); }
.ox-rules { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: 1.4rem; margin: 1.1rem 0; }
.ox-rules b { display: block; font-size: 0.86rem; font-weight: 800; color: var(--ow-ink); margin-bottom: 0.3rem; }
.ox-rules ul { margin: 0; padding-left: 1.05rem; } .ox-rules li { font-size: 0.93rem; color: var(--ox-text); line-height: 1.55; margin-bottom: 0.2rem; }
.ox-purpose { border-left: 3px solid var(--ow-acc); padding: 0.55rem 0 0.55rem 1rem; margin: 1.3rem 0; font-size: 0.97rem; line-height: 1.6; color: var(--ox-text); }
.ox-purpose > span:first-child { display: block; font-size: 0.76rem; font-weight: 800; color: var(--ow-ink); margin-bottom: 0.15rem; }

/* 05 광고 카드 */
.ox-ad { position: relative; background: var(--bg); border-radius: 14px; aspect-ratio: 16 / 9; max-width: 720px; margin: 0.4rem 0 1.4rem;
  display: flex; align-items: center; justify-content: center; overflow: hidden; }
.ox-ad-top { position: absolute; top: 7%; left: 0; right: 0; text-align: center; }
.ox-ad-top img { height: clamp(22px, 5vw, 40px); width: auto; }
.ox-ad-logo { color: #FFFFFF; font-weight: 800; letter-spacing: 0.32em; font-size: clamp(0.7rem, 1.8vw, 0.95rem); opacity: 0.92; }
.ox-ad-main { color: var(--main); font-size: clamp(2.6rem, 10vw, 5.6rem); font-weight: 900; letter-spacing: -0.02em; line-height: 1; }
.ox-ad-sub { position: absolute; bottom: 8%; left: 0; right: 0; text-align: center; color: var(--sub); font-size: clamp(0.8rem, 2.2vw, 1.05rem); font-weight: 600; letter-spacing: 0.12em; }
.ox-dirs { display: grid; grid-template-columns: repeat(auto-fit, minmax(10.5rem, 1fr)); gap: 1.1rem; margin: 0.3rem 0 0.6rem; }
.ox-dirs > div { display: flex; flex-direction: column; gap: 0.15rem; } .ox-dirs b { font-size: 0.98rem; color: var(--ox-text); }
.ox-dirs span { font-size: 0.86rem; color: var(--ox-muted); line-height: 1.5; }
.ox-flow { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; margin: 0.2rem 0 0.6rem; }
.ox-flow span { padding: 0.42rem 0.75rem; border: 1px solid var(--ox-line); border-radius: 999px; font-size: 0.9rem; color: var(--ox-text); background: #FFFFFF; }
.ox-flow i { font-style: normal; color: var(--ow-acc); font-weight: 900; }
.ox-flow.loop span:last-of-type { border-color: var(--ow-acc); font-weight: 700; }
.ox-flow.loop::after { content: "↺ 다시 노출"; font-size: 0.8rem; color: var(--ow-ink); font-weight: 700; margin-left: 0.2rem; }

/* 06 사업 효과 표 · 07 일정 */
.ox-biz td:not(:first-child), .ox-biz th:not(:first-child) { text-align: right; white-space: nowrap; }
.ox-gantt > div { display: grid; grid-template-columns: 4.5rem 6rem minmax(0, 1fr); gap: 1rem; padding: 0.68rem 0; border-bottom: 1px solid var(--ox-line); align-items: baseline; }
.ox-gantt > div:first-child { border-top: 1px solid var(--ox-line); }
.ox-gantt em { font-style: normal; font-weight: 800; color: var(--ow-ink); font-size: 0.86rem; }
.ox-gantt b { font-size: 0.93rem; color: var(--ox-text); } .ox-gantt span { font-size: 0.95rem; color: var(--ox-text); line-height: 1.5; }
.ox-credits { margin: 2rem 0 0; font-size: 0.8rem; color: var(--ox-muted); }
.ox-credits summary { cursor: pointer; } .ox-credits ul { margin: 0.4rem 0 0; padding-left: 1.1rem; }
body:has(.gp-ow-page) .ow-conclusion { background: #FFFFFF !important; border: 0 !important; border-left: 3px solid var(--ow-acc) !important;
  border-radius: 0 !important; color: var(--ox-text) !important; box-shadow: none !important; }

@media (max-width: 760px) {
  .ox-h { margin-top: 2rem; } .ox-h h3 { font-size: 1.22rem; }
  .ox-path { grid-template-columns: 1fr; } .ox-path > div { border-left: 0; padding: 0.85rem 0; border-top: 1px solid var(--ox-line); }
  .ox-path > div:first-child { border-top: 0; }
  .ox-sumt > div { grid-template-columns: 1fr; gap: 0.15rem; }
  .ox-strats { grid-template-columns: 1fr; gap: 1rem; }
  .ox-lv { grid-template-columns: 1fr; gap: 0; }
  .ox-lv > div { border-top: 0; border-left: 4px solid rgba(249, 158, 26, calc(0.25 + var(--i) * 0.1875)); padding: 0.5rem 0 0.5rem 0.8rem; }
  .ox-gantt > div { grid-template-columns: 4rem minmax(0, 1fr); } .ox-gantt span { grid-column: 1 / -1; }
  .ox-stats b { font-size: 1.45rem; }
  body:has(.gp-ow-page) .ow-tabbar { flex-wrap: nowrap !important; overflow-x: auto; -webkit-overflow-scrolling: touch; padding-bottom: 0.2rem; }
  body:has(.gp-ow-page) .ow-tabbar button { flex: 0 0 auto; }
  .st-key-ow_tab [data-testid="stRadioGroup"] { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }
}
"""
