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
:root:has(.gp-ow-page) .owx-hero { background: #FFFFFF !important; border: 0 !important; border-radius: 0 !important; padding: 0.4rem 0 1.2rem !important;
  border-bottom: 1px solid var(--ox-line) !important; margin-bottom: 1rem !important; }
:root:has(.gp-ow-page) .owx-hero .ow-cover-t { color: var(--ow-ink) !important; font-weight: 800; letter-spacing: 0.08em; font-size: 0.9rem; }
:root:has(.gp-ow-page) .owx-q { color: var(--ox-text) !important; font-weight: 800 !important; }
:root:has(.gp-ow-page) .owx-s { color: var(--ox-muted) !important; font-size: 1.02rem !important; }
:root:has(.gp-ow-page) .owx-img img { box-shadow: none !important; border: 1px solid var(--ox-line); border-radius: 10px !important; }

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

# 2차: 위계·여백 · 성장형 스킨 데모 · 광고 카드 · 퍼널 · KPI 3단 · 사업 효과 시뮬레이터
OW_REDESIGN_CSS += """
/* 다른 게임용 포인트 컬러 토큰 (적용은 각 게임 확인 후) */
:root { --fc-acc: #00C853; --fc-ink: #007A33; --pg-acc: #243B64; --pg-ink: #243B64; --df-acc: #B51D25; --df-ink: #B51D25; }

/* 위계: 본문 섹션은 넓은 여백, 상세 보기는 가볍게 */
.ox-h { margin: 3.4rem 0 1rem !important; }
.ow-pane > .ox-h:first-of-type, .sx-pane-h + .ox-h { margin-top: 1.6rem !important; }
body:has(.gp-ow-page) .sx-exp, .stApp:has(.gp-ow-page) [data-testid="stExpander"] details {
  border: 0 !important; border-top: 1px solid var(--ox-line) !important; border-radius: 0 !important; box-shadow: none !important; margin: 0 !important; }
body:has(.gp-ow-page) .sx-exp > summary, .stApp:has(.gp-ow-page) [data-testid="stExpander"] summary {
  font-size: 0.88rem !important; font-weight: 600 !important; color: var(--ox-muted) !important; padding: 0.7rem 0 !important; }
body:has(.gp-ow-page) .sx-exp > summary .sx-more { background: none !important; color: var(--ow-ink) !important; padding: 0 !important; }
body:has(.gp-ow-page) .sx-exp[open] > summary { color: var(--ox-text) !important; }
.ox-legend { margin-bottom: 0 !important; }

/* 이미지 자리 (사용자 전달 이미지) */
.ox-slots { display: grid; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr)); gap: 0.8rem; margin: 1rem 0 0.4rem; }
.ox-slot { aspect-ratio: 16 / 9; border: 1.5px dashed #D1D5DB; border-radius: 10px; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 0.25rem; text-align: center; padding: 0.6rem; color: var(--ox-muted); background: #FFFFFF; }
.ox-slot b { font-size: 0.9rem; color: var(--ox-text); } .ox-slot small { font-size: 0.72rem; word-break: break-all; }
.ox-img { margin: 0; } .ox-img img { width: 100%; height: auto; display: block; border-radius: 10px; border: 1px solid var(--ox-line); }
.ox-img figcaption { font-size: 0.78rem; color: var(--ox-muted); margin-top: 0.3rem; }

/* 성장형 스킨 데모 */
.ox-ctl { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 0.4rem 1rem; align-items: center; margin: 0.4rem 0 1rem; }
.ox-ctl label { grid-column: 1 / -1; font-size: 0.9rem; color: var(--ox-text); font-weight: 600; }
.ox-ctl output { font-weight: 800; color: var(--ow-ink); margin-left: 0.3rem; }
.ox-ctl input[type=range] { width: 100%; accent-color: var(--ow-acc); }
.ox-btn { font: inherit; font-size: 0.88rem; font-weight: 700; padding: 0.45rem 0.95rem; border-radius: 8px; border: 1px solid var(--ox-line);
  background: #FFFFFF; color: var(--ox-text); cursor: pointer; }
.ox-btn:hover { border-color: var(--ow-acc); }
.ox-skin-top { display: grid; grid-template-columns: minmax(0, 20rem) minmax(0, 1fr); gap: 1.4rem; align-items: center; }
.ox-skin-now span { font-size: 0.78rem; font-weight: 800; color: var(--ox-muted); }
.ox-skin-now strong { display: block; font-size: 2.6rem; font-weight: 900; color: var(--ox-text); line-height: 1.1; letter-spacing: -0.02em; }
.ox-skin-now > b { display: block; font-size: 1.1rem; color: var(--ox-text); margin-top: 0.15rem; }
.ox-skin-now p { margin: 0.5rem 0 0.6rem; font-size: 0.95rem; color: var(--ox-text); } .ox-skin-now p b { color: var(--ow-ink); }
.ox-skin-now small { font-size: 0.8rem; color: var(--ox-muted); }
.ox-bar { height: 10px; background: #F3F4F6; border-radius: 999px; overflow: hidden; margin-bottom: 0.3rem; }
.ox-bar i { display: block; height: 100%; background: var(--ow-acc); border-radius: 999px; transition: width 0.2s; }
.ox-lvl { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 0.5rem; margin: 1.4rem 0 0.4rem; }
.ox-lvl > div { border-top: 4px solid #E5E7EB; padding: 0.65rem 0 0; display: flex; flex-direction: column; gap: 0.15rem; opacity: 0.55; }
.ox-lvl > div.on { border-top-color: var(--ow-acc); opacity: 1; }
.ox-lvl > div.cur b { color: var(--ow-ink); }
.ox-lvl em { font-style: normal; font-size: 0.8rem; font-weight: 800; color: var(--ox-text); }
.ox-lvl b { font-size: 0.94rem; color: var(--ox-text); line-height: 1.4; } .ox-lvl small { font-size: 0.78rem; color: var(--ox-muted); }
.ox-protect { columns: 2; column-gap: 2rem; margin: 0.2rem 0 0; padding-left: 1.1rem; }
.ox-protect li { font-size: 0.95rem; color: var(--ox-text); line-height: 1.55; margin-bottom: 0.35rem; break-inside: avoid; }

/* 광고 카드: 16:9 고정 · 글자 크기도 카드 너비에 비례 */
.ox-ad { container-type: inline-size; position: relative; background: var(--bg); border-radius: 12px; aspect-ratio: 16 / 9; width: 100%;
  max-width: 760px; margin: 0.4rem 0 2rem; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.ox-ad-top { position: absolute; top: 8%; left: 0; right: 0; display: flex; justify-content: center; }
.ox-ad-top img { height: 9cqw; max-height: 64px; width: auto; }
.ox-ad-slot { font-size: 2.2cqw; color: #9CA3AF; border: 1px dashed #4B5563; border-radius: 6px; padding: 0.6cqw 2cqw; }
.ox-ad-c { text-align: center; margin-top: 4cqw; }
.ox-ad-main { color: var(--main); font-size: 15.5cqw; font-weight: 900; font-style: italic; letter-spacing: -0.03em; line-height: 1; }
.ox-ad-sub { position: static !important; color: var(--sub); font-size: 4.6cqw; font-weight: 700; letter-spacing: 0.02em; margin-top: 2.2cqw; }

/* 퍼널: 단계가 좁아지는 막대 (전환율은 표시하지 않음) */
.ox-funnel { list-style: none; padding: 0; margin: 0.4rem 0 0.5rem; display: flex; flex-direction: column; gap: 0.3rem; max-width: 640px; }
.ox-funnel li { width: var(--w); min-width: 13rem; display: flex; align-items: center; gap: 0.7rem; padding: 0.5rem 0.9rem; border-radius: 6px;
  background: #FEF3E2; color: var(--ox-text); }
.ox-funnel li:nth-child(n+4) { background: #FDE7C4; } .ox-funnel li:last-child { background: var(--ow-acc); }
.ox-funnel span { font-size: 0.78rem; font-weight: 800; color: var(--ow-ink); width: 1.1rem; } .ox-funnel li:last-child span { color: var(--ox-text); }
.ox-funnel b { font-size: 0.95rem; }
.ox-funnel-loop { font-size: 0.86rem; font-weight: 700; color: var(--ow-ink); margin: 0.2rem 0 0.3rem; }

/* KPI 3단 */
.ox-kpi3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.6rem; }
.ox-kpi3 > div { border-top: 3px solid var(--ox-line); padding-top: 0.7rem; }
.ox-kpi3 > div.g0 { border-top-color: var(--ow-acc); } .ox-kpi3 > div.g2 { border-top-color: #9CA3AF; }
.ox-kpi3 b { display: block; font-size: 0.95rem; color: var(--ox-text); margin-bottom: 0.35rem; }
.ox-kpi3 ul { margin: 0; padding-left: 1.05rem; } .ox-kpi3 li { font-size: 0.93rem; color: var(--ox-text); line-height: 1.6; }

/* 사업 효과 시뮬레이터 */
.ox-res { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0; border-top: 1px solid var(--ox-line); border-bottom: 1px solid var(--ox-line); margin: 0.4rem 0 0.9rem; }
.ox-res > div { padding: 1rem 1rem 1rem 0; display: flex; flex-direction: column; gap: 0.2rem; }
.ox-res > div + div { padding-left: 1rem; border-left: 1px solid var(--ox-line); }
.ox-res span { font-size: 0.8rem; font-weight: 700; color: var(--ox-muted); }
.ox-res b { font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em; color: var(--ox-text); line-height: 1.2; }
.ox-res .neg b { color: #DC2626; } .ox-res .pos b { color: #2563EB; }
.ox-res small { font-size: 0.78rem; color: var(--ox-muted); line-height: 1.45; }
.ox-verdict { border-left: 3px solid #DC2626; padding: 0.5rem 0 0.5rem 0.9rem; margin: 0 0 1.2rem; font-size: 1rem; color: var(--ox-text); }
.ox-verdict.near { border-left-color: var(--ow-acc); } .ox-verdict.profit { border-left-color: #2563EB; }
.ox-verdict small { display: block; font-size: 0.82rem; color: var(--ox-muted); margin-top: 0.2rem; }
.ox-presets { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0 0 0.9rem; }
.ox-fields { display: grid; grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr)); gap: 0.8rem 1rem; margin: 0 0 0.9rem; }
.ox-fields.basic { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.ox-f { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.85rem; color: var(--ox-text); font-weight: 600; }
.ox-f small { color: var(--ox-muted); font-weight: 500; }
.ox-f input { font: inherit; font-size: 0.95rem; font-weight: 500; padding: 0.45rem 0.6rem; border: 1px solid #D1D5DB; border-radius: 8px; width: 100%; box-sizing: border-box; }
.ox-f input:focus { outline: 2px solid var(--ow-acc); outline-offset: 0; border-color: var(--ow-acc); }
.ox-chart { margin: 1.2rem 0 0.4rem; min-width: 0; overflow: hidden; } .ox-chart .sx-chart-c { width: 100%; } .ox-chart2 { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1.2rem; }
.ox-note { font-size: 0.8rem; color: var(--ox-muted); margin: 0.5rem 0 0; }
.ox-adv { margin-bottom: 0.4rem !important; }

@media (max-width: 760px) {
  .ox-skin-top { grid-template-columns: 1fr; }
  .ox-lvl { grid-template-columns: 1fr; gap: 0; } .ox-lvl > div { border-top: 0; border-left: 4px solid #E5E7EB; padding: 0.45rem 0 0.45rem 0.75rem; }
  .ox-lvl > div.on { border-left-color: var(--ow-acc); }
  .ox-protect { columns: 1; }
  .ox-kpi3 { grid-template-columns: 1fr; gap: 1rem; }
  .ox-res { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .ox-res > div { padding: 0.8rem 0.6rem 0.8rem 0; } .ox-res > div + div { padding-left: 0.6rem; }
  .ox-res > div:nth-child(3) { border-left: 0; padding-left: 0; border-top: 1px solid var(--ox-line); } .ox-res > div:nth-child(4) { border-top: 1px solid var(--ox-line); }
  .ox-res b { font-size: 1.25rem; }
  .ox-fields.basic { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .ox-chart2 { grid-template-columns: 1fr; }
  .ox-funnel li { min-width: 0; width: max(var(--w), 64%); box-sizing: border-box; }
}
"""

OW_REDESIGN_CSS += """
.ox-slot.skin, .ox-img.skin { aspect-ratio: 4 / 3; max-height: 15rem; }
.ox-slots .ox-slot { aspect-ratio: 16 / 10; }
"""

# 3차 (최종): 섹션 번호 · 이미지 확대 · 좌우 비교 · 신규 BM 블록 · 여백 정리
OW_REDESIGN_CSS += """
.ox-h { margin: 2.6rem 0 0.8rem !important; }
.ox-h.n::before { display: none; }
.ox-secn { font-size: 0.82rem; font-weight: 700; color: var(--ox-muted); margin-bottom: 0.35rem; letter-spacing: 0.01em; }
.ox-secn b { color: var(--ow-ink); font-weight: 900; margin-right: 0.45rem; font-size: 0.95rem; }
.ox-cover { display: flex !important; align-items: center; gap: 1.6rem; }
.owx-logo { width: 112px; height: auto; flex: 0 0 auto; }
.ox-tracks { display: flex; flex-wrap: wrap; gap: 0.4rem 1.2rem; margin-top: 0.6rem; font-size: 0.95rem; color: var(--ox-text); }
.ox-tracks b { color: var(--ow-ink); margin-right: 0.4rem; }
.ox-fig { margin: 0.4rem 0 0.6rem; min-width: 0; }
.ox-fig img { width: 100%; height: auto; display: block; border-radius: 8px; border: 1px solid var(--ox-line); }
.ox-fig figcaption { font-size: 0.8rem; color: var(--ox-muted); margin-top: 0.35rem; line-height: 1.45; }
.ox-fig figcaption b { font-weight: 800; margin-right: 0.4rem; color: #2563EB; }
.ox-fig.plan figcaption b { color: var(--ow-ink); }
.ox-zoom > summary { list-style: none; cursor: zoom-in; display: block; }
.ox-zoom > summary::-webkit-details-marker { display: none; } .ox-zoom > summary::marker { content: ""; }
.ox-zoom[open] > summary { position: fixed; inset: 0; z-index: 100000; background: rgba(17, 24, 39, 0.92); display: flex;
  align-items: center; justify-content: center; cursor: zoom-out; padding: 2vh 2vw; }
.ox-zoom[open] > summary img { width: auto; max-width: 96vw; max-height: 94vh; border: 0; border-radius: 4px; }
.ox-pair { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 0.9rem; }
.ox-facts { margin: 0.3rem 0 0.4rem; padding-left: 1.1rem; }
.ox-facts li { font-size: 0.94rem; color: var(--ox-text); line-height: 1.6; margin-bottom: 0.15rem; }
.ox-prob { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1.6rem; }
.ox-prob > div { border-top: 3px solid var(--ow-acc); padding-top: 0.7rem; }
.ox-prob > div > span { display: block; font-size: 1rem; font-weight: 800; color: var(--ox-text); margin-bottom: 0.3rem; }
.ox-prob small { display: block; font-size: 0.82rem; color: var(--ox-muted); line-height: 1.5; }
.ox-bm { max-width: 900px; }
.ox-cols3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.4rem; margin: 0.6rem 0 0.4rem; }
.ox-cols3 > div > b { display: block; font-size: 0.9rem; font-weight: 800; color: var(--ow-ink); margin-bottom: 0.3rem; }
.ox-cols3 ul, .ox-cols3 ol { margin: 0; padding-left: 1.1rem; } .ox-cols3 li { font-size: 0.93rem; color: var(--ox-text); line-height: 1.6; }
.ox-cols3 em { font-style: normal; font-weight: 800; margin-right: 0.3rem; }
.ox-ins { margin: 0.2rem 0 1rem; padding-left: 1.3rem; } .ox-ins li { font-size: 0.97rem; color: var(--ox-text); line-height: 1.65; margin-bottom: 0.5rem; }
.ox-fields.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.ox-strat6 td { font-size: 0.88rem; vertical-align: top; } .ox-strat6 td:first-child { white-space: nowrap; }
@media (max-width: 760px) {
  .ox-cover { flex-direction: column; align-items: flex-start; gap: 0.8rem; } .owx-logo { width: 72px; }
  .ox-pair, .ox-prob, .ox-cols3 { grid-template-columns: 1fr; }
  .ox-fields.three { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .ox-strat6 td:first-child { white-space: normal; }
}
"""

# 4차: RE:START 흐름도 · 번호 상자 화면 확대
OW_REDESIGN_CSS += """
.ox-route { display: grid; grid-template-columns: minmax(0, 0.8fr) auto minmax(0, 1.2fr) auto minmax(0, 1fr); grid-template-rows: auto auto;
  gap: 0.4rem 0.6rem; align-items: center; margin: 0.4rem 0 1.4rem; }
.ox-route > div { border: 1px solid var(--ox-line); border-radius: 10px; padding: 0.7rem 0.85rem; display: flex; flex-direction: column; gap: 0.1rem; background: #FFFFFF; }
.ox-route > div:first-child { grid-row: 1 / 3; } .ox-route > i:nth-of-type(1) { grid-row: 1 / 3; } .ox-route > i:nth-of-type(2) { grid-row: 1 / 3; grid-column: 4; }
.ox-route > div.r { grid-column: 3; grid-row: 1; border-color: var(--ow-acc); } .ox-route > div.n { grid-column: 3; grid-row: 2; border-color: var(--ow-acc); }
.ox-route > div:last-child { grid-column: 5; grid-row: 1 / 3; }
.ox-route span { font-size: 0.76rem; font-weight: 800; color: var(--ox-muted); } .ox-route b { font-size: 1.02rem; color: var(--ox-text); }
.ox-route small { font-size: 0.82rem; color: var(--ox-muted); } .ox-route > i { font-style: normal; font-weight: 900; color: var(--ow-acc); font-size: 1.2rem; }
.ox-roster .ox-zoom > summary { cursor: zoom-in; }
.ox-zoom[open] .ow-mark { display: none; }
.ox-zoom[open] .ow-shot-img { background: transparent; line-height: normal; }
.ox-roster figcaption { padding: 0.5rem 0.8rem; font-size: 0.85rem; color: #E2E8F0; }
@media (max-width: 760px) {
  .ox-route { grid-template-columns: 1fr; grid-template-rows: none; }
  .ox-route > div, .ox-route > div.r, .ox-route > div.n, .ox-route > div:first-child, .ox-route > div:last-child { grid-column: auto; grid-row: auto; }
  .ox-route > i, .ox-route > i:nth-of-type(1), .ox-route > i:nth-of-type(2) { grid-column: auto; grid-row: auto; transform: rotate(90deg); justify-self: center; }
}
"""

# 5차: 손익 표시는 경고색 없이 (음수도 본문색)
OW_REDESIGN_CSS += """
.ox-res .neg b { color: var(--ox-text) !important; }
.ox-verdict, .ox-verdict.loss { border-left-color: #9CA3AF; }
.ox-verdict.near, .ox-verdict.profit { border-left-color: var(--ow-acc); }
"""

# 6차: 개선 효과 시뮬레이터 · 마케팅 전략 표
OW_REDESIGN_CSS += """
.ox-imp-r { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr) minmax(0, 1fr); gap: 0.6rem 1rem; align-items: end;
  padding: 0.6rem 0; border-top: 1px solid var(--ox-line); }
.ox-imp-r > div b { display: block; font-size: 0.92rem; color: var(--ox-text); } .ox-imp-r > div small { font-size: 0.78rem; color: var(--ox-muted); }
.ox-res .acc b { color: var(--ow-ink) !important; }
.ox-mops td { font-size: 0.9rem; vertical-align: top; } .ox-mops td:first-child { white-space: nowrap; }
@media (max-width: 760px) { .ox-imp-r { grid-template-columns: 1fr 1fr; } .ox-imp-r > div:first-child { grid-column: 1 / -1; } .ox-mops td:first-child { white-space: normal; } }
"""

OW_REDESIGN_CSS += """
.ox-res .pos b { color: var(--ow-ink) !important; }
"""

# 7차: 최종 판단표 · BM 로드맵 · 전략 카드 대상 줄
OW_REDESIGN_CSS += """
.ox-strats > div > small:first-of-type { color: var(--ow-ink); font-weight: 700; }
.ox-final td { font-size: 0.88rem; vertical-align: top; } .ox-final td:first-child { white-space: nowrap; }
.ox-road { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; margin: 0.4rem 0 1rem; }
.ox-road > div { border-top: 3px solid var(--ow-acc); padding-top: 0.6rem; display: flex; flex-direction: column; gap: 0.2rem; }
.ox-road em { font-style: normal; font-size: 1.5rem; font-weight: 900; color: var(--ow-acc); line-height: 1; }
.ox-road b { font-size: 1rem; color: var(--ox-text); } .ox-road > div > small { font-size: 0.82rem; color: var(--ox-muted); }
.ox-road ol { margin: 0.3rem 0; padding-left: 1.1rem; } .ox-road li { font-size: 0.9rem; color: var(--ox-text); line-height: 1.55; }
.ox-road p { margin: 0.2rem 0 0; font-size: 0.85rem; color: var(--ox-text); line-height: 1.5; }
.ox-road p span { display: block; font-size: 0.75rem; font-weight: 800; color: var(--ow-ink); }
@media (max-width: 760px) { .ox-road { grid-template-columns: 1fr; } .ox-final td:first-child { white-space: normal; } }
"""

# 8차: 정적 사이트 위젯 (선택·페이지·토글·하위 탭)
OW_REDESIGN_CSS += """
.ox-f select, .ox-search input { font: inherit; font-size: 0.95rem; padding: 0.45rem 0.6rem; border: 1px solid #D1D5DB; border-radius: 8px; width: 100%; box-sizing: border-box; background: #FFFFFF; }
.ox-f select:focus, .ox-search input:focus { outline: 2px solid var(--ow-acc); border-color: var(--ow-acc); }
.ox-fields.two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.ox-pager { display: flex; align-items: center; gap: 0.5rem; } .ox-pager b { font-size: 0.9rem; color: var(--ox-text); min-width: 6rem; text-align: center; }
.ox-btn:disabled { opacity: 0.45; cursor: default; }
.ox-btn.pri { background: var(--ow-acc); border-color: var(--ow-acc); color: var(--ox-text); }
.ox-btns { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.6rem 0; }
.ox-pills { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.ox-pill { font: inherit; font-size: 0.86rem; padding: 0.35rem 0.75rem; border-radius: 999px; border: 1px solid var(--ox-line); background: #FFFFFF; color: var(--ox-text); cursor: pointer; }
.ox-pill.on { background: var(--ow-acc); border-color: var(--ow-acc); font-weight: 700; }
.ox-toggle { display: inline-flex; align-items: center; gap: 0.35rem; font-size: 0.88rem; color: var(--ox-text); cursor: pointer; }
.ox-toggle input { accent-color: var(--ow-acc); width: 1rem; height: 1rem; }
.ox-search { margin: 1rem 0 0.3rem; }
.ox-scroll { max-height: 26rem; overflow: auto; }
body:has(.gp-ow-page) .ow-pane .sx-tabnav a { cursor: pointer; color: var(--ox-text); background: #FFFFFF; border: 1px solid var(--ox-line); padding: 0.35rem 0.8rem; font-weight: 600; }
body:has(.gp-ow-page) .ow-pane .sx-tabnav a.on { background: var(--ow-acc); border-color: var(--ow-acc); color: var(--ox-text); }
body:has(.gp-ow-page) .ow-pane .sx-tab-h { display: none; }
@media (max-width: 760px) { .ox-fields.two { grid-template-columns: 1fr; } }
"""

# 9차: 06 전략 카드
OW_REDESIGN_CSS += """
.ox-mcards { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.8rem 1.2rem; margin: 0.4rem 0 0.8rem; }
.ox-mcards > div { border-top: 3px solid var(--ow-acc); padding-top: 0.55rem; display: flex; flex-direction: column; gap: 0.15rem; }
.ox-mcards b { font-size: 0.98rem; color: var(--ox-text); } .ox-mcards span { font-size: 0.88rem; color: var(--ox-text); }
.ox-mcards em { font-style: normal; font-weight: 800; color: var(--ow-ink); } .ox-mcards small { font-size: 0.78rem; color: var(--ox-muted); }
@media (max-width: 760px) { .ox-mcards { grid-template-columns: 1fr; } }
"""


# 10차: FC 온라인 개편 (오버워치와 같은 레이아웃 · 테마 #16A34A · 글자 #15803D) — FC 페이지에만 적용
OW_REDESIGN_CSS += """
:root:has(.gp-fc-page) { --ow-acc: #16A34A; --ow-ink: #15803D; }
.st-key-fc_tab [data-testid="stRadioGroup"] { grid-template-columns: repeat(4, minmax(0, 1fr)) !important; gap: 0.4rem !important; }
.st-key-fc_tab label[data-testid="stRadioOption"] { min-height: 2.7rem !important; padding: 0.5rem 0.8rem !important; border-radius: 8px !important; box-shadow: none !important;
  background: #FFFFFF !important; border: 1px solid var(--ox-line) !important; }
.st-key-fc_tab label[data-testid="stRadioOption"] p { color: var(--ox-text) !important; }
.st-key-fc_tab label[data-testid="stRadioOption"]:has(input:checked) { background: var(--ow-ink) !important; border-color: var(--ow-ink) !important; }
.st-key-fc_tab label[data-testid="stRadioOption"]:has(input:checked) p { color: #FFFFFF !important; }
body:has(.gp-fc-page) .ow-tabbar button[aria-selected="true"] { background: var(--ow-ink) !important; border-color: var(--ow-ink) !important; color: #FFFFFF !important; }
body:has(.gp-fc-page) .ow-tabbar button[aria-selected="true"] b { color: #FFFFFF !important; }
body:has(.gp-fc-page) .ox-btn.pri, body:has(.gp-fc-page) .ox-pill.on { color: #FFFFFF; }
.fx-cover { display: grid !important; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); gap: 1.4rem; align-items: center; }
.fx-cover-img .ox-fig { margin: 0; }
.fx-pts { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border-top: 1px solid var(--ox-line); border-bottom: 1px solid var(--ox-line); margin: 0.3rem 0 1rem; }
.fx-pts > div { padding: 0.8rem 0.9rem 0.8rem 0; display: flex; flex-direction: column; gap: 0.1rem; }
.fx-pts > div + div { padding-left: 0.9rem; border-left: 1px solid var(--ox-line); }
.fx-pts span { font-size: 0.78rem; font-weight: 700; color: var(--ox-muted); } .fx-pts b { font-size: 1.55rem; font-weight: 800; color: var(--ox-text); }
.fx-pts em { font-style: normal; font-weight: 800; color: var(--ow-ink); font-size: 0.9rem; } .fx-pts small { font-size: 0.74rem; line-height: 1.4; }
.fx-pts small a { color: var(--ox-muted); }
.fx-4 { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.8rem; margin: 0.4rem 0 0.6rem; }
.fx-4 > div { border-top: 3px solid var(--ow-acc); padding-top: 0.6rem; display: flex; flex-direction: column; gap: 0.2rem; }
.fx-4 em { font-style: normal; font-weight: 900; font-size: 1.02rem; color: var(--ox-text); } .fx-4 span { font-size: 0.9rem; color: var(--ox-text); }
.fx-chain { display: flex; flex-wrap: wrap; align-items: center; gap: 0.35rem; margin: 0.3rem 0 0.6rem; }
.fx-chain span { padding: 0.45rem 0.75rem; border-radius: 999px; border: 1px solid var(--ox-line); font-size: 0.88rem; color: var(--ox-text); background: #FFFFFF; }
.fx-chain span.hot { border-color: var(--ow-acc); background: #F0FDF4; font-weight: 700; }
.fx-chain i { font-style: normal; color: var(--ow-acc); font-weight: 900; }
.fx-mock { position: relative; border-radius: 12px; background: linear-gradient(160deg, #1E1B4B, #312E81); color: #F8FAFC; padding: 2.1rem 1.1rem 1.1rem; margin: 0.4rem 0 0.6rem; }
.fx-mock.pitch { background: repeating-linear-gradient(90deg, #14532D 0 64px, #166534 64px 128px); }
.fx-mock-tag { position: absolute; top: 0.55rem; left: 0.8rem; font-size: 0.72rem; font-weight: 800; color: #FDE68A; letter-spacing: 0.02em; }
.fx-mock span { font-size: 0.74rem; color: #C7D2FE; display: block; } .fx-mock.pitch span { color: #BBF7D0; }
.fx-mock b { color: #FFFFFF; } .fx-mock small { font-size: 0.76rem; color: #E2E8F0; display: block; }
.fx-care { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; }
.fx-spark { display: flex; align-items: flex-end; gap: 6px; height: 90px; margin: 0.5rem 0; }
.fx-spark i { flex: 1; background: #4ADE80; border-radius: 3px 3px 0 0; }
.fx-care-r { display: grid; gap: 0.5rem; } .fx-care-r > div { background: rgba(255,255,255,0.08); border-radius: 8px; padding: 0.5rem 0.7rem; }
.fx-rb { display: grid; gap: 0.8rem; }
.fx-rb-v { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.6rem; } .fx-rb-v b { font-size: 1.4rem; } .fx-rb-v b.dn { color: #FCA5A5; }
.fx-rb-c { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; }
.fx-rb-c > div { border: 1px solid rgba(255,255,255,0.25); border-radius: 8px; padding: 0.55rem 0.7rem; } .fx-rb-c > div.on { border-color: #4ADE80; background: rgba(74,222,128,0.12); }
.fx-rb-m .ox-bar { background: rgba(255,255,255,0.18); margin: 0.35rem 0; } .fx-rb-m .ox-bar i { background: #4ADE80; }
.fx-war-h { font-size: 1.6rem; font-weight: 900; font-style: italic; letter-spacing: -0.02em; margin-bottom: 0.6rem; }
.fx-war-h small { font-style: normal; font-weight: 600; font-size: 0.8rem; margin-top: 0.1rem; }
.fx-war-g { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.6rem; }
.fx-war-g > div { background: rgba(0,0,0,0.28); border-radius: 8px; padding: 0.6rem 0.7rem; }
.fx-war-r > div { display: grid; grid-template-columns: 1.2rem 1fr; gap: 0 0.4rem; margin-top: 0.25rem; } .fx-war-r small { grid-column: 2; }
.fx-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr)); gap: 0.6rem; margin: 0.6rem 0; }
.fx-steps > div { border-top: 3px solid var(--ow-acc); padding-top: 0.5rem; display: flex; flex-direction: column; gap: 0.1rem; }
.fx-steps em { font-style: normal; font-size: 0.76rem; font-weight: 800; color: var(--ow-ink); } .fx-steps b { font-size: 0.95rem; color: var(--ox-text); }
.fx-steps small { font-size: 0.84rem; color: var(--ox-text); line-height: 1.5; }
.fx-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; margin: 0.4rem 0; }
.fx-3 > div { border-top: 3px solid var(--ox-line); padding-top: 0.5rem; } .fx-3 span { font-size: 0.86rem; font-weight: 800; color: var(--ow-ink); }
.fx-3 ul { margin: 0.3rem 0 0; padding-left: 1.05rem; } .fx-3 li, .fx-3 p { font-size: 0.92rem; color: var(--ox-text); line-height: 1.55; margin: 0.3rem 0 0; }
.fx-funnel { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; margin: 0.3rem 0 0.6rem; }
.fx-funnel span { padding: 0.4rem 0.8rem; border-radius: 8px; background: #F0FDF4; border: 1px solid #BBF7D0; font-weight: 700; font-size: 0.92rem; color: var(--ox-text); }
.fx-funnel i { font-style: normal; color: var(--ow-acc); font-weight: 900; }
.fx-voc td:nth-child(3) a { font-weight: 600; }
@media (max-width: 760px) {
  .fx-cover, .fx-care, .fx-3 { grid-template-columns: 1fr !important; }
  .fx-pts, .fx-4, .fx-war-g { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fx-pts > div:nth-child(3) { border-left: 0; padding-left: 0; }
  .fx-rb-v { grid-template-columns: 1fr 1fr; }
}
"""


# 11차: FC 온라인 최종 개선 (MY CLUB WAR 대표 기획 · BM 카드 · 구단 가치 UI) — fx-* 클래스 · FC 페이지에만 적용
OW_REDESIGN_CSS += """
.fx-dirs { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.8rem; }
.fx-dirs span { display: inline-flex; gap: 0.4rem; align-items: center; padding: 0.35rem 0.75rem; border-radius: 999px; background: #F0FDF4; border: 1px solid #BBF7D0; font-size: 0.88rem; font-weight: 700; color: var(--ox-text); }
.fx-dirs b { color: var(--ow-ink); }
.fx-nums { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.8rem; margin: 0.6rem 0 0.9rem; }
.fx-nums > div { background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; padding: 0.9rem 1rem; display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; }
.fx-nums b { font-size: 2rem; font-weight: 900; color: var(--ow-ink); letter-spacing: -0.03em; line-height: 1.1; }
.fx-nums.big b { font-size: 2.4rem; }
.fx-nums span { font-size: 0.92rem; font-weight: 700; color: var(--ox-text); } .fx-nums small { font-size: 0.76rem; color: var(--ox-muted); line-height: 1.4; }
.fx-nums small a { color: var(--ox-muted); }
.fx-mcw-strip { display: grid; grid-template-columns: auto auto 1fr; gap: 0.2rem 0.9rem; align-items: center; text-decoration: none !important; margin: 0 0 0.9rem;
  padding: 0.9rem 1.1rem; border-radius: 12px; color: #F8FAFC !important; background: radial-gradient(120% 140% at 85% 0%, #22C55E33, transparent 60%), linear-gradient(135deg, #052E16, #14532D); }
.fx-mcw-strip span { font-size: 0.72rem; font-weight: 800; color: #052E16; background: #4ADE80; border-radius: 4px; padding: 2px 7px; }
.fx-mcw-strip b { font-size: 1.3rem; font-weight: 900; font-style: italic; color: #FFFFFF; } .fx-mcw-strip em { font-style: normal; font-weight: 700; color: #BBF7D0; }
.fx-mcw-strip small { grid-column: 1 / -1; font-size: 0.8rem; color: #D1FAE5; }
.fx-4.slim > div { padding-top: 0.45rem; } .fx-4.slim span { font-size: 0.84rem; color: var(--ox-muted); }
.fx-3.str > div { border-top-color: var(--ow-acc); }
.fx-slot { aspect-ratio: 16 / 9; border: 2px dashed #BBF7D0; border-radius: 10px; background: #F7FEF9; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 0.15rem; text-align: center; padding: 0.6rem; }
.fx-slot b { font-size: 0.92rem; color: var(--ow-ink); } .fx-slot span { font-size: 0.82rem; color: var(--ox-text); } .fx-slot small { font-size: 0.7rem; color: var(--ox-muted); word-break: break-all; }
.fx-bms { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.9rem; margin: 0.5rem 0 0.8rem; }
.fx-bm { border: 1px solid var(--ox-line); border-radius: 12px; padding: 0.7rem; display: flex; flex-direction: column; gap: 0.4rem; min-width: 0; background: #FFFFFF; }
.fx-bm .ox-fig { margin: 0; } .fx-bm .ox-fig img { aspect-ratio: 16 / 9; object-fit: cover; }
.fx-bm-t { display: flex; justify-content: space-between; align-items: center; gap: 0.4rem; } .fx-bm-t b { font-size: 1rem; color: var(--ox-text); }
.fx-bm-t i { font-style: normal; font-size: 0.7rem; font-weight: 800; border-radius: 4px; padding: 1px 6px; white-space: nowrap; }
.fx-bm-t i.ok { background: #DCFCE7; color: #166534; } .fx-bm-t i.wait { background: #FEF3C7; color: #92400E; }
.fx-bm p { margin: 0; font-size: 0.86rem; line-height: 1.5; color: var(--ox-text); }
.fx-bm p span { display: block; font-size: 0.72rem; font-weight: 800; color: var(--ow-ink); }
.fx-cycle { position: relative; width: min(100%, 460px); aspect-ratio: 1; margin: 0.4rem auto 0.8rem; }
.fx-cycle::before { content: ""; position: absolute; inset: 11%; border: 3px dashed #86EFAC; border-radius: 50%; }
.fx-cycle > div { position: absolute; left: 50%; top: 50%; width: 31%; transform: translate(-50%, -50%);
  background: #FFFFFF; border: 2px solid var(--ow-acc); border-radius: 12px; padding: 0.4rem 0.3rem; text-align: center; font-size: 0.8rem; font-weight: 700; color: var(--ox-text); line-height: 1.3; }
.fx-cycle > div em { display: block; font-style: normal; font-size: 0.7rem; color: var(--ow-ink); font-weight: 900; }
.fx-cycle-c { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); text-align: center; font-weight: 900; font-size: 0.9rem; color: var(--ow-ink); }
.fx-risk { border-left-color: #F59E0B !important; }
.fx-vocs { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.7rem; margin: 0.4rem 0 0.8rem; }
.fx-vocs > div { border: 1px solid var(--ox-line); border-left: 4px solid #9CA3AF; border-radius: 8px; padding: 0.6rem 0.7rem; display: flex; flex-direction: column; gap: 0.25rem; min-width: 0; }
.fx-vocs > div.t-n { border-left-color: #DC2626; }
.fx-vocs span { font-size: 0.72rem; font-weight: 800; color: var(--ox-muted); } .fx-vocs b { font-size: 0.9rem; line-height: 1.45; color: var(--ox-text); }
.fx-vocs small { font-size: 0.72rem; color: var(--ox-muted); } .fx-vocs small a { color: var(--ow-ink); } .fx-vocs em { font-style: normal; font-size: 0.78rem; font-weight: 700; color: var(--ow-ink); }
body:has(.gp-fc-page) .ox-fields.four { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.fx-chain2 { display: grid; grid-template-columns: repeat(8, minmax(0, 1fr)); gap: 0.35rem; margin: 0.4rem 0 0.2rem; }
.fx-chain2 > div { border: 1px solid var(--ox-line); border-radius: 8px; padding: 0.45rem 0.4rem; font-size: 0.8rem; line-height: 1.35; color: var(--ox-text); background: #FFFFFF; min-width: 0; }
.fx-chain2 > div em { display: block; font-style: normal; font-weight: 900; font-size: 0.72rem; color: var(--ox-muted); }
.fx-chain2 > div.care { background: #EFF6FF; border-color: #93C5FD; } .fx-chain2 > div.reb { background: #F0FDF4; border-color: #86EFAC; }
.fx-zone { display: grid; grid-template-columns: 3fr 4fr; gap: 0.35rem; margin: 0 0 0.8rem 12.5%; }
.fx-zone span { font-size: 0.76rem; font-weight: 800; text-align: center; padding: 0.25rem; border-radius: 0 0 8px 8px; }
.fx-zone .care { background: #DBEAFE; color: #1E40AF; } .fx-zone .reb { background: #DCFCE7; color: #166534; }
.fx-tabs { display: flex; gap: 0.3rem; margin-bottom: 0.5rem; } .fx-tabs span { display: inline-block !important; padding: 0.15rem 0.6rem; border-radius: 999px; border: 1px solid rgba(255,255,255,0.3); font-size: 0.74rem; }
.fx-tabs span.on { background: #4ADE80; color: #052E16 !important; font-weight: 800; border-color: #4ADE80; }
.fx-mock b.dn, .fx-mock em.dn { color: #FCA5A5; } .fx-mock em.up { color: #86EFAC; }
.fx-care-pl { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.4rem; margin-top: 0.6rem; }
.fx-care-pl > div { background: rgba(255,255,255,0.08); border-radius: 8px; padding: 0.4rem 0.5rem; } .fx-care-pl em { font-style: normal; font-weight: 800; display: block; }
.fx-ba { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr); gap: 0.8rem; }
.fx-pitch { background: repeating-linear-gradient(180deg, #166534 0 34px, #15803D 34px 68px); border: 2px solid rgba(255,255,255,0.5); border-radius: 8px; padding: 0.5rem 0.3rem;
  display: flex; flex-direction: column; gap: 0.45rem; margin-top: 0.3rem; }
.fx-line { display: flex; justify-content: space-around; gap: 0.25rem; }
.fx-line span { display: inline-block !important; background: rgba(0,0,0,0.45); color: #FFFFFF !important; border-radius: 6px; padding: 0.15rem 0.35rem; font-size: 0.72rem !important; white-space: nowrap; }
.fx-after { background: rgba(255,255,255,0.08); border-radius: 8px; padding: 0.6rem 0.7rem; margin-top: 0.3rem; display: flex; flex-direction: column; gap: 0.2rem; }
.fx-after b { color: #86EFAC !important; }
.fx-mock.night { background: radial-gradient(60% 50% at 20% 0%, rgba(255,255,255,0.22), transparent 70%), radial-gradient(60% 50% at 80% 0%, rgba(255,255,255,0.18), transparent 70%),
  linear-gradient(180deg, #020617 0%, #0B1F3A 55%, #14532D 100%); }
.fx-stadium { padding-top: 0.4rem; }
.fx-vs { background: rgba(2,6,23,0.55); border: 1px solid rgba(255,255,255,0.18); border-radius: 12px; padding: 0.9rem 1rem; }
.fx-vs-n { font-size: 0.82rem; font-weight: 800; color: #FDE68A; text-align: center; margin-bottom: 0.4rem; }
.fx-vs-row { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 0.6rem; }
.fx-vs-row > div { display: flex; align-items: center; gap: 0.5rem; min-width: 0; } .fx-vs-row .b { justify-content: flex-end; text-align: right; }
.fx-vs-row i { width: 14px; height: 14px; border-radius: 50%; flex: none; } .fx-vs-row .a i { background: var(--ca); } .fx-vs-row .b i { background: var(--cb); }
.fx-vs-row b { font-size: 0.95rem; } .fx-vs-row strong { font-size: 1.7rem; font-weight: 900; color: #FFFFFF; }
.fx-vs-row .vs { font-weight: 900; font-style: italic; font-size: 1.1rem; color: #FDE68A; }
.fx-vs-bar { height: 10px; border-radius: 999px; background: var(--cb); overflow: hidden; margin: 0.6rem 0 0.5rem; filter: saturate(0.8); }
.fx-vs-bar span { display: block !important; height: 100%; background: var(--ca); border-right: 2px solid #FFFFFF; }
.fx-vs-meta { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 0.3rem; } .fx-vs-meta span { display: inline !important; font-size: 0.8rem !important; color: #E2E8F0 !important; }
.fx-league td:last-child .up { color: #16A34A; font-weight: 800; } .fx-league td:last-child .dn { color: #DC2626; font-weight: 800; }
.fx-funnel8 { display: flex; flex-direction: column; align-items: center; gap: 0.25rem; margin: 0.4rem 0; }
.fx-funnel8 > div { box-sizing: border-box; width: var(--w); max-width: 100%; min-width: 12rem; background: linear-gradient(90deg, #16A34A, #22C55E); color: #FFFFFF; border-radius: 6px; padding: 0.35rem 0.6rem; font-size: 0.86rem; font-weight: 700; text-align: center; }
.fx-funnel8 em { font-style: normal; opacity: 0.8; margin-right: 0.4rem; }
.fx-weeks { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 0.4rem; margin: 0.4rem 0; }
.fx-weeks > div { border-top: 3px solid var(--ow-acc); padding-top: 0.4rem; min-width: 0; } .fx-weeks em { font-style: normal; font-weight: 900; font-size: 0.78rem; color: var(--ow-ink); display: block; }
.fx-weeks span { font-size: 0.84rem; color: var(--ox-text); line-height: 1.4; }
.fx-io { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin: 0.5rem 0 0.8rem; }
.fx-io > div { border: 1px solid var(--ox-line); border-radius: 12px; padding: 0.9rem 1rem; display: flex; align-items: center; gap: 0.7rem; }
.fx-io b { font-size: 2.2rem; font-weight: 900; color: var(--ow-ink); } .fx-io span { font-size: 1rem; font-weight: 700; color: var(--ox-text); }
.fx-io i { width: 36px; height: 24px; border-radius: 6px; border: 2px solid var(--ow-acc); flex: none; } .fx-io i.pad { border-radius: 12px; }
.fx-chips { display: flex; flex-wrap: wrap; gap: 0.35rem; margin: 0.5rem 0; }
.fx-chips span { padding: 0.3rem 0.7rem; border-radius: 999px; background: #F0FDF4; border: 1px solid #BBF7D0; font-size: 0.84rem; color: var(--ox-text); }
.fx-road { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.7rem; margin: 0.4rem 0 0.8rem; }
.fx-road > div { border-top: 3px solid var(--ow-acc); padding-top: 0.5rem; display: flex; flex-direction: column; gap: 0.25rem; min-width: 0; }
.fx-road em { font-style: normal; font-weight: 900; color: var(--ow-ink); } .fx-road b { font-size: 0.88rem; color: var(--ox-text); line-height: 1.45; }
.fx-road p { margin: 0; font-size: 0.8rem; line-height: 1.45; color: var(--ox-text); } .fx-road p span { font-weight: 800; color: var(--ox-muted); margin-right: 0.3rem; }
.fx-vocs > div.t-p { border-left-color: #16A34A; }
.ox-fig.off figcaption b { background: #DCFCE7; color: #166534; }
.fx-exist { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr); gap: 1rem; align-items: center; margin: 0.6rem 0; padding: 0.8rem; border: 1px dashed #86EFAC; border-radius: 12px; }
.fx-exist .ox-fig { margin: 0; } .fx-exist b { font-size: 0.95rem; color: var(--ox-text); }
.fx-exist p { margin: 0.35rem 0 0; font-size: 0.86rem; line-height: 1.5; color: var(--ox-text); } .fx-exist p span { font-weight: 800; color: var(--ow-ink); margin-right: 0.35rem; }
.fx-exist p a { color: var(--ow-ink); } .fx-exist .fx-exist-n { font-weight: 700; }
.fx-union { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem; align-items: center; margin: 0.4rem 0 0.6rem; }
.fx-union .ox-fig { margin: 0; } .fx-union .ox-facts { margin: 0; }
.fx-diff3 { display: grid; gap: 0; border: 1px solid var(--ox-line); border-radius: 12px; overflow: hidden; margin: 0.4rem 0 1rem; }
.fx-diff3 > div { display: grid; grid-template-columns: 7.5rem minmax(0, 1fr) minmax(0, 1fr); gap: 0.8rem; align-items: center; padding: 0.6rem 0.9rem; border-top: 1px solid var(--ox-line); }
.fx-diff3 > div.hd { border-top: 0; background: #F8FAFC; } .fx-diff3 .hd b { font-size: 0.82rem; color: var(--ox-muted); } .fx-diff3 .hd b:last-child { color: var(--ow-ink); }
.fx-diff3 span { font-size: 0.82rem; font-weight: 800; color: var(--ox-muted); }
.fx-diff3 p { margin: 0; font-size: 0.92rem; color: var(--ox-text); line-height: 1.45; } .fx-diff3 p.new { font-weight: 800; color: var(--ow-ink); }
.fx-off { border-left-color: #2563EB !important; } .fx-off a { color: #1D4ED8; }
@media (max-width: 1000px) {
  .fx-bms, .fx-vocs { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fx-chain2 { grid-template-columns: repeat(4, minmax(0, 1fr)); } .fx-zone { display: none; }
  .fx-weeks, .fx-road { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 760px) {
  .fx-nums, .fx-bms, .fx-vocs, .fx-ba, .fx-road, .fx-care-pl { grid-template-columns: 1fr !important; }
  .fx-exist, .fx-union { grid-template-columns: 1fr; }
  .fx-diff3 > div { grid-template-columns: 1fr 1fr; gap: 0.3rem 0.8rem; } .fx-diff3 > div > span { grid-column: 1 / -1; } .fx-diff3 .hd span { display: none; }
  .fx-nums b, .fx-nums.big b { font-size: 1.8rem; }
  .fx-chain2, .fx-weeks, .fx-io { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  body:has(.gp-fc-page) .ox-fields.four { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fx-mcw-strip { grid-template-columns: auto 1fr; } .fx-mcw-strip em { grid-column: 1 / -1; }
  .fx-vs-row strong { font-size: 1.3rem; } .fx-vs-row b { font-size: 0.76rem; word-break: keep-all; line-height: 1.3; }
  .fx-cycle > div { font-size: 0.7rem; }
  .fx-funnel8 > div { min-width: 0; width: 100% !important; }
  .fx-mock { padding-top: 0.8rem; } .fx-mock-tag { position: static; display: block; margin-bottom: 0.5rem; line-height: 1.4; }
  .ow-table.fx-league { display: table; width: 100%; } .ow-table.fx-league tbody { display: table-row-group; width: auto; }
  .ow-table.fx-league tr, .ow-table.fx-league tr:first-child { display: table-row; width: auto; border: 0; }
  .ow-table.fx-league td, .ow-table.fx-league th { display: table-cell; width: auto; padding: 0.4rem 0.3rem; font-size: 0.8rem; background: #FFFFFF !important; border-bottom: 1px solid var(--ox-line); }
  .ow-table.fx-league td::before { content: none; }
  .ow-table.fx-league td:nth-child(3), .ow-table.fx-league th:nth-child(3) { display: none; }
  .fx-io b { font-size: 1.6rem; } .fx-io > div { padding: 0.7rem; gap: 0.45rem; min-width: 0; flex-wrap: wrap; } .fx-io i { width: 28px; height: 20px; }
}
"""


# 12차: PUBG 최종 개선 (대표 기획 카드 · 시장 최신값 · 복귀 여정 · 광고 3종 차별화 · 14경기 실측) — pz-* 클래스 · PUBG 페이지에만 있음
OW_REDESIGN_CSS += """
.pz-mkt { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.8rem; margin: 0.5rem 0 0.3rem; }
.pz-mkt > div { border: 1px solid #CBD5E1; border-top: 4px solid #142D50; border-radius: 10px; padding: 0.8rem 0.9rem; display: flex; flex-direction: column; gap: 0.2rem; min-width: 0; background: #FFFFFF; }
.pz-mkt > div.i { border-top-color: #64748B; background: #F8FAFC; }
.pz-mkt span { font-size: 0.78rem; font-weight: 700; color: #475569; } .pz-mkt b { font-size: 1.55rem; font-weight: 900; color: #142D50; letter-spacing: -0.02em; line-height: 1.2; }
.pz-mkt b em { font-style: normal; color: #DC2626; font-size: 1.1rem; } .pz-mkt small { font-size: 0.76rem; color: #475569; line-height: 1.45; } .pz-mkt small a { color: #1E40AF; }
.pz-flags { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin: 0.9rem 0 0.6rem; }
.pz-flag { border-radius: 14px; padding: 1rem 1.1rem; background: #FFFFFF; border: 1px solid #CBD5E1; border-top: 6px solid #2563EB; min-width: 0; }
.pz-flag.b { border-top-color: #142D50; background: linear-gradient(180deg, #F1F5FB 0%, #FFFFFF 40%); }
.pz-flag-k { font-size: 0.78rem; font-weight: 800; color: #2563EB; letter-spacing: 0.02em; } .pz-flag.b .pz-flag-k { color: #142D50; }
.pz-flag-t { font-size: 1.45rem; font-weight: 900; color: #0F172A; letter-spacing: -0.02em; line-height: 1.25; margin: 0.15rem 0 0.6rem; }
.pz-flag-t small { display: block; font-size: 0.78rem; font-weight: 700; color: #64748B; letter-spacing: 0.04em; }
.pz-row { display: grid; grid-template-columns: 3.4rem minmax(0, 1fr); gap: 0.6rem; align-items: start; padding: 0.45rem 0; border-top: 1px dashed #E2E8F0; }
.pz-row span { font-size: 0.74rem; font-weight: 800; color: #FFFFFF; background: #64748B; border-radius: 4px; padding: 2px 0; text-align: center; }
.pz-row:nth-of-type(4) span { background: #2563EB; } .pz-flag.b .pz-row:nth-of-type(4) span { background: #142D50; }
.pz-row:last-child span { background: #16A34A; }
.pz-row p { margin: 0; font-size: 0.92rem; line-height: 1.5; color: #1E293B; }
.pz-jour { border: 1px solid #CBD5E1; border-radius: 14px; padding: 0.9rem 1rem; margin: 0.6rem 0 0.9rem; background: #F8FAFC; }
.pz-jour-h { font-size: 0.86rem; font-weight: 800; color: #142D50; margin-bottom: 0.6rem; }
.pz-jour-r { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 0.5rem; align-items: end; }
.pz-jour-r > div { position: relative; display: flex; flex-direction: column; gap: 0.15rem; padding-top: 0.2rem; min-width: 0; }
.pz-jour-r > div i { display: block; height: 70px; border-radius: 6px 6px 0 0; background: linear-gradient(0deg, #142D50 var(--h), #E2E8F0 var(--h)); order: -1; margin-bottom: 0.35rem; }
.pz-jour-r em { font-style: normal; font-size: 0.72rem; font-weight: 900; color: #64748B; } .pz-jour-r b { font-size: 0.92rem; color: #0F172A; }
.pz-jour-r strong { font-size: 1.25rem; font-weight: 900; color: #142D50; } .pz-jour-r small { font-size: 0.76rem; color: #475569; line-height: 1.4; }
.pz-jour-n { font-size: 0.78rem; color: #475569; margin-top: 0.5rem; }
.pz-ads { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.7rem; margin: 0.6rem 0 0.8rem; }
.pz-ads > div { border: 1px solid #CBD5E1; border-radius: 10px; padding: 0.7rem 0.8rem; background: #FFFFFF; min-width: 0; }
.pz-ads > div.ad2 { border: 2px solid #142D50; background: #F1F5FB; }
.pz-ads em { font-style: normal; font-size: 0.74rem; font-weight: 800; color: #64748B; } .pz-ads .ad2 em { color: #142D50; }
.pz-ads b { display: block; font-size: 1rem; color: #0F172A; margin: 0.15rem 0 0.4rem; line-height: 1.35; }
.pz-ads p { margin: 0.2rem 0 0; font-size: 0.84rem; line-height: 1.45; color: #1E293B; } .pz-ads p span { font-weight: 800; color: #475569; margin-right: 0.35rem; }
.pz-my14 { border: 1px solid #CBD5E1; border-radius: 12px; padding: 0.8rem 0.9rem; background: #0F1B2D; color: #F8FAFC; margin-bottom: 0.5rem; }
.pz-my14-h { font-size: 0.84rem; font-weight: 800; color: #FDE68A; margin-bottom: 0.5rem; } .pz-my14-h .gp-badge { margin-left: 0.3rem; }
.pz-my14 .g { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.5rem; }
.pz-my14 .g > div { background: rgba(255,255,255,0.07); border-radius: 8px; padding: 0.5rem 0.6rem; display: flex; flex-direction: column; min-width: 0; }
.pz-my14 .g b { font-size: 1.45rem; font-weight: 900; color: #FACC15; line-height: 1.2; } .pz-my14 .g span { font-size: 0.82rem; font-weight: 700; }
.pz-my14 .g small { font-size: 0.72rem; color: #CBD5E1; } .pz-my14 p { margin: 0.6rem 0 0.2rem; font-size: 0.86rem; line-height: 1.5; color: #F8FAFC; }
.pz-my14 > small { font-size: 0.7rem; color: #94A3B8; }
.pz-vs tr:last-child td { background: #EEF2FF !important; } .pz-vs tr:last-child td:first-child b { color: #142D50; }
@media (max-width: 760px) {
  .pz-mkt, .pz-flags, .pz-ads { grid-template-columns: 1fr; }
  .pz-jour-r { grid-template-columns: 1fr; gap: 0.4rem; }
  .pz-jour-r > div { display: grid; grid-template-columns: 1.6rem minmax(0, 1fr) auto; grid-template-areas: "e b s" "e d d"; align-items: center; gap: 0 0.5rem; padding: 0.4rem 0; border-top: 1px dashed #CBD5E1; }
  .pz-jour-r > div i { display: none; } .pz-jour-r em { grid-area: e; } .pz-jour-r b { grid-area: b; } .pz-jour-r strong { grid-area: s; font-size: 1.05rem; } .pz-jour-r small { grid-area: d; }
  .pz-flag-t { font-size: 1.25rem; }
}
"""
