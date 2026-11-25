const KEY="crashFlightEvents";
const TARGETS=new Set(["OnStage","OnBetting","OnStart","OnCrash","OnBets","OnProfits"]);
const RELEVANT=/(round|crash|bet|start|stage|tick|coef|mult|update|state|progress|fly|game|factor|rate|speed)/i;
let pendingRecords=[];
const lastTransportDiagnostic=new Map();
let flushPromise=null;
let flushTimer=null;
const flushWaiters=[];
function flushRecords(){
 if(flushPromise)return flushPromise;
 flushPromise=(async()=>{
  while(pendingRecords.length){
   const batch=pendingRecords.splice(0,pendingRecords.length);
   const data=await chrome.storage.local.get({[KEY]:[]});
   const arr=data[KEY];
   arr.push(...batch);
   if(arr.length>20000)arr.splice(0,arr.length-20000);
   await chrome.storage.local.set({[KEY]:arr});
  }
 })().catch(error=>{
  console.error("Crash Flight storage flush failed:",error);
  throw error;
 }).finally(()=>{
  flushPromise=null;
  if(pendingRecords.length) scheduleFlush();
  while(flushWaiters.length)flushWaiters.shift()();
 });
 return flushPromise;
}
function scheduleFlush(){
 if(flushTimer!==null)return;
 flushTimer=setTimeout(()=>{
  flushTimer=null;
  flushRecords().catch(()=>{});
 },200);
}
chrome.runtime.onMessage.addListener((message,sender,respond)=>{
 if(message?.type==="crash-flight-get-events"){
  const reply=async()=>{
   if(flushTimer!==null){clearTimeout(flushTimer);flushTimer=null;}
   if(flushPromise)await new Promise(resolve=>flushWaiters.push(resolve));
   await flushRecords();
   const data=await chrome.storage.local.get({[KEY]:[]});
   respond({events:data[KEY].slice(-5000)});
  };
  reply().catch(error=>{console.error(error);respond({error:"storage-unavailable",events:[]});});
  return true;
 }
 if(message?.type!=="crash-flight-event"||!sender.tab?.id)return;
 const event=message.event;
 if(event?.kind==="transport"&&event.target==="__transport__"){
  const allowed=["websocket-created","websocket-open","messagepack-decoded","messagepack-unreadable"];
  if(!allowed.includes(event.transportType))return;
  const now=Date.now();
  // Throttle repeated frame diagnostics so a busy socket cannot flood local storage.
  if(event.transportType.startsWith("messagepack-")){
   const last=lastTransportDiagnostic.get(event.transportType)||0;
   if(now-last<1000)return;
   lastTransportDiagnostic.set(event.transportType,now);
  }
  pendingRecords.push({
   target:"__transport__",kind:"transport",transportType:event.transportType,
   byteLength:Number.isFinite(event.byteLength)?Math.max(0,Math.min(event.byteLength,4194304)):0,
   decodedCount:Number.isInteger(event.decodedCount)?Math.max(0,Math.min(event.decodedCount,1000)):0,
   malformedCount:Number.isInteger(event.malformedCount)?Math.max(0,Math.min(event.malformedCount,1000)):0,
   incomplete:event.incomplete===true,receivedAt:now
  });
  scheduleFlush();
  return;
 }
 if(!event||typeof event.target!=="string"||(!TARGETS.has(event.target)&&!RELEVANT.test(event.target)))return;
 const record={target:event.target.slice(0,80),receivedAt:Date.now(),captureVersion:typeof event.captureVersion==="string"?event.captureVersion.slice(0,24):null,roundId:typeof event.l==="number"||typeof event.l==="string"?String(event.l).slice(0,60):null};
 if(typeof event.ln==="number"&&Number.isFinite(event.ln))record.ln=event.ln;
 if(typeof event.ts==="number"&&Number.isFinite(event.ts))record.ts=event.ts;
 if(event.target==="OnCrash"&&typeof event.f==="number"&&Number.isFinite(event.f))record.f=event.f;
 if(event.metrics&&typeof event.metrics==="object"){
  record.metrics={};
  for(const [key,value] of Object.entries(event.metrics).slice(0,80)){
   if(/^[a-zA-Z0-9_]{1,48}$/.test(key)&&typeof value==="number"&&Number.isFinite(value))record.metrics[key]=value;
  }
 }
 if(Number.isInteger(event.argCount))record.argCount=event.argCount;
 if(Array.isArray(event.numericPaths))record.numericPaths=event.numericPaths.slice(0,160).filter(x=>x&&typeof x.path==="string"&&x.path.length<=180&&typeof x.value==="number"&&Number.isFinite(x.value));
 if(Array.isArray(event.shape))record.shape=event.shape.slice(0,120).filter(x=>typeof x==="string"&&x.length<=160&&/^[a-zA-Z0-9_$.[\]:_-]+$/.test(x));
 pendingRecords.push(record);
 scheduleFlush();
});