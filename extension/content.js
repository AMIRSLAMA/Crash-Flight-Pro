(()=>{
 "use strict";
 const INSTALLED="__crashFlightContentBridgeInstalled";
 if(window[INSTALLED])return;
 window[INSTALLED]=true;
 let captureEnabled=false;
 window.addEventListener("message",event=>{
  if(event.source!==window)return;
  if(event.data?.source==="crash-flight-control"&&typeof event.data.enabled==="boolean"){
   captureEnabled=event.data.enabled;
   return;
  }
  if(!captureEnabled||event.data?.source!=="crash-flight-pro-capture")return;
  try{
   const pending=chrome.runtime.sendMessage({type:"crash-flight-event",event:event.data.event});
   if(pending&&typeof pending.catch==="function")pending.catch(()=>{});
  }catch(_){}
 });
})();