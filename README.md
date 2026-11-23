# Crash Flight Pro

A lightweight Arabic web dashboard for manually recording and reviewing completed Crash rounds. No Chrome extension, browser permissions, scraping, or betting automation is required.

## Web edition
Open the GitHub Pages site. Press **ابدأ تسجيل الجولة** when a round starts, then enter its final multiplier after it ends and press **تسجيل النتيجة**. You can also import/export a CSV containing a `multiplier` column. Records are stored in the browser's local storage on that device.

**Important limitation:** a normal website cannot read another tab's private game traffic or know when that game round starts/ends. Without a permitted integration supplied by the game, a browser extension, or a user-provided data export, recording is manual. This web edition deliberately does not claim automatic live capture or predict the next crash multiplier.

## Desktop analyzer
The Windows desktop historical analyzer remains available in the repository. See the source files and workflow for setup/build instructions.

## Responsible use
Historical frequencies and medians describe past records only. They do not establish a reliable signal for the next independent round. No betting automation or credential collection is implemented.
