# Retirement Model — Visualization Ideas

**Status:** Ideas / decision doc — nothing built yet.
**Companion to:** `retirement_projection.py` (the engine), `retirement_plan.yaml` (tracking),
`MODEL_VALIDATION.md` (audit + scenario knobs).
**Question being captured:** how to put interactive levers + charts on top of the model.

---

## 1. Why this is easy now (the precondition is already met)

The engine is a **pure, fast, fully-tested function**: `simulate(Params) -> (survived,
ending_balance, year_by_year_history)`. No hidden state, no file I/O, ~250 lines of
stdlib Python, sub-millisecond per run (2,000 Monte Carlo paths in well under a second),
and every lever already a field on the `Params` dataclass. The 41-test suite pins its
outputs.

**Consequence:** a dashboard is a *thin shell* over `simulate(Params)`, not a project.
The hard part — a trustworthy engine — is done. The only real decisions are (a) where the
Python runs and (b) how we keep the displayed numbers honest.

**Two non-negotiables for any option below:**
1. **Single source of truth.** The numbers a dashboard shows must come from the tested
   Python engine — or, if an option reimplements the math, a test must prove the
   reimplementation reproduces the Python (golden JSON fixtures). We spent two PRs
   eliminating model drift; a viz layer must not quietly reintroduce it.
2. **YAML stays the baseline, not a scratchpad.** `retirement_plan.yaml` is the saved
   checkpoint record. A dashboard should *load* it to seed slider defaults, then let
   levers move in memory. Persisting every slider drag back into the YAML would pollute
   the tracking document. If we ever want to keep an explored scenario, that's an
   explicit "save named scenario" action, not an auto-write.

---

## 2. Correcting one part of the original framing

The initial idea floated a **"model script in a loop to update in real time"** or a
**"file-watcher triggered when the YAML changes."** Both are over-engineering for this
engine. Polling loops and watchers exist for slow or stateful computations; `simulate()`
is a pure microsecond function. The correct interaction is simply:

> **lever changes → recompute → re-render**, synchronously.

No daemon, no polling, no trigger. (A YAML file-watcher is fine as a *developer*
convenience while editing, but it is not the core interaction model.)

---

## 3. The options

All paths are viable because the engine is pure. They differ mainly in **where the Python
runs** and **whether a second copy of the model is introduced**.

### Option A — Static HTML with a precomputed lever grid  ⭐ recommended for "in this repo"
A `generate_retirement_dashboard.py` runs the model across a grid of lever positions and
bakes the results into **one self-contained HTML file**. JS sliders index the precomputed
data; moving a slider just looks up the matching result and redraws.

- **Fits the repo's established ethos exactly** — `generate_dashboard.py` already does this
  for budgets: stdlib-only Python, no external JS dependencies, output is a single HTML file
  you open in a browser.
- Numbers come straight from the tested Python (baked at generate-time) → source-of-truth
  guarantee holds for free.
- **Trade-off:** levers are *discrete* (grid steps), not continuous; the file grows with the
  cartesian product of lever values, so pick a sane set (e.g. retire age, spend, return,
  claim age, side-income on/off, conversions on/off).
- **Effort:** low.

### Option B — Streamlit app  ⭐ recommended for "private tool, least effort"
`streamlit run retirement_dashboard.py`. Sliders bind directly to `Params`, the model
recomputes live on every change, charts render with ~zero frontend code.

- **Lowest effort** for true *continuous* sliders + charts; pure Python, calls `simulate()`
  directly so source-of-truth is automatic.
- **Trade-off:** needs a running Python process (`streamlit run`) and adds a heavy
  dependency — not a static artifact, not something that lives as a committed HTML file.
- **Best when:** it's a private exploration tool for the two of us and "run a command to
  launch it" is acceptable.
- **Effort:** lowest.

### Option C — FastAPI (or Flask) backend + React frontend
A small Python HTTP API wraps `simulate()`; a React frontend sends `Params` as JSON, gets
back the history + outcomes, and renders continuous sliders with a charting lib (Recharts /
visx).

- True continuous levers, polished UX, recompute is sub-100ms so it feels instant.
- Source-of-truth holds (React just renders what the Python API returns).
- **Trade-off:** it's a real app — a server to run + a JS build toolchain + a JS dependency
  tree, a clear departure from the repo's current no-JS-deps norm.
- **Effort:** medium-high.

### Option D — Port the model to TypeScript, run entirely in the browser
Rewrite the ~250 lines of engine in TS; ship a fully static React site (deployable to
GitHub Pages) with instant continuous levers and no server at all.

- Best for a **hosted, shareable, server-free** web app.
- **Trade-off — the big one:** it reintroduces the exact drift risk we just spent two PRs
  removing — *two* implementations of the model that can silently disagree.
- **Only acceptable with a cross-check test:** generate golden JSON fixtures from the Python
  engine and assert the TS port reproduces them in CI. Without that, the single-source-of-
  truth guarantee is gone.
- **Effort:** medium + ongoing maintenance.

### Option D′ — Pyodide (the clever middle path)
Run the *actual* Python engine in the browser via WebAssembly (Pyodide). Static site, no
server, **one** implementation (no drift), real continuous levers.

- **Trade-off:** a multi-MB Pyodide download on first load, and a more involved build.
- **Best when:** we want a static/shareable site but refuse to maintain a second copy of
  the model.

---

## 4. Comparison

| Option | Levers | Server? | JS deps? | 2nd model copy? | Fits repo ethos | Effort |
|---|---|---|---|---|---|---|
| **A. Static HTML + precomputed grid** | discrete | no | none | no | ✅ strong | low |
| **B. Streamlit** | continuous | yes (local) | none | no | ⚠️ heavy dep | lowest |
| **C. FastAPI + React** | continuous | yes | yes | no | ⚠️ departs | med-high |
| **D. TS port, in-browser** | continuous | no | yes | **yes (risk)** | ❌ | med + upkeep |
| **D′. Pyodide** | continuous | no | (wasm) | no | ⚠️ heavy load | medium |

---

## 5. Recommendation

- **Ship-today, lives-in-repo:** **Option A.** Discrete-but-rich levers, zero runtime deps,
  one self-contained HTML file, numbers traceable to the tested Python. Honest extension of
  the existing dashboard generator.
- **Private continuous-lever tool, minimal effort:** **Option B (Streamlit).**
- **Hosted/shareable web app:** **Option D′ (Pyodide)** over D (TS port), to avoid a second
  model implementation. If D is chosen anyway, the golden-fixture cross-check is mandatory.

Suggested levers to expose first (all already on `Params`): retire age, annual spend, real
return, taxable savings, SS claim age, side income (amount + window), conversions on/off,
SS haircut. Suggested displays: the year-by-year portfolio trajectory (stacked by
bucket: taxable / tax-deferred / Roth), the survive-vs-deplete verdict + ending balance,
and — if cheap enough at runtime — the Monte Carlo success rate.

---

## 6. Open questions before building

1. **Audience:** just us (favors B), or shareable with an advisor / family (favors A or D′)?
2. **Hosting:** open a local file (A), run a command (B), or a real URL (C/D/D′)?
3. **Continuous vs discrete levers:** is grid-stepping (A) acceptable, or is smooth dragging
   required (B/C/D/D′)?
4. **Monte Carlo live?** Showing the success probability interactively is the most
   compute-heavy piece — fine server-side or in Pyodide, needs precompute in Option A.
5. **Scenario saving:** do we ever want to persist a named "what-if" (e.g. to compare runs),
   and if so, where — a separate scenarios file, not the checkpoint YAML.
