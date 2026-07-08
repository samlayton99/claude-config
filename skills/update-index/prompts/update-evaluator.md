You are deciding whether an existing INDEX.md entry for a repo needs to
change, based on recent git activity. Your default answer is NO_CHANGE.

**Repo:** {{REPO_NAME}}
**Path:** {{REPO_PATH}}

## Current index entry
{{CURRENT_ENTRY}}

## Current KG paragraph
{{CURRENT_KG}}

## Change signals (precomputed)
Top-level dir changes:
{{DIR_DIFF}}

Commit subjects since last index scan:
{{COMMIT_SUBJECTS}}

README diff summary:
{{README_DIFF}}

## The test
Apply this test and nothing else:

> Would a future agent reading the current index entry get a materially
> wrong picture of this repo, now that these changes have happened?

### YES (meaningful — worth an update):
- A domain in the entry is gone, renamed, or moved to another repo.
- A new top-level domain/module exists that the entry doesn't mention.
- "Purpose" would read differently now.
- The `Description` paragraph would be inaccurate — e.g., what's
  actually in the repo has materially shifted.
- Entry points named in the entry no longer exist or no longer serve
  that role.
- Tech stack fundamentally shifted (framework swap, language migration).
- Service extracted / merged / renamed.
- The repo's product/business role changed (e.g., was internal tool,
  now customer-facing; was docs, now code).

### NO (not meaningful — regardless of diff size):
- Refactors within existing files.
- Bug fixes, test additions, dependency bumps.
- Mass reformatting, moves that preserve purpose.
- Auto-generated diffs (migrations, lockfiles).
- Docs tweaks that don't change the conceptual story.

**When uncertain, return NO_CHANGE.** Inaction is correct when the signal
is ambiguous.

## Output
Reply with exactly one of:

NO_CHANGE

— or —

CHANGED
<rewritten entry in the same format — full block, including Description>
---KG---
<rewritten KG paragraph, ≤120 words>

Do not add commentary outside these forms.
