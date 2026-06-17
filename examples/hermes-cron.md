# Hermes Integration

Run `tabstack-spec-watcher` as a weekly Hermes cron job that delivers breaking changes to Telegram.

## Setup

1. Make sure `tabstack-spec-watcher` is cloned somewhere on your machine (e.g., `~/projects/tabstack-spec-watcher`).

2. Run the baseline snapshot first:

```bash
cd ~/projects/tabstack-spec-watcher
TABSTACK_API_KEY=your_key python watch.py --snapshot-only
```

3. Create the Hermes cron with this prompt:

```
Run tabstack-spec-watcher and report any new spec/API changes.

Steps:
1. cd ~/projects/tabstack-spec-watcher
2. Run: TABSTACK_API_KEY=$TABSTACK_API_KEY python watch.py --format json
3. Parse the JSON output.
4. If the array is empty, go [SILENT] — nothing to report.
5. If there are changes:
   - Group by severity: high first, then medium, then low.
   - Format each change as:
     🔴 [BREAKING] {source} — {name}
     {summary}
     Affects: {affects joined by ", "}
     {link}
   - Use 🟡 for additive, ℹ️ for informational.
   - Deliver to Telegram with header: "**Spec Watcher — {date}**"
6. After delivering, update snapshots: python watch.py --snapshot-only
```

Schedule: `0 9 * * 1` (every Monday at 9am)

## Severity routing

- `severity: high` or `change_type: breaking` → immediate ping
- Everything else → weekly digest

To get immediate pings on breaking changes only, create a second cron that filters:

```python
import json, subprocess
result = subprocess.run(
    ["python", "watch.py", "--format", "json"],
    capture_output=True, text=True
)
changes = json.loads(result.stdout or "[]")
breaking = [c for c in changes if c["severity"] == "high"]
if breaking:
    print(json.dumps(breaking))
# else: [SILENT]
```

## What [SILENT] means

When `watch.py` returns `[]`, there are no changes since the last run.
The Hermes cron should output nothing — no "no changes detected" message,
no empty report. Just silence. The absence of a message is the signal.
