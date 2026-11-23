# Sky Predictor

A compact Arabic crash-round monitor with a small aircraft display. The dashboard receives real round events only when the companion browser extension is installed and active on the supported game page.

## Use
1. Install the unpacked extension from the `extension` folder in Chrome.
2. Open the supported game page and use the extension popup to enable capture, then reload the game tab.
3. Open the GitHub Pages dashboard. It shows a live round state when captured events arrive and the last multiplier only when a supported crash-result field is present.

## Important limits
A standalone website cannot read another browser tab's private network traffic. Live monitoring therefore requires the companion extension or another permitted game-provided integration. A round-end event is not an early warning. The app does not claim to know the next crash point or display fabricated warnings.

The interface is intentionally compact and does not fill the screen.
