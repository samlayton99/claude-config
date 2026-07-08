---
name: lecture-notes
description: "Parse and expand raw lecture note scaffolding into rigorous, LaTeX-formatted markdown study notes. Use this skill whenever a user pastes lecture notes, class notes, or a note scaffold and wants them filled out, expanded, or turned into study material. Also trigger when a user mentions \"lecture notes\", \"class notes\", \"fill in my notes\", \"notes from class\", \"note scaffold\", \"study notes\", or asks to turn rough lecture jottings into polished review material. If the user mentions a Stanford applied math, statistics, or CS course alongside notes, definitely use this skill."
---

# Lecture Notes Parser

Turn raw lecture note scaffolding into rigorous, well-structured, LaTeX-rich
markdown study notes. The user takes rough notes in class (definition names,
theorem names, professor emphasis, questions, chronological jottings) and you
expand them into notes detailed enough to pass a test, but concise enough to
review at a glance months later.

## Core Principle

**Stay faithful to the scaffold.** The user's notes define the scope. Fill in
the math, definitions, and explanations for what they wrote down — do not
invent your own lesson plan or dump everything the internet knows about a
topic. The scaffold is the contract.

---

## Phase 0: Context Gathering

When the user first provides notes, identify the course if mentioned. Use web
search to pull light context: who teaches it, what textbook it uses, and where
it sits in the curriculum. This is background — a few sentences max, not a
research report. If the course is already known from a previous turn, skip.

Also scan the notes for:
- **Direct questions** — anything in parentheses like `(explain this)` or
  `(I didn't understand X)`
- **Emphasized section** — things the professor harped on
- **Key definitions/theorems section** — names the user recorded but didn't
  write out

---

## Phase 1: Tutor Mode (default on, skippable)

Start here unless the user says "skip to notes" or "just fill in the notes."

1. **Brief high-level orientation** (2–4 sentences): What the lecture covered,
   how it connects to the arc of the course. Keep it short.
2. **Answer the user's embedded questions**: Address every `(question)` and
   `(I don't understand X)` from their notes. Be precise and rigorous, but
   explain with intuition first, formalism second.
3. **Interactive exploration**: The user will explain their understanding back.
   Your job is to verify correctness, catch subtle misunderstandings, and push
   toward precise understanding. Challenge them — they'd rather be corrected
   than coddled.

This phase ends when the user is satisfied or prompts you to move to notes
(e.g., "let's do the notes", "fill it in", "notes mode").

If the user provides notes with no questions and says something like "just
clean these up," skip directly to Phase 2.

---

## Phase 2: Notes Mode

When triggered (or when the user skips Phase 1), produce the final notes.

**Before writing, re-read the original note scaffold.** Reflect on it. The
output structure must mirror what the user actually wrote, not what you think
the lecture should have covered. Incorporate context from the Phase 1
discussion — if you clarified a misconception or explored a subtlety, that
understanding should be reflected in the notes.

### Output Structure

Use this exact structure for the final markdown:

```
# Lecture [number]—[2-4 concise words] (e.g., "Lecture 4—Flow Matching", don't move on until they give you the lecture number)

## Overview
[A roadmap for orienting in the notes — not just a summary, but a guide to
what the lecture builds toward and how the pieces connect. Can be a few
sentences or a few paragraphs depending on complexity. Can include LaTeX and
equations when they help set up the landscape (e.g., stating the central
problem or objective the lecture addresses). The reader should finish this
section knowing where they are in the course and what to expect below.]

## Key Concepts
[Single line listing the names of key theorems, techniques, and concepts — just names, comma-separated]

## Lecture Notes
[Chronological, detailed notes following the user's scaffold. This is the meat.
Every definition written rigorously with LaTeX. Every theorem stated precisely.
But also: explain the intuition, connect the dots, make it readable as a
narrative — not an incoherent list. Introduce variables and mathematical
objects before using them.]

## Emphasized Topics
[Not core content — that belongs in Lecture Notes above. This section is for
extra detail, additional context, or deeper dives on things the professor
specifically called out as important. Think of it as annotations: exam hints,
"make sure you understand why..." pointers, subtleties worth revisiting.]

## Key Theorems & Definitions
[Reference section: each theorem/definition stated precisely with LaTeX,
self-contained enough to be useful on its own.]
```

### LaTeX Requirements

This is critical. All math must use LaTeX:
- Inline math: `$...$`
- Display math: `$$...$$`
- Introduce every variable/symbol when it first appears:
  `Let $X_n$ be a sequence of random variables on $(\Omega, \mathcal{F}, P)$`
- Write theorems/definitions rigorously:
  ```
  **Theorem (Dominated Convergence).**
  Let $\{f_n\}$ be a sequence of measurable functions such that $f_n \to f$
  a.e., and suppose there exists an integrable function $g$ with
  $|f_n| \leq g$ a.e. for all $n$. Then:
  $$\lim_{n \to \infty} \int f_n \, d\mu = \int f \, d\mu$$
  ```

### Tone & Density

- **Notes, not a textbook.** Concise. Every sentence should earn its place.
- **But rigorous.** Don't hand-wave the math. State things precisely.
- The "glance test": the user should be able to re-read these 3 months later
  and reconstruct the full picture quickly.
- Match the mathematical maturity of a Stanford graduate student in applied
  math, statistics, or CS. Don't over-explain prerequisites.

---

## Delivering the Notes

When the notes are complete, save them as a `.md` file and provide it for
download. Use the title as the filename:
`Lecture [number]—[2-4 concise words].md`.

The user may want to inspect and edit — the markdown file is the deliverable,
not inline chat text. Always produce the file.

---

## Input Format Reference

The user's raw notes will typically contain:
- **Chronological jottings**: "talked about how X implies Y",
  "professor showed that Z"
- **Emphasized section**: things the professor stressed repeatedly
- **Questions to you**: in parentheses — `(explain this)`,
  `(why does this work?)`
- **Key definitions/theorems**: names recorded without full statements
- **Rough markdown**: not sophisticated, not mathematical — that's your job
  to upgrade

---

## Edge Cases

- If the user provides notes with no course name, ask for it (or infer from
  content if obvious).
- If the scaffold is very sparse (just a few bullet points), fill in
  proportionally — don't balloon a 5-line scaffold into 5 pages.
- If the user asks you to go beyond the scaffold ("also cover X"), do so, but
  keep the scaffold as the backbone.
- If the user pastes notes and immediately says "fill these in" or similar,
  skip Phase 1 entirely.