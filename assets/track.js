/* 주니어솔로몬·소포스에듀 공통 집계 (익명, 개인정보 없음) */
(function(){
  try{
    var SB_URL='https://gyuuimwalbxsocnamtqk.supabase.co';
    var SB_KEY='sb_publishable_Kj2bX4fe9CRSkhvGzBbaJw_y1ZqkjOz';
    var SITE=(window.JS_SITE==='sophos')?'sophos':'solomon';
    if(!window.supabase||!window.supabase.createClient) return;
    var sb=window.supabase.createClient(SB_URL,SB_KEY,{auth:{persistSession:false,autoRefreshToken:false,detectSessionInUrl:false,storageKey:'js-track'}});   // 집계 전용: 로그인 정보를 읽거나 갱신하지 않음(갱신이 겹치면 로그인이 풀림)

    var sid;
    try{ sid=localStorage.getItem('js_sid'); if(!sid){ sid=Math.random().toString(36).slice(2)+Date.now().toString(36); localStorage.setItem('js_sid',sid); } }
    catch(e){ sid='x'+Date.now().toString(36); }

    var device=/Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent)?'mobile':'desktop';
    var refHost=''; try{ if(document.referrer){ var h=new URL(document.referrer).hostname; if(h && h!==location.hostname) refHost=h; } }catch(e){}
    var path=location.pathname||'/';

    function row(ev,detail,dwell){ return {site:SITE,event:ev,path:path,ref:refHost||null,session:sid,device:device,detail:detail||null,dwell_ms:dwell||null}; }
    function log(ev,detail,dwell){ try{ sb.from('site_events').insert(row(ev,detail,dwell)); }catch(e){} }

    log('pageview');

    // 머문 시간
    var t0=Date.now(), sent=false;
    function dwell(useBeacon){
      if(sent) return; sent=true;
      var ms=Date.now()-t0;
      if(useBeacon && navigator.sendBeacon){
        try{
          var url=SB_URL+'/rest/v1/site_events?apikey='+encodeURIComponent(SB_KEY);
          navigator.sendBeacon(url, new Blob([JSON.stringify(row('dwell',null,ms))],{type:'application/json'}));
          return;
        }catch(e){}
      }
      log('dwell',null,ms);
    }
    document.addEventListener('visibilitychange',function(){ if(document.visibilityState==='hidden') dwell(false); });
    window.addEventListener('pagehide',function(){ dwell(true); });

    // 핵심 클릭
    document.addEventListener('click',function(e){
      var a=e.target.closest&&e.target.closest('a,button'); if(!a) return;
      try{
        if(a.hasAttribute('data-go-sophos')){ log('transition','sophos'); return; }
        var href=(a.getAttribute&&a.getAttribute('href'))||'';
        var txt=((a.textContent||'').trim()).slice(0,20);
        var s=href+' '+txt;
        if(/consult\.html|상담/.test(s)) log('click','상담');
        else if(/seojae\.html|서재/.test(s)) log('click','서재');
        else if(/member\.html|가입|카카오|로그인/.test(s)) log('click','가입');
        else if(/fees\.html|교습비/.test(s)) log('click','교습비');
        else if(/programs\.html|프로그램/.test(s)) log('click','프로그램');
      }catch(e){}
    }, true);
  }catch(e){}
})();
