"""Opt-in, best-effort in-page WebSocket event observer.

Only whitelisted round metadata is forwarded via console messages. Never stores
raw frames, cookies, headers, URLs, credentials, player IDs, or bet details.
Some games block instrumentation or use other transports.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript

PREFIX = "__CFP_EVENT__"
TARGETS = {"OnRegistration", "OnStage", "OnBetting", "OnStart", "OnCrash"}
SCRIPT = r"""
(() => {
  if (window.__cfpCaptureInstalled) return;
  Object.defineProperty(window, '__cfpCaptureInstalled', {value:true});
  const NativeSocket = window.WebSocket;
  if (!NativeSocket) return;
  // Event names and minimal fields verified against the Crash-Game-Source client.
  const allowed = new Set(['OnRegistration','OnStage','OnBetting','OnStart','OnCrash']);
  const stages = {planned:0,waiting:1,betting:2,started:3,ended:4,closed:5};
  function finiteNumber(v) {
    if (typeof v === 'number' && Number.isFinite(v)) return v;
    return null;
  }
  function inspect(raw) {
    if (typeof raw !== 'string') return;
    for (const part of raw.split('\u001e')) {
      if (!part) continue;
      let parsed;
      try { parsed = JSON.parse(part); } catch (_) { continue; }
      const frames = Array.isArray(parsed) ? parsed : [parsed];
      for (const message of frames) {
        if (!message || typeof message !== 'object' || !allowed.has(message.target)) continue;
        const a = Array.isArray(message.arguments) ? message.arguments[0] : null;
        if (!a || typeof a !== 'object' || Array.isArray(a)) continue;
        const event = {target:message.target};
        if ((typeof a.l === 'string' && a.l.length < 60) ||
            (typeof a.l === 'number' && Number.isSafeInteger(a.l))) event.l = a.l;
        for (const key of ['ln','ts']) {
          const value = finiteNumber(a[key]);
          if (value !== null) event[key] = value;
        }
        if (message.target === 'OnRegistration') {
          const stage = finiteNumber(a.s);
          if (stage !== null) event.s = stage;
          // Client checkStage consumes registration.p only for ended/closed states.
          if (stage === stages.ended || stage === stages.closed) {
            const final = finiteNumber(a.p);
            if (final !== null && final >= 1) event.p = final;
          }
        }
        if (message.target === 'OnCrash') {
          const final = finiteNumber(a.f);
          if (final !== null && final >= 1) event.f = final;
        }
        if (message.target === 'OnBetting') {
          const windowMs = finiteNumber(a.a);
          if (windowMs !== null && windowMs >= 0) event.a = windowMs;
        }
        // Do not collect account info, betting details, headers, URLs or raw frames.
        console.info('__CFP_EVENT__' + JSON.stringify(event));
      }
    }
  }
  class ObservedSocket extends NativeSocket {
    constructor(...args) {
      super(...args);
      this.addEventListener('message', ev => {
        try { inspect(ev.data); } catch (_) {}
      });
    }
  }
  window.WebSocket = ObservedSocket;
})();
"""


class CapturePage(QWebEnginePage):
    def __init__(self, profile, store_path, parent=None):
        super().__init__(profile, parent)
        self.store_path = Path(store_path)
        self.capture_enabled = False
        self.events_seen = 0
        self.on_event = None

    def install_capture(self):
        script = QWebEngineScript()
        script.setName("Crash Flight Pro opt-in event observer")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)
        script.setSourceCode(SCRIPT)
        self.scripts().insert(script)

    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        if not self.capture_enabled or not message.startswith(PREFIX):
            return
        try:
            data = json.loads(message[len(PREFIX):])
            if data.get("target") not in TARGETS:
                return
            permitted = {"target", "l", "ln", "ts", "f", "s", "p", "a"}
            if any(key not in permitted for key in data):
                return
            record = {
                "received_at_utc": datetime.now(timezone.utc).isoformat(),
                **data,
            }
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            with self.store_path.open("a", encoding="utf-8") as output:
                output.write(json.dumps(record) + "\n")
            self.events_seen += 1
            if self.on_event:
                self.on_event(record)
        except (ValueError, OSError, TypeError):
            pass
