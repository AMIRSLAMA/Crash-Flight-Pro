# Sky Predictor

A compact Arabic crash-round dashboard with a small animated aircraft, live round status, and a history of observed results.

## Live capture setup
1. In Chrome, open `chrome://extensions` and enable **Developer mode**.
2. Choose **Load unpacked** and select this repository's `extension` folder.
3. Open the supported game page on `1xbet.com` or `eg1xbet.com` and reload it after installing the extension.
4. Open the published dashboard: https://amirslama.github.io/Crash-Flight-Pro/

The extension observes supported WebSocket SignalR JSON events and forwards sanitized round events to the dashboard. It stores recent event metadata locally in Chrome. It does not collect login credentials, place bets, or automate gameplay.

## What the dashboard can and cannot show
- `OnStart` starts the plane animation when that event is actually observed.
- `OnCrash` ends the animation and displays the final multiplier only when the event payload contains it.
- Connection status reflects whether recent captured events are arriving.
- The aircraft moves only from a numeric live-multiplier field actually present in captured game events; it does not fake flight progress from elapsed time.
- Pre-round numeric fields are shown as observed telemetry, not interpreted as a forecast.
- An `OnCrash` event is sent after the round ends; it is **not** an early warning.
- The app does not know the next multiplier or guarantee a pre-crash alert. No prediction is displayed unless a genuinely predictive source is established and tested separately.

## Troubleshooting
If the dashboard says the extension is unavailable, confirm the extension is enabled and reload both the game tab and dashboard. If it says it is waiting for game events, the current game session may use a different host, transport, frame, or message format than the supported capture. The capture currently handles SignalR JSON text and length-prefixed JSON frames; it does not decode MessagePack.

## Desktop analyzer
Historical desktop analyzer sources and build workflows remain in the repository.

## Optional Crash Live Collector bridge

Version 0.3.1 can forward only completed `OnCrash` results (round ID and final multiplier) to a collector running on the operator's own machine at `http://127.0.0.1:3038`. Other captured event metadata remains in local Chrome storage.

To connect to the private VPS collector, open an SSH local-forward tunnel on the same Windows computer where Chrome runs:

```powershell
ssh -N -L 3038:127.0.0.1:3038 amir@100.91.140.35
```

Keep that terminal open while capturing. The collector remains bound to the VPS loopback interface; do not expose port 3038 publicly or through Funnel. If the tunnel is unavailable, the extension keeps the sanitized event locally and logs a warning; export remains available as a fallback. Duplicate round IDs are treated as already imported.

The bridge sends no cookies, credentials, account identifiers, raw WebSocket frames, or betting data. Forwarding occurs only for a completed `OnCrash` event containing a numeric final multiplier and round ID. This is result collection, not advance prediction.
