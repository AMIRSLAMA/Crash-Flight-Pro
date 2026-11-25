# Crash Flight — Pre-round Forensic Audit

This is a separate research branch. It does not modify the existing capture engine or the main branch.

## What it tests
It examines exported `crash-flight-events.jsonl` records and asks one narrow, falsifiable question:

**Did an explicitly named crash-multiplier field arrive for the same round before its `OnStart` event, and did it later match `OnCrash`?**

The analyzer intentionally does not treat generic numeric values or `OnProfits` curve coordinates (`u/v`) as a crash prediction. Those values may describe animation/progress rather than the final outcome.

## Run on Windows
1. Export the events from the extension popup as `crash-flight-events.jsonl`.
2. Open a terminal in this folder.
3. Run:

```powershell
py -m unittest -v
py pre_round_audit.py .\crash-flight-events.jsonl
```

The report is written to `pre-round-audit-report.json`.

## Interpretation
- A candidate is only counted when its event is linked to a round and precedes `OnStart`.
- Exact matches are reported separately from mismatches.
- Zero candidates means this capture did not expose an explicitly named pre-start multiplier field; it does not prove that no other source exists.
- A match in one or a few rounds is not proof of a reliable leak. Repeated, out-of-sample matches and an understood protocol field are required.
- This is a read-only research tool. It does not place bets, automate cash-outs, access account credentials, or bypass access controls.
