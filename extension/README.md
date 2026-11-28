# Crash Flight Pro browser capture — experimental

Chrome/Edge extension. Open `chrome://extensions` or `edge://extensions`, enable Developer mode, select **Load unpacked**, and choose this extension folder.

Open a supported game tab and reload it after installing/updating the extension. Capture starts **disabled**. Click the extension icon, then **Start capture** to enable forwarding in the current tab; use **Stop capture** when finished. The popup reports if an older injected version remains and the page must be reloaded.

This proof-of-concept observes WebSocket connections created after injection and may miss game connections that start before it. Export JSONL and import into the web dashboard. It does not automatically connect to the dashboard, cannot bypass site isolation, does not extract credentials, and cannot guarantee a future multiplier. The event schema has not been verified against live 1xBet messages. Do not bet based on its output.
