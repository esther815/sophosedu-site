/* 소포스에듀 이전·다음 화면 버튼 — 홈 화면 앱(주소창 없는 화면)에서도 쓸 수 있게 */
(function(){
  if(window.__spnav)return;window.__spnav=1;
  var css='.spnav{position:fixed;left:14px;bottom:calc(14px + env(safe-area-inset-bottom));z-index:90;display:flex;border:1px solid rgba(217,190,138,.55);background:rgba(62,17,27,.92);box-shadow:0 6px 18px rgba(30,10,15,.25);backdrop-filter:blur(4px)}'+
  '.spnav button{font:500 14px/1 "Noto Sans KR",sans-serif;color:#F1E3C3;background:none;border:0;padding:12px 15px;cursor:pointer;letter-spacing:.02em}'+
  '.spnav button+button{border-left:1px solid rgba(217,190,138,.35)}.spnav button:active{background:rgba(241,227,195,.14)}'+
  '@media print{.spnav{display:none}}';
  var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
  var n=document.createElement('nav');n.className='spnav';n.setAttribute('aria-label','화면 이동');
  n.innerHTML='<button type="button" data-n="b" aria-label="이전 화면">‹ 이전</button><button type="button" data-n="f" aria-label="다음 화면">다음 ›</button>';
  n.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
    if(b.dataset.n==='b'){var here=location.href;history.back();setTimeout(function(){if(location.href===here&&document.visibilityState==='visible')location.href='/'},450)}
    else history.forward()});
  function add(){document.body.appendChild(n)}
  if(document.body)add();else document.addEventListener('DOMContentLoaded',add);
})();
