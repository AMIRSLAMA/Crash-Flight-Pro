/* SignalR MessagePack hub-protocol decoder. */
(function (root) {
 "use strict";
 function decodeMessagePack(input) {
  const bytes=input instanceof Uint8Array?input:new Uint8Array(input);
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
  let offset=0;
  function need(n){if(offset+n>bytes.length)throw new RangeError("truncated MessagePack value");}
  function take(n){need(n);const out=bytes.subarray(offset,offset+n);offset+=n;return out;}
  function u8(){need(1);return bytes[offset++];}
  function u16(){need(2);const n=view.getUint16(offset);offset+=2;return n;}
  function u32(){need(4);const n=view.getUint32(offset);offset+=4;return n;}
  function i8(){need(1);const n=view.getInt8(offset);offset++;return n;}
  function i16(){need(2);const n=view.getInt16(offset);offset+=2;return n;}
  function i32(){need(4);const n=view.getInt32(offset);offset+=4;return n;}
  function f32(){need(4);const n=view.getFloat32(offset);offset+=4;return n;}
  function f64(){need(8);const n=view.getFloat64(offset);offset+=8;return n;}
  function str(n){return new TextDecoder().decode(take(n));}
  function uint64(){need(8);const hi=view.getUint32(offset),lo=view.getUint32(offset+4);offset+=8;const n=hi*4294967296+lo;return Number.isSafeInteger(n)?n:String(hi)+":"+String(lo);}
  function int64(){need(8);const hi=view.getInt32(offset),lo=view.getUint32(offset+4);offset+=8;const n=hi*4294967296+lo;return Number.isSafeInteger(n)?n:String(hi)+":"+String(lo);}
  function read(depth){
   if(depth>48)throw new RangeError("MessagePack nesting limit");
   const c=u8();
   if(c<=0x7f)return c;
   if(c>=0xe0)return c-256;
   if((c&0xf0)===0x80){const n=c&15,o={};for(let i=0;i<n;i++){const k=read(depth+1);o[String(k)]=read(depth+1);}return o;}
   if((c&0xf0)===0x90){const n=c&15,o=[];for(let i=0;i<n;i++)o.push(read(depth+1));return o;}
   if((c&0xe0)===0xa0)return str(c&31);
   switch(c){
    case 0xc0:return null;case 0xc2:return false;case 0xc3:return true;
    case 0xc4:return take(u8());case 0xc5:return take(u16());case 0xc6:return take(u32());
    case 0xca:return f32();case 0xcb:return f64();
    case 0xcc:return u8();case 0xcd:return u16();case 0xce:return u32();case 0xcf:return uint64();
    case 0xd0:return i8();case 0xd1:return i16();case 0xd2:return i32();case 0xd3:return int64();
    case 0xd9:return str(u8());case 0xda:return str(u16());case 0xdb:return str(u32());
    case 0xdc:{const n=u16(),o=[];for(let i=0;i<n;i++)o.push(read(depth+1));return o;}
    case 0xdd:{const n=u32(),o=[];if(n>100000)throw new RangeError("array too large");for(let i=0;i<n;i++)o.push(read(depth+1));return o;}
    case 0xde:{const n=u16(),o={};for(let i=0;i<n;i++){const k=read(depth+1);o[String(k)]=read(depth+1);}return o;}
    case 0xdf:{const n=u32(),o={};if(n>100000)throw new RangeError("map too large");for(let i=0;i<n;i++){const k=read(depth+1);o[String(k)]=read(depth+1);}return o;}
    case 0xc7:{const n=u8();u8();return take(n);}case 0xc8:{const n=u16();u8();return take(n);}case 0xc9:{const n=u32();u8();return take(n);}
    case 0xd4:u8();return take(1);case 0xd5:u8();return take(2);case 0xd6:u8();return take(4);case 0xd7:u8();return take(8);case 0xd8:u8();return take(16);
    default:throw new Error("unsupported MessagePack code 0x"+c.toString(16));
   }
  }
  const result=read(0);if(offset!==bytes.length)throw new Error("trailing MessagePack bytes");return result;
 }
 function parseSignalRFrames(input){
  const bytes=input instanceof Uint8Array?input:new Uint8Array(input);
  const invocations=[];let offset=0,incomplete=false,malformed=0;
  while(offset<bytes.length){
   const frameStart=offset;let length=0,multiplier=1,prefixDone=false,invalidPrefix=false;
   for(let i=0;i<5;i++){
    if(offset>=bytes.length){incomplete=true;offset=frameStart;break;}
    const b=bytes[offset++],chunk=b&127;
    // A uint32 varint has at most four bits in its fifth byte.
    if(i===4&&(chunk>15||(b&128))){invalidPrefix=true;break;}
    length+=chunk*multiplier;
    if(!(b&128)){prefixDone=true;break;}
    multiplier*=128;
   }
   if(incomplete)break;
   // Do not scan arbitrary payload bytes for a new frame after a bad length prefix.
   if(invalidPrefix||!prefixDone||length<=0||length>4194304){malformed++;offset=frameStart;break;}
   if(offset+length>bytes.length){incomplete=true;offset=frameStart;break;}
   try{
    const decoded=decodeMessagePack(bytes.subarray(offset,offset+length));
    const messages=Array.isArray(decoded)&&Array.isArray(decoded[0])?decoded:[decoded];
    for(const m of messages){
     // SignalR MessagePack InvocationMessage: [1, headers, invocationId, target, arguments, streamIds]
     if(Array.isArray(m)&&m[0]===1&&typeof m[3]==="string"&&Array.isArray(m[4]))
      invocations.push({type:1,target:m[3],arguments:m[4]});
    }
   }catch(_){malformed++;}
   offset+=length;
  }
  return {invocations,incomplete,malformed,consumedBytes:offset};
 }
 root.CrashFlightMessagePack={decodeMessagePack,parseSignalRFrames};
 if(typeof module!=="undefined"&&module.exports)module.exports=root.CrashFlightMessagePack;
})(typeof globalThis!=="undefined"?globalThis:this);
