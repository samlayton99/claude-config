---
name: make-course
description: "Distill a long conversation, book, transcript, or other substantial source into a comprehensive first-principles mini-course, built to be read top-to-bottom and covering every topic in the source. Primary use: turning a long, wide-ranging chat with Claude into a cohesive course; also works for PDFs and transcripts. Use whenever the user says '/make-course', 'make-course', 'turn this into a course', 'make a mini-book from this', 'distill this into a guide', 'first-principles breakdown of this topic', or asks for a comprehensive guide or explainer longer than a quick note but shorter than a textbook. Covers every topic in the source, first-principles by default, with a dedicated structural-planning phase and user checkpoint, and uses examples as a first-class tool. Length tiers: compact, standard, comprehensive (defaults to comprehensive). Compact mode produces a short, dense glance-note — also trigger on 'quick note', 'glance note', 'distill this', 'write up what I just learned'."
---

# Make Course

> **Required reading. Do this first.** Before following anything below, read `learning-with-sam` and `technical-explanations` in full and apply them throughout.
>
> *`learning-with-sam`* is the complete, detailed way this reader learns: diagnose the misconception, motivate before formalizing, introduce every concept responsibly, name the invariants, inoculate the wrong reading. Read it because a course is a teaching artifact, and the reader loses trust and stops the instant a concept is used before it's introduced.
>
> *`technical-explanations`* owns writing quality and format for technical material. It is the technical-domain version of `avoid-ai-writing`, so use it here for anti-slop and formatting, **not** `avoid-ai-writing`, which does not run on this output. Read it because good structure can't rescue sloppy prose or sloppy formatting.

Distill substantial source material (most often a long, wide-ranging chat between the user and Claude, but also books, transcripts, or similar long-form inputs) into a comprehensive but dense mini-course. The output is a markdown file designed to be read top-to-bottom, where every section builds from first principles on what came before. It also has a **compact mode** (see Modes and length tiers): the same instincts dialed down to a short, dense narrative note when that's all the source warrants.

## Core principle

**First principles are the spine.** In standard and comprehensive courses, first-principles exposition is the organizing structure, not a selective tool. A reader who finishes the course should be able to reconstruct the topic from its foundations, not just recognize its vocabulary.

**Cover every topic discussed.** `make-course` selects for *coverage*. Every distinct concept the source actually engages with belongs in the course, even the ones that landed easily. Confusion-dispelling is a tool used *within* sections (where to spend more careful prose, where to deploy a "tempting to think X, but Y" callout). It is not the filter that decides what gets a section.

**Built for top-to-bottom reading.** Each section assumes only what came before. If a concept from Chapter 7 is needed to explain Chapter 3, the course is mis-ordered. This constraint is absolute.

**Distillation, not regurgitation.** Length is earned; density is the goal. A multi-hour conversation touching ten concepts becomes a course with roughly ten tight sections, not ten sprawling ones. Coverage operates *across* topics (drop none); brevity operates *within* each topic (cut anything that doesn't serve the explanation).

---

## Phase 1: Understand the material

Read the full input carefully before anything else. For long chats, read every turn. Don't skim based on topic shifts. For PDFs and transcripts, read all of it.

Build a mental inventory. The first item is the most important:

- **Topic inventory (primary).** Enumerate every distinct concept the source actually engages with. This is the course's coverage contract: every item here gets a section. Err toward *over*-listing at this stage; merging is easy later, recovering dropped topics isn't.
- **Dependencies.** What depends on what. Which ideas are foundational, which are derivative.
- **Pedagogical gaps.** Where the source skipped a step the reader needs.
- **Pedagogical bloat.** Where the source spent pages on something that can be one paragraph from first principles.
- **Sticking points (tool, not guide).** Where the user in the conversation got stuck, reformulated, or had a framing corrected. These do *not* gate inclusion; topics are selected by coverage. They tell you *where to spend prose*: a concept that took five turns to converge gets more careful explanation and often earns a "tempting to think X, but Y" callout. A concept that landed on the first pass still gets a section, just a tighter one.

Goal of Phase 1: know the material well enough to teach it from memory, with a complete list of what needs teaching.

---

## Modes and length tiers

Pick a tier at the start. **Default to comprehensive**: when scope is unclear or the user hasn't said otherwise, build the full course. Drop to standard or compact only when the source is small or the user signals they want less. The tier controls length, ceremony, and figures, not just page count, which is unreliable to hit precisely. For standard and comprehensive, length is negotiated and locked at the Phase 2 checkpoint ("make this the 10-page version, drop the Y digression"); page numbers are targets, not promises.

### Comprehensive mode (default)

The full first-principles course, and the default when nothing says otherwise. It runs the entire Phase 1 → 2 → 3 pipeline below: complete topic coverage, the minimal-foundation-then-topological-sort structuring, the Phase 2 checkpoint, examples for every major abstraction, traps where they earn their place, and figures where a picture shows what text can't. ~30–50 pages for a wide-ranging source. Choose it whenever the goal is a course a reader could learn the whole topic from, reconstructing it from its foundations, not just recognizing the vocabulary.

### Standard mode

The same machinery as comprehensive (full coverage, first-principles spine, Phase 2 checkpoint), distilled harder. ~10–15 pages, figures only where one genuinely shows what text can't. Choose it for a moderate source, or when the user wants the complete picture in a leaner read than the comprehensive build. It is not lower coverage; it is tighter prose per topic.

### Compact mode (short, dense glance-notes)

Compact mode distills a conversation or tangent into a short, dense explainer calibrated for the **"glance in three years" test**: self-contained, navigable, brutally concise. It is narrative-first, skips the Phase 2 checkpoint and figures, and goes straight from breakdown to delivery. It is not a smaller comprehensive course; it is a different instinct, where brevity is the whole game.

**Break it down, then reassemble.** Before writing a word, reread the conversation with three lenses, in order:
1. **Content inventory (primary).** List every distinct concept the conversation actually engaged with: definitions, results, techniques, connections. Coverage is the selection criterion: a concept that landed easily still belongs if it was discussed. Over-list; merging is easy, recovering a dropped concept isn't.
2. **First-principles dependency order.** For each concept: what does it rest on, what does it enable, what's the minimal foundation, what's the natural build order? This determines section order: **the logic of the concept, not the chronology of the conversation.** A late insight may belong early if the logic demands it.
3. **Hiccup map (a tool, not the filter).** Where did the reader get stuck, reformulate, or have a framing corrected? Those spots get the most careful prose and earn a *"tempting to think X, but Y"* callout. Hiccups control **prose density, not inclusion**: they decide where to spend words, never what gets covered.

**Output shape.** A 2–5 word title; a 2–3 sentence aim intro (an aim, not a TL;DR); a hierarchical numbered Index that maps 1:1 to the body; named narrative sections (not "Section 1, 2, 3") that read as one cohesive flow where each idea sets up the next; and an optional **Key Definitions & Theorems** section, included only when a precise statement is worth pinning for lookup. Omit by default. Ground every term before use; this is what makes the narrative cohere.

**Brevity is the whole game.** The user generates many of these; one that's too long won't get reread, which makes it worthless. First draft will be too long; cut 20–30% before delivering. Delete transitional prose ("Now we turn to…"), delete anything the Index already conveys, prefer a tight table or short code block over a paragraph when the content is structured. If the note runs past ~1.5 screens, you haven't cut enough.

**What to avoid in compact mode:** dropping content because it wasn't confusing (coverage isn't gated by hiccups); conversation recaps ("you asked X and I explained Y": write the lesson, not the transcript); filler definitions the reader could look up; bullet carpet-bombing (narrative prose with occasional lists, not a wall of bullets); over-scoping past what the conversation actually engaged.

---

## Phase 2: Structure the course (slow down here)

**This is the hardest phase. Take it slowly; spend disproportionate effort here.** A course with wrong structure wastes the reader's time regardless of how well each section is written.

Structural work:

1. **Identify the minimal foundation.** What is the smallest set of primitives from which everything else can be derived? The course starts there.
2. **Topologically sort the concepts.** Each section assumes only what prior sections established. When the source's order violates this, reorder.
3. **Chunk into chapters.** 3–8 chapters is typical. Each chapter is a coherent unit of the build. More than 8 and the arc gets lost.
4. **Mark where examples belong.** For each major abstraction, one concrete example immediately after introducing it.
5. **Mark where figures earn their place.** Only where a picture shows something text cannot. Most courses need 0–3 figures total.

### Checkpoint with the user

Before writing prose, present the outline: chapters, section-level beats within each, and brief reasoning for the ordering (especially where it diverges from the source). Let the user redirect before you commit to 30 pages. This checkpoint is the single highest-leverage step in the skill. Do not skip it.

Outline format for the checkpoint:

```
Proposed structure:

Chapter 1: [Title]
  1.1 [Beat], [one-line reason]
  1.2 [Beat], [one-line reason]
Chapter 2: [Title]
  ...

Ordering notes:
- [Where this diverges from the source, and why]
- [Any gaps I'm filling that the source didn't]
```

Wait for user confirmation or redirection before proceeding. (Compact mode is the one exception: it skips this checkpoint and goes straight to writing.)

---

## Phase 3: Write

### Output structure

```
# [Course Title, 3–6 words]

[Intro: 3–5 sentences. What this course teaches, why it's organized this
way, what the reader should be able to do by the end.]

## Table of Contents
1. Chapter 1: [Title]
    1.1 [Section Title]
    1.2 [Section Title]
2. Chapter 2: [Title]
    2.1 [Section Title]
    ...

## 1. Chapter 1: [Title]
[Chapter intro: 1–2 sentences framing what this chapter establishes and
why it comes first.]

### 1.1 [Section Title]
[Narrative prose. Motivation, then formalism, then example.]

### 1.2 [Section Title]
[...]

## 2. Chapter 2: [Title]
[...]

## Appendix: Key Definitions & Theorems (optional)
[Only when precise statements warrant a reference section.]
```

Chapter and section titles are content-named ("Chapter 3: Measure-Theoretic Foundations"), not generic ("Chapter 3: More Concepts").

### Building from first principles

Every major concept is *derived*, not just stated. Default pattern: **motivation → formalism → example.**
- *Motivation:* what problem forces this concept to exist?
- *Formalism:* the rigorous statement or definition.
- *Example:* the minimum concrete instance that shows it working.

### Ground every term before using it

Absolute constraint. No variable, symbol, or sub-concept may appear before it has been introduced. If the prose wants to reference something not yet covered, either introduce it now or restructure. In a top-to-bottom course this rule has no exceptions.

### Narrative flow

Read the seam between every two consecutive sections. Does the second follow from the first? If not, either the ordering is wrong, or one transition sentence (*one*, not a paragraph) is owed.

### Examples as a tool

Examples earn their place; they are not decoration. Rules:

- **One example per new abstraction**, immediately after it is introduced.
- **Minimum concrete instance** that shows the idea working. Not a sprawling case study.
- **Skip examples for already-concrete concepts**: the concept itself is the example.
- **Counterexamples are high-value** when the boundary matters: "X holds when A is true; consider B where A fails, then X breaks because […]." Use wherever the "but not when" distinction is load-bearing.
- **Do not stack examples.** If one isn't landing, the *explanation* is wrong, not the example count.

### Surfacing traps

Used sparingly:

> *Tempting to think [wrong framing], but [correct framing] because […].*

Reserve for genuinely common confusions. A trap warning every other page loses its weight.

### Figures (optional, default off)

Include a figure only when a picture shows something text cannot: phase portraits, geometric constructions, architecture diagrams, decision boundaries, flowcharts. Most courses need 0–3 figures total. A figure that merely re-illustrates prose is clutter; cut it.

If generating figures: use matplotlib or equivalent, save to a `figures/` directory alongside the markdown, embed with relative paths:

    ![Decision Boundary](figures/decision-boundary.png)

Match notation and labels to the course's prose. Deliver figures alongside the `.md` so links work out of the box.

### LaTeX

All math uses LaTeX. Inline `$...$`, display `$$...$$`. Introduce every variable on first appearance. Same rigor as `lecture-notes` and `technical-explanations`.

### Length calibration

- **The tier sets the page target** (see Modes and length tiers); within a tier, scale to the scope of the source. Comprehensive runs long, standard is the same coverage in leaner prose, compact is a glance-note. Page counts are targets, not promises.
- **Coverage across topics is fixed; brevity within each topic is the lever.** A multi-hour chat touching ~10 concepts becomes ~10 tight sections, not 10 sprawling ones. A bigger source means more sections, not longer ones.
- Every paragraph earns its place *within its section*. If removing it would not strand the reader later, cut it. Never drop a whole section to hit a length target: coverage is fixed, prose is compressible.
- Delete scaffolding sentences ("In this chapter we will examine...", "Having covered X, we now turn to Y"). Section headers do that work.
- If a chapter exceeds ~8 sections, or a section exceeds ~2 screens, you are probably conflating two concepts. Split or cut.

---

## Source material

The source is most often a long conversation between the user and Claude. Read every turn; content is distributed across the whole chat, not concentrated at the end. Do not use confusion as a filter; every topic discussed is in scope.

For PDFs, read the whole file. For transcripts, ignore filler and timestamps; extract the content spine. For combined inputs (e.g., a conversation plus a referenced paper), the conversation defines scope; the paper is reference.

Supplementary materials (a cited paper, a related chapter) are **reference only**: they sharpen understanding but do not expand scope unless the user explicitly asks.

---

## Delivery

Save as a `.md` file named after the course title: `[Course Title].md`. If figures were generated, deliver them in an adjacent `figures/` directory.

For very long courses (~50+ pages), offer to split into one file per chapter. Single-file is the default; ask before splitting.

---

## What to avoid

- **Dropping topics because they weren't confusing.** Coverage is not gated by sticking points. Every concept the source actually engaged with gets a section, even the easy ones.
- **Regurgitation.** A course that mirrors the source's chapter structure is a summary, not a course. Rebuild from first principles.
- **Skipping the Phase 2 checkpoint.** The outline review is the highest-leverage step. Always present it before writing prose.
- **Forward references.** If section 3 uses something introduced in section 6, the course is mis-ordered.
- **Scaffolding prose.** "In this chapter we will..." Delete on sight.
- **Example stacking.** Two examples of the same idea means the explanation isn't good enough. Fix the explanation.
- **Figure-for-figure's-sake.** A figure that merely re-illustrates prose is clutter.
- **Course-that-is-a-book.** This is a distillation. If the reader could have just read the source in the same time, the course has failed.

---

## Where this sits

- **make-course** owns scope, coverage, structure, tiers, and delivery. It is invoked by the user.
- It calls **learning-with-sam** (how to teach) and **technical-explanations** (how to write and format) every time. See the required-reading header at the top.
- For anti-slop and formatting it uses **technical-explanations**, not **avoid-ai-writing** (which is told not to run on course output).
- Its **compact mode** produces short, dense glance-notes (~1–3 pages) for small-scope sources.
- Distinct from **lecture-notes**, which takes a different input (a class-note scaffold, not a conversation) and is faithful to that scaffold rather than rebuilding from first principles.