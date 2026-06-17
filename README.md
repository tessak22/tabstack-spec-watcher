# tabstack-spec-watcher

Extraction primitives that turn heterogeneous spec and changelog pages into normalized, structured JSON — using [Tabstack](https://tabstack.ai).

You decide what to do with it: monitor, one-shot, diff, alert, pipe to Slack, run in Hermes. The watcher owns the extraction and normalization. You own the pipeline.

---

## What it watches

| Source | What it tracks | Endpoint |
|--------|---------------|----------|
| **TC39** | JavaScript proposal stage changes (Stage 1→4) | `/extract` |
| **WebAssembly** | Wasm proposal phase changes (Phase 1→5) | `/extract` |
| **W3C** | Recommendations, Candidate Recommendations, Working Drafts | `/extract` |
| **Node.js** | New releases — major (breaking), minor, security patches | `/extract` |
| **TypeScript** | New releases — compiler breaking changes, new type features | `/extract` |
| **Deno** | New releases — breaking changes, security patches | `/extract` |
| **Bun** | New releases — runtime/bundler/test runner changes | `/extract` |
| **Anthropic** | API changelog, new models, deprecations, breaking changes | `/extract` |
| **OpenAI** | API changelog, model releases, deprecations | `/extract` |
| **Google AI** | Gemini API changelog, model deprecations, breaking changes | `/extract` |
| **npm ecosystem** | React, Next.js, Vue, Vite, Remix, Astro, Svelte releases | `/extract` |

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
  "affects": ["date/time handling"],
  "stage_before": "Stage 3",
  "stage_after": "Stage 4",
  "version_before": null,
  "version_after": null,
  "link": "https://github.com/tc39/proposal-temporal",
  "fetched_at": "2026-06-17T09:00:00+00:00"
}
```

`change_type`: `breaking | additive | informational`
`severity`: `high | medium | low`

`affects` is inferred from the proposal/release name and description — e.g., a TC39 proposal mentioning "date" and "timezone" returns `["date/time handling"]` rather than the generic `["JavaScript"]`.

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
python watch.py --source nodejs
python watch.py --source npm

# First run: establish baseline (no diff output)
python watch.py --snapshot-only

# One-shot: fetch current state, print, no snapshot stored
python watch.py --one-shot

# JSON output (pipe to anything)
python watch.py --format json

# Filter to breaking changes only
python watch.py --format json | python3 -c "
import json,sys
changes = json.load(sys.stdin)
print(json.dumps([c for c in changes if c['severity'] == 'high'], indent=2))
"
```

---

## Usage patterns

### Monitor (weekly cron — GitHub Actions)

See [`examples/github-actions.yml`](examples/github-actions.yml) for a complete workflow that:
- Runs every Monday at 9am UTC
- Diffs against stored snapshots
- Commits updated snapshots back to the repo
- Notifies Slack on any changes
- Escalates breaking/high-severity changes separately

### Hermes integration

See [`examples/hermes-cron.md`](examples/hermes-cron.md) for a weekly Hermes cron that delivers breaking changes to Telegram and goes `[SILENT]` when nothing changed.

### One-shot research

```bash
# What is the current state of the TC39 pipeline?
python watch.py --one-shot --source tc39

# What npm framework releases have happened recently?
python watch.py --one-shot --source npm
```

### Pipe to any downstream

```bash
# Only high-severity items
python watch.py --format json | jq '.[] | select(.severity == "high")'

# Group by source
python watch.py --format json | jq 'group_by(.source)'

# Slack message
python watch.py | xargs -I{} curl -X POST $SLACK_WEBHOOK -d "payload={\"text\":\"{}\"}"
```

---

## How diffing works

On each run, the watcher:
1. Fetches current state from each source via Tabstack `/extract`
2. Loads the previous snapshot from `./snapshots/<source>.json`
3. Diffs structurally — stage/phase changes for proposals, semver for releases, new titles for changelogs
4. Emits only what's new
5. Saves the updated snapshot

First run with `--snapshot-only` establishes the baseline. Nothing is emitted on the first run.

---

## Structure

```
watch.py                      # entry point
schema.py                     # shared SpecChange dataclass
sources/
  _utils.py                   # shared: affects inference, semver classify, shared schemas
  tc39.py                     # TC39 proposals
  wasm_proposals.py           # WebAssembly proposals
  w3c_publications.py         # W3C publications
  nodejs_releases.py          # Node.js releases
  typescript_releases.py      # TypeScript releases
  deno_releases.py            # Deno releases
  bun_releases.py             # Bun releases
  anthropic_changelog.py      # Anthropic API changelog
  openai_changelog.py         # OpenAI API changelog
  google_ai_changelog.py      # Google AI / Gemini changelog
  npm_ecosystem.py            # React, Next.js, Vue, Vite, Remix, Astro, Svelte
snapshots/                    # auto-created on first run, gitignored
examples/
  github-actions.yml          # complete GitHub Actions workflow
  hermes-cron.md              # Hermes cron setup
```

---

## API key

Get a Tabstack API key at [tabstack.ai](https://tabstack.ai).

---

## License

MIT
