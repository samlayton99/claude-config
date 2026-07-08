---
description: Check performance of specified files, or of staged/unstaged git changes.
argument-hint: [path/to/file]... (optional)
allowed-tools: Bash(git:diff)
---
Use the **performance-profiler** subagent to analyze code for performance issues.

Your analysis target is determined by the following rules:

1.  **If file paths are provided as arguments**, your analysis must focus exclusively on them: **$ARGUMENTS**

2.  **If no arguments are provided**, your analysis MUST focus on the recent git changes provided below. Please prioritize the **'Staged Changes'**. If that section is empty, then analyze the **'Unstaged Changes'**.

### Context from Git (if no arguments provided)

**Staged Changes (Priority 1):**
```diff
!git diff --staged
```

**Unstaged Changes (Priority 2):**
```diff
!git diff HEAD
```
---
*Your final report should identify backend bottlenecks in FastAPI/GraphQL (Strawberry) services: async blocking, resolver N+1, Pydantic validation/serialization cost, database access patterns, caching opportunities, and startup overhead.*
