You are indexing a single repository for a workspace-level INDEX.md. Your
deliverable is:
  (a) a block in a strict markdown format (written to {{ENTRY_SCRATCH_PATH}}),
  (b) a one-paragraph context blob for a concept map (written to
      {{KG_SCRATCH_PATH}}).

**This is directive scaffolding, not comprehension.** A future agent will
read INDEX.md to figure out which repos are relevant for a question and
where to start looking. You are NOT producing context to edit the repo.

**The scaffolding must cover BOTH dimensions:**
- **Technical / SWE context** — domains, entry points, tech stack,
  interactions with other repos, "start here" paths.
- **Product / business context** — what this repo is *for* in the
  business. Customer-facing app? Internal ops tool? Sales collateral?
  Research code? Docs? Infra? Billing-model docs? Whose work is this
  repo the home for?

Agents reading the index may be asked abstract questions like "describe
the current customer experience" or "what are the fixed vs. variable
costs?" The product/business half is often what lets them pick the
right repos.

**Repo:** {{REPO_NAME}}
**Path:** {{REPO_PATH}}

## Depth of exploration
You have judgment here. Read at the level needed to produce a confident,
useful deliverable — no more, no less.
- Reading source files line-by-line is NOT the default, but it is
  allowed when structure alone doesn't tell you what a module is for.
  A 50-line scan of a key file is cheap and often worth it.
- You do not need to understand every implementation detail. You need
  enough understanding to describe the repo accurately in the required
  format.

## What to explore (usual order, stop when you have enough)
1. README and any ARCHITECTURE.md / DESIGN.md / CLAUDE.md / AGENTS.md /
   docs/*.md. These often describe business context directly.
2. Top-level directory names and what they suggest (e.g., `billing/`,
   `api/`, `infra/`, `accounts/`, `material/`).
3. Manifest files: `package.json` / `pyproject.toml` / `go.mod` /
   `Cargo.toml` / similar — language, frameworks, notable deps.
4. Entry points: `main.py`, `src/index.ts`, `cmd/*/main.go`, etc.
   Skim them if structure alone doesn't reveal the purpose.
5. Recent commit log (`git -C {{REPO_PATH}} log --oneline -20`) — names
   of recent work reveal the active domains and business priorities.

## Spawning sub-subagents
Do NOT spawn them by default. Only spawn them when it is obviously
needed for deeper understanding or constructing a better index — e.g.,
a monorepo with multiple distinct services where a single pass will
produce a vague entry. If you spawn, scope each sub-subagent to one
subdirectory or service and pass this same scope reminder.

## Entry format (write to {{ENTRY_SCRATCH_PATH}})
Follow this format exactly. Use `-` for any field that genuinely has
no content (e.g., `Interacts with: -`).

## {{REPO_NAME}}
**Purpose:** <one sentence — crisp, what this repo does>
**Description:** <2–3 sentences, unstructured. What's actually in the
  repo, its role in the product/business, and anything that doesn't
  fit cleanly in the structured fields below. Include product and
  business context here. If this is a sales / ops / docs / research
  repo (not a code repo), say so clearly.>
**Domains:**
- <domain> — <role note> (<entry_point_path>)
- ...
**Interacts with:** <comma-separated other repo names, or "-">
**Start here:** <path> → <path>
**Tech:** <language(s), frameworks, key datastores, or "-" for non-code repos>
**Recent substantial changes:**
- <YYYY-MM-DD> — <one-line description> (<path>)
- ...

## KG paragraph (write to {{KG_SCRATCH_PATH}})
One paragraph, ≤120 words, naming the concepts this repo participates
in and how. Include both technical concepts (e.g., "auth",
"metering API") and business/product concepts (e.g., "pricing",
"customer onboarding", "sales collateral"). Think of it as what you'd
tell someone building a concept-to-repo map: "this repo owns X,
contributes to Y, has a tangential role in Z." Use the exact domain
names you used in the Domains section so they collate cleanly. Do not
repeat the Purpose sentence.

## Report format
When done, reply with one line:
  DONE <number_of_subagents_you_spawned>
or
  BLOCKED <short reason>

Do not include the entry or KG paragraph in your reply — they go to
the scratch files.
