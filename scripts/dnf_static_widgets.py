"""정적 보고서(GitHub Pages)용 던파 시뮬레이터 2종 — gamepulse/sim/dnf_biz.py 와 같은 식 · gamepulse/views/dnf.py 의 결과 마크업과 같다.

dfreward : PROJECT ACHIEVEMENT 누적 보장 보상 (동적 계획법)
dfgold   : ARAD CARE 수리 지원 · 순골드 공급
"""

from __future__ import annotations

import json
from pathlib import Path

from fc_static_widgets import _inputs, _j, _wire

FMT = ("function n0(x){return Math.round(x).toLocaleString('en-US');}function f1(x){return x.toLocaleString('en-US',{minimumFractionDigits:1,maximumFractionDigits:1});}"
       "function f2(x){return x.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});}"
       "function gold(x){var a=Math.abs(x),s=x<0?'−':(x>0?'+':'');return s+(a>=1e8?f2(a/1e8)+'억':n0(a/1e4)+'만')+' 골드';}"
       "function goldu(x){var a=Math.abs(x),s=x<0?'−':'';return s+(a>=1e8?f2(a/1e8)+'억':n0(a/1e4)+'만')+' 골드';}")


def reward(d: dict) -> str:
    cfg = d["sims"]["reward"]
    return (f'<div class="ox-w" id="dfRw"><div id="dfRwRes"></div>{_inputs("dr", cfg)}</div><script>(function(){{{FMT}{_wire("dfRw", cfg)}'
            "function dist(n,p,k,s,st){var cap=k>0?k:n+1,pm=new Array(cap).fill(0),e1=new Array(cap).fill(0),e2=new Array(cap).fill(0);pm[0]=1;"
            "function pr(j){var q=p+((s>0&&j>=s-1)?(j-s+1)*st:0);return (k>0&&j===k-1)?1:Math.min(Math.max(q,0),1);}"
            "for(var t=0;t<n;t++){var a=new Array(cap).fill(0),b=new Array(cap).fill(0),c=new Array(cap).fill(0);for(var j=0;j<cap;j++){if(pm[j]===0)continue;var q=pr(j);"
            "a[0]+=pm[j]*q;b[0]+=(e1[j]+pm[j])*q;c[0]+=(e2[j]+2*e1[j]+pm[j])*q;if(j+1<cap){a[j+1]+=pm[j]*(1-q);b[j+1]+=e1[j]*(1-q);c[j+1]+=e2[j]*(1-q);}}pm=a;e1=b;e2=c;}"
            "var m=e1.reduce(function(x,y){return x+y;},0),v=Math.max(e2.reduce(function(x,y){return x+y;},0)-m*m,0),z=1;for(var i=0;i<n;i++)z*=(1-pr(i));return [m,v,z];}"
            "function sim(x0){var x=clamp(x0),n=Math.round(x.n),k=Math.round(x.k),s=Math.round(x.s),p=x.p/100,st=x.step/100,b=dist(n,p,0,0,0),w=dist(n,p,k,s,st),q=x.qty,u=x.users;"
            "var s0=b[0]*q*u,s1=w[0]*q*u;return {x:x,base:{mean:b[0]*q,sd:Math.sqrt(b[1])*q,zero:b[2]*100,supply:s0},nw:{mean:w[0]*q,sd:Math.sqrt(w[1])*q,zero:w[2]*100,supply:s1},"
            "zero_users:w[2]*u,zero_users0:b[2]*u,supply_pct:s0>0?(s1/s0-1)*100:null};}"
            "function draw(){var r=sim(cur()),B=r.base,N=r.nw,sp=r.supply_pct===null?'—':(r.supply_pct>=0?'+':'−')+f1(Math.abs(r.supply_pct))+'%';"
            "document.getElementById('dfRwRes').innerHTML='<div class=\"ox-res\"><div class=\"acc\"><span>한 번도 못 얻을 확률</span><b>'+f2(B.zero)+'% → '+f2(N.zero)+'%</b><small>참여 '+n0(r.x.users)+'명 중 '+n0(r.zero_users0)+'명 → '+n0(r.zero_users)+'명</small></div>'"
            "+'<div><span>1인 평균 획득</span><b>'+f2(B.mean)+' → '+f2(N.mean)+'개</b><small>'+n0(r.x.n)+'회 플레이 기준</small></div>'"
            "+'<div><span>획득 편차 (표준편차)</span><b>'+f2(B.sd)+' → '+f2(N.sd)+'</b><small>작을수록 운 차이가 작음</small></div>'"
            "+'<div class=\"'+(r.supply_pct!==null&&r.supply_pct>5?'neg':'')+'\"><span>보상 공급 증가</span><b>'+sp+'</b><small>총 '+n0(B.supply)+' → '+n0(N.supply)+'개 · 가드레일 +5%</small></div></div>'"
            "+'<div class=\"df2-bars\"><div><span>현행 (확률만)</span><i style=\"width:'+Math.min(B.zero,100).toFixed(1)+'%\"></i><b>'+f2(B.zero)+'%</b></div><div class=\"n\"><span>제안 (누적 보장)</span><i style=\"width:'+Math.min(N.zero,100).toFixed(1)+'%\"></i><b>'+f2(N.zero)+'%</b></div><small>막대 = 한 번도 못 얻는 유저 비율</small></div>';}"
            "window.dfReward=sim;setv(C.d);draw();})();</script>")


def gold(d: dict) -> str:
    cfg = d["sims"]["gold"]
    return (f'<div class="ox-w" id="dfGd"><div id="dfGdRes"></div>{_inputs("dg", cfg)}</div><script>(function(){{{FMT}{_wire("dfGd", cfg)}'
            "function sim(x0){var x=clamp(x0),r0=x.chars*x.rep,sv=Math.min(r0*x.rate/100,x.cap),r1=r0-sv,act=x.users*x.util/100,g=x.grow/100,"
            "dr=act*sv,pr=act*x.prod*g,rc=act*r1*g,net=dr+pr-rc,base=act*x.prod;return {x:x,r0:r0,r1:r1,save:sv,save_m:sv*4,act:act,drop:dr,prod:pr,rec:rc,net:net,net_pct:base>0?net/base*100:null};}"
            "function draw(){var r=sim(cur()),np=r.net_pct===null?'—':(r.net_pct>=0?'+':'−')+f1(Math.abs(r.net_pct))+'%';"
            "document.getElementById('dfGdRes').innerHTML='<div class=\"ox-res\"><div><span>계정 주간 수리비</span><b>'+goldu(r.r0)+' → '+goldu(r.r1)+'</b><small>캐릭터 '+n0(r.x.chars)+'개</small></div>'"
            "+'<div class=\"acc\"><span>계정당 절감</span><b>주 '+goldu(r.save)+'</b><small>4주 '+goldu(r.save_m)+' · 상한 '+goldu(r.x.cap)+'</small></div>'"
            "+'<div><span>서버 골드 회수 감소 (주)</span><b>'+goldu(r.drop)+'</b><small>이용 계정 '+n0(r.act)+'개</small></div>'"
            "+'<div class=\"'+(r.net_pct!==null&&r.net_pct>5?'neg':'')+'\"><span>순골드 공급 변화 (주)</span><b>'+gold(r.net)+'</b><small>기존 생산 대비 '+np+' · 가드레일 +5%</small></div></div>'"
            "+'<div class=\"df2-flow\"><span>회수 감소 '+goldu(r.drop)+'</span><i>+</i><span>추가 생산 '+goldu(r.prod)+'</span><i>−</i><span>추가 회수 '+goldu(r.rec)+'</span><i>=</i><b>'+gold(r.net)+'</b></div>';}"
            "window.dfGold=sim;setv(C.d);draw();})();</script>")


def voc(root: Path) -> str:
    """VOC 전체 목록 + 채널·주제·성향 필터 (views/dnf.py t3 와 같은 표 · 필터는 JS)."""
    import html as H
    from collections import Counter
    v = json.loads((root / "data" / "dnf" / "voc.json").read_text(encoding="utf-8"))
    cats, srcs = v["categories"], v["sources"]
    items = [x for x in v["items"] if x["channel"] != "지인 인터뷰"]
    names = [cats[str(c)] for c, _ in Counter(x["cat"] for x in items).most_common()]
    chs = ["유튜브 댓글", "공식 게시판", "인벤", "디시 던파IP 갤러리"]

    def sel(i, lab, opts):
        return f'<label class="ox-f"><span>{lab}</span><select id="{i}">' + "".join(f"<option>{H.escape(o)}</option>" for o in ["전체"] + opts) + "</select></label>"

    def link(x):
        t, u = srcs[x["src"]][0], srcs[x["src"]][1]
        return f'<a href="{H.escape(u, quote=True)}" target="_blank" rel="noopener">{H.escape(t[:40])}</a>' if u else H.escape(t)
    rows = "".join(
        f'<tr data-h="{H.escape(x["channel"], quote=True)}" data-c="{H.escape(cats[str(x["cat"])], quote=True)}" data-t="{H.escape(x["stance"], quote=True)}">'
        f'<td data-label="번호">{x["id"]}</td><td data-label="채널 · 날짜">{H.escape(x["channel"])}<br><small>{H.escape(x["date"])}</small></td>'
        f'<td data-label="출처">{link(x)}</td><td data-label="요약">{H.escape(x["summary"])}</td><td data-label="주제">{H.escape(cats[str(x["cat"])])}</td>'
        f'<td data-label="성향">{H.escape(x["stance"])}</td></tr>' for x in items)
    return (f'<div class="ox-w" id="dfVoc"><div class="ox-fields three">{sel("dfVh", "채널", chs)}{sel("dfVc", "주제", names)}'
            f'{sel("dfVt", "성향", ["부정", "질문", "제안", "중립", "긍정"])}</div><p class="ox-note" id="dfVn"></p>'
            '<div class="gp-table-wrap ox-scroll"><table class="gp-table ow-table ox-mops fx-voc"><tr><th>번호</th><th>채널 · 날짜</th><th>출처</th><th>요약</th><th>주제</th><th>성향</th></tr>'
            f'{rows}</table></div></div>'
            "<script>(function(){var A=document.getElementById('dfVh'),C=document.getElementById('dfVc'),T=document.getElementById('dfVt'),tr=document.querySelectorAll('#dfVoc tr[data-c]');"
            "function m(s,v){return s.value==='전체'||v===s.value;}function f(){var n=0;tr.forEach(function(t){var ok=m(A,t.dataset.h)&&m(C,t.dataset.c)&&m(T,t.dataset.t);t.hidden=!ok;if(ok)n++;});"
            "document.getElementById('dfVn').textContent=n?(n+'건 표시 · 전체 '+tr.length+'건 · 출처를 누르면 원문'):'조건에 맞는 VOC가 없습니다';}"
            "[A,C,T].forEach(function(e){e.addEventListener('change',f);});f();})();</script>")


def widgets(root: Path) -> dict[str, str]:
    d = json.loads((root / "data" / "dnf" / "dnf2.json").read_text(encoding="utf-8"))
    return {"dfreward": reward(d), "dfvoc": voc(root)}   # gold() 는 ARAD CARE 백업용 (공개 화면 제외)
