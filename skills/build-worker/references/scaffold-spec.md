# Worker Scaffold Specification

## Folder Structure

```
<worker-name>/
  prompt.md              # System prompt: role, instructions, behavior rules
  output.md              # Expected response format with concrete examples
  config.yaml            # Name, type, model, trigger, tools, retry, output destination
  runner.py              # One-shot execution (or runner.ts for TypeScript)
  state.json             # Empty {} -- runner populates at runtime
  prompt_builder.py      # ONLY if complex context assembly needed (optional)
```

## File Templates

### prompt.md

```markdown
You are [role]. Your job is to [purpose].

## Rules
- [derived from questioning -- specific, actionable constraints]

## Context You Receive
- [describe each piece of data passed in and what it means]

## Behavior
- [constraints, priorities, edge cases]
- [what to do when data is missing or ambiguous]
```

### output.md

```markdown
Respond with ONLY a JSON [array/object]. No markdown, no explanation.

[concrete example with realistic data]

## Field Definitions
- field_name: type -- description and constraints
```

### config.yaml

```yaml
name: <worker-name>
type: worker
description: <one-line description>

model:
  provider: claude
  model: claude-sonnet-4-6
  max_tokens: 2048

trigger:
  type: <cron|api|agent|manual>
  schedule: <cron expression if applicable>
  called_by: <agent name if applicable>

tools: []    # MCP tools needed, e.g. ["mcp__dashboard__*"]

retry:
  parse_retries: 1
  retry_suffix: "\n\nIMPORTANT: Respond with ONLY valid JSON."

output:
  destination: <supabase|agent|file|notification>
  table: <table name if supabase>
  event_type: <event type for events table>
```

### runner.py (Python)

```python
"""
<Worker Name>
<One-line description>

Usage: python runner.py [--date DATE]
"""
import asyncio
import json
import os
import yaml
from datetime import datetime
from pathlib import Path

import httpx

BASE = Path(__file__).parent


def load_config():
    return yaml.safe_load((BASE / "config.yaml").read_text())


def load_prompts():
    system = (BASE / "prompt.md").read_text()
    output_fmt = (BASE / "output.md").read_text()
    return system, output_fmt


def load_state():
    state_file = BASE / "state.json"
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {}


def save_state(state: dict):
    (BASE / "state.json").write_text(json.dumps(state, indent=2))


async def gather_context(config: dict) -> str:
    """Gather input data for the prompt. Customize per worker."""
    # TODO: implement context gathering
    return ""


def parse_output(raw: str) -> list | dict:
    """Parse LLM response. Strips markdown fences if present."""
    cleaned = raw.strip()
    match = cleaned.find("```")
    if match != -1:
        end = cleaned.rfind("```")
        cleaned = cleaned[match:end].split("\n", 1)[-1].strip()
    return json.loads(cleaned)


async def call_llm(system: str, user: str, model_config: dict) -> str:
    """Single Claude API call."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model_config.get("model", "claude-sonnet-4-6"),
                "max_tokens": model_config.get("max_tokens", 2048),
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


async def write_results(results, config: dict):
    """Write results to destination. Customize per worker."""
    # TODO: implement based on config output.destination
    pass


async def main():
    config = load_config()
    system_prompt, output_format = load_prompts()
    state = load_state()

    # 1. Gather context
    context = await gather_context(config)

    # 2. Build full prompt
    full_system = f"{system_prompt}\n\n## Output Format\n{output_format}"

    # 3. Call LLM
    response = await call_llm(full_system, context, config["model"])

    # 4. Parse
    result = parse_output(response)

    # 5. Write results
    await write_results(result, config)

    # 6. Update state
    state["last_run"] = datetime.now().isoformat()
    save_state(state)


if __name__ == "__main__":
    asyncio.run(main())
```

### runner.ts (TypeScript)

```typescript
/**
 * <Worker Name>
 * <One-line description>
 */
import { readFileSync, writeFileSync, existsSync } from "fs";
import { join } from "path";
import { parse } from "yaml";

const BASE = __dirname;

function loadConfig() {
  return parse(readFileSync(join(BASE, "config.yaml"), "utf-8"));
}

function loadPrompts() {
  const system = readFileSync(join(BASE, "prompt.md"), "utf-8");
  const output = readFileSync(join(BASE, "output.md"), "utf-8");
  return { system, output };
}

function loadState(): Record<string, unknown> {
  const f = join(BASE, "state.json");
  return existsSync(f) ? JSON.parse(readFileSync(f, "utf-8")) : {};
}

function saveState(state: Record<string, unknown>) {
  writeFileSync(join(BASE, "state.json"), JSON.stringify(state, null, 2));
}

async function gatherContext(config: any): Promise<string> {
  // TODO: implement context gathering
  return "";
}

function parseOutput(raw: string): unknown {
  let cleaned = raw.trim();
  const match = cleaned.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (match) cleaned = match[1].trim();
  return JSON.parse(cleaned);
}

async function callLLM(
  system: string,
  user: string,
  model: any
): Promise<string> {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": process.env.ANTHROPIC_API_KEY!,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json",
    },
    body: JSON.stringify({
      model: model?.model ?? "claude-sonnet-4-6",
      max_tokens: model?.max_tokens ?? 2048,
      system,
      messages: [{ role: "user", content: user }],
    }),
  });
  if (!res.ok) throw new Error(`LLM error: ${res.status}`);
  const data = await res.json();
  return data.content[0].text;
}

async function main() {
  const config = loadConfig();
  const { system, output } = loadPrompts();
  const state = loadState();

  const context = await gatherContext(config);
  const fullSystem = `${system}\n\n## Output Format\n${output}`;
  const response = await callLLM(fullSystem, context, config.model);
  const result = parseOutput(response);

  // TODO: write results based on config.output.destination

  saveState({ ...state, last_run: new Date().toISOString() });
}

main().catch(console.error);
```

### prompt_builder.py (optional -- only when context assembly is complex)

```python
"""
Assembles the full prompt from context data.
Only create this file when the worker needs to gather data from multiple sources
and format it into a structured prompt.
"""


def build_prompt(system_prompt: str, context: dict) -> tuple[str, str]:
    """Returns (system, user) prompt pair."""
    parts = []

    # Example patterns:
    # if context.get("pushes"):
    #     push_lines = [f"- {p['name']}: {p['description']}" for p in context["pushes"]]
    #     parts.append(f"## Active Pushes\n" + "\n".join(push_lines))
    #
    # if context.get("recent_actions"):
    #     action_lines = [f"- [{a['needle_score']}] {a['description']}" for a in context["recent_actions"]]
    #     parts.append(f"## Recent Actions\n" + "\n".join(action_lines))

    return system_prompt, "\n\n".join(parts)
```

### state.json

Always initialize as empty:
```json
{}
```
The runner populates this at runtime with operational state (last_run, cursors, counts).
