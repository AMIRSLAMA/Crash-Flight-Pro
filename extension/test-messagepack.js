"use strict";
const assert=require("node:assert/strict");
const {parseSignalRFrames}=require("./messagepack.js");
function str(s){const b=Buffer.from(s,"utf8");if(b.length<32)return Buffer.concat([Buffer.from([0xa0|b.length]),b]);if(b.length<=255)return Buffer.concat([Buffer.from([0xd9,b.length]),b]);if(b.length<=65535){const h=Buffer.alloc(3);h[0]=0xda;h.writeUInt16BE(b.length,1);return Buffer.concat([h,b]);}throw new RangeError("test string too long");}
function num(n){if(Number.isInteger(n)&&n>=0&&n<=127)return Buffer.from([n]);const b=Buffer.alloc(9);b[0]=0xcb;b.writeDoubleBE(n,1);return b;}
function arr(xs){return Buffer.concat([Buffer.from([0x90|xs.length]),...xs]);}
function map(xs){return Buffer.concat([Buffer.from([0x80|xs.length]),...xs.flatMap(([k,v])=>[str(k),v])]);}
function frame(b){let n=b.length,prefix=[];while(n>=128){prefix.push((n&127)|128);n=Math.floor(n/128);}prefix.push(n);return Buffer.concat([Buffer.from(prefix),b]);}
function invoke(target,args){return arr([num(1),map([]),Buffer.from([0xc0]),str(target),arr(args),arr([])]);}
const crash=frame(invoke("OnCrash",[map([["l",num(77)],["f",num(2.5)]])]));
const stage=frame(invoke("OnStage",[map([["l",num(78)]])]));
const parsed=parseSignalRFrames(Buffer.concat([crash,stage]));
assert.equal(parsed.invocations.length,2);
assert.equal(parsed.invocations[0].target,"OnCrash");
assert.equal(parsed.invocations[0].arguments[0].f,2.5);
assert.equal(parsed.invocations[1].target,"OnStage");
assert.equal(parsed.incomplete,false);

// A SignalR MessagePack frame longer than 127 bytes uses a multi-byte
// varint length prefix. Also verify a packed array of invocations.
const longTarget="OnDiagnostic"+("x".repeat(150));
const longFrame=frame(invoke(longTarget,[map([["value",num(9)]])]));
assert.ok(longFrame[0]&0x80,"long frame must use a multi-byte prefix");
const longParsed=parseSignalRFrames(longFrame);
assert.equal(longParsed.invocations.length,1);
assert.equal(longParsed.invocations[0].target,longTarget);
const bundled=frame(arr([invoke("OnStart",[]),invoke("OnStage",[num(12)])]));
const bundledParsed=parseSignalRFrames(bundled);
assert.equal(bundledParsed.invocations.length,2);
assert.deepEqual(bundledParsed.invocations.map(x=>x.target),["OnStart","OnStage"]);
const partial=parseSignalRFrames(crash.subarray(0,crash.length-2));
assert.equal(partial.invocations.length,0);
assert.equal(partial.incomplete,true);
const ignored=frame(arr([num(6),map([]),Buffer.from([0xc0])]));
assert.equal(parseSignalRFrames(ignored).invocations.length,0);

// Truncated varint prefixes must remain incomplete and must not throw.
const truncatedPrefix=parseSignalRFrames(Buffer.from([0x80,0x80]));
assert.equal(truncatedPrefix.incomplete,true);
assert.equal(truncatedPrefix.malformed,0);

// Oversized and overflowing frame lengths are rejected without scanning
// subsequent bytes as if they were a fresh frame.
const oversized=parseSignalRFrames(Buffer.concat([Buffer.from([0x83,0x80,0x80,0x03]),crash]));
assert.equal(oversized.malformed,1);
assert.equal(oversized.invocations.length,0);
const overflow=parseSignalRFrames(Buffer.concat([Buffer.from([0xff,0xff,0xff,0xff,0x10]),crash]));
assert.equal(overflow.malformed,1);
assert.equal(overflow.invocations.length,0);
console.log("MessagePack SignalR tests passed.");
