# Worker Questioning Guide

Walk through these phases in order. Be conversational -- ask 1-2 questions at a time, build on answers. Do not dump all questions at once.

## Phase 1: Purpose

1. What does this worker do? (get a one-sentence answer)
2. What problem does it solve? Why does it exist? (understand the motivation)

## Phase 2: Trigger

3. How is it initiated? Determine exactly one:
   - **Cron schedule** -- what time/frequency? (e.g., "daily at 7am", "every 6 hours")
   - **Called by another agent** -- which agent? what input does it receive?
   - **HTTP endpoint** -- what triggers the request? what's in the payload?
   - **Manual invocation** -- CLI command? slash command? how does the user run it?
   - **Dashboard event** -- what user action in the UI triggers it?

## Phase 3: Input

4. What data does it need to do its job?
   - Where does that data come from? Options:
     - Supabase query (which tables?)
     - External API call (which API?)
     - User-provided text (from message, form, CLI arg?)
     - File on disk
     - Output from another worker/agent
   - Is context assembly simple (just pass the input through) or complex (gather from multiple sources, format, combine)?
   - If complex: a prompt_builder.py will be generated

## Phase 4: Output

5. Where do results go? Determine destination:
   - **Supabase table** -- which table? existing or new? what columns?
   - **Returned to calling agent** -- what format does the caller expect?
   - **Written to file/scratchpad** -- where? what format?
   - **Sent as notification** -- Telegram, email, Slack? what channel?
   - **Multiple destinations** -- e.g., write to Supabase AND notify

6. What does the output look like?
   - JSON structure -- define the schema with the user
   - Free text -- what sections/format?
   - Get a concrete example of what the output should look like

## Phase 5: Tools & Integration

7. Does it need any external services?
   - Gmail, Google Calendar, Slack (check for first-party MCP connectors)
   - Twitter/X, arXiv, Semantic Scholar (check for community MCP servers)
   - Supabase, Postgres (check for database MCP servers)
   - Custom APIs (will need a custom MCP server or direct HTTP calls)

8. Check `tools/` folder in/above the output directory:
   - List existing MCP servers
   - Ask user which ones this worker needs
   - Note any new MCP servers that need to be built as TODOs

9. Are there existing workers/agents with similar patterns to reference?
   - Check sibling directories for structural patterns to follow

## Phase 6: Language

10. Determine automatically, confirm with user:
    - If triggered by a Next.js/TypeScript cron or API route: **TypeScript**
    - If standalone on VM or called by Hermes: **Python**
    - If user has a strong preference: respect it
    - Default: **Python**
