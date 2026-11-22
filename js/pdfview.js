/* PDF를 그림으로 그려 보여 주기 (아이폰 사파리는 PDF 보기 창이 비어 보이므로) */
(function(){
  var ready=null;
  function load(){if(ready)return ready;ready=new Promise(function(res,rej){var s=document.createElement('script');s.src='/js/pdf.min.js';s.onload=function(){window.pdfjsLib.GlobalWorkerOptions.workerSrc='/js/pdf.worker.min.js';res(window.pdfjsLib)};s.onerror=rej;document.head.appendChild(s)});return ready}
  window.spPdf=function(blob,box,opts){
    opts=opts||{};box.innerHTML='<div class="pdfv" style="flex:1;overflow:auto;-webkit-overflow-scrolling:touch;padding:0 16px 16px"></div>';var wrap=box.firstChild;
    return Promise.all([load(),blob.arrayBuffer()]).then(function(a){return a[0].getDocument({data:new Uint8Array(a[1])}).promise}).then(function(doc){
      var w=Math.max(280,wrap.clientWidth-32),dpr=Math.min(window.devicePixelRatio||1,2.5),chain=Promise.resolve();
      for(var n=1;n<=doc.numPages;n++)(function(n){chain=chain.then(function(){return doc.getPage(n)}).then(function(pg){var v1=pg.getViewport({scale:1}),sc=w/v1.width,vp=pg.getViewport({scale:sc*dpr});var c=document.createElement('canvas');c.width=vp.width;c.height=vp.height;c.style.cssText='display:block;width:100%;height:auto;margin:0 auto 12px;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.3)';wrap.appendChild(c);return pg.render({canvasContext:c.getContext('2d'),viewport:vp}).promise.then(function(){if(opts.mark)opts.mark(c)})})})(n);
      return chain;
    }).catch(function(){box.innerHTML='<p style="color:#F1E3C3;margin:30px auto;text-align:center">이 문서는 미리보기가 되지 않습니다.<br>내려받기로 여십시오.</p>'});
  };
})();
