---
name: build-worker
description: >
  Planning partner and scaffold generator for creating workers -- one-shot LLM
  tasks that take input, call Claude once, and produce structured output. Use
  when the user wants to create a new worker, cron job, or single-pass LLM task.
  Triggers on: "build a worker", "new worker", "create a cron job",
  "I need a script that calls Claude to...", "/build-worker".
---

# Build Worker

Create a standardized worker -- a one-shot LLM task with editable config files.

## Workflow

Follow these phases in order. Be conversational -- ask 1-2 questions at a time, not a form.

### Phase 1: Understand

Read `references/questioning-guide.md` for the full question framework. Walk through each phase with the user:

1. **Purpose** -- What does it do? What problem does it solve?
2. **Trigger** -- What starts it? (cron, API call, agent, manual, dashboard event)
3. **Input** -- What data does it need? Where does that data come from?
4. **Output** -- Where do results go? What format?
5. **Tools** -- Does it need external services? Check for existing MCP servers.
6. **Language** -- TypeScript if triggered by Next.js/dashboard, Python otherwise.

### Phase 2: Discover Existing Tools

Before scaffolding, check for reusable infrastructure:

1. Look for a `tools/` directory at or above the output path
2. List any existing MCP servers found (read their README.md or server.py docstrings)
3. Present available servers to the user and ask which ones this worker needs
4. For common integrations (Gmail, Calendar, GitHub, Postgres, Supabase), suggest well-known community MCP servers if no local one exists
5. If a needed integration doesn't exist, note it as a TODO in the generated config

### Phase 3: Scaffold

Read `references/scaffold-spec.md` for the exact file formats and templates.

1. Ask the user where to create the worker folder
2. Run `scripts/scaffold.py` with the collected answers to generate all files
3. Review the generated files with the user
4. Customize prompt.md and output.md based on the specific use case
5. Fill in gather_context() and write_results() in the runner based on the input/output discussion

### Phase 4: Verify

1. Ensure config.yaml is valid
2. Ensure runner imports are correct for the chosen language
3. Walk through any TODOs that need manual implementation
4. Confirm the worker is ready to run or note what's left
