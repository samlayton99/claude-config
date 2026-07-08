# Agent Questioning Guide

Includes all worker questions (Phases 1-5) plus agent-specific phases (6-9).
Be conversational -- ask 1-2 questions at a time, build on answers.

## Phase 1: Purpose

1. What does this agent do? (one sentence)
2. What problem does it solve? Why does it need to be an agent (multi-step, tool-using) rather than a worker (one-shot)?

## Phase 2: Trigger

3. How is it initiated?
   - **Cron schedule** -- what time/frequency?
   - **Message from user** -- what prefix or pattern? (e.g., Telegram message)
   - **Called by another agent** -- which agent? what input?
   - **Manual invocation** -- how does the user run it?

## Phase 3: Input

4. What data does it need to start?
   - Where does that data come from?
   - Does it discover additional data during execution via tools?

## Phase 4: Output

5. Where do final results go?
   - Supabase table? Which one?
   - Notification to user? What channel?
   - Written to file?
   - Multiple destinations?

6. What does the output look like?
   - JSON structure for the final summary/report
   - Get a concrete example

## Phase 5: Language

7. Determine automatically:
   - Standalone agents: **Python** (default -- Agent SDK, Hermes compatibility)
   - Dashboard-embedded: **TypeScript** (rare for agents)

---

## Phase 6: Tools & Capabilities (agent-specific)

8. What tools does this agent need to do its job?
   - Read email (Gmail MCP)
   - Read/write calendar (Calendar MCP)
   - Read/write to dashboard (Dashboard MCP)
   - Search the web (WebSearch)
   - Read files (filesystem)
   - Call external APIs (custom MCP or direct HTTP)
   - Other

9. Check `tools/` folder -- which existing MCP servers can be reused?
   - List available servers
   - Ask which ones apply

10. Does it need a NEW MCP server?
    - What API does it wrap?
    - What tools should it expose?
    - Note as a TODO -- build separately with a dedicated MCP server scaffold

11. What tool permissions?
    - Read-only vs read-write
    - Draft-only vs send (for email/messaging)
    - Which tools should NEVER be called without user approval?

## Phase 7: Loop Behavior (agent-specific)

12. How many turns should the agent be allowed? (safety limit)
    - Simple agents: 5-10 turns
    - Complex agents: 15-25 turns
    - Default: 15

13. What's the cost budget per run?
    - Default: $0.50
    - High-complexity agents: $1-2
    - Background agents running frequently: keep low ($0.10-0.25)

14. What should the agent do when stuck?
    - Retry with different approach
    - Degrade gracefully (partial results)
    - Abort and log error
    - Ask user for help (only for interactive agents)

15. What does "done" look like?
    - All items processed
    - Summary written to Supabase
    - Notification sent
    - Specific condition met

## Phase 8: Memory & Learning (agent-specific)

16. Does this agent need to remember things across runs?
    - If NO: skip to Phase 9
    - If YES: continue

17. What kind of state?
    - **Operational** (cursors, timestamps, IDs) -> state.json
      Examples: last processed email ID, last tweet ID, run count
    - **Behavioral patterns** (learning) -> memory.md or Supabase
      Examples: "user ignores emails from X", "meetings on Tuesdays are usually cancelled"

18. Where should learning state live?
    - **memory.md** (file next to runner) -- only this agent needs it
    - **Hermes MEMORY.md** -- orchestrator should know this too
    - **Supabase** (events or patterns table) -- dashboard should display it

19. Does it need to summarize/compress what it learns?
    - If memory.md grows unbounded, it needs periodic compression
    - Pattern: weekly summary agent reads memory.md, distills key patterns, rewrites

20. Should it update its own behavior based on patterns?
    - Self-improving: agent reads its memory and adjusts approach
    - Static: agent always follows the same prompt regardless of history

## Phase 9: Observability (agent-specific)

21. What events should be logged to the events table?
    - Every run (start + completion)
    - Only on findings/results
    - Only on errors
    - All of the above

22. Should it notify the user?
    - **Always** -- every run sends a message
    - **Only when important** -- use [SILENT] pattern: agent starts response with [SILENT] to suppress notification
    - **Never** -- background agent, results only visible on dashboard
    - What channel? (Telegram, email, dashboard notification)

23. What does a "nothing to report" run look like?
    - [SILENT] -- no message sent
    - Brief acknowledgment: "Checked, nothing new"
    - Skip entirely
