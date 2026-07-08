#!/usr/bin/env python3
"""scaffold.py — deterministic project emitter for the dl-trainer skill.

Copies the scaffold/ template into a destination directory and, if a task is
named, deep-merges that task's verified hyperparameters (tasks/<task>/config.yaml)
into the first experiment's config. The folder setup is done by CODE here so it is
identical every time — the model does not hand-write the project.

Usage:
    scaffold.py --dest PATH [--name RUN] [--task TASK] [--force]
    scaffold.py --list-tasks

Tasks live in ../tasks/<task>/config.yaml (verified hyperparameters + a _recipe block).
The workspace template lives in ../scaffold/.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "scaffold"
TASKS = SKILL_ROOT / "tasks"


def list_tasks():
    if not TASKS.exists():
        print("(no tasks directory)")
        return
    for d in sorted(TASKS.iterdir()):
        cfg = d / "config.yaml"
        if not d.is_dir() or d.name.startswith("_") or not cfg.exists():
            continue                      # skip _template and non-task entries
        doc = yaml.safe_load(cfg.read_text()) or {}
        note = doc.get("_recipe", {}).get("summary", "")
        print(f"  {d.name:24s} {note}")


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override wins on scalar conflicts."""
    out = dict(base)
    for k, v in override.items():
        if k.startswith("_"):  # metadata keys (_recipe) are kept as-is
            out[k] = v
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", help="destination project directory")
    ap.add_argument("--name", default="baseline", help="run name (stamped into config)")
    ap.add_argument("--task", help="task name (see --list-tasks)")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    ap.add_argument("--list-tasks", action="store_true")
    args = ap.parse_args()

    if args.list_tasks:
        list_tasks()
        return
    if not args.dest:
        ap.error("--dest is required (or use --list-tasks)")

    dest = Path(args.dest).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)

    # ── copy the template tree, preserving subfolders (scripts/, utilities/) ──
    # Refuse to clobber existing files unless --force. This lays down a working
    # REFERENCE project; the model then adapts it (model.py / dataloader.py) to the task.
    copied = []
    SKIP = {"__pycache__", ".git", ".DS_Store", ".ipynb_checkpoints"}  # junk only
    for src in sorted(TEMPLATES.rglob("*")):
        parts = src.relative_to(TEMPLATES).parts
        if any(p in SKIP for p in parts) or src.suffix == ".pyc":
            continue  # NOTE: .gitignore / .gitkeep are intentional — kept
        rel = src.relative_to(TEMPLATES)
        target = dest / rel
        if src.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if target.exists() and not args.force:
            print(f"skip (exists): {rel}  [use --force to overwrite]")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        copied.append(str(rel))

    # ── create the first experiment from the template, merging the task config ──
    # The workspace ships shared core/; each run is an experiment folder. We seed
    # one (experiments/<name>) so there's an immediately-runnable starting point.
    # GUARDRAIL: an existing experiment is left fully untouched unless --force — we
    # never silently rewrite a config.yaml that may hold real work.
    template = dest / "experiments" / "_template"
    exp_dir = dest / "experiments" / args.name
    fresh = (not exp_dir.exists()) or args.force
    if not fresh:
        print(f"\nexperiment {exp_dir.name} already exists — left untouched [use --force to overwrite]")
    else:
        exp_dir.mkdir(parents=True, exist_ok=True)
        for f in template.iterdir():
            if f.is_file():
                shutil.copy2(f, exp_dir / f.name)   # verbatim copy keeps the config's inline knob docs

    # Apply the task's verified hyperparameters onto a FRESH experiment only. No task:
    # keep the commented template config verbatim (don't round-trip away its docs).
    cfg_path = exp_dir / "config.yaml"
    recipe = None
    if args.task:
        preset_path = TASKS / args.task / "config.yaml"
        if not preset_path.exists():
            print(f"\nunknown task '{args.task}'. Available:")
            list_tasks()
            sys.exit(1)
        preset = yaml.safe_load(preset_path.read_text()) or {}
        recipe = preset.pop("_recipe", None)
        if fresh:
            cfg = deep_merge(yaml.safe_load(cfg_path.read_text()), preset)
            if "model" in preset:                  # task architecture REPLACES the MLP placeholder
                cfg["model"] = preset["model"]
            cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False))
        else:
            print(f"  not applying task '{args.task}' to the existing config (use --force).")

    extra = recipe.get("extra") if recipe else None

    print(f"\nscaffolded {len(copied)} files into {dest}")
    print(f"{'created' if fresh else 'kept'} first experiment: experiments/{args.name}")
    if recipe:
        print(f"\napplied task '{args.task}':")
        print(f"  {recipe.get('summary','')}")
        if recipe.get("source"):
            print(f"  source: {recipe['source']}  (last verified {recipe.get('last_verified','?')})")
        if extra:
            print(f"  needs extra libraries: uv sync --extra {extra}")
        if recipe.get("todo"):
            print("  before running, you must:")
            for t in recipe["todo"]:
                print(f"    - {t}")
    print("\nnext (adapt, then run):")
    print(f"  cd {dest}")
    print("  # READ AGENTS.md first — it's the contract for keeping this clean.")
    print(f"  # ADAPT experiments/{args.name}/ to your task (config.yaml; experiment.py for a")
    print("  #   custom model/data/loss/optimizer). core/ is shared — don't edit it per experiment.")
    print(f"  uv sync{(' --extra ' + extra) if extra else ''}                                       # create .venv (+ uv.lock)")
    print("  uv run python -m utilities.hardware           # probe GPU / dtype")
    print(f"  uv run python -m core.run experiments/{args.name}   # sanity gate, then trains")


if __name__ == "__main__":
    main()
