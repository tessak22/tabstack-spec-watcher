# tabstack-spec-watcher

Extraction primitives that turn heterogeneous spec and changelog pages into normalized, structured JSON — using [Tabstack](https://tabstack.ai).

You decide what to do with it: monitor, one-shot, diff, alert, pipe to Slack, run in Hermes. The watcher owns the extraction and normalization. You own the pipeline.

---

## What it watches

| Source | What it tracks | Endpoint |
|--------|---------------|----------|
| TC39 | JavaScript proposal stage changes (Stage 1 → 4) | `/extract` |
| Anthropic | API changelog, new models, deprecations, breaking changes | `/extract` |
| OpenAI | API changelog, model releases, deprecations | `/extract` |

More sources in v2: WHATWG, W3C, IETF, Google AI.

---

## Output schema

Every source returns the same shape:

```json
{
  "source": "TC39",
  "name": "Temporal",
  "change_type": "breaking",
  "severity": "high",
  "summary": "Temporal advanced from Stage 3 to Stage 4: date/time API replacing legacy Date",
  "affects": ["JavaScript", "date handling"],
  "stage_before": "Stage 3",
  "stage_after": "Stage 4",
  "version_before": null,
  "version_after": null,
  "link": "https://github.com/tc39/proposal-temporal",
  "fetched_at": "2026-06-17T09:00:00+00:00"
}
```

`change_type` is one of `breaking | additive | informational`.  
`severity` is one of `high | medium | low`.

---

## Install

```bash
pip install tabstack
export TABSTACK_API_KEY=your_key_here
```

---

## Usage

```bash
# Run all sources, diff against last snapshot, print changes
python watch.py

# Single source
python watch.py --source tc39

# First run: establish baseline (no diff output)
python watch.py --snapshot-only

# One-shot: fetch current state, print, no snapshot stored
python watch.py --one-shot

# JSON output (pipe to anything)
python watch.py --format json
```

---

## Usage patterns

### Monitor (weekly cron)

```bash
# GitHub Actions — .github/workflows/spec-watch.yml
on:
  schedule:
    - cron: '0 9 * * 1'   # Every Monday 9am UTC
  workflow_dispatch:

jobs:
  watch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install tabstack
      - run: python watch.py --format json > changes.json
      - name: Notify Slack if changes found
        run: |
          if [ -s changes.json ] && [ "$(cat changes.json)" != "[]" ]; then
            curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
              -H 'Content-type: application/json' \
              -d "{\"text\": \"$(python watch.py)\"}"
          fi
        env:
          TABSTACK_API_KEY: ${{ secrets.TABSTACK_API_KEY }}
```

### One-shot research

```bash
# Just tell me what the current state is
python watch.py --one-shot --source tc39
```

### Pipe to any downstream tool

```bash
python watch.py --format json | jq '.[] | select(.severity == "high")'
```

---

## Hermes integration

If you're running [Hermes](https://hermes-agent.nousresearch.com), you can wire this as a weekly cron that delivers breaking changes directly to your Telegram:

```
Run weekly: python watch.py --format json
→ filter for severity=high or change_type=breaking
→ deliver to Telegram as a formatted report
→ [SILENT] if nothing changed
```

See `examples/hermes-cron.md` for the full setup.

---

## Structure

```
watch.py               # entry point
schema.py              # shared SpecChange dataclass
sources/
  tc39.py              # TC39 proposals (GitHub)
  anthropic_changelog.py
  openai_changelog.py
snapshots/             # auto-created on first run, gitignored
examples/              # usage patterns (GitHub Actions, Hermes)
```

---

## API key

Get a Tabstack API key at [tabstack.ai](https://tabstack.ai).

---

## License

MIT
