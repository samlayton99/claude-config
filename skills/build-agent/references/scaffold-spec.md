# Agent Scaffold Specification

## Folder Structure

```
<agent-name>/
  prompt.md              # System prompt: role, instructions, behavior
  output.md              # Expected output format for final summary/report
  config.yaml            # Name, type, model, tools, budget, schedule, memory, notify
  runner.py              # Agent SDK loop: query() with MCP tools
  state.json             # Empty {} -- runner populates at runtime
  prompt_builder.py      # Context assembly (usually needed for agents)
  memory.md              # ONLY if agent needs cross-run learning (optional)
```

## Key Differences from Worker Scaffold

| Aspect | Worker | Agent |
|--------|--------|-------|
| Runner | Single call_llm() | Agent SDK query() loop |
| Tools | Usually none | MCP servers (Gmail, Dashboard, etc.) |
| Loop | No | Yes -- Claude decides when to stop |
| Memory | state.json only | state.json + optional memory.md |
| Config | Basic | Adds budget, memory, notify sections |
| Cost | ~$0.01-0.05 per run | ~$0.10-2.00 per run |

## File Templates

### config.yaml (agent-specific additions)

```yaml
name: <agent-name>
type: agent
description: <one-line>

model:
  provider: claude
  model: claude-sonnet-4-6
  max_tokens: 8192

trigger:
  type: <cron|message|agent|manual>
  schedule: <cron expression>
  default_prompt: "Execute your task."

tools:
  - mcp__dashboard__*
  - mcp__gmail__*

budget:
  max_turns: 15
  max_cost_usd: 0.50

memory:
  type: <none|file|supabase|hermes>
  # none = no cross-run memory
  # file = memory.md next to runner
  # supabase = patterns stored in events table
  # hermes = updates Hermes MEMORY.md

notify:
  on_complete: true
  silent_when: "nothing notable"    # [SILENT] pattern
  channel: telegram

retry:
  parse_retries: 1
  retry_suffix: "\nIMPORTANT: Respond with ONLY valid JSON."

output:
  destination: supabase
  table: <table>
  event_type: <event_type>
```

### runner.py (Agent SDK loop)

```python
"""
<Agent Name>
<One-line description>

Usage: python runner.py [--prompt "custom prompt"]
"""
import asyncio
import json
import os
import yaml
from datetime import datetime
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

BASE = Path(__file__).parent


def load_config():
    return yaml.safe_load((BASE / "config.yaml").read_text())


def load_prompts():
    system = (BASE / "prompt.md").read_text()
    output_fmt = (BASE / "output.md").read_text()
    return f"{system}\n\n## Output Format\n{output_fmt}"


def load_state():
    state_file = BASE / "state.json"
    return json.loads(state_file.read_text()) if state_file.exists() else {}


def save_state(state: dict):
    (BASE / "state.json").write_text(json.dumps(state, indent=2))


def load_memory():
    mem_file = BASE / "memory.md"
    return mem_file.read_text() if mem_file.exists() else ""


def save_memory(content: str):
    (BASE / "memory.md").write_text(content)


def resolve_mcp_servers(config: dict) -> dict:
    """Resolve MCP server configs from tools/ directory."""
    servers = {}
    tools_dir = BASE.parent / "tools"

    for tool_ref in config.get("tools", []):
        parts = tool_ref.replace("mcp__", "").split("__")
        server_name = parts[0] if parts else tool_ref
        server_dir = tools_dir / server_name
        if (server_dir / "server.py").exists():
            servers[server_name] = {
                "command": "python",
                "args": [str(server_dir / "server.py")],
            }
    return servers


async def run(prompt: str = None):
    config = load_config()
    system_prompt = load_prompts()
    state = load_state()
    memory = load_memory()

    if memory:
        system_prompt = f"{system_prompt}\n\n## Agent Memory\n{memory}"

    mcp_servers = resolve_mcp_servers(config)
    budget = config.get("budget", {})

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        mcp_servers=mcp_servers,
        allowed_tools=config.get("tools", []),
        max_turns=budget.get("max_turns", 15),
        max_budget_usd=budget.get("max_cost_usd", 1.0),
    )

    default_prompt = prompt or config.get("trigger", {}).get(
        "default_prompt", "Execute your task."
    )
    result_text = ""

    async for message in query(prompt=default_prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    result_text = block.text
        elif isinstance(message, ResultMessage):
            if message.subtype == "error_during_execution":
                print(f"Agent error: {message}")

    state["last_run"] = datetime.now().isoformat()
    state["runs"] = state.get("runs", 0) + 1
    save_state(state)

    return result_text


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default=None)
    args = parser.parse_args()
    result = asyncio.run(run(args.prompt))
    print(result)
```

### memory.md (when agent needs cross-run learning)

Initialize as:
```markdown
# Agent Memory

This file is updated by the agent across runs.
```

The agent reads this at startup (injected into system prompt as `## Agent Memory`) and can update it via save_memory(). Content should be bounded -- if it grows past ~2000 chars, the agent should summarize/compress.

### Scaffolding

The /build-agent skill reuses the scaffold script from /build-worker:

```bash
python ~/.claude/skills/build-worker/scripts/scaffold.py \
  --type agent \
  --name <agent-name> \
  --path <output-dir> \
  --description "..." \
  --trigger-type cron \
  --schedule "0 7 * * *" \
  --tools "mcp__dashboard__*,mcp__gmail__*" \
  --max-turns 15 \
  --max-cost 0.50 \
  --memory-type file \
  --needs-memory \
  --needs-prompt-builder
```
