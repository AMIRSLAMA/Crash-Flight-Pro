const KEY="crashFlightEvents";const ALLOWED=new Set(["OnStage","OnBetting","OnStart","OnCrash","OnBets","OnProfits"]);
chrome.runtime.onMessage.addListener((message,sender,respond)=>{
 if(message?.type!=="crash-flight-event"||!sender.tab?.id)return;
 const event=message.event;
 if(!event||!ALLOWED.has(event.target))return;
 const record={target:event.target,receivedAt:Date.now(),roundId:typeof event.l==="number"||typeof event.l==="string"?String(event.l):null};
 if(typeof event.ln==="number"&&Number.isFinite(event.ln))record.ln=event.ln;
 if(typeof event.ts==="number"&&Number.isFinite(event.ts))record.ts=event.ts;
 if(event.target==="OnCrash"&&typeof event.f==="number"&&Number.isFinite(event.f))record.f=event.f;
 chrome.storage.local.get({[KEY]:[]},data=>{
  const arr=data[KEY];arr.push(record);
  if(arr.length>20000)arr.splice(0,arr.length-20000);
  chrome.storage.local.set({[KEY]:arr});
 });
});
