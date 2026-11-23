// Runs only on the published dashboard origin. The page cannot access extension APIs directly.
window.addEventListener("message", async (event) => {
  if (event.source !== window || event.origin !== location.origin) return;
  if (event.data?.source !== "crash-flight-dashboard" || event.data?.type !== "get-events") return;
  try {
    const result = await chrome.runtime.sendMessage({type:"crash-flight-get-events"});
    window.postMessage({source:"crash-flight-extension",type:"events",requestId:event.data.requestId,events:result?.events||[]}, location.origin);
  } catch (_) {
    window.postMessage({source:"crash-flight-extension",type:"unavailable",requestId:event.data.requestId}, location.origin);
  }
});