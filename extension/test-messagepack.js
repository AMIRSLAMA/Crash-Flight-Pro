"use strict";
const assert=require("node:assert/strict");
const {parseSignalRFrames}=require("./messagepack.js");
function str(s){const b=Buffer.from(s,"utf8");return Buffer.concat([Buffer.from([0xa0|b.length]),b]);}
function num(n){if(Number.isInteger(n)&&n>=0&&n<=127)return Buffer.from([n]);const b=Buffer.alloc(9);b[0]=0xcb;b.writeDoubleBE(n,1);return b;}
function arr(xs){return Buffer.concat([Buffer.from([0x90|xs.length]),...xs]);}
function map(xs){return Buffer.concat([Buffer.from([0x80|xs.length]),...xs.flatMap(([k,v])=>[str(k),v])]);}
function frame(b){assert.ok(b.length<128);return Buffer.concat([Buffer.from([b.length]),b]);}
function invoke(target,args){return arr([num(1),map([]),Buffer.from([0xc0]),str(target),arr(args),arr([])]);}
const crash=frame(invoke("OnCrash",[map([["l",num(77)],["f",num(2.5)]])]));
const stage=frame(invoke("OnStage",[map([["l",num(78)]])]));
const parsed=parseSignalRFrames(Buffer.concat([crash,stage]));
assert.equal(parsed.invocations.length,2);
assert.equal(parsed.invocations[0].target,"OnCrash");
assert.equal(parsed.invocations[0].arguments[0].f,2.5);
assert.equal(parsed.invocations[1].target,"OnStage");
assert.equal(parsed.incomplete,false);
const partial=parseSignalRFrames(crash.subarray(0,crash.length-2));
assert.equal(partial.invocations.length,0);
assert.equal(partial.incomplete,true);
const ignored=frame(arr([num(6),map([]),Buffer.from([0xc0])]));
assert.equal(parseSignalRFrames(ignored).invocations.length,0);
console.log("MessagePack SignalR tests passed.");
