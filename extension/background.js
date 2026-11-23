const KEY="crashFlightEvents";
const TARGETS=new Set(["OnStage","OnBetting","OnStart","OnCrash","OnBets","OnProfits"]);
const RELEVANT=/(round|crash|bet|start|stage|tick|coef|mult|update|state|progress|fly|game|factor|rate|speed)/i;
chrome.runtime.onMessage.addListener((message,sender,respond)=>{
 if(message?.type==="crash-flight-get-events"){
  chrome.storage.local.get({[KEY]:[]},data=>respond({events:data[KEY].slice(-5000)}));
  return true;
 }
 if(message?.type!=="crash-flight-event"||!sender.tab?.id)return;
 const event=message.event;
 if(event?.kind==="transport"&&event.target==="__transport__"){
  const record={target:"__transport__",kind:"transport",transportType:String(event.transportType||"unknown").slice(0,24),byteLength:Number.isFinite(event.byteLength)?Math.max(0,event.byteLength):0,receivedAt:Date.now()};
  chrome.storage.local.get({[KEY]:[]},data=>{const arr=data[KEY];arr.push(record);if(arr.length>20000)arr.splice(0,arr.length-20000);chrome.storage.local.set({[KEY]:arr});});
  return;
 }
 if(!event||typeof event.target!=="string"||(!TARGETS.has(event.target)&&!RELEVANT.test(event.target)))return;
 const record={target:event.target.slice(0,80),receivedAt:Date.now(),captureVersion:typeof event.captureVersion==="string"?event.captureVersion.slice(0,24):null,roundId:typeof event.l==="number"||typeof event.l==="string"?String(event.l).slice(0,60):null};
 if(typeof event.ln==="number"&&Number.isFinite(event.ln))record.ln=event.ln;
 if(typeof event.accountId==="string"&&event.accountId.length>0&&event.accountId.length<=80)record.accountId=event.accountId;
 if(typeof event.ts==="number"&&Number.isFinite(event.ts))record.ts=event.ts;
 if(event.target==="OnCrash"&&typeof event.f==="number"&&Number.isFinite(event.f))record.f=event.f;
 if(event.metrics&&typeof event.metrics==="object"){
  record.metrics={};
  for(const [key,value] of Object.entries(event.metrics).slice(0,80)){
   if(/^[a-zA-Z0-9_]{1,48}$/.test(key)&&(typeof value==="number"&&Number.isFinite(value)))record.metrics[key]=value;
  }
 }
 if(Number.isInteger(event.argCount))record.argCount=event.argCount;
 if(Array.isArray(event.shape))record.shape=event.shape.slice(0,120).filter(x=>typeof x==="string"&&x.length<=160&&/^[a-zA-Z0-9_$.[\]:_-]+$/.test(x));
 chrome.storage.local.get({[KEY]:[]},data=>{
  const arr=data[KEY];arr.push(record);
  if(arr.length>20000)arr.splice(0,arr.length-20000);
  chrome.storage.local.set({[KEY]:arr});
 });
});