(()=>{if(window.__crashFlightCaptureInstalled)return;window.__crashFlightCaptureInstalled=true;
 const TARGETS=new Set(["OnStage","OnBetting","OnStart","OnCrash","OnBets","OnProfits"]);
 function handle(raw){
  if(typeof raw!=="string")return;
  for(const part of raw.split("\x1e")){
   if(!part)continue;
   let obj;try{obj=JSON.parse(part)}catch{continue}
   const messages=Array.isArray(obj)?obj:[obj];
   for(const m of messages){
    if(!m||typeof m!=="object")continue;
    const target=typeof m.target==="string"?m.target:null;
    if(!TARGETS.has(target))continue;
    const args=Array.isArray(m.arguments)?m.arguments:[];
    const payload=args.find(a=>a&&typeof a==="object")||{};
    const event={target};
    for(const key of ["l","ln","ts"]){
      const val=payload[key]??m[key];
      if(typeof val==="number"&&Number.isFinite(val))event[key]=val;
      else if(key==="l"&&typeof val==="string"&&val.length<60)event[key]=val;
    }
    if(target==="OnCrash"){
      const f=payload.f??m.f;
      if(typeof f==="number"&&Number.isFinite(f))event.f=f;
    }
    window.postMessage({source:"crash-flight-pro-capture",event},"*");
   }
  }
 }
 const Native=window.WebSocket;
 if(typeof Native!=="function")return;
 class ObservedWebSocket extends Native{
  constructor(...args){super(...args);this.addEventListener("message",e=>{if(typeof e.data==="string")handle(e.data)})}
 }
 window.WebSocket=ObservedWebSocket;
})();