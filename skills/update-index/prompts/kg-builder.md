You are building a concept map from per-repo KG paragraphs. The map is
appended to INDEX.md as a convenience index for agents answering
high-level questions. It is NOT a filter: agents are instructed to read
per-repo blocks first and treat the map as hints.

## Input — KG paragraphs

{{KG_PARAGRAPHS}}

(Format: one section per repo, headed `## <repo_name>`, followed by the
paragraph from that repo's scratch file.)

## Output format

Produce exactly this structure and nothing else:

# Concept Map

_Incomplete by construction. Use as a starting hint; verify by reading
per-repo blocks above. Repos may touch concepts not listed here._

## <concept>
- <repo> — <role note> (primary / contributes / tangential)
- ...

## <concept>
- ...

## Guidelines
- Concepts are DOMAIN-LEVEL, not implementation-level. They span BOTH
  technical concerns AND business/product concerns. Good: "ACU / metering",
  "customer onboarding", "customer experience", "pricing", "fixed vs
  variable costs", "ML research", "sales collateral", "developer tooling".
  Bad: "Postgres", "React", "monorepo tooling".
- Every repo that meaningfully participates in a concept gets listed — even
  if the map feels crowded. Recall > precision.
- Use role labels conservatively. "primary" = owns the implementation or
  domain model. "contributes" = material participant. "tangential" = aware
  of the concept but not the natural place to look first.
- Aim for 15–40 concepts total across the workspace. If you produce fewer
  than 10 or more than 60, reconsider granularity.
- Order concepts alphabetically.

Do not add a preamble, footer, or commentary outside the structure above.
