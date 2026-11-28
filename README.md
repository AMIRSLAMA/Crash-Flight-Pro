# Sky Predictor

A compact Arabic crash-round dashboard with a small animated aircraft, live round status, and a history of observed results.

## Live capture setup
1. In Chrome, open `chrome://extensions` and enable **Developer mode**.
2. Choose **Load unpacked** and select this repository's `extension` folder.
3. Open a supported game page on `1xbet.com` or `eg1xbet.com` and reload it after installing or updating the extension.
4. Open the extension popup and press **Start capture** for the current game tab. Capture is disabled by default; use **Stop capture** to stop forwarding events in that tab.
5. Open the published dashboard: https://amirslama.github.io/Crash-Flight-Pro/

The extension observes WebSocket SignalR JSON and MessagePack invocation frames only after the user enables capture in the popup. It forwards sanitized event metadata and stores recent records locally in Chrome. It does not collect login credentials, place bets, or automate gameplay.

## What the dashboard can and cannot show
- `OnStart` starts the plane animation when that event is actually observed.
- `OnCrash` ends the animation and displays the final multiplier only when the event payload contains it.
- Connection status reflects whether recent captured events are arriving.
- The aircraft moves only from a numeric live-multiplier field actually present in captured game events; it does not fake flight progress from elapsed time.
- Pre-round numeric fields are shown as observed telemetry, not interpreted as a forecast.
- An `OnCrash` event is sent after the round ends; it is **not** an early warning.
- The app does not know the next multiplier or guarantee a pre-crash alert. No prediction is displayed unless a genuinely predictive source is established and tested separately.

## Troubleshooting
If the dashboard says the extension is unavailable, confirm the extension is enabled and reload both the game tab and dashboard. If it says it is waiting for game events, the current game session may use a different host, transport, frame, or message format than the supported capture. The capture handles SignalR JSON text, legacy length-prefixed JSON frames, and SignalR MessagePack invocation frames with varint length prefixes. MessagePack support is covered by the Node test in `extension/test-messagepack.js`; explicit capture gating is tested in `extension/test-capture-optin.js`.

## Desktop analyzer
Historical desktop analyzer sources and build workflows remain in the repository.
