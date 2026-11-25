(()=>{
 "use strict";
 const INSTALLED="__crashFlightContentBridgeInstalled";
 if(window[INSTALLED])return;
 window[INSTALLED]=true;
 window.addEventListener("message",event=>{
  if(event.source!==window||event.data?.source!=="crash-flight-pro-capture")return;
  try{
   const pending=chrome.runtime.sendMessage({type:"crash-flight-event",event:event.data.event});
   if(pending&&typeof pending.catch==="function")pending.catch(()=>{});
  }catch(_){}
 });
})();