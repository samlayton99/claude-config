---
name: build-agent
description: >
  Planning partner and scaffold generator for creating agents -- async LLM loops
  that use tools, make decisions, and produce side effects. Use when the user wants
  to create a new agent that needs to explore, call APIs, or make multi-step decisions.
  Triggers on: "build an agent", "new agent", "create an agent",
  "I need an agent that...", "/build-agent".
---

# Build Agent

Create a standardized agent -- an async LLM loop with tools, memory, and observability.

Agents differ from workers: they call tools, make decisions across multiple turns, and can learn across runs. Use `/build-worker` instead for one-shot LLM tasks.

## Workflow

Follow these phases in order. Be conversational -- ask 1-2 questions at a time.

### Phase 1: Understand (same as /build-worker)

Read `references/questioning-guide.md` for the full question framework. Walk through:

1. **Purpose** -- What does it do? What problem does it solve?
2. **Trigger** -- What starts it? (cron, message, agent, manual)
3. **Input** -- What data does it need? Where from?
4. **Output** -- Where do results go? What format?
5. **Language** -- Python (default for standalone agents)

### Phase 2: Agent-Specific Questions

Continue with the agent-specific phases in `references/questioning-guide.md`:

6. **Tools & Capabilities** -- What MCP servers does it need? What can it do?
7. **Loop Behavior** -- Max turns, cost budget, completion criteria
8. **Memory & Learning** -- Does it remember across runs? Where does it store knowledge?
9. **Observability** -- What events to log? When to notify the user?

### Phase 3: Discover Existing Tools

Before scaffolding, check for reusable infrastructure:

1. Look for a `tools/` directory at or above the output path
2. List any existing MCP servers found
3. Present available servers to the user and ask which ones this agent needs
4. For common integrations, suggest well-known MCP servers
5. If a needed integration doesn't exist, note it as a TODO
6. If the agent needs a NEW MCP server, discuss what API it wraps and note it for separate creation

### Phase 4: Scaffold

Read `references/scaffold-spec.md` for the exact file formats and templates.

1. Ask the user where to create the agent folder
2. Run the scaffold script: `python ~/.claude/skills/build-worker/scripts/scaffold.py --type agent [options]`
   (Reuses the same scaffold.py from build-worker with --type agent flag)
3. Review the generated files with the user
4. Customize prompt.md, output.md, and the runner based on the discussions
5. Set up memory.md if the agent needs cross-run learning
6. Configure MCP server references in config.yaml

### Phase 5: Verify

1. Ensure config.yaml is valid and all tool references resolve
2. Ensure runner.py has correct Agent SDK imports
3. Walk through TODOs
4. Confirm MCP servers exist or are noted as TODOs
5. Verify memory strategy is configured correctly
