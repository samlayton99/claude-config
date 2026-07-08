---
name: technical-explanations
description: "The quality and formatting standard for WRITING UP technical material — trigger any time you produce, draft, or format a technical, mathematical, or scientific explanation, walkthrough, write-up, or document in markdown, in any hard field (math, CS, biology, science, technical philosophy). It is the technical-domain version of avoid-ai-writing, applied at generation. Also invoked by make-course and lecture-notes. Do NOT trigger on casual conversational back-and-forth, quick clarifying questions, or live drilling — that is learning-with-sam's domain."
---

# Technical explanations

Generate technical and intuitive explanations a reader follows on the first pass, in any hard domain: math, CS, biology, the sciences, even technical philosophy when it's rigorous enough. The job is a story that builds genuine understanding: easy to read, saying significant things, introducing every idea responsibly as it arrives.

Every sentence is condensed against one filter (*does this directly improve the quality of the explanation and the clarity of the idea, or is it unnecessary verbose exposition?*), but **readability is the constraint that wins ties.** An explanation exists to be understood, not to be short and not to be impressive.

Six things do the work: **responsible introduction**, **condensing for readability** (the central balance), **technical anti-slop**, **format**, **momentum**, and a **self-audit**.

## Where this sits

- This is the **technical-domain version of `avoid-ai-writing`**, run at *generation* time, not review. `avoid-ai-writing` owns general writing and is told not to fire on technical explanations, `make-course`, or `lecture-notes` output. This skill owns that domain.
- It carries a lightweight, prose-level echo of `learning-with-sam`. The full interactive pedagogy lives there; `make-course` and `lecture-notes` invoke it for complete teaching.
- On overlap, the specialist wins: format and technical anti-slop → here; live teaching and model-diagnosis → `learning-with-sam`; general-writing review → `avoid-ai-writing`.

## How heavily this applies: match the weight to the request

The clarity standard always applies: responsible introduction, condensing for readability, and anti-slop hold for *any* technical explanation, down to a one-line chat answer. Those are cheap and never hurt.

The **heavy apparatus** (the full two-pass build-out, liberal display LaTeX, headers, tables, the formal self-audit) is for when the user is **producing or requesting an explanation or document**: a write-up, a "explain X" deliverable, a section, or a course/notes via the formatter skills.

In **rapid live Q&A** (quick clarifying questions, drilling, back-and-forth), keep it light. Apply the principles, but do not inflate a two-sentence answer into a formatted mini-essay with headers and display equations. There, `learning-with-sam` governs scale: minimal diff, answer the root, one job. Adding structure a short answer didn't need is friction, not quality.

Rule of thumb: **a question wants an answer; a write-up wants the full treatment.** Read which one you were handed before reaching for format.

---

## 1. Responsible introduction (two passes)

The reader distrusts the entire document the instant a concept is used before it is properly introduced, and then they stop reading and rabbit-hole. So every introduction is your responsibility. Build each topic in two passes:

1. **Orient.** Lead with motivation, framing, and the problem the idea solves, engaging enough to make the formalism worth caring about and easy to grasp. Often: grant the obvious alternative the reader already has in mind, then show exactly where it breaks.
2. **Then dive hard into the formalism.**

Both passes are held to the same standard: **the orientation is not a license to be vague or to name-drop undefined terms.** A compelling orientation that smuggles in an unexplained concept loses trust faster than no orientation at all.

- **Term-before-use is a hard rule.** No variable, symbol, sub-concept, acronym, or metaphor appears before it is introduced in place.
- **Introduce objects by type first, then intuition.** State what kind of thing it is (for math, the space it lives in and the maps acting on it) *before* the physical or intuitive meaning. Intuition before the object hands the reader a metaphor with nothing under it.
- **Name the load-bearing invariants and reuse the exact name.** Repetition of the precise term is a retention hook, not a flaw.
- **License every abstraction you leave closed.** "We treat X as a black box here; safe to skip because ___." An unlicensed gap sends the reader down a hole.
- **Inoculate the tempting misreading:** *Tempting to think [wrong], but [right] because […].* Reserve for genuine confusions.

(The full interactive version lives in `learning-with-sam`: diagnosing the reader's model, grading teach-backs.)

---

## 2. Condense for readability: the central balance

This is the heart of technical writing, and it has two failure modes that pull in opposite directions. Hold both.

The filter every sentence passes: **does this directly improve the quality of the explanation and the clarity of the idea, or is it just unnecessary verbose exposition?** If it doesn't earn its place by making the idea clearer, cut it. Dramatic openers, throat-clearing, fluff, and significance theater all fail this filter.

But over-condensing is the opposite failure, and just as bad: a paragraph crushed into a dense brick of technical terms is not clear, even when every word is load-bearing. High signal is the goal; high *syntactic* density is fatal: the reader skips it rather than fighting through it.

So the target is neither a list of dense facts nor meaningless exposition. It is a story that builds genuine understanding, reads easy, says significant things, introduces each idea responsibly as it arrives.

Levers:
- **One idea per sentence; short paragraphs; use line breaks.** White space is part of clarity, not wasted space. Give the reader room to absorb.
- **Cutting and spacing are two separate jobs.** Condensing removes the fluff; it does not mean cramming the survivors together. Cut what fails the filter, then let what's left breathe.
- **Never let jargon stack undefined.** Density usually comes from unintroduced terms piling up. The fix is to introduce them (§1), not to strip the precision: a defined term reads easy, an undefined one reads as a brick.
- **Connective tissue, not fact-listing.** Each sentence sets up the next so the reader is carried, not quizzed. If it reads like a spec in paragraph form, rewrite it as narrative.
- **After drafting a section, hunt for sentences that say almost nothing.** Reread it looking for flowery, throat-clearing, or padded passages: the place where three sentences do one sentence's work, or a clause just restates what you already said, or a sentence sounds substantial but carries no information. Collapse each to the shortest phrasing that keeps the meaning, often a single clause. This pass is separate from the per-sentence filter above, because this kind of bloat only becomes visible once the whole section exists.

---

## 3. Technical anti-slop

This is `avoid-ai-writing`'s job, scoped to technical prose and done at generation. **Structure is the #1 tell. AI text is metronomic; fix rhythm, not just words.**

### Structure and rhythm
- **Vary sentence length.** Mix short (3–8 words) with long (20+). Fragments are fine. If the text could be read by a TTS engine without sounding odd, it's too uniform.
- **Vary paragraph length.** Some one sentence, some longer. Uniform blocks read as generated.
- **Paragraph-reshuffle test.** If two body paragraphs can swap without breaking the piece, you wrote a list, not an argument. Establish the through-line.
- **Treadmill test.** Each paragraph must add a new fact, claim, or turn. If you could cut 40–60% with no loss, do.
- **Don't over-polish into uniformity.** Sanding away every irregularity pushes prose *back* toward an AI profile. Keep natural rhythm and idiosyncrasy.

### Vocabulary
- **Tier-1, always replace:** delve, tapestry, beacon, embark, testament to, game-changer, harness, paradigm, pivotal, underscores, meticulous, deep dive, unpack, leverage (verb)→use, utilize→use, showcasing, intricate, daunting.
- **Technical carve-outs, do NOT flag when used precisely:** robust, comprehensive, seamless, ecosystem, facilitate, underpin, streamline. These carry real technical meaning; this is the key difference from generic de-slopping. A genuine parameter/step list is also legitimate; don't strip it.
- **Repeat the precise term; never synonym-cycle.** "developers… engineers… practitioners" for one referent is thesaurus abuse. Doubly true in technical writing where the term is exact.
- **Prefer plain copulas.** "is" / "has" over "serves as," "features," "boasts," "represents."

### Honesty failures (high-stakes here)
- **Speculative gap-filling:** guesses formatted as fact ("likely begins," "appears to," "is believed to"). Cut, or source it. Worse than admitting a gap, because the reader can't tell known from invented.
- **Novelty inflation:** treating an established concept as invented ("a failure mode nobody names"). Describe what was *done with* the concept instead.
- **Vague attribution:** "studies show," "experts believe" → cite specifically or cut.
- **Cutoff disclaimers:** "as of my last update," "I don't have access to…" Never publish.
- **Significance inflation / self-labeling:** "a pivotal moment," "this is the clever part," "here's where it gets interesting." State what happened; let the content carry its own weight.

### Filler and framing
- Reasoning-chain artifacts: "let me think step by step," "Step 1:," "breaking this down."
- Confidence-calibration words: "it's worth noting," "notably," "interestingly," "importantly" (flag by density, one is fine, three in 500 words isn't).
- Rhetorical-question openers; "Let's [verb]" transitions; emotional flatline ("what surprised me most").
- Hedge-stacked predictions ("could potentially," "may eventually"); false ranges ("from the Big Bang to dark matter"); false concession ("while X is impressive, Y remains a challenge").
- "It's not X, it's Y": state the two things plainly and let the difference land.
- Compulsive rule of three: AI defaults to triads (adjective, adjective, and adjective). Vary the grouping; use two items, four, or a full clause.

### Escape hatch
Code blocks, quoted material, and text explicitly marked as an illustrative bad example are exempt from all anti-slop flagging. Don't rewrite a quoted specimen.

---

## 4. Format (the heavy section)

Format mirrors the concept map; it never decorates. The test for any element: does it make the dependency order or a comparison *visible*?

- **Headers carry information, in sentence case.** "How attention routes information," not "Overview." Not Title Case. No emoji in headers. Not too many in short text (3+ headings under 300 words reads as AI trying to look organized).
- **LaTeX, used liberally.** Inline `$...$`, display `$$...$$`. Every variable and object introduced with its type on first appearance: `Let $X_n$ be a sequence on $(\Omega,\mathcal{F},P)$`. Definitions and theorems state full hypotheses before the conclusion. Notation stays consistent: one symbol, one meaning. In a derivation, the load-bearing step is written out, not waved past with "it follows that."
- **Tables and labeled columns for things that would blur:** an owner/actor column plus one end-to-end trace, or two side-by-side columns for two conflated concepts.
- **Prose for reasoning; structure for genuinely list-shaped content.** Bulleting an argument hides the connectives that make it an argument.
- **No carpet-bombing.** No wall of bullets; no inline-header lists that repeat themselves ("**Speed:** Speed improved…"); no lists of bare adjective-noun phrases.
- **Line breaks and short paragraphs are formatting too:** they're the main lever for the readability balance in §2.
- **Em dashes in prose: target zero.** In body prose they are the single most recognizable AI tell, so this rule is strict, not "sparingly." Before keeping one, rewrite it: a comma for an aside, a colon to introduce, a period to split a run-on, parentheses for a true aside. At most one survives per ~1,000 words of prose, and only where no other punctuation does the job. Titles and headings are exempt: an em dash in a heading, a section title, or a figure or file name is fine. (Code blocks and quoted specimens are also exempt.)
- **Bold sparingly**, as scan handles, not on every phrase.
- **Called-out definitions and named invariants are fine:** a real retention hook, used for the two or three things that matter most.

---

## 5. Momentum

- **Lead with the point, then support it.** State the claim or result first; reasoning after.
- **Each paragraph earns the next:** end on what opens the next paragraph's question.
- **Cut scaffolding prose** ("In this section we will…", "Having covered X, we now turn to Y"). Headers do that job.

---

## 6. Self-audit before delivering

Run internally, fix in place, deliver clean. Do not surface the audit unless asked.

1. **Followable on first read?** Every object defined and typed before use?
2. **The §2 balance:** nothing that fails the clarity filter survives, and nothing readable got crushed into a brick. Line breaks where the reader needs air. No flowery, padded, or three-sentences-for-one passages left standing; the ones that say little are collapsed to a phrase.
3. **Structure:** rhythm varied, paragraphs reshuffle-immune, no treadmill.
4. **Anti-slop:** none of the credibility-killers (cutoff disclaimers, speculative gap-fill, vague attribution, significance inflation); slop vocabulary replaced; technical carve-outs respected; no synonym cycling or copula avoidance.
5. **Format:** LaTeX consistent, headers informative and sentence-case, no em dashes in prose (commas, colons, periods, or parentheses instead; titles and headings may keep them), no carpet-bombing.
6. **Didn't over-edit** good prose into uniformity.

`avoid-ai-writing` does not run on this output. This skill is the technical review, performed at generation. The output is the finished explanation. Deliver it directly.