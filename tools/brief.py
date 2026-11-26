"""소포스 저널(brief.html) 생성 + 홈페이지 미리보기 조각 생성.
news.json 한 파일만 고치면 페이지와 홈페이지 미리보기가 함께 바뀐다."""
import json, html, sys, base64, datetime, os
ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))  # 저장소 맨 위 폴더

E = html.escape
items = sorted(json.load(open(os.path.join(ROOT, 'data', 'news.json'), encoding='utf8')), key=lambda x: x['date'], reverse=True)
CATS = ['전체', '수능', '논술', '서·논술형', '대입', '고입', '내신', '교육정책']
WD = '월화수목금토일'
SITE = 'https://sophosedu.co.kr/brief.html'
# 저널 구독하기 단추: 알림톡 발송을 켠 뒤(ALIMTALK_MODE=live) True 로 바꾼다. 그전에는 숨긴다.
SUBSCRIBE_ON = False
SHARE_ICON = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="vertical-align:-3px"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg>'

def NB(s):
    p=s.rsplit(' ',2)
    if len(p)<3 or len(p[1])+len(p[2])>10: p=s.rsplit(' ',1); return s if len(p)<2 else p[0]+' <span style="white-space:nowrap">'+p[1]+'</span>'
    return p[0]+' <span style="white-space:nowrap">'+p[1]+' '+p[2]+'</span>'
def kdate(d):
    t = datetime.date.fromisoformat(d)
    return f"{t.year}. {t.month}. {t.day}.({WD[t.weekday()]})"

def card(x):
    pts = ''.join(f'<li>{E(p)}</li>' for p in x['points'])
    return f'''<article class="nc" data-cat="{E(x['cat'])}" id="{E(x['id'])}">
  <div class="meta"><span class="cat">{E(x['cat'])}</span><time datetime="{x['date']}">{kdate(x['date'])}</time><span class="src">{E(x['source'])}</span></div>
  <h2>{E(x['title'])}</h2>
  <p class="deck">{E(x['deck'])}</p>
  <div class="three"><p class="lab">세 줄 요약</p><ol>{pts}</ol></div>
  <p class="note"><b>소포스 노트</b>{E(x['note'])}</p>
  <div class="acts"><a class="orig" href="{E(x['url'])}" target="_blank" rel="noopener nofollow">원문 기사 보기 · {E(x['source'])} →</a>
  <button type="button" class="shr" data-share-id="{E(x['id'])}" data-share-title="{E(x['title'])}">{SHARE_ICON} 공유하기</button></div>
</article>'''

def page(icon_src, home_href):
    top3 = ''.join(f'<li><a href="#{E(x["id"])}"><span>{E(x["cat"])}</span>{E(x["title"])}</a></li>' for x in items[:3])
    chips = ''.join(f'<button type="button" class="chip" data-f="{c}" aria-pressed="{"true" if c=="전체" else "false"}">{c}</button>' for c in CATS)
    cards = '\n'.join(card(x) for x in items)
    SUB = '<a class="sub" href="member.html?ns=1">✉ 소포스 저널 구독하기 <small style="font-weight:400;opacity:.85">재원생 가족</small></a>' if SUBSCRIBE_ON else ''
    ld = json.dumps({"@context": "https://schema.org", "@type": "CollectionPage", "name": "소포스 저널",
                     "description": "중·고등 학부모를 위한 입시·교육 뉴스 요약", "publisher": {"@type": "EducationalOrganization", "name": "소포스에듀"}}, ensure_ascii=False)
    return f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>소포스 저널 | 중·고등 입시·교육 뉴스 세 줄 요약 · 소포스에듀</title>
<meta name="description" content="중·고등 학부모가 꼭 알아야 할 입시·교육 뉴스를 소포스에듀가 골라 세 줄로 정리합니다. 2028 대입, 내신 5등급제, 수능, 고입 소식.">
<meta property="og:title" content="소포스 저널 · 제목만 읽어도 알 수 있게">
<meta property="og:description" content="입시·교육 뉴스를 세 줄로 정리합니다."><meta property="og:type" content="website"><meta property="og:url" content="https://sophosedu.co.kr/brief.html"><meta property="og:site_name" content="소포스에듀">
<meta name="theme-color" content="#3E111B"><link rel="icon" href="img/favicon.ico?v=2" sizes="any"><link rel="apple-touch-icon" href="img/apple-touch-icon.png?v=2"><meta property="og:image" content="https://sophosedu.co.kr/img/og.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Noto+Serif+KR:wght@600;700&family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">
<script type="application/ld+json">{ld}</script>
<style>
:root{{--ivory:#F7F1E6;--paper:#FCF9F3;--wine:#3E111B;--wine2:#5C1A28;--rose:#B8404D;--gold:#A9824A;--gold-l:#D9BE8A;--ink:#271B1D;--text:#3B2E31;--muted:#76666A;--line:#E4D7C4;--serif:'Noto Serif KR',serif;--latin:'Cormorant Garamond','Noto Serif KR',serif}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--text);font-family:'Noto Sans KR',sans-serif;font-size:17px;line-height:1.8;word-break:keep-all;overflow-wrap:break-word;-webkit-font-smoothing:antialiased}}
a{{color:inherit}}h1,h2{{text-wrap:balance}}p,li{{text-wrap:pretty}}
.wrap{{max-width:880px;margin:0 auto;padding:0 24px}}
.hd{{position:sticky;top:0;z-index:20;background:rgba(252,249,243,.95);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}}
.hd .wrap{{max-width:1200px;display:flex;align-items:center;justify-content:space-between;height:68px}}
.brand{{display:flex;align-items:center;gap:10px;text-decoration:none}}.brand img{{height:34px}}
.brand b{{font-family:var(--latin);font-size:21px;letter-spacing:.14em;color:#4F3F40}}.brand span{{display:block;font-size:11px;color:var(--rose);font-weight:700;letter-spacing:.16em}}
.back{{font-size:15px;text-decoration:none;color:var(--wine2);font-weight:700}}
.mast{{padding:84px 0 40px;text-align:center}}
.mast .k{{font-family:var(--latin);letter-spacing:.42em;color:var(--gold);font-size:15px;margin:0}}
.mast h1{{margin:10px 0 0;font-family:var(--serif);font-size:clamp(40px,6vw,64px);color:var(--ink);letter-spacing:-.03em;line-height:1.2}}
.mast p{{margin:16px auto 0;max-width:560px;color:var(--muted)}}
.rule{{height:12px;margin:34px auto 0;width:220px;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'%3E%3Cpath d='M0 18H20M16 18V2H4V14H12V6H8V10' fill='none' stroke='%23B8404D' stroke-width='1.6'/%3E%3C/svg%3E");background-size:12px 12px;background-repeat:repeat-x;opacity:.8}}
.top3{{background:var(--wine);color:#F4E9D8;padding:30px 34px;margin-top:10px}}
.top3 p{{margin:0 0 12px;font-family:var(--latin);letter-spacing:.3em;color:var(--gold-l);font-size:14px}}
.top3 ol{{margin:0;padding-left:22px}}.top3 li{{margin:8px 0;font-family:var(--serif);font-size:18.5px;line-height:1.55}}
.top3 a{{text-decoration:none;color:#fff}}.top3 a span{{display:inline-block;margin-right:10px;padding:0 9px;border:1px solid rgba(217,190,138,.6);color:var(--gold-l);font-family:'Noto Sans KR',sans-serif;font-size:12.5px;vertical-align:2px}}
.tools{{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin:40px 0 10px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px}}
.chip{{font:inherit;font-size:14.5px;padding:7px 16px;border-radius:999px;border:1px solid var(--line);background:#fff;color:var(--ink);cursor:pointer}}
.chip[aria-pressed="true"]{{background:var(--wine2);border-color:var(--wine2);color:#fff}}
.q{{font:inherit;font-size:15px;padding:9px 16px;border:1px solid var(--line);border-radius:999px;background:#fff;min-width:220px}}
.nc{{padding:40px 0 36px;border-bottom:1px solid var(--line)}}
.meta{{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;font-size:14px;color:var(--muted)}}
.cat{{padding:1px 10px;background:var(--ivory);border:1px solid var(--line);color:var(--wine2);font-weight:700;font-size:13px}}
.nc h2{{margin:14px 0 0;font-family:var(--serif);font-size:clamp(25px,3vw,32px);line-height:1.38;color:var(--ink);letter-spacing:-.02em}}
.deck{{margin:12px 0 0;font-size:17.5px;color:var(--wine2);font-weight:500;line-height:1.7}}
.three{{margin-top:20px;padding:20px 24px;background:#fff;border:1px solid var(--line)}}
.three .lab{{margin:0 0 8px;font-size:13px;font-weight:700;letter-spacing:.08em;color:var(--gold)}}
.three ol{{margin:0;padding-left:22px}}.three li{{margin:6px 0;font-size:16px;line-height:1.7}}
.note{{margin:16px 0 0;font-size:15.5px;line-height:1.7;color:var(--text);padding-left:14px;border-left:3px solid var(--rose)}}
.note b{{display:inline-block;margin-right:10px;color:var(--rose);font-size:13.5px;letter-spacing:.04em}}
.orig{{display:inline-block;margin-top:16px;font-size:14.5px;color:var(--wine2);text-decoration:none;border-bottom:1px solid var(--gold-l)}}
.empty{{display:none;padding:50px 0;text-align:center;color:var(--muted)}}
footer{{margin-top:70px;padding:34px 0 50px;border-top:1px solid var(--line);font-size:13px;color:var(--muted);line-height:1.9}}
@media (max-width:600px){{.top3{{padding:24px 20px}}.q{{min-width:0;width:100%}}}}
.acts{{display:flex;flex-wrap:wrap;align-items:center;gap:10px 18px;margin-top:16px}}.acts .orig{{margin-top:0}}
.shr{{display:inline-flex;align-items:center;gap:6px;padding:7px 15px;border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--wine2);font:600 13.5px 'Noto Sans KR',sans-serif;cursor:pointer}}
.shr:hover{{border-color:var(--gold-l)}}
.mbtn{{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin:22px 0 0}}
.mbtn button,.mbtn a{{display:inline-flex;align-items:center;gap:8px;padding:11px 22px;border-radius:999px;border:1px solid var(--gold-l);background:#fff;color:var(--wine2);font:600 14.5px 'Noto Sans KR',sans-serif;cursor:pointer;text-decoration:none}}
.mbtn a.sub{{background:var(--wine);border-color:var(--wine);color:#fff}}
.nc{{scroll-margin-top:84px}}.nc.hl{{animation:hl 1.5s ease 2}}@keyframes hl{{50%{{background:#F6EEE0}}}}
.sh-bg{{position:fixed;inset:0;background:rgba(39,27,29,.45);z-index:998;display:none}}.sh-bg.on{{display:block}}
.sh{{position:fixed;left:50%;bottom:0;transform:translate(-50%,100%);width:min(480px,100%);background:#fff;z-index:999;padding:22px 20px calc(22px + env(safe-area-inset-bottom));transition:transform .25s;border-top:3px solid var(--wine)}}
.sh.on{{transform:translate(-50%,0)}}
.sh h3{{margin:0 0 4px;font:700 16px 'Noto Serif KR',serif;color:var(--ink)}}.sh .st{{margin:0 0 16px;font-size:13.5px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.sh .g{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.sh .g button{{display:flex;flex-direction:column;align-items:center;gap:7px;padding:12px 4px;border:1px solid var(--line);background:#fff;font:500 13px 'Noto Sans KR',sans-serif;color:var(--text);cursor:pointer}}
.sh .g i{{display:flex;align-items:center;justify-content:center;width:38px;height:38px;border-radius:50%;font:700 15px 'Noto Sans KR',sans-serif;font-style:normal;color:#fff}}
.sh .x{{display:block;width:100%;margin-top:14px;padding:11px;border:0;background:var(--paper);font:inherit;font-size:14px;cursor:pointer}}
.toast{{position:fixed;left:50%;bottom:30px;transform:translateX(-50%);background:var(--ink);color:#fff;padding:12px 22px;border-radius:999px;font-size:14px;z-index:1000;opacity:0;pointer-events:none;transition:opacity .25s;max-width:88vw;text-align:center}}.toast.on{{opacity:1}}
</style></head><body>
<header class="hd"><div class="wrap"><a class="brand" href="{home_href}"><img src="{icon_src}" alt=""><span><b>Sophos Edu</b><span>소포스에듀</span></span></a><a class="back" href="{home_href}">홈으로 →</a></div></header>
<main class="wrap">
<section class="mast"><p class="k">SOPHOS JOURNAL</p><h1>소포스 저널</h1><p>학부모가 꼭 알아야 할 입시·교육 뉴스를 골라, 제목만 읽어도 알 수 있게 정리합니다.</p><div class="mbtn"><button type="button" id="shareAll">{SHARE_ICON} 소포스 저널 공유하기</button>{SUB}</div><div class="rule"></div></section>
<section class="top3" aria-label="최근 소식 세 줄"><p>LATEST · 최근 세 줄</p><ol>{top3}</ol></section>
<div class="tools"><div class="chips" role="group" aria-label="분류">{chips}</div><input class="q" type="search" placeholder="검색 (예: 5등급, 정시)" aria-label="소포스 저널 검색"></div>
<section id="list">{cards}</section>
<p class="empty" id="empty">해당하는 소식이 아직 없습니다.</p>
<footer>요약과 소포스 노트는 소포스에듀가 기사를 읽고 정리한 것입니다. 정확한 내용은 각 원문 기사에서 확인해 주세요.<br>© 소포스에듀. 무단 복제·전재·배포·변형 및 생성형 AI를 이용한 학습·분석·유사·파생 콘텐츠 제작을 금합니다.<br>위반 시 관련 법령에 따른 책임을 물을 수 있습니다.</footer>
</main>
<script>
(function(){{var f='전체',q='';var cards=[].slice.call(document.querySelectorAll('.nc'));
function run(){{var n=0;cards.forEach(function(c){{var ok=(f==='전체'||c.getAttribute('data-cat')===f)&&(!q||c.textContent.indexOf(q)>=0);c.style.display=ok?'':'none';if(ok)n++}});document.getElementById('empty').style.display=n?'none':'block'}}
[].forEach.call(document.querySelectorAll('.chip'),function(b){{b.onclick=function(){{f=b.getAttribute('data-f');[].forEach.call(document.querySelectorAll('.chip'),function(x){{x.setAttribute('aria-pressed',x===b?'true':'false')}});run()}}}});
document.querySelector('.q').addEventListener('input',function(e){{q=e.target.value.trim();run()}});
/* 공유하기 — 카카오톡 · 네이버 블로그 · X · 스레드 · 인스타그램 · 링크 복사 */
var BASE='{SITE}',cur=null,tEl=null;
function toast(t){{if(!tEl){{tEl=document.createElement('div');tEl.className='toast';document.body.appendChild(tEl)}}tEl.textContent=t;tEl.classList.add('on');clearTimeout(toast.k);toast.k=setTimeout(function(){{tEl.classList.remove('on')}},3000)}}
function copy(u,msg){{function ok(){{toast(msg)}}if(navigator.clipboard&&window.isSecureContext)navigator.clipboard.writeText(u).then(ok,function(){{window.prompt('아래 링크를 복사해 주세요.',u)}});else window.prompt('아래 링크를 복사해 주세요.',u)}}
function open_(u){{window.open(u,'_blank','noopener,width=620,height=680')}}
var mob=/Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
var bg=document.createElement('div');bg.className='sh-bg';var sh=document.createElement('div');sh.className='sh';sh.setAttribute('role','dialog');sh.setAttribute('aria-label','공유하기');
sh.innerHTML='<h3>공유하기</h3><p class="st" id="sht"></p><div class="g">'+
 [['kakao','#FEE500','<span style="color:#191919">K</span>','카카오톡'],['naver','#03C75A','N','네이버 블로그'],['x','#111','X','X'],['threads','#111','@','스레드'],['insta','#C13584','◎','인스타그램'],['copy','#5C1A28','⧉','링크 복사']]
 .map(function(o){{return '<button type="button" data-s="'+o[0]+'"><i style="background:'+o[1]+'">'+o[2]+'</i>'+o[3]+'</button>'}}).join('')+'</div><button type="button" class="x">닫기</button>';
document.body.appendChild(bg);document.body.appendChild(sh);
function openSheet(d){{cur=d;document.getElementById('sht').textContent=d.title;bg.classList.add('on');sh.classList.add('on')}}
function close_(){{bg.classList.remove('on');sh.classList.remove('on')}}
bg.onclick=close_;sh.querySelector('.x').onclick=close_;document.addEventListener('keydown',function(e){{if(e.key==='Escape')close_()}});
sh.addEventListener('click',function(e){{var b=e.target.closest('[data-s]');if(!b||!cur)return;var s=b.getAttribute('data-s'),u=cur.url,t=cur.title,eu=encodeURIComponent(u),et=encodeURIComponent(t);
  if(s==='kakao'||s==='insta'){{
    if(mob&&navigator.share){{navigator.share({{title:t,text:t,url:u}}).catch(function(){{}});close_();return}}
    copy(u,s==='kakao'?'링크를 복사했습니다. 카카오톡 대화창에 붙여 넣어 보내 주세요.':'링크를 복사했습니다. 인스타그램 스토리·메시지에 붙여 넣어 주세요.');close_();return}}
  if(s==='naver')open_('https://share.naver.com/web/shareView?url='+eu+'&title='+et);
  else if(s==='x')open_('https://twitter.com/intent/tweet?text='+et+'&url='+eu);
  else if(s==='threads')open_('https://www.threads.net/intent/post?text='+encodeURIComponent(t+' '+u));
  else if(s==='copy')copy(u,'링크를 복사했습니다.');
  close_()}});
document.getElementById('shareAll').onclick=function(){{openSheet({{title:'소포스 저널 · 입시·교육 뉴스 세 줄 요약',url:BASE}})}};
[].forEach.call(document.querySelectorAll('.shr'),function(b){{b.onclick=function(){{openSheet({{title:'소포스 저널 | '+b.getAttribute('data-share-title'),url:BASE+'#'+b.getAttribute('data-share-id')}})}}}});
/* 공유 링크로 들어오면 그 기사로 이동해 잠깐 강조 */
if(location.hash.length>1){{var tg=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(tg)setTimeout(function(){{tg.scrollIntoView({{behavior:'smooth',block:'start'}});tg.classList.add('hl');setTimeout(function(){{tg.classList.remove('hl')}},3200)}},80)}}
}})();
</script><script src="/nav.js" defer></script></body></html>'''

def teaser(brief_href):
    rows = ''.join(f'''<a class="bt-item" href="{brief_href}#{E(x['id'])}"><span class="bt-cat">{E(x['cat'])}</span><span class="bt-t">{NB(E(x['title']))}</span><span class="bt-d">{NB(E(x['deck']))}</span><time>{kdate(x['date'])}</time></a>''' for x in items[:3])
    return rows

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'page-file':      # 배포용 (img/icon.png 상대경로)
        print(page('img/icon.png', sys.argv[2]))
    elif mode == 'page-inline':  # 미리보기용 (아이콘 내장)
        ic = 'data:image/png;base64,' + base64.b64encode(open(os.path.join(ROOT, 'img', 'icon.png'), 'rb').read()).decode()
        print(page(ic, 'index.html'))
    elif mode == 'teaser':
        print(teaser(sys.argv[2]))
