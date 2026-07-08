# {{project}}

> Scaffolded by the `setup-experiments` skill. This file is the house contract: it keeps work
> reproducible and the codebase from rotting as experiments accumulate. Read it before adding
> anything. Placeholders marked `<FILL: ...>` are for the project owner to complete — fill what is
> known now and leave a clear stub for what is not yet decided; do not delete a placeholder, replace it.

## Research Question

<FILL: the central question in 1-3 sentences. What are you trying to find out, and why does it matter?>

<FILL (optional): the specific hypotheses / failure modes / sub-questions that frame the work, as a
numbered list. In precisionMLPs this was "three violations explain the gap"; yours may differ.>

## How to Succeed

1. **Get context first.** The material guiding this work lives in `papers/` (papers, specs,
   datasets-of-record, prior art). Read the relevant pieces before designing an experiment — do not
   reinvent what a source already settles. <FILL: name the key source(s) and what each is for.>
2. **Read `docs/roadmap.md` every time.** It is the single design-spec doc and the place to pick up:
   the central question, the prioritized experiment arc, and live open questions. Work through it with
   the owner.
3. **Use neighboring/related repos as resources, not as things to copy.** <FILL: list any sibling repos
   or reference implementations worth consulting; delete this line if none.>
4. **When you build new machinery, prove it.** Write tests that show the implementation actually matches
   the intent (e.g. a known-answer case reaches the precision/accuracy it should). Communicate those
   tests clearly to the owner before relying on the machinery.

## Architecture

```
papers/         Source material that guides everything (papers, specs, reference data, prior art).
src/            Core reusable library. Shared code that experiments IMPORT — never copy.
                Grows by deliberate promotion (rule of three), not per-run edits. See src/README.md.
experiments/    ONE FLAT folder per experiment: expXNN_name/ (X = {{group}} letter, NN = number).
                Each is self-contained: a config (config.yaml) + a runnable script (run.py) that
                imports from src/, runs, analyzes, and saves. Flat — NOT nested under {{group}}s —
                so run.py can resolve the repo root by a fixed parent depth.
results/        Mirrors experiments/, grouped by {{group}}: results/{{group}}_<X>_<name>/expXNN_name/.
                Per-experiment writeup expXNN_results.md lives here; raw data/figures land here too
                (gitignored). The only global doc is results/results.md.
docs/           roadmap.md (the design spec — read every time) + thoughts.md (scratch) + any theory.
tests/          Unit tests, including the verification tests for new machinery.
```

The split is deliberate: **experiments stay flat** (so the repo-root path is constant), while
**results stay grouped** by {{group}} (so cross-experiment synthesis is organized). A new idea or
one-off analysis is a new experiment folder; a sweep over variants is still one folder.

## Key Abstractions

<FILL: the core reusable pieces in src/ that experiments build on — name each, one line on what it is
and its contract. Examples of the shape (from precisionMLPs): a config dataclass where every field has
a default and YAML overrides only what it needs; a metrics collector that logs a fixed metric set as
JSONL; an immutable result dataclass that is pure data. Leave a stub here until src/ takes shape.>

## Conventions

- **Configuration.** Each experiment carries a `config.yaml` that overrides only what it needs; sensible
  defaults live in the shared schema/loader in `src/`. Sweeps are expressed in the config and expanded
  in `run.py`.
- **Self-contained `run.py`.** Each experiment's `run.py` imports from `src/`, resolves the repo root by
  a fixed parent depth (`REPO_ROOT = Path(__file__).resolve().parents[2]`), runs, does its OWN analysis,
  and writes results to its mirrored `results/` path. No pre-built analysis module — analysis is
  per-experiment.
- **Structured, machine-readable output.** Metrics as JSONL (append-only, one record per eval step);
  the resolved config saved alongside. So results can be re-aggregated and figures regenerated without
  recomputing.
- **Don't recompute.** Figures are regenerated from saved data, never by re-running the experiment.
- **Reproducibility.** <FILL: fix seeds; record the runtime/version/precision the project standardizes on.
  precisionMLPs used "all computation in float64, device auto-select CUDA→MPS→CPU"; state yours.>
- **Reuse, don't copy.** Experiments import shared pieces from `src/`; when something is reused (~rule of
  three) and stable, PROMOTE it into `src/` rather than duplicating. Selection-by-name keeps configs
  unchanged when code is promoted.
- **Math in writeups is LaTeX.** `$...$` inline, `$$...$$` display, KaTeX-safe (no `\*`, no `\emph`). Do
  NOT hard-wrap prose — write each paragraph as a single line and let the editor wrap.
- **Figure legends go OUTSIDE the axes, above the plot** — never inside (they occlude data). Use a
  per-axes legend above the axes (`ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=...,
  borderaxespad=0)`) or one shared figure legend across the top, reserving the top margin.

## Experiment Workflow

Each `run.py` is self-contained and follows this shape:

```python
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]   # experiments/expXNN_name/run.py -> repo root
# import shared pieces from src/
# load this experiment's config.yaml; expand any sweeps
# RESULTS_DIR = REPO_ROOT / "results" / "{{group}}_X_name" / "expXNN_name"  (mirror of this folder)
# for each sweep cell / seed:
#     run the experiment, collect metrics
# do the analysis here (this script owns its analysis)
# save metrics (JSONL) + config + figures to RESULTS_DIR
```

Run with `python experiments/expXNN_name/run.py`. See `experiments/_template/` for a working skeleton —
copy it to start a new experiment.

## Results Format

`results/` is gitignored EXCEPT the human-authored writeups: `*_results.md`, `results/results.md`, and
any explicitly pinned artifact (see `.gitignore`). So writeups are version-controlled; raw data and
figures are not.

- **One writeup per experiment** at `results/{{group}}_<X>_<name>/expXNN_<name>/expXNN_results.md`.
  Never a shared per-{{group}} doc — the only global doc is `results/results.md`.
- **`results/results.md`** is the cross-experiment summary: a "story so far" synthesis, then a section per
  {{group}} listing each experiment's key finding in one line, with that {{group}}'s open questions
  re-aggregated. It does NOT repeat numbers or figures — those stay in the per-experiment writeups.

### Per-experiment writeup template (every writeup, in this order)

1. **Title + Status** — one line. Status is one of: `approved by <owner>` / `data-obvious` /
   `draft-pending-<owner>`.
2. **TL;DR** — 2-4 lean bullets, the takeaways; numbers only where they carry the point.
3. **Question / hypothesis** — the heart in 1-2 sentences; do not pad.
4. **Experiment design** — THE section that earns depth: a reader should come away knowing *exactly* what
   was tested. State the actual math (definitions, estimators, formulas), the key params (sweeps, sizes,
   seeds), and the metric definitions. Sub-bullets for variants/checks. End with a single **Code & data**
   block — the ONLY place file paths appear (run.py/config, data files, figures).
5. **Results** — the signal in plain language, sparse numbers. Then a **Figures** subsection with ONE
   bullet per figure: name it, give its layout (axes, what each line/color is), and what to look for.
6. **Additional details** — flexible; include only if it earns its place (derivations, confounds,
   caveats). Goes ABOVE Conclusions; omit the section entirely if nothing is load-bearing.
7. **Conclusions** — the signed-off claim in 1-2 sentences; do NOT re-list the TL;DR.
8. **Open questions** — conservative (few); `results.md` re-aggregates them per {{group}}.

**Voice / calibration:** plain language, ~5/10 fluff — actively cut redundancy (the biggest offender is
the TL;DR restated in Conclusions). Keep the references and the per-figure how-to-reads; cut hedging and
restatement. If a sentence adds no information, delete it. The design section is the one place to add
depth, not subtract it.

**Number discipline:** spend raw numbers like currency — only where they matter. Do not saturate prose
with values. Tables only when they tell a clean story.

**Conclusions are special:** a statement goes in Conclusions ONLY if it is plainly obvious from the data,
OR it was proposed, discussed, and explicitly approved by the owner. Do not write conclusions before the
owner has reviewed the numbers and signed off; keep proposed-but-unapproved conclusions out (or clearly
marked pending). Write conservatively: state only what the data shows, and flag any metric that is not
independent evidence.

## Success Criterion

<FILL: the concrete, measurable bar that means the research question is answered. precisionMLPs used
"error reaches eval relative L2 <= 1e-13 at machine epsilon, across the width ladder over 3-5 seeds,
without initializing from the known solution." Make yours specific enough to test an experiment against.>
