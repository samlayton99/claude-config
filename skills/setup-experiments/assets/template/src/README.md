# src/ — core reusable library

Shared code that experiments **import**, never copy. This is the layer that keeps the codebase from
rotting as experiments accumulate: one canonical implementation, reused everywhere.

## What goes here

- Configuration: a schema (every field has a default) + a loader, so each experiment's `config.yaml`
  overrides only what it needs, and sweeps expand from the config.
- Data / problem setup: dataset construction, the family of test cases, samplers.
- The core method(s) under study, and any shared analysis/metrics utilities (e.g. a metrics collector
  that logs a fixed metric set as JSONL).
- Pure-data result types (immutable; never reference an experiment).

Organize into subpackages as the project takes shape (precisionMLPs used `config/`, `data/`, `models/`,
plus domain packages). Keep it minimal until a second experiment actually needs a piece.

## The promotion rule

Code earns its way in; it does not start here.

- **Local first.** A new model / loss / helper lives in the experiment's own folder.
- **Promote on reuse (~rule of three).** When a second experiment needs it and it is stable, move it
  into the relevant `src/` file. Prefer selection-by-name (a registry) so promotion does not churn the
  configs that reference it.
- **No casual per-run edits to `src/`.** Touch it only to promote proven-reusable code or make a real,
  backward-compatible shared improvement.
