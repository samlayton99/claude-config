---
name: setup-experiments
description: >-
  Scaffold a rigorous, reproducible research-experiment repository — for ANY field, not just ML.
  Lays down the folder structure (papers/, src/ core library, flat experiments/, results/ mirrored and
  grouped by checkpoint, docs/ roadmap, tests/), a self-contained CLAUDE.md house-contract, an
  experiment template (config.yaml + run.py), and the per-experiment writeup discipline (8-part
  template, voice/number rules, figure-legend rules) plus a global results.md summary. Use when the user
  wants to start a new research project, "set up experiments", scaffold a science/research repo, create
  an experiment workspace, or get the precisionMLPs-style structure for a new investigation. Triggers:
  "/setup-experiments", "set up experiments", "scaffold a research repo", "new research project",
  "start an experiment workspace", "give me the experiment structure for X".
---

# setup-experiments

Stand up a **research-experiment repository** with a structure that stays organized as experiments
accumulate, and a writeup discipline that keeps results honest and synthesizable. Field-agnostic: the
value is the *organization and conventions*, not any domain code. This is the general, rigor-first
cousin of `dl-trainer` (which is ML-training-specific).

Call it once at the start of a research project. It does not generate domain code or pick methods —
it builds the skeleton and the contract, then you fill in the science.

## What it produces

```
<repo>/
  CLAUDE.md        the house contract — research question, architecture, conventions, the 8-part
                   writeup template, success criterion. Self-contained (no dependency on this skill).
  papers/          papers / specs / reference data that guide the work (tracked).
  src/             core reusable library experiments import (starts minimal; grows by promotion).
  experiments/     ONE FLAT folder per experiment (expXNN_name) — config.yaml + run.py. _template/ included.
  results/         mirrors experiments/, grouped by checkpoint; only writeups + results.md tracked.
  docs/            roadmap.md (the design spec, read every time) + thoughts.md (scratch).
  tests/           unit + verification tests.
  .gitignore       tracks writeups; ignores raw data/figures.
```

The two load-bearing ideas: **experiments are flat, results mirror them grouped by checkpoint**; and
**every experiment gets one writeup following a fixed 8-part template**, with a single global
`results.md` synthesizing across them.

## Workflow

### 1. Short interview (don't over-ask)

The structure is fixed; only the *content* varies. Gather just enough to fill the CLAUDE.md and roadmap,
and explicitly stub what is not yet decided (the templates carry `<FILL: ...>` markers for this — fill
what's known, leave a clear stub for the rest). Ask, in one or two rounds:

- **Research question** — the central question in 1-3 sentences, and any framing hypotheses / failure
  modes / sub-questions.
- **Success criterion** — the concrete, measurable bar that means the question is answered.
- **Source material** — what's in `papers/` (papers, specs, datasets-of-record), and any sibling repos
  worth consulting.
- **Phases (checkpoints)** — if the user already sees the arc (e.g. A: validation, B: scaling, ...),
  capture it; if not, leave one stub checkpoint and move on.
- **Runtime / reproducibility standard** — language, precision/seed conventions (e.g. "Python, float64,
  fixed seeds"). Default to Python if unsaid.

If the project is still vague, that is fine — scaffold anyway and leave rich stubs; the roadmap is meant
to be worked through with the owner over time.

### 2. Emit the skeleton (deterministic — do not hand-build it)

```
python ~/.claude/skills/setup-experiments/scripts/scaffold.py \
    --dest <repo-dir> --project "<Project Name>" [--group checkpoint]
```

`--group` is the experiment-grouping term (default `checkpoint`). The script is **safe on existing
repos** — it skips files that already exist unless `--force`. Never pass `--force` to a repo holding real
work.

### 3. Fill the placeholders from the interview

Edit the `<FILL: ...>` markers — fill what the interview established, leave a clear stub otherwise. Order:

1. **CLAUDE.md** — Research Question, Key Abstractions (stub until `src/` exists), Success Criterion, and
   any project-specific Conventions (the reproducibility line especially).
2. **docs/roadmap.md** — Central question, Success criterion, the decisive arc (top 1-3 experiments).
3. **results/results.md** — "the story so far" (a one-paragraph stub of the question + plan until there
   are results).

Grep the repo for `<FILL:` afterward and confirm each remaining one is a *deliberate* stub, not an
oversight. Keep the embedded writeup template, conventions, and figure rules intact — they are the point.

### 4. Seed the first experiment (optional)

If a first experiment is clear, copy `experiments/_template/` to `experiments/expA01_<name>/`, set its
`config.yaml` (`group`, `group_name`, knobs), and adapt `run.py`. Otherwise leave `_template/` as the
pattern to copy later.

### 5. Verify and initialize

- Confirm the tree exists and CLAUDE.md reads correctly for this project.
- `git init` if this is a new repo (the `.gitignore` is already in place).
- Remind the owner: read `docs/roadmap.md` every time; one writeup per experiment; `results.md` is the
  only global doc.

## The conventions you are preserving (why they matter)

These live in the scaffolded CLAUDE.md so the repo is self-sufficient — do not water them down:

- **Flat experiments, mirrored grouped results.** Keeps `run.py`'s repo-root path constant while results
  stay organized for cross-experiment synthesis.
- **The 8-part writeup template** (Title+Status → TL;DR → Question → Design → Results+Figures → Additional
  details → Conclusions → Open questions). The **design** section earns depth; **conclusions** are
  signed-off-only; **open questions** re-aggregate into `results.md`.
- **Voice/number discipline** — plain language, cut the TL;DR-restated-as-Conclusions redundancy, spend
  raw numbers like currency.
- **Figure legends outside the axes**; math in LaTeX; prose not hard-wrapped.
- **Prove new machinery with tests** before relying on it.

A concrete, well-formed instance of the writeup template is in
`~/.claude/skills/setup-experiments/references/example-writeup.md` — show it to the user or drop a copy
into the repo as a model if helpful.
