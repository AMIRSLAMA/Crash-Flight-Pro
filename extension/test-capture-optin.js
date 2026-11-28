"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const manifest=JSON.parse(fs.readFileSync("extension/manifest.json","utf8"));
const popupSource=fs.readFileSync("extension/popup.js","utf8");
assert.match(popupSource,new RegExp('const CAPTURE_VERSION="'+manifest.version+'"'),"popup version must match extension manifest");
function makeWindow(){
 const listeners={};
 const posted=[];
 class FakeWebSocket{
  constructor(){this.listeners={};}
  addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);}
  emit(type,event={}){for(const fn of this.listeners[type]||[])fn(event);}
 }
 const window={
  WebSocket:FakeWebSocket,
  postMessage(data){posted.push(data);},
  addEventListener(type,fn){(listeners[type]??=[]).push(fn);},
  dispatchMessage(data,source=this){for(const fn of listeners.message||[])fn({source,data});}
 };
 return {window,posted,FakeWebSocket};
}
const raw=JSON.stringify({type:1,target:"OnStage",arguments:[{l:21,x:1.7}]})+"\x1e";
{
 const {window,posted}=makeWindow();
 vm.runInNewContext(fs.readFileSync("extension/inject.js","utf8"),{window,Uint8Array,TextDecoder,JSON,Set,Number,Object,Array,String,RegExp,Error,Map,Promise});
 const ws=new window.WebSocket("wss://fixture.invalid");
 ws.emit("open");
 ws.emit("message",{data:raw});
 assert.equal(posted.length,0,"transport and game events must be silent before opt-in");
 window.dispatchMessage({source:"crash-flight-control",enabled:true});
 ws.emit("message",{data:raw});
 assert.equal(posted.length,1,"enabled capture should forward one event");
 assert.equal(posted[0].event.target,"OnStage");
 ws.emit("open");
 assert.equal(posted.length,2,"enabled capture should emit transport diagnostics");
 window.dispatchMessage({source:"crash-flight-control",enabled:false});
 ws.emit("message",{data:raw});
 ws.emit("open");
 assert.equal(posted.length,2,"disabled capture must stop event and transport forwarding");
 console.log("inject.js opt-in tests passed");
}
{
 const {window}=makeWindow();
 const sent=[];
 const chrome={runtime:{sendMessage(message){sent.push(message);return Promise.resolve();}}};
 vm.runInNewContext(fs.readFileSync("extension/content.js","utf8"),{window,chrome});
 window.dispatchMessage({source:"crash-flight-pro-capture",event:{target:"OnStage"}});
 assert.equal(sent.length,0,"content bridge must ignore events before opt-in");
 window.dispatchMessage({source:"crash-flight-control",enabled:true});
 window.dispatchMessage({source:"crash-flight-pro-capture",event:{target:"OnStage"}});
 assert.equal(sent.length,1,"content bridge forwards after opt-in");
 window.dispatchMessage({source:"crash-flight-control",enabled:false});
 window.dispatchMessage({source:"crash-flight-pro-capture",event:{target:"OnCrash",f:2.1}});
 assert.equal(sent.length,1,"content bridge stops forwarding after opt-out");
 window.dispatchMessage({source:"crash-flight-pro-capture",event:{target:"OnCrash"}},null);
 assert.equal(sent.length,1,"content bridge ignores messages from other sources");
 console.log("content.js opt-in tests passed");
}
