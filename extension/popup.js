const status=document.getElementById("status");const KEY="crashFlightEvents";const CAPTURE_VERSION="0.4.1";
async function getGameTab(){
 const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
 if(!tab?.id||!/^https:\/\//.test(tab.url||""))throw Error("افتح صفحة اللعبة HTTPS أولًا");
 const host=new URL(tab.url).hostname;
 if(!/(^|\.)(1xbet\.com|eg1xbet\.com|1xlite-11151\.pro)$/.test(host))throw Error("التسجيل متاح فقط على صفحة اللعبة");
 return tab;
}
async function setCaptureEnabled(enabled){
 const tab=await getGameTab(),target={tabId:tab.id,frameIds:[0]};
 const [version]=await chrome.scripting.executeScript({target,world:"MAIN",func:()=>window.__crashFlightCaptureInstalled||null});
 if(version.result&&version.result!==CAPTURE_VERSION){
  status.textContent="الصفحة تحمل نسخة قديمة من التسجيل. أعد تحميل صفحة اللعبة قبل التحكم في الالتقاط.";
  return;
 }
 if(enabled&&!version.result){
  await chrome.scripting.executeScript({target:{tabId:tab.id,allFrames:true},files:["messagepack.js","inject.js"],world:"MAIN"});
 }
 if(enabled){
  await chrome.scripting.executeScript({target:{tabId:tab.id,allFrames:true},files:["content.js"],world:"ISOLATED"});
 }
 await chrome.scripting.executeScript({target:{tabId:tab.id,allFrames:true},world:"MAIN",func:(value)=>window.postMessage({source:"crash-flight-control",enabled:value},"*"),args:[enabled]});
 status.textContent=enabled?"تم تشغيل التسجيل في التبويب الحالي. أعد تحميل اللعبة إذا لم تظهر أحداث.":"تم إيقاف التسجيل في التبويب الحالي.";
}
document.getElementById("start").onclick=async()=>{try{await setCaptureEnabled(true)}catch(e){status.textContent="خطأ: "+e.message}};
document.getElementById("stop").onclick=async()=>{try{await setCaptureEnabled(false)}catch(e){status.textContent="خطأ: "+e.message}};
document.getElementById("export").onclick=async()=>{
 const data=await chrome.storage.local.get({[KEY]:[]});const rows=data[KEY];
 if(!rows.length){status.textContent="مفيش رسائل مسجلة لسه";return}
 const text=rows.map(x=>JSON.stringify(x)).join("\n")+"\n";
 const url="data:application/x-ndjson;charset=utf-8,"+encodeURIComponent(text);
 await chrome.downloads.download({url,filename:"crash-flight-events.jsonl",saveAs:true});
 status.textContent="تم تجهيز "+rows.length+" رسالة للتصدير";
};
document.getElementById("clear").onclick=async()=>{await chrome.storage.local.set({[KEY]:[]});status.textContent="تم المسح"};