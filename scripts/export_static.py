"""GamePulse AI 정적 HTML 보고서 생성기 (GitHub Pages 용).

Streamlit 앱은 JavaScript·WebSocket 으로 화면을 그리기 때문에, 글자만 읽는 AI 검토 도구는 내용을 볼 수 없다.
이 스크립트는 실제 앱을 Streamlit 테스트 실행기(AppTest)로 돌려 화면 요소를 순서대로 읽고,
같은 CSS 를 입힌 정적 HTML 로 docs/ 에 저장한다. 내용을 따로 옮겨 적지 않으므로 앱이 바뀌면 다시 실행만 하면 된다.

사용법 (프로젝트 폴더에서):
    .venv\\Scripts\\python.exe scripts\\export_static.py

변환 규칙
- 탭      → 차례대로 펼친 섹션 + 목차
- 펼치기  → 열린 상태로 표시 (내용 누락 방지)
- 차트    → 같은 Plotly 엔진으로 그리고, 아래에 숫자 표를 함께 넣음 (글자만 읽는 도구용)
- 버튼·슬라이더 등 → 기본값 스냅샷 (직접 조작은 원본 앱에서)
- 이미지  → docs/assets/img/ 에 파일로 저장. 원본 파일은 이미 닉네임을 가린 사본이며,
           표시 단계에서도 manifest 의 blur 영역을 한 번 더 가린다.

앱 코드·데이터·디자인은 수정하지 않는다. 결과물은 docs/ 폴더에만 쓴다.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import html as H
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402
from streamlit.testing.v1.element_tree import Block  # noqa: E402

from gamepulse.config import APP_NAME, APP_TAGLINE  # noqa: E402
from gamepulse.content.games import GAME_ORDER, GAMES  # noqa: E402
from gamepulse.ui.components import badge  # noqa: E402
from gamepulse.ui.styles import CSS as APP_CSS  # noqa: E402
from gamepulse.views.overwatch import TAB_LABELS as OW_TABS  # noqa: E402
from gamepulse.views.pubg import TAB_LABELS as PG_TABS  # noqa: E402
from gamepulse.views.fconline import TAB_LABELS as FC_TABS  # noqa: E402
from gamepulse.views.dnf import TAB_LABELS as DF_TABS  # noqa: E402

DOCS = ROOT / "docs"
import csv as _csv  # noqa: E402
OW_VERIFIED = sum(1 for r in _csv.DictReader(open(ROOT / "data" / "overwatch" / "opinions.csv", encoding="utf-8")) if r["verification_status"] == "검증 완료")
IMG_DIR = DOCS / "assets" / "img"
LIVE_URL = "https://gamepulse-ai2.streamlit.app/"
REPO_URL = "https://github.com/dbswnsghek3-cmyk/gamepulse.ai"
SITE_URL = "https://dbswnsghek3-cmyk.github.io/gamepulse.ai/"
KST = dt.timezone(dt.timedelta(hours=9))

# (앱 페이지 id, 파일명, 메뉴 이름, 차트 기본 분류)
PAGES = [("overwatch", "overwatch.html", "오버워치 · PROJECT RE:START", "real"),
         ("fconline", "fconline.html", "FC 온라인 · 축구 게임인가, 주식 게임인가?", "real"),
         ("pubg", "pubg.html", "PUBG · NEW START", "real"),
         ("dnf", "dnf.html", "던전앤파이터 · 노력은 남고, 성취는 이어져야 한다", "real")]
PAGES += [("home", "home.html", "사이트 홈 · 개요", "sample")]
PAGES += [(g, f"{g}.html", GAMES[g]["name"], "sample") for g in GAME_ORDER if g not in ("overwatch", "pubg", "fconline", "dnf")]
PAGES += [("assistant", "assistant.html", "사업PM 어시스턴트", "plan")]   # 데이터 랩은 메뉴에서 제외 (코드만 보존)

KIND_BADGE = {"real": badge("실제 자료", "k-real"), "sim": badge("가정 시뮬레이션", "k-sim"),
              "plan": badge("분석자 해석", "k-interp"), "sample": badge("예시 데이터", "k-sample")}


# ----------------------------------------------------------------------
# 마크다운(일부 문법)을 HTML 로
def md_inline(s: str) -> str:
    s = H.escape(s, quote=False).replace("\\~", "~")
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


def md_block(text: str) -> str:
    out, para, lst = [], [], None

    def flush():
        nonlocal para
        if para:
            out.append("<p>" + "<br>".join(para) + "</p>")
            para = []

    def close():
        nonlocal lst
        if lst:
            out.append(f"</{lst}>")
            lst = None

    for line in text.split("\n"):
        mu, mo, mh = re.match(r"^\s*[-*]\s+(.*)", line), re.match(r"^\s*\d+\.\s+(.*)", line), re.match(r"^(#{1,6})\s+(.*)", line)
        if mu or mo:
            flush()
            tag = "ul" if mu else "ol"
            if lst != tag:
                close()
                out.append(f"<{tag}>")
                lst = tag
            out.append(f"<li>{md_inline((mu or mo).group(1))}</li>")
        elif mh:
            flush(); close()
            out.append(f"<h4>{md_inline(mh.group(2))}</h4>")
        elif line.strip() == "---":
            flush(); close()
            out.append("<hr>")
        elif not line.strip():
            flush(); close()
        else:
            close()
            para.append(md_inline(line.strip()))
    flush(); close()
    return f'<div class="sx-md">{"".join(out)}</div>'


# ----------------------------------------------------------------------
# 차트: Plotly spec (배열은 base64 typed array 로 인코딩돼 있을 수 있음)
def _arr(v):
    if isinstance(v, dict) and "bdata" in v:
        import numpy as np

        a = np.frombuffer(base64.b64decode(v["bdata"]), dtype=np.dtype(v["dtype"]))
        if v.get("shape"):
            a = a.reshape([int(x) for x in str(v["shape"]).split(",")])
        return a.tolist()
    return v


def _cell(v) -> str:
    if isinstance(v, float):
        return f"{v:,.2f}".rstrip("0").rstrip(".") if abs(v) < 1e15 else str(v)
    if isinstance(v, int):
        return f"{v:,}"
    return H.escape(str(v))


def _plain(v) -> str:
    """차트 라벨의 HTML 태그 제거 (예: '복귀 D7  <b>+2.0%p</b>' → '복귀 D7 +2.0%p')."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(v))).strip()


def _cat(v) -> str:
    """범주 값 표시: 날짜(ISO)는 날짜로, 그 밖에는 태그를 지운 글자."""
    s = str(v)
    m = re.match(r"^(\d{4}-\d{2}-\d{2})(?:[T ]00:00:00(?:\.0+)?)?$", s)
    if m:
        return m.group(1)
    return _cell(v) if isinstance(v, (int, float)) else H.escape(_plain(v))


def _title(obj) -> str:
    t = obj.get("title") if isinstance(obj, dict) else None
    if isinstance(t, dict):
        return t.get("text") or ""
    return t or ""


class Exporter:
    def __init__(self, page_kind: str, id_prefix: str = ""):
        self.page_kind = page_kind
        self.id_prefix = id_prefix  # 탭별로 따로 변환할 때 차트·내부 탭 id 가 겹치지 않게
        self.n_chart = 0
        self.n_tabs = 0
        self.toc: list[tuple[str, str]] = []
        self.tab_extras: dict[str, str] = {}
        self.charts = 0
        self.kinds: list[tuple[str, str]] = []

    # ---------------- 차트
    def chart(self, spec_json: str) -> str:
        spec = json.loads(spec_json)
        layout = spec.setdefault("layout", {})
        title = _title(layout)
        axes = " ".join(_title(layout.get(k, {}) or {}) for k in ("xaxis", "yaxis"))
        words = f"{title} {axes}"
        kind = ("sample" if "예시" in words else
                "plan" if ("정성" in words or "기획자 평가" in words) else
                "sim" if ("가정" in words or "시뮬레이션" in words) else self.page_kind)
        self.kinds.append((kind, title))
        layout.pop("width", None)
        layout["autosize"] = True
        layout.setdefault("font", {}).setdefault("family", "Pretendard, 'Noto Sans KR', 'Malgun Gothic', sans-serif")
        h = int(layout.get("height") or 380)
        self.n_chart += 1
        cid = f"chart{self.id_prefix}{self.n_chart}"
        payload = json.dumps({"data": spec.get("data", []), "layout": layout}, ensure_ascii=False).replace("</", "<\\/")

        # 글자만 읽는 도구를 위한 숫자 표 · 열 제목은 차트가 알려 준 의미(layout.meta.table) → 축 제목 → 일반 이름 순
        meta = (layout.get("meta") or {}).get("table", {}) if isinstance(layout.get("meta"), dict) else {}
        xt, yt = _title(layout.get("xaxis", {}) or {}), _title(layout.get("yaxis", {}) or {})
        traces = spec.get("data", [])
        horizontal = any(tr.get("orientation") == "h" for tr in traces)
        cat_t, val_t = (yt, xt) if horizontal else (xt, yt)
        cat_h = meta.get("category") or cat_t or "항목"
        val_h = meta.get("value") or val_t or "값"
        ser_h = meta.get("series") or "구분"
        rows = []
        for tr in traces:
            x, y = _arr(tr.get("x")), _arr(tr.get("y"))
            cat, val = (y, x) if tr.get("orientation") == "h" else (x, y)
            name = tr.get("name") or ""
            if isinstance(cat, list) and isinstance(val, list):
                rows += [(name, a, b) for a, b in zip(cat, val)]
            elif isinstance(val, list):
                rows += [(name, i + 1, b) for i, b in enumerate(val)]
        multi = len({n for n, _, _ in rows}) > 1
        table = ""
        if rows:
            total, cap = len(rows), 200
            note = f" · 원자료 {total:,}행 중 앞 {cap}행만 표시 (차트는 전체 자료로 그림)" if total > cap else ""
            body = "".join("<tr>" + (f"<td>{H.escape(_plain(n))}</td>" if multi else "")
                           + f"<td>{_cat(a)}</td><td>{_cell(b)}</td></tr>" for n, a, b in rows[:cap])
            head = (f"<th>{H.escape(ser_h)}</th>" if multi else "") + f"<th>{H.escape(cat_h)}</th><th>{H.escape(val_h)}</th>"
            table = (f'<details class="sx-chartdata"><summary>차트 데이터 표 · {min(total, cap)}행{note} <span class="sx-more">펼쳐보기</span></summary>'
                     f'<div class="gp-table-wrap"><table class="gp-table"><tr>{head}</tr>{body}</table></div></details>')
        self.charts += 1
        # 제목이 없는 차트는 앱의 차트 카드(배지·제목·단위)가 바로 위에 있으므로 캡션을 다시 달지 않는다
        cap = f'<figcaption class="sx-chart-h">{KIND_BADGE[kind]} {H.escape(title)}</figcaption>' if title else ""
        return (f'<figure class="sx-chart{"" if title else " bare"}">{cap}'
                f'<div id="{cid}" class="sx-chart-c" style="height:{h}px"></div>'
                f'<script>(function(s){{Plotly.newPlot("{cid}", s.data, s.layout, {{displayModeBar:false, responsive:true}});}})'
                f'({payload});</script>{table}</figure>')

    # ---------------- 위젯 스냅샷
    def widget(self, n) -> str:
        t, label = n.type, H.escape(str(getattr(n, "label", "") or ""))
        if t == "radio" and label == "섹션 선택":   # 오버워치 01~06 탭 선택 → 정적 탭 바로 교체
            return "<!--OW_TABBAR-->"
        if t in ("radio", "selectbox", "multiselect", "select_slider"):
            opts = [str(o) for o in (getattr(n, "options", None) or [])]
            val = n.value
            sel = {str(v) for v in val} if isinstance(val, (list, tuple)) else {str(val)}
            chips = "".join(f'<span class="{"on" if o in sel else ""}">{H.escape(o)}</span>' for o in opts[:30])
            more = f"<span>외 {len(opts) - 30}개</span>" if len(opts) > 30 else ""
            return f'<div class="sx-w"><span class="sx-w-l">{label}</span><span class="sx-w-o">{chips}{more}</span></div>'
        if t in ("slider", "number_input"):
            return f'<div class="sx-w"><span class="sx-w-l">{label}</span><span class="sx-w-v">{_cell(n.value)}</span></div>'
        if t in ("toggle", "checkbox"):
            return f'<div class="sx-w"><span class="sx-w-l">{label}</span><span class="sx-w-v">{"켜짐" if n.value else "꺼짐"}</span></div>'
        if t in ("button", "download_button"):
            # 앱 버튼의 실제 기능을 정적 페이지에서 재현: 페이지 이동(go_*)은 링크, 나머지는 BTN_JS 가 key 로 동작을 찾는다
            k = str(getattr(n, "key", "") or "")
            if k.startswith("go_"):
                return f'<a class="sx-btn" href="{H.escape(k[3:])}.html">{label}</a>'
            return f'<button type="button" class="sx-btn" data-btn="{H.escape(k)}">{label}</button>'
        if t in ("text_input", "text_area", "chat_input"):
            ph = H.escape(str(getattr(n, "placeholder", "") or ""))
            return f'<div class="sx-w"><span class="sx-w-l">{label or "입력"}</span><span class="sx-w-in">{ph}</span></div>'
        if t == "file_uploader":
            return f'<div class="sx-w"><span class="sx-w-l">{label}</span><span class="sx-w-in">파일 업로드는 원본 앱에서</span></div>'
        return ""

    # ---------------- 요소 → HTML
    def render(self, n, depth: int = 0) -> str:
        if isinstance(n, Block):
            return self.block(n, depth)
        t = n.type
        if t == "markdown":
            v = n.value
            if "<style" in v:
                return ""
            return v if v.lstrip().startswith("<") else md_block(v)
        if t == "caption":
            return f'<div class="sx-cap">{md_inline(n.value)}</div>'
        if t in ("info", "warning", "success", "error", "exception"):
            return f'<div class="sx-alert {t}">{md_inline(str(n.value))}</div>'
        if t == "metric":
            d = f'<div class="sx-metric-d">{H.escape(str(n.delta))}</div>' if getattr(n, "delta", "") else ""
            return (f'<div class="sx-metric"><div class="sx-metric-l">{H.escape(str(n.label))}</div>'
                    f'<div class="sx-metric-v">{H.escape(str(n.value))}</div>{d}</div>')
        if t == "dataframe":
            return self.dataframe(n.value)
        if t == "plotly_chart":
            return self.chart(n.proto.spec)
        w = self.widget(n)
        if w:
            return w
        return f"<!-- 미지원 요소: {H.escape(t)} -->"

    def children(self, n, depth: int) -> str:
        return "".join(self.render(c, depth) for _, c in sorted(n.children.items()))

    def block(self, n, depth: int) -> str:
        t = n.type
        if t == "tab_container":
            tabs = [c for _, c in sorted(n.children.items())]
            self.n_tabs += 1
            ids = [f"t{self.id_prefix}{self.n_tabs}-{i}" for i in range(len(tabs))]
            if depth == 0 and not self.toc:
                self.toc = [(i, tb.label) for i, tb in zip(ids, tabs)]
            nav = "".join(f'<a href="#{i}">{H.escape(tb.label)}</a>' for i, tb in zip(ids, tabs))
            secs = "".join(
                f'<section class="sx-tab" id="{i}"><h2 class="sx-tab-h"><span>탭</span>{H.escape(tb.label)}</h2>'
                f'{self.children(tb, depth + 1)}{self.tab_extras.get(tb.label, "")}</section>'
                for i, tb in zip(ids, tabs))
            return f'<div class="sx-tabs d{min(depth, 2)}"><nav class="sx-tabnav">{nav}</nav>{secs}</div>'
        if t == "expander":
            # 앱과 같이 접힌 상태로 둔다 (본문은 핵심만). 내용은 HTML 에 그대로 있어 글자만 읽는 도구도 읽을 수 있다.
            return (f'<details class="sx-exp"><summary>{H.escape(n.label)} <span class="sx-more">펼쳐보기</span></summary>'
                    f'<div class="sx-exp-b">{self.children(n, depth)}</div></details>')
        if t == "column":
            w = getattr(n.proto, "weight", 0) or 1
            return f'<div class="sx-col" style="flex:{w:.4f} 1 0">{self.children(n, depth)}</div>'
        if t == "flex_container" and "HORIZONTAL" in str(n.proto):
            return f'<div class="sx-row">{self.children(n, depth)}</div>'
        if "border: true" in str(n.proto):  # st.container(border=True) · 차트 카드
            return f'<div class="sx-box">{self.children(n, depth)}</div>'
        return f"<div>{self.children(n, depth)}</div>"

    def dataframe(self, df: pd.DataFrame) -> str:
        if df is None or df.empty:
            return '<div class="sx-cap">표시할 자료가 없습니다.</div>'
        head = "".join(f"<th>{H.escape(str(c))}</th>" for c in df.columns)
        body = []
        for _, r in df.iterrows():
            cells = []
            for v in r.tolist():
                if isinstance(v, pd.Timestamp) and not pd.isna(v) and v == v.normalize():
                    v = v.strftime("%Y-%m-%d")
                s = "" if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NaT else str(v)
                if s.startswith(("http://", "https://")):
                    cells.append(f'<td><a href="{H.escape(s)}" target="_blank" rel="noopener">열기</a></td>')
                else:
                    cells.append(f"<td>{_cell(v) if isinstance(v, (int, float)) and s else H.escape(s)}</td>")
            body.append("<tr>" + "".join(cells) + "</tr>")
        return (f'<div class="gp-table-wrap sx-df"><table class="gp-table"><tr>{head}</tr>{"".join(body)}</table></div>'
                f'<div class="sx-cap">표 {len(df)}행 · 원본 앱에서는 정렬·검색 가능</div>')


# ----------------------------------------------------------------------
def run_page(page: str, tab: str | None = None, tab_key: str = "ow_tab") -> AppTest:
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180)
    at.session_state["page"] = page
    if tab:
        at.session_state[tab_key] = tab
    at.run()
    if at.exception:
        raise RuntimeError(f"{page} 페이지 실행 오류: {[e.value for e in at.exception]}")
    return at


def overwatch_extras() -> dict[str, str]:
    """기본 화면에 안 보이는 시안 단계(A 복귀 브리핑 1~3단계)를 클릭해 얻은 화면을 탭 끝에 덧붙인다."""
    at = run_page("overwatch", tab=OW_TABS[2])
    shots = []
    at.button(key="ow_a_start").click().run()
    for step in range(1, 4):
        cards = [m.value for m in at.markdown if 'class="ow-proto-card mock' in m.value]
        if cards:
            shots.append(cards[0])
        at.button(key="ow_a_next").click().run()
    if not shots:
        return {}
    body = "".join(shots)
    return {"A 복귀 브리핑": (
        '<details class="sx-exp" id="ow-a-steps"><summary>시안 단계 미리보기 · "3분 요약 보기"를 눌렀을 때 1~3단계 (예시 계정: 2026년 1월 마지막 접속) '
        '<span class="sx-more">펼쳐보기</span></summary>'
        f'<div class="sx-exp-b">{body}</div></details>')}


TAB_JS = """<script>(function(){
  var bar=document.querySelector('.ow-tabbar'); if(!bar) return;
  function show(n, write){
    document.querySelectorAll('.ow-pane').forEach(function(p){ p.hidden = p.getAttribute('data-tab')!==n; });
    bar.querySelectorAll('button').forEach(function(b){ var on=b.getAttribute('data-tab')===n; b.setAttribute('aria-selected', String(on)); if(on && bar.scrollWidth>bar.clientWidth) bar.scrollLeft = b.offsetLeft - (bar.clientWidth - b.offsetWidth)/2; });
    if (write) history.replaceState(null, '', '#t'+n);   /* 해시만 바꾸고 스크롤은 그대로 */
    if (window.Plotly) document.querySelectorAll('#pane-'+n+' .sx-chart-c').forEach(function(c){
      if (!c.closest('details:not([open])')) Plotly.Plots.resize(c); });
  }
  bar.querySelectorAll('button').forEach(function(b){ b.addEventListener('click', function(){ show(b.getAttribute('data-tab'), true); }); });
  function fromHash(){ var m=(location.hash||'').match(/^#t?(0[1-9])$/); show(m?m[1]:'01', false); }
  window.addEventListener('hashchange', fromHash); fromHash();
})();</script>"""


BTN_JS = """<script>(function(){
  /* 앱 버튼 재현: sx-btn-map 의 key → 동작 (ans 답변 표시 · clear 답변 지우기 · info 안내 문구 · open 펼치기) */
  var el=document.getElementById('sx-btn-map'); if(!el) return; var M=JSON.parse(el.textContent);
  document.addEventListener('click',function(ev){
    var b=ev.target.closest&&ev.target.closest('button.sx-btn[data-btn]'); if(!b) return;
    var k=b.getAttribute('data-btn'), a=M[k]; if(!a) return;
    if(a.t==='ans'){
      var box=document.getElementById('sx-answers'), x=box&&box.querySelector('.sx-ans[data-for="'+k+'"]'); if(!x) return;
      box.querySelectorAll('.sx-ans details').forEach(function(d){ d.open=false; });   /* 앱처럼 최신 답변만 펼침 */
      box.insertBefore(x, box.querySelector('.sx-ans-end')); x.hidden=false; box.hidden=false;
      x.querySelectorAll('details').forEach(function(d){ d.open=true; });
      x.scrollIntoView({behavior:'smooth',block:'start'});
    } else if(a.t==='clear'){
      var bx=document.getElementById('sx-answers'); if(!bx) return;
      bx.querySelectorAll('.sx-ans').forEach(function(x){ x.hidden=true; }); bx.hidden=true;
    } else if(a.t==='info'){
      var row=b.closest('.sx-row')||b.parentNode, n=row.nextElementSibling;
      if(!(n&&n.classList.contains('sx-btn-msg'))){ n=document.createElement('div'); n.className='sx-alert info sx-btn-msg'; row.parentNode.insertBefore(n,row.nextSibling); }
      n.textContent=a.m;
    } else if(a.t==='open'){
      var d=document.querySelector(a.sel); if(d){ d.open=true; d.scrollIntoView({behavior:'smooth',block:'start'}); }
    }
  });
})();</script>"""


def btn_script(actions: dict) -> str:
    data = json.dumps(actions, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/json" id="sx-btn-map">{data}</script>{BTN_JS}'


def btn_check(body: str, actions: dict, page: str) -> None:
    """페이지의 모든 버튼에 정적 동작이 연결됐는지 확인 (클릭되지 않는 버튼 방지)."""
    import re
    missing = sorted(set(re.findall(r'data-btn="([^"]*)"', body)) - set(actions))
    if missing:
        raise RuntimeError(f"{page}: 정적 동작이 없는 버튼 {missing}")


def overwatch_btn_actions() -> dict:
    """오버워치 04 시안 버튼: '3분 요약 보기' → 1~3단계 미리보기 펼침 · 나머지는 앱이 띄우는 안내 문구 그대로."""
    acts = {"ow_a_start": {"t": "open", "sel": "#ow-a-steps"}}
    for k in ("ow_a_later", "ow_b_practice", "ow_b_off"):
        at = run_page("overwatch", tab=OW_TABS[2])
        before = [i.value for i in at.info]
        at.button(key=k).click().run()
        new = [i.value for i in at.info if i.value not in before]
        if not new:
            raise RuntimeError(f"오버워치 {k}: 클릭 결과 안내 문구를 찾지 못함")
        acts[k] = {"t": "info", "m": new[-1]}
    return acts


def assistant_answers(kind: str, base: AppTest) -> tuple[str, dict]:
    """어시스턴트 추천 질문: 버튼마다 앱에서 실제로 눌러 얻은 답변을 숨겨 두고, 누르면 표시 (대화 지우기 포함)."""
    from streamlit.testing.v1.element_tree import Block

    def chats(n):
        if isinstance(n, Block):
            if n.type == "chat_message":
                yield n
            for _, c in sorted(n.children.items()):
                yield from chats(c)
    keys = [b.key for b in base.button if b.key and b.key.startswith(("faq_", "qa_"))]
    parts, acts = [], {}
    for k in keys:
        at = run_page("assistant")
        at.button(key=k).click().run()
        if at.exception:
            raise RuntimeError(f"어시스턴트 {k}: {[e.value for e in at.exception]}")
        ex = Exporter(kind, id_prefix=f"a_{k}_")
        parts.append(f'<div class="sx-ans" data-for="{H.escape(k)}" hidden>{"".join(ex.block(m, 1) for m in chats(at.main))}</div>')
        acts[k] = {"t": "ans"}
    acts["as_clear"] = {"t": "clear"}
    box = ('<div id="sx-answers" hidden>' + "".join(parts) +
           '<div class="sx-ans-end"><button type="button" class="sx-btn" data-btn="as_clear">대화 지우기</button></div></div>')
    return box, acts


def overwatch_body(kind: str) -> tuple[str, int]:
    body, charts = tabbed_body("overwatch", OW_TABS, "ow_tab", kind, {})   # A 데모 단계는 JS 위젯이 직접 보여 줌
    # YOUR CHOICE · 신규 스킨 손익 시뮬레이터: Streamlit 위젯 구역을 같은 계산식의 JavaScript 데모로 교체
    from ow_static_demos import demos as ow_demos
    dm = ow_demos(ROOT)
    from ow_static_widgets import SUBTAB_JS, widgets as ow_widgets   # 선택·슬라이더·입력·버튼을 실제로 동작하게
    dm.update(ow_widgets(ROOT))
    body, n = re.subn(r'<div class="ox-js-start" data-demo="(\w+)"></div>.*?<div class="ox-js-end"></div>',
                      lambda m: dm[m.group(1)], body, flags=re.S)
    if n != len(dm):
        raise RuntimeError(f"오버워치 JS 데모 교체 {n}/{len(dm)}개 · 표식 확인 필요")
    acts = overwatch_btn_actions()
    btn_check(body, acts, "overwatch")
    return body + btn_script(acts) + SUBTAB_JS, charts


PG_SCREENS_SRC = ROOT / "assets" / "pubg" / "site"      # scripts/capture_pubg_screens.py 가 만든 Streamlit 화면 캡처
PG_SCREENS_DIR = "assets/pubg-screens"


def pubg_screens() -> dict[str, str]:
    """탭별 Streamlit 원본 화면 캡처(JPEG)를 docs/ 로 복사하고 {탭 번호: 경로} 를 돌려준다. 없으면 빈 dict."""
    out = {}
    for n in [lab[:2] for lab in PG_TABS]:
        src = PG_SCREENS_SRC / f"tab-{n}.jpg"
        if src.is_file():
            (DOCS / PG_SCREENS_DIR).mkdir(parents=True, exist_ok=True)
            shutil.copy(src, DOCS / PG_SCREENS_DIR / src.name)
            out[n] = f"{PG_SCREENS_DIR}/{src.name}"
    return out


def pubg_body(kind: str) -> tuple[str, int]:
    """PUBG 전용: 01~06 내용을 HTML 에 모두 펼쳐 두고(JavaScript 없이도 읽힘) JS 가 선택한 탭만 남긴다.
    하위 탭(A1~C 데모) 전환, 시안 칸의 JS 조작판, 탭별 Streamlit 화면 캡처를 더한다. 오버워치 출력은 그대로."""
    from pubg_static_demos import PAGE_CSS, PAGE_JS, demos   # 정적 페이지용 JS 시연 (같은 newstart.json 값 사용)
    import streamlit
    # Streamlit 앱과 같은 본문 글꼴 (앱 패키지에 포함된 Source Sans 가변 글꼴 · SIL OFL)
    font = next((Path(streamlit.__file__).parent / "static" / "static" / "media").glob("SourceSansVF-Upright*.woff2"))
    (DOCS / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    shutil.copy(font, DOCS / "assets" / "fonts" / "SourceSansVF-Upright.woff2")
    shots = pubg_screens()
    labels = {lab[:2]: lab for lab in PG_TABS}

    def pane_extra(n: str) -> str:
        if n not in shots:
            return ""
        return (f'<details class="sx-exp pg-screen"><summary>이 탭의 Streamlit 원본 화면 캡처 (디자인 확인용 이미지) '
                f'<span class="sx-more">펼쳐보기</span></summary><div class="sx-exp-b"><a href="{shots[n]}" target="_blank" rel="noopener">'
                f'<img src="{shots[n]}" alt="Streamlit 원본 화면 · {H.escape(labels[n])}" loading="lazy"></a></div></details>')

    body, charts = tabbed_body("pubg", PG_TABS, "pg_tab", kind, demos(ROOT), all_visible=True, pane_extra=pane_extra)
    top = ""
    if shots:
        top = ('<div class="pg-shotlist"><b>디자인 확인용 원본 화면 캡처</b>' + "".join(
            f'<a href="{shots[n]}" target="_blank" rel="noopener">{H.escape(labels[n])}</a>' for n in labels if n in shots) + "</div>")
    note = ('<div class="sx-note">이 페이지는 JavaScript 없이도 01~06 탭 내용을 모두 HTML 글자로 담고 있습니다 '
            '(JavaScript 가 켜져 있으면 선택한 탭만 표시). 04 탭의 A1·A2·B2·C 데모는 이 페이지에서 직접 조작할 수 있고, B1 복귀 랜딩페이지 데모는 별도 페이지로 열립니다.</div>')
    # 2026-11-26 가독성: 상단 안내문·원본 캡처 링크 목록은 채용 담당자에게 불필요해 뺀다 (탭별 원본 캡처는 각 탭 끝 펼쳐보기에 그대로)
    return PAGE_CSS + '<div class="pg-static">' + body + "</div>" + PAGE_JS, charts


def fconline_body(kind: str) -> tuple[str, int]:
    """FC 온라인 (2026-11 개편 · 7탭): 오버워치와 같은 탭 전환 · 위젯 구역은 같은 계산식의 JavaScript 로 교체."""
    from fc_static_widgets import widgets as fc_widgets
    from ow_static_widgets import SUBTAB_JS
    body, charts = tabbed_body("fconline", FC_TABS, "fc_tab", kind, {})
    dm = fc_widgets(ROOT)
    body, n = re.subn(r'<div class="ox-js-start" data-demo="(\w+)"></div>.*?<div class="ox-js-end"></div>',
                      lambda m: dm[m.group(1)], body, flags=re.S)
    if n != len(dm):
        raise RuntimeError(f"FC 온라인 JS 위젯 교체 {n}/{len(dm)}개 · 표식 확인 필요")
    return body + SUBTAB_JS, charts


def dnf_body(kind: str) -> tuple[str, int]:
    """던전앤파이터 (2026-11-27 개편 · 7탭): FC 온라인과 같은 탭 전환 · 시뮬레이터·VOC 필터 구역은 같은 계산식의 JavaScript 로 교체."""
    from dnf_static_widgets import widgets as df_widgets
    from ow_static_widgets import SUBTAB_JS
    body, charts = tabbed_body("dnf", DF_TABS, "df_tab", kind, {})
    dm = df_widgets(ROOT)
    body, n = re.subn(r'<div class="ox-js-start" data-demo="(\w+)"></div>.*?<div class="ox-js-end"></div>',
                      lambda m: dm[m.group(1)], body, flags=re.S)
    if n != len(dm):
        raise RuntimeError(f"던파 JS 위젯 교체 {n}/{len(dm)}개 · 표식 확인 필요")
    return body + SUBTAB_JS, charts


def tabbed_body(pid: str, labels: list[str], tab_key: str, kind: str, extras: dict,
                all_visible: bool = False, pane_extra=None) -> tuple[str, int]:
    """6개 탭을 각각 실행해 모은 뒤, 탭 버튼 + 패널(선택한 1개만 표시) + JS 로 합친다.
    숨은 패널의 내용도 HTML 에 그대로 있어 글자만 읽는 도구는 모든 탭을 읽을 수 있다. 주소 #t04 로 바로 열 수 있다."""
    OW_TABS_ = labels
    prefix, panes, charts, tail = None, [], 0, None
    for i, label in enumerate(OW_TABS_):
        n = label[:2]
        ex = Exporter(kind, id_prefix=f"p{n}_")
        ex.tab_extras = extras if i == (2 if pid == "overwatch" else 3) else {}
        at = run_page(pid, tab=label, tab_key=tab_key)
        body = ex.children(at.main, 0)
        pre, mark, rest = body.partition('<div class="ow-pane-mark"')
        if not mark:
            raise RuntimeError(f"탭 {label}: 탭 경계 표식을 찾지 못함")
        pane = rest.split("</div>", 1)[1]
        if pid in ("overwatch", "fconline", "dnf"):   # 개편: 탭마다 반복되던 어시스턴트 안내·하단 고지는 페이지 끝에 한 번만
            pane, cut, tail_ = pane.partition('<div class="gp-xlinks"')
            if cut and tail is None:
                tail = cut + tail_
        prefix = prefix if prefix is not None else pre
        hide = "" if (i == 0 or all_visible) else " hidden"
        more = pane_extra(n) if pane_extra else ""
        panes.append(f'<section class="ow-pane" id="pane-{n}" role="tabpanel" aria-labelledby="tb-{n}" data-tab="{n}"{hide}>'
                     f'<h2 class="sx-pane-h">{H.escape(label)}</h2>{pane}{more}</section>')
        charts += ex.charts
    tabbar = ('<div class="ow-tabbar" role="tablist" aria-label="섹션">' + "".join(
        f'<button type="button" role="tab" id="tb-{lab[:2]}" aria-controls="pane-{lab[:2]}" data-tab="{lab[:2]}" '
        f'aria-selected="{"true" if j == 0 else "false"}"><b>{lab[:2]}</b>{H.escape(lab[3:])}</button>'
        for j, lab in enumerate(OW_TABS_)) + "</div>")
    return prefix.replace("<!--OW_TABBAR-->", tabbar) + "".join(panes) + (tail or "") + TAB_JS, charts


def save_images(doc: str) -> str:
    """data URI 이미지를 파일로 분리 (같은 이미지는 한 번만 저장) · 앱 전용 링크(?page=x&tab=NN)는 정적 파일 링크로 바꾼다."""
    doc = re.sub(r'href="\?page=(\w+)(?:&(?:amp;)?tab=\d+)?"', lambda m: f'href="{m.group(1)}.html"', doc)
    def repl(m):
        ext = "jpg" if m.group(1) in ("jpeg", "jpg") else m.group(1)
        raw = base64.b64decode(m.group(2))
        name = hashlib.sha1(raw).hexdigest()[:16] + "." + ext
        p = IMG_DIR / name
        if not p.exists():
            p.write_bytes(raw)
        return f"assets/img/{name}"
    return re.sub(r"data:image/(jpeg|jpg|png);base64,([A-Za-z0-9+/=]+)", repl, doc)


STATIC_CSS = """
body { margin: 0; background: #fff; color: #0B1F3A; }
.sx-top { position: sticky; top: 0; z-index: 10; background: #0B1F3A; color: #E8EEF9; }
.sx-top-in { max-width: 1240px; margin: 0 auto; padding: 0.6rem 16px; display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; align-items: center; }
.sx-top .gp-brand { font-size: 1.15rem; margin: 0; color: #fff; }
.sx-top .gp-brand a { color: inherit; text-decoration: none; }
.sx-top nav { display: flex; flex-wrap: wrap; gap: 0.25rem; }
.sx-top nav a { color: #C9D6EE; text-decoration: none; font-size: 0.85rem; padding: 0.25rem 0.55rem; border-radius: 6px; }
.sx-top nav a.on, .sx-top nav a:hover { background: rgba(255,255,255,0.12); color: #fff; }
.sx-main { max-width: 1240px; margin: 0 auto; padding: 1.2rem 16px 3rem; }
.sx-note { background: #FFF8EC; border: 1px solid #F5D6A8; border-radius: 12px; padding: 0.75rem 1rem; font-size: 0.9rem; line-height: 1.6; margin-bottom: 0.8rem; }
.sx-note a { color: #1E5EFF; }
.sx-live { background: #EEF4FF; border: 2px solid #1E5EFF; border-radius: 12px; padding: 0.85rem 1rem; font-size: 0.95rem; line-height: 1.6; margin: 0 0 1rem; }
.sx-live a { color: #1E5EFF; font-weight: 800; }
.sx-legend { display: flex; flex-wrap: wrap; gap: 0.4rem 0.9rem; align-items: center; font-size: 0.85rem; color: #3A4A63; margin: 0 0 1rem; }
.sx-toc { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0 0 1.2rem; padding: 0.7rem; background: #F4F7FC; border-radius: 12px; }
.sx-toc b { width: 100%; font-size: 0.8rem; color: #6B7A90; }
.sx-toc a { background: #fff; border: 1px solid #DDE4EF; border-radius: 8px; padding: 0.35rem 0.7rem; color: #0B1F3A; text-decoration: none; font-weight: 700; font-size: 0.9rem; }
.sx-tabnav { display: flex; flex-wrap: wrap; gap: 0.3rem; border-bottom: 2px solid #DDE4EF; margin: 0.6rem 0 0.8rem; padding-bottom: 0.4rem; }
.sx-tabnav a { font-size: 0.85rem; color: #1E5EFF; text-decoration: none; padding: 0.2rem 0.5rem; border-radius: 6px; background: #F4F7FC; }
.sx-tab { scroll-margin-top: 4rem; margin-bottom: 2rem; }
.sx-tab-h { font-size: 1.45rem; margin: 1.4rem 0 0.6rem; padding-bottom: 0.35rem; border-bottom: 3px solid #1E5EFF; }
.sx-tabs.d1 > .sx-tab > .sx-tab-h, .sx-tabs.d2 > .sx-tab > .sx-tab-h { font-size: 1.15rem; border-bottom-width: 2px; border-color: #8DB3FF; }
.sx-tab-h span { font-size: 0.7rem; font-weight: 800; color: #fff; background: #1E5EFF; border-radius: 6px; padding: 0.1rem 0.4rem; margin-right: 0.5rem; vertical-align: middle; }
.sx-exp { border: 1px solid #DDE4EF; border-radius: 12px; margin: 0.6rem 0 1rem; background: #fff; }
.sx-exp > summary { cursor: pointer; padding: 0.7rem 1rem; font-weight: 700; color: #0B1F3A; }
.sx-more { display: inline-block; margin-left: 0.4rem; font-size: 0.75rem; font-weight: 700; color: #1E5EFF; background: #EAF1FF;
  border-radius: 999px; padding: 0.05rem 0.5rem; vertical-align: middle; }
details[open] > summary .sx-more { display: none; }
.sx-exp-b { padding: 0 1rem 0.8rem; }
.sx-row { display: flex; flex-wrap: wrap; gap: 1rem; margin: 0.3rem 0; }
.sx-col { min-width: 0; }
.sx-md p { line-height: 1.65; margin: 0.4rem 0; } .sx-md li { line-height: 1.6; margin-bottom: 0.2rem; }
.sx-md code { background: #F4F7FC; padding: 0 0.3rem; border-radius: 4px; font-size: 0.85em; }
.sx-md a, .sx-cap a, .gp-table a { color: #1E5EFF; overflow-wrap: anywhere; }
.sx-cap { font-size: 0.85rem; color: #6B7A90; margin: 0.3rem 0 0.8rem; line-height: 1.55; }
.sx-alert { border-radius: 10px; padding: 0.7rem 0.9rem; margin: 0.5rem 0; font-size: 0.92rem; line-height: 1.55; }
.sx-alert.info { background: #EAF1FF; color: #1B3358; } .sx-alert.warning { background: #FFF6E0; color: #7A4B00; }
.sx-alert.success { background: #E8F7EE; color: #14532D; } .sx-alert.error, .sx-alert.exception { background: #FDECEC; color: #7F1D1D; }
.sx-metric { border: 1px solid #DDE4EF; border-radius: 12px; padding: 0.7rem 0.9rem; margin: 0.3rem 0; }
.sx-metric-l { font-size: 0.82rem; color: #6B7A90; } .sx-metric-v { font-size: 1.6rem; font-weight: 800; } .sx-metric-d { font-size: 0.82rem; color: #1E5EFF; }
.sx-chart { margin: 0.6rem 0 1.2rem; border: 1px solid #DDE4EF; border-radius: 12px; padding: 0.6rem 0.6rem 0.4rem; background: #fff; }
.sx-chart-h { font-weight: 700; font-size: 0.95rem; padding: 0.1rem 0.3rem 0.4rem; }
.sx-chart-c { width: 100%; }
.sx-chart.bare { border: 0; padding: 0; margin: 0.3rem 0 0.6rem; }
.sx-pane-h { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.ow-pane[hidden] { display: none !important; }
.sx-box { border: 1px solid #E2E8F0; border-radius: 12px; padding: 0.9rem 0.9rem 0.7rem; margin: 0.6rem 0 1.2rem; background: #fff; max-width: 940px; }
.sx-top { background: #FFFFFF !important; color: #142B4D !important; border-bottom: 1px solid #E2E8F0; }
.sx-top .gp-brand, .sx-top .gp-brand a { color: #142B4D !important; } .sx-top .gp-brand span { color: #2563EB !important; }
.sx-top nav a { color: #475569 !important; } .sx-top nav a.on, .sx-top nav a:hover { background: #EFF6FF !important; color: #2563EB !important; }
.sx-note { background: transparent !important; border: 0 !important; padding: 0 !important; font-size: 0.76rem !important; color: #94A3B8 !important; margin-bottom: 0.4rem !important; }
.sx-note b { color: #64748B; font-weight: 600; }
body { background: #FFFFFF; }
.sx-box > div > .sx-md, .sx-box .sx-chart.bare { margin: 0; }
html { scroll-behavior: smooth; }
.ow-sec, .ow-nav { scroll-margin-top: 4.5rem; }
.sx-chartdata > summary { cursor: pointer; font-size: 0.82rem; color: #6B7A90; padding: 0.3rem; }
.sx-df { max-height: 520px; overflow: auto; }
.sx-w { display: flex; flex-wrap: wrap; gap: 0.3rem 0.6rem; align-items: center; margin: 0.35rem 0; font-size: 0.88rem; }
.sx-w-l { color: #6B7A90; font-weight: 600; }
.sx-w-v, .sx-w-o span.on { background: #EAF1FF; color: #0B1F3A; border: 1px solid #B9CFFF; border-radius: 6px; padding: 0.1rem 0.5rem; font-weight: 700; }
.sx-w-o { display: inline-flex; flex-wrap: wrap; gap: 0.25rem; }
.sx-w-o span { border: 1px solid #DDE4EF; border-radius: 6px; padding: 0.1rem 0.5rem; color: #3A4A63; }
.sx-w-in { border: 1px solid #DDE4EF; border-radius: 6px; padding: 0.15rem 0.6rem; color: #9AA6B8; min-width: 10rem; }
.sx-btn { display: inline-block; margin: 0.25rem 0.35rem 0.25rem 0; border: 1px solid #C9D3E3; border-radius: 8px; padding: 0.35rem 0.8rem; font-size: 0.88rem; font-weight: 600; color: #0B1F3A; background: #fff; }
button.sx-btn { font-family: inherit; line-height: inherit; text-align: left; cursor: pointer; } a.sx-btn { text-decoration: none; cursor: pointer; }
button.sx-btn:hover, a.sx-btn:hover { border-color: #0B1F3A; background: #F4F7FC; }
#sx-answers { border-top: 1px solid #DDE4EF; margin-top: 0.8rem; padding-top: 0.4rem; } .sx-ans { border-bottom: 1px solid #EEF2F7; padding: 0.4rem 0 0.6rem; scroll-margin-top: 80px; }
.sx-foot { max-width: 1240px; margin: 0 auto; padding: 1rem 16px 2rem; font-size: 0.8rem; color: #6B7A90; border-top: 1px solid #DDE4EF; }
.sx-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 0.9rem; margin: 0.8rem 0 1.4rem; }
.sx-card { display: block; border: 1px solid #DDE4EF; border-radius: 14px; padding: 1rem 1.1rem; color: #0B1F3A; text-decoration: none; background: #fff; }
.sx-card:hover { border-color: #1E5EFF; }
.sx-card.feature { grid-column: 1 / -1; background: linear-gradient(135deg, #0B1F3A 0%, #1B3358 60%, #1E5EFF 140%); color: #fff; border: 0; }
.sx-card.feature p { color: #D6E2FA; }
.sx-card h3 { margin: 0 0 0.3rem; font-size: 1.1rem; color: inherit; } .sx-card p { margin: 0; font-size: 0.9rem; line-height: 1.55; color: #3A4A63; }
.sx-card .k { font-size: 0.75rem; font-weight: 800; color: #F99E1A; letter-spacing: 0.04em; }
.sx-ul { line-height: 1.7; padding-left: 1.2rem; }
@media (max-width: 640px) {
  .sx-top-in { padding: 0.45rem 12px; }
  .sx-top nav { flex-wrap: nowrap; overflow-x: auto; -webkit-overflow-scrolling: touch; width: 100%; padding-bottom: 0.15rem; }
  .sx-top nav a { white-space: nowrap; font-size: 0.8rem; }
  .sx-note { font-size: 0.82rem; padding: 0.5rem 0.7rem; }
  .sx-row { flex-direction: column; } .sx-col { flex: 1 1 auto !important; width: 100%; }
  .sx-tab-h { font-size: 1.2rem; }
}
"""


def legend() -> str:
    return ('<div class="sx-legend"><b>배지 뜻</b>'
            f'{badge("실제 자료", "k-real")} 공개 출처·직접 캡처로 확인'
            f'{badge("분석자 해석", "k-interp")} 자료를 바탕으로 한 판단'
            f'{badge("검증 전 가설", "k-hypo")} 아직 입증되지 않음'
            f'{badge("기획 시안", "k-mock")} 게임에 없는 제안·계획'
            f'{badge("가정 시뮬레이션", "k-sim")} 가정값으로 계산 (실적 아님)'
            f'{badge("예시 데이터", "k-sample")} 시연용 가상 데이터</div>')


def page_html(title: str, desc: str, current: str, body: str, toc: list, charts: bool, gen: str) -> str:
    nav = "".join(f'<a class="{"on" if f == current else ""}" href="{f}">{H.escape(n)}</a>'
                  for _, f, n, _ in [("index", "index.html", "보고서 첫 화면", "")]
                  + sorted(PAGES, key=lambda p: p[0] != "home"))   # 메뉴 순서: 홈 → 4개 게임 → 사업PM 어시스턴트
    toc_html = ("" if not toc else '<nav class="sx-toc"><b>이 페이지 목차</b>'
                + "".join(f'<a href="#{i}">{H.escape(l)}</a>' for i, l in toc) + "</nav>")
    own_legend = current in ("overwatch.html", "pubg.html", "fconline.html", "dnf.html")   # 탭형 프로젝트는 앱이 배지 설명을 직접 표시
    note = ("" if current == "index.html" else
            f'<div class="sx-note"><b>정적 보고서</b> · <a href="{LIVE_URL}">원본 앱</a> 스냅샷 ({gen}) · '
            + (("01~07" if current in ("overwatch.html", "fconline.html") else "01~06") + " 탭으로 섹션 전환 · " if own_legend else "")
            + '버튼·슬라이더는 기본값 · 차트 수치는 "차트 데이터 표"에</div>')
    # 접힌 펼치기 안의 차트는 숨은 상태로 그려지므로, 펼칠 때 너비를 다시 맞춘다
    resize = ("<script>document.addEventListener('toggle',function(e){var d=e.target;if(d.tagName==='DETAILS'&&d.open&&window.Plotly){"
              "d.querySelectorAll('.sx-chart-c').forEach(function(c){Plotly.Plots.resize(c);});}},true);</script>")
    script = f'<script src="assets/plotly.min.js"></script>{resize}' if charts else ""
    return (f'<!doctype html><html lang="ko" translate="no"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{H.escape(title)} · {APP_NAME}</title><meta name="description" content="{H.escape(desc)}">'
            f'{APP_CSS}<style>{STATIC_CSS}</style>{script}</head><body>'
            f'<header class="sx-top"><div class="sx-top-in"><div class="gp-brand"><a href="index.html">Game<span>Pulse</span> AI</a></div>'
            f'<nav>{nav}</nav></div></header><main class="sx-main">{note}'
            f'{legend() if current not in ("index.html", "overwatch.html", "pubg.html", "fconline.html", "dnf.html") else ""}{toc_html}{body}</main>'
            f'<footer class="sx-foot">{APP_NAME} 정적 보고서 · 생성 {gen} · <a href="{LIVE_URL}">원본 앱</a> · '
            f'<a href="{REPO_URL}">GitHub 저장소</a> · 언급된 게임 및 상표는 각 권리자에게 있으며, 본 보고서는 해당 게임사와 관련이 없는 개인 분석물입니다.</footer>'
            '</body></html>')


def index_html(gen: str) -> str:
    rs = json.loads((ROOT / "data" / "overwatch" / "restart.json").read_text(encoding="utf-8"))
    cards = [f'<a class="sx-card feature" href="overwatch.html"><div class="k">대표 프로젝트 · 실제 자료 기반</div>'
             f'<h3>오버워치 · PROJECT RE:START</h3><p><b>{H.escape(rs["summary"]["headline"])}</b> — '
             f'{H.escape(rs["cover"]["solution_sub"])}. 최신 한국어 게임 화면, 검증한 유저 의견 {OW_VERIFIED}건, 공식 업데이트·이용 지표를 근거로 '
             '개선안 A·B·C, 단계적 A/B 테스트, 가정 시뮬레이션까지 하나의 가정값으로 연결했습니다.</p></a>',
             '<a class="sx-card feature" href="pubg.html"><div class="k">두 번째 프로젝트 · 실제 자료 기반</div>'
             '<h3>PUBG · NEW START</h3><p><b>첫 치킨을 맛보기도 전에 떠나는 유저들. 그리고 돌아오지 않는 전우들.</b> — 신규 유저 정착(A 50%) · '
             '휴면 유저 복귀(B 40%) · BM 신뢰·수익성(C 10%). 공식 자료와 Steam 리뷰(신규 45건 · 복귀 21건, 별도 표본)를 근거로 '
             '다음 경기 코치(NEXT MATCH COACH) 데모, 복귀 캠페인 «야, 배그 한 판 할래?» 광고 3종과 클릭 가능한 랜딩페이지, A/B 테스트 설계를 만들었습니다.</p></a>']
    cards.append('<a class="sx-card feature" href="fconline.html"><div class="k">세 번째 프로젝트 · 실제 자료 기반</div>'
                 '<h3>FC 온라인 · 축구 게임인가, 주식 게임인가?</h3><p><b>구단 가치 하락에 따른 이탈은 막고, 축구 팬덤으로 새 고객을 데려온다</b> — '
                 'CLUB CARE · CLUB REBUILD (이탈 방지) · MY CLUB WAR «답답해서 내가 뛴다» (유럽 인기 구단 16개 가상 팬덤 챔피언십 · 우승 구단 홈경기 직관) · '
                 'FAIR PLAY (키보드·패드 경쟁 환경). 공식 배너·작성자 캡처·UEFA 등록 명단·VOC 50건을 근거로 했습니다.</p></a>')
    dn = json.loads((ROOT / "data" / "dnf" / "dnf.json").read_text(encoding="utf-8"))
    cards.append('<a class="sx-card feature" href="dnf.html"><div class="k">네 번째 프로젝트 · 실제 자료 기반</div>'
                 f'<h3>던전앤파이터 · 노력은 남고, 성취는 이어져야 한다</h3><p><b>어려운 콘텐츠를 깨도 운에 갈리는 보상 · 다음 시즌으로 이어지는 성취</b> — '
                 '공식 공지·가이드, 10/27 D-Note Live 보도, 공개 VOC 130건(유튜브·공식 게시판·인벤·디시), 현역 이용자 인터뷰를 근거로 '
                 'PROJECT ACHIEVEMENT(50%) · SEASON LEGACY(30%) · DNF RE:TRUST(20%)와 누적 보장 보상 시뮬레이터를 만들었습니다.</p></a>')
    for pid, f, name, _ in PAGES[4:]:
        one = GAMES[pid].get("one_liner", "") if pid in GAMES else {
            "home": "프로젝트 소개 · 4개 게임 핵심 문제 · 사업PM 어시스턴트 바로가기",
            "assistant": "포트폴리오 기반 검색형 PM 어시스턴트 (생성형 AI 아님) · 정적 화면은 게임별 자주 묻는 질문 답변 · 직접 질문은 원본 앱"}.get(pid, "")
        tag = "예시 데이터 기반 분석" if pid in GAMES else "도구 화면"
        cards.append(f'<a class="sx-card" href="{f}"><div class="k">{tag}</div><h3>{H.escape(name)}</h3><p>{H.escape(one)}</p></a>')
    body = (f'<div class="gp-hero"><div class="gp-eyebrow">Static Report for Reviewers</div><h1>{APP_NAME} 포트폴리오 보고서</h1>'
            f'<p>{H.escape(APP_TAGLINE)}</p></div>'
            '<h2>검토자 안내</h2><ul class="sx-ul">'
            f'<li>이 보고서는 <a href="{LIVE_URL}">원본 Streamlit 앱</a>을 자동 변환한 정적 HTML입니다. JavaScript 없이도 모든 글자를 읽을 수 있습니다.</li>'
            '<li><b>오버워치 · PUBG · FC 온라인 · 던전앤파이터</b> 4개 페이지가 실제 자료 기반 분석입니다. 사업PM 어시스턴트의 정적 화면은 자주 묻는 질문 답변을 미리 담았고, 직접 질문은 <a href="' + LIVE_URL + '?page=assistant">원본 앱</a>에서 할 수 있습니다.</li>'
            '<li>각 수치·차트에 출처 성격을 배지로 표시했습니다. 아래 배지 뜻을 참고하세요.</li>'
            '<li>게임 스크린샷은 작성자가 직접 캡처한 최신 한국어 화면이며, 다른 플레이어 닉네임은 가림 처리했습니다.</li>'
            f'<li>생성 시각 {gen} · 코드: <a href="{REPO_URL}">GitHub 저장소</a></li></ul>'
            f'{legend()}<h2>페이지</h2><div class="sx-cards">{"".join(cards)}</div>')
    return page_html("보고서 첫 화면", f"{APP_NAME} 게임 사업PM 포트폴리오 정적 보고서", "index.html", body, [], False, gen)


# ----------------------------------------------------------------------
PII = re.compile(r"[A-Za-z0-9._%+-]+@(gmail|naver|daum|kakao|hanmail|outlook|hotmail)\.|C:\\\\Users|010-?\d{4}-?\d{4}|sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}", re.I)


def check(files: list[Path]) -> list[str]:
    problems = []
    for f in files:
        s = f.read_text(encoding="utf-8")
        if "data:image" in s:
            problems.append(f"{f.name}: 분리되지 않은 이미지")
        for src in re.findall(r'src="(assets/[^"]+)"', s):
            if not (DOCS / src).exists():
                problems.append(f"{f.name}: 없는 파일 {src}")
        for href in re.findall(r'href="([a-z_]+\.html)(?:#[^"]*)?"', s):
            if not (DOCS / href).exists():
                problems.append(f"{f.name}: 깨진 링크 {href}")
        m = PII.search(s)
        if m:
            problems.append(f"{f.name}: 개인정보·키 의심 문자열 '{m.group(0)}'")
        if "미지원 요소" in s:
            problems.append(f"{f.name}: 변환하지 못한 요소 {re.findall(r'미지원 요소: ([a-z_]+)', s)}")
        heads = [re.sub(r"<[^>]+>", "", h).strip() for h in re.findall(r"<th[^>]*>(.*?)</th>", s, flags=re.S)]
        tech = [h for h in heads if h in ("계열", "x", "y", "value", "category", "ID")]
        if tech:
            problems.append(f"{f.name}: 기술 변수명 열 제목 {sorted(set(tech))}")
        if f.name == "overwatch.html":  # RE:START 단일 프로젝트 · 과거(v0.1) 분석이 공개 본문에 다시 들어오면 실패
            for k in LEGACY_OW:
                if k in s:
                    problems.append(f"{f.name}: 과거 분석 문구 '{k}' 노출")
        if f.name == "pubg.html":       # NEW START 단일 프로젝트 · v0.1 예시 분석이 섞이면 실패
            for k in LEGACY_PG:
                if k in s:
                    problems.append(f"{f.name}: 과거 예시 분석 문구 '{k}' 노출")
    return problems


LEGACY_PG = ["첫 5판", "파티 유형", "신규 보호 장치", "조기 탈락·학습 불가", "솔로 vs 스쿼드", "숙련자–신규 이용자"]
LEGACY_OW = ["보호 매칭", "역할별 잔존", "그룹 플레이", "North Star", "v0.1", "부록", "보관함", "18%→22%", "18% → 22%",
             "주력 역할별", "전략 우선순위 매트릭스", "불만 유형 분포 (예시"]


def main() -> int:
    gen = dt.datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    if DOCS.exists():
        shutil.rmtree(DOCS)
    IMG_DIR.mkdir(parents=True)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    from plotly.offline import get_plotlyjs

    (DOCS / "assets" / "plotly.min.js").write_text(get_plotlyjs(), encoding="utf-8")

    written = []
    for pid, fname, name, kind in PAGES:
        if pid in ("overwatch", "pubg", "fconline", "dnf"):
            body, n_charts = {"overwatch": overwatch_body, "pubg": pubg_body, "fconline": fconline_body, "dnf": dnf_body}[pid](kind)
            from gamepulse.ui.theme import recolor_scripts
            body = recolor_scripts(body, pid)   # JavaScript 데모·차트의 기본 파랑 → 게임 테마 색
            desc = {"overwatch": GAMES[pid].get("theme", name), "pubg": "신규 유저 정착과 휴면 유저 재활성화 전략",
                    "fconline": "구단 가치 하락에 따른 이탈 방지 · 축구 팬덤 마케팅 · 키보드·패드 경쟁 환경",
                    "dnf": "노력은 남고, 성취는 이어져야 한다 · 성취감 · 시즌 기대 · 운영 소통"}[pid]
            doc = save_images(page_html(name, desc, fname, body, [], n_charts > 0, gen))
            (DOCS / fname).write_text(doc, encoding="utf-8")
            written.append(DOCS / fname)
            print(f"  {fname:18} 차트 {n_charts:2} · {len(doc) / 1024:,.0f} KB · 탭 {doc.count('role="tab"')}개")
            continue
        ex = Exporter(kind)
        at = run_page(pid)
        body = ex.children(at.main, 0)
        if pid == "assistant":     # 정적 화면: 추천 질문 버튼마다 앱의 실제 답변을 담아 두고 누르면 표시 (직접 질문은 원본 앱)
            box, acts = assistant_answers(kind, at)
            body = (f'<div class="sx-live"><b>직접 질문하기</b> · GitHub Pages는 정적 화면이라 질문 입력이 동작하지 않습니다 → '
                    f'<a href="{LIVE_URL}?page=assistant">Streamlit 원본 앱에서 질문하기 ↗</a> · 추천 질문 버튼을 누르면 원본 앱과 같은 검색 답변이 아래에 표시됩니다.</div>') + body + box
            btn_check(body, acts, "assistant")
            body += btn_script(acts)
        elif "data-btn=" in body:
            btn_check(body, {}, pid)
        desc = GAMES[pid].get("one_liner", name) if pid in GAMES else name
        toc = ex.toc
        doc = save_images(page_html(name, desc, fname, body, toc, ex.charts > 0, gen))
        (DOCS / fname).write_text(doc, encoding="utf-8")
        written.append(DOCS / fname)
        print(f"  {fname:18} 차트 {ex.charts:2} · {len(doc) / 1024:,.0f} KB")
        if pid == "overwatch":
            label = {"real": "실제 자료", "sim": "가정 시뮬레이션", "plan": "기획자 평가", "sample": "예시 데이터"}
            for k, t in ex.kinds:
                print(f"      [{label[k]}] {t}")
    from pubg_return_landing import build as build_landing   # B1 복귀 랜딩페이지 데모 (docs/pubg-return.html)
    written.append(build_landing(ROOT, DOCS))
    print("  pubg-return.html   B1 복귀 랜딩페이지 데모")
    (DOCS / "index.html").write_text(index_html(gen), encoding="utf-8")
    written.append(DOCS / "index.html")

    imgs = list(IMG_DIR.iterdir())
    print(f"  이미지 {len(imgs)}개 · {sum(p.stat().st_size for p in imgs) / 1e6:.1f} MB")
    problems = check(written)
    if problems:
        print("[점검 실패]")
        for p in problems:
            print("  -", p)
        return 1
    print(f"[점검 통과] {len(written)}개 페이지 → {DOCS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
