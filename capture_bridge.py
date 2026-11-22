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
TARGETS = {"OnStage", "OnBetting", "OnStart", "OnCrash", "OnBets", "OnProfits"}
SCRIPT = r"""
(() => {
  if (window.__cfpCaptureInstalled) return;
  Object.defineProperty(window, '__cfpCaptureInstalled', {value:true});
  const NativeSocket = window.WebSocket;
  if (!NativeSocket) return;
  const allowed = new Set(['OnStage','OnBetting','OnStart','OnCrash','OnBets','OnProfits']);
  function inspect(raw) {
    if (typeof raw !== 'string') return;
    for (const part of raw.split('\u001e')) {
      let message;
      try { message = JSON.parse(part); } catch (_) { continue; }
      if (!message || !allowed.has(message.target)) continue;
      const a = Array.isArray(message.arguments) ? message.arguments[0] : null;
      if (!a || typeof a !== 'object') continue;
      const event = {target:message.target};
      for (const key of ['l','ln','ts']) {
        if (typeof a[key] === 'number' && Number.isFinite(a[key])) event[key] = a[key];
      }
      if (message.target === 'OnCrash' && typeof a.f === 'number' && Number.isFinite(a.f))
        event.f = a.f;
      // Do not collect bet amounts, user IDs, profits, or account information.
      console.info('__CFP_EVENT__' + JSON.stringify(event));
    }
  }
  class ObservedSocket extends NativeSocket {
    constructor(...args) {
      super(...args);
      super.addEventListener('message', ev => { try { inspect(ev.data); } catch (_) {} });
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
            permitted = {"target", "l", "ln", "ts", "f"}
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
