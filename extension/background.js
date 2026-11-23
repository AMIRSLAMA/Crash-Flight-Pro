const KEY="crashFlightEvents";const ALLOWED=new Set(["OnStage","OnBetting","OnStart","OnCrash","OnBets","OnProfits"]);
chrome.runtime.onMessage.addListener((message,sender,respond)=>{
 if(message?.type==="crash-flight-get-events"){
  chrome.storage.local.get({[KEY]:[]},data=>respond({events:data[KEY].slice(-2000)}));
  return true;
 }
 if(message?.type!=="crash-flight-event"||!sender.tab?.id)return;
 const event=message.event;
 if(!event||!ALLOWED.has(event.target))return;
 const record={target:event.target,receivedAt:Date.now(),roundId:typeof event.l==="number"||typeof event.l==="string"?String(event.l):null};
 if(typeof event.ln==="number"&&Number.isFinite(event.ln))record.ln=event.ln;
 if(typeof event.ts==="number"&&Number.isFinite(event.ts))record.ts=event.ts;
 if(event.target==="OnCrash"&&typeof event.f==="number"&&Number.isFinite(event.f))record.f=event.f;
 if(event.metrics&&typeof event.metrics==="object"){
  record.metrics={};
  for(const [key,value] of Object.entries(event.metrics).slice(0,60)){
   if(/^[a-zA-Z0-9_]{1,48}$/.test(key)&&((typeof value==="number"&&Number.isFinite(value))||(typeof value==="string"&&value.length<=48)))record.metrics[key]=value;
  }
 }
 if(Number.isInteger(event.argCount))record.argCount=event.argCount;
 chrome.storage.local.get({[KEY]:[]},data=>{
  const arr=data[KEY];arr.push(record);
  if(arr.length>20000)arr.splice(0,arr.length-20000);
  chrome.storage.local.set({[KEY]:arr});
 });
});