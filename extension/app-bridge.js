// Runs only on the published dashboard origin. The page cannot access extension APIs directly.
window.addEventListener("message", async (event) => {
  if (event.source !== window || event.origin !== location.origin) return;
  if (event.data?.source !== "crash-flight-dashboard" || event.data?.type !== "get-events") return;
  try {
    if (!globalThis.chrome?.runtime?.sendMessage) throw new Error("Extension runtime unavailable");
    const result = await chrome.runtime.sendMessage({type:"crash-flight-get-events"});
    if (!result || !Array.isArray(result.events)) throw new Error("No event list returned");
    window.postMessage({source:"crash-flight-extension",type:"events",requestId:event.data.requestId,events:result.events}, location.origin);
  } catch (error) {
    window.postMessage({source:"crash-flight-extension",type:"unavailable",requestId:event.data.requestId,error:String(error?.message||error)}, location.origin);
  }
});
