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
