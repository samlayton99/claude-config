#!/usr/bin/env python3
"""
Worker Scaffold Generator

Creates a standardized worker folder with all required files.
Called by the /build-worker skill after the questioning phase.

Usage:
    python scaffold.py --name <worker-name> --path <output-dir> --type worker [options]
    python scaffold.py --name <worker-name> --path <output-dir> --type agent [options]

Options:
    --description TEXT       One-line description
    --trigger-type TYPE      cron|api|agent|manual
    --schedule CRON          Cron expression (if trigger is cron)
    --called-by NAME         Agent name (if trigger is agent)
    --output-dest DEST       supabase|agent|file|notification
    --output-table TABLE     Supabase table name
    --event-type TYPE        Event type for events table
    --language LANG          python|typescript (default: python)
    --tools TOOLS            Comma-separated MCP tool patterns
    --needs-prompt-builder   Include prompt_builder.py
    --needs-memory           Include memory.md (agents only)
    --max-turns N            Max agent loop turns (agents only)
    --max-cost FLOAT         Max cost per run in USD (agents only)
    --memory-type TYPE       none|file|supabase|hermes (agents only)
"""
import argparse
import os
import sys
from pathlib import Path


PYTHON_RUNNER_TEMPLATE = '''"""
{name}
{description}

Usage: python runner.py
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
    return {{}}


def save_state(state: dict):
    (BASE / "state.json").write_text(json.dumps(state, indent=2))


async def gather_context(config: dict) -> str:
    """Gather input data for the prompt. Customize per worker."""
    # TODO: implement context gathering
    return ""


def parse_output(raw: str) -> list | dict:
    """Parse LLM response. Strips markdown fences if present."""
    cleaned = raw.strip()
    fence = cleaned.find("```")
    if fence != -1:
        end = cleaned.rfind("```")
        cleaned = cleaned[fence:end].split("\\n", 1)[-1].strip()
    return json.loads(cleaned)


async def call_llm(system: str, user: str, model_config: dict) -> str:
    """Single Claude API call."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={{
                "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }},
            json={{
                "model": model_config.get("model", "claude-sonnet-4-6"),
                "max_tokens": model_config.get("max_tokens", 2048),
                "system": system,
                "messages": [{{"role": "user", "content": user}}],
            }},
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
    full_system = f"{{system_prompt}}\\n\\n## Output Format\\n{{output_format}}"

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
'''

TS_RUNNER_TEMPLATE = '''/**
 * {name}
 * {description}
 */
import {{ readFileSync, writeFileSync, existsSync }} from "fs";
import {{ join }} from "path";
import {{ parse }} from "yaml";

const BASE = __dirname;

function loadConfig() {{
  return parse(readFileSync(join(BASE, "config.yaml"), "utf-8"));
}}

function loadPrompts() {{
  const system = readFileSync(join(BASE, "prompt.md"), "utf-8");
  const output = readFileSync(join(BASE, "output.md"), "utf-8");
  return {{ system, output }};
}}

function loadState(): Record<string, unknown> {{
  const f = join(BASE, "state.json");
  return existsSync(f) ? JSON.parse(readFileSync(f, "utf-8")) : {{}};
}}

function saveState(state: Record<string, unknown>) {{
  writeFileSync(join(BASE, "state.json"), JSON.stringify(state, null, 2));
}}

async function gatherContext(config: any): Promise<string> {{
  // TODO: implement context gathering
  return "";
}}

function parseOutput(raw: string): unknown {{
  let cleaned = raw.trim();
  const match = cleaned.match(/```(?:json)?\\s*([\\s\\S]*?)```/);
  if (match) cleaned = match[1].trim();
  return JSON.parse(cleaned);
}}

async function callLLM(system: string, user: string, model: any): Promise<string> {{
  const res = await fetch("https://api.anthropic.com/v1/messages", {{
    method: "POST",
    headers: {{
      "x-api-key": process.env.ANTHROPIC_API_KEY!,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json",
    }},
    body: JSON.stringify({{
      model: model?.model ?? "claude-sonnet-4-6",
      max_tokens: model?.max_tokens ?? 2048,
      system,
      messages: [{{ role: "user", content: user }}],
    }}),
  }});
  if (!res.ok) throw new Error(`LLM error: ${{res.status}}`);
  const data = await res.json();
  return data.content[0].text;
}}

async function main() {{
  const config = loadConfig();
  const {{ system, output }} = loadPrompts();
  const state = loadState();

  const context = await gatherContext(config);
  const fullSystem = `${{system}}\\n\\n## Output Format\\n${{output}}`;
  const response = await callLLM(fullSystem, context, config.model);
  const result = parseOutput(response);

  // TODO: write results based on config.output.destination

  saveState({{ ...state, last_run: new Date().toISOString() }});
}}

main().catch(console.error);
'''

AGENT_RUNNER_TEMPLATE = '''"""
{name}
{description}

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
    return f"{{system}}\\n\\n## Output Format\\n{{output_fmt}}"


def load_state():
    state_file = BASE / "state.json"
    return json.loads(state_file.read_text()) if state_file.exists() else {{}}


def save_state(state: dict):
    (BASE / "state.json").write_text(json.dumps(state, indent=2))


def load_memory():
    mem_file = BASE / "memory.md"
    return mem_file.read_text() if mem_file.exists() else ""


def save_memory(content: str):
    (BASE / "memory.md").write_text(content)


def resolve_mcp_servers(config: dict) -> dict:
    """Resolve MCP server configs from tools/ directory."""
    servers = {{}}
    tools_dir = BASE.parent / "tools"

    for tool_ref in config.get("tools", []):
        parts = tool_ref.replace("mcp__", "").split("__")
        server_name = parts[0] if parts else tool_ref
        server_dir = tools_dir / server_name
        if (server_dir / "server.py").exists():
            servers[server_name] = {{
                "command": "python",
                "args": [str(server_dir / "server.py")],
            }}
    return servers


async def run(prompt: str = None):
    config = load_config()
    system_prompt = load_prompts()
    state = load_state()
    memory = load_memory()

    if memory:
        system_prompt = f"{{system_prompt}}\\n\\n## Agent Memory\\n{{memory}}"

    mcp_servers = resolve_mcp_servers(config)
    budget = config.get("budget", {{}})

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        mcp_servers=mcp_servers,
        allowed_tools=config.get("tools", []),
        max_turns=budget.get("max_turns", 15),
        max_budget_usd=budget.get("max_cost_usd", 1.0),
    )

    default_prompt = prompt or config.get("trigger", {{}}).get(
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
                print(f"Agent error: {{message}}")

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
'''

PROMPT_BUILDER_TEMPLATE = '''"""
Assembles the full prompt from context data.
Only needed when the worker gathers data from multiple sources.
"""


def build_prompt(system_prompt: str, context: dict) -> tuple[str, str]:
    """Returns (system, user) prompt pair."""
    parts = []

    # TODO: assemble context sections from gathered data
    # Example:
    # if context.get("pushes"):
    #     lines = [f"- {{p['name']}}: {{p['description']}}" for p in context["pushes"]]
    #     parts.append("## Active Pushes\\n" + "\\n".join(lines))

    return system_prompt, "\\n\\n".join(parts)
'''


def create_worker_config(args):
    """Generate config.yaml content."""
    tools_line = ""
    if args.tools:
        tools_list = [t.strip() for t in args.tools.split(",")]
        tools_line = "\n".join(f"  - {t}" for t in tools_list)
    else:
        tools_line = "[]"

    trigger_block = f"  type: {args.trigger_type}"
    if args.schedule:
        trigger_block += f'\n  schedule: "{args.schedule}"'
    if args.called_by:
        trigger_block += f"\n  called_by: {args.called_by}"

    config = f"""name: {args.name}
type: {args.type}
description: {args.description or 'TODO: add description'}

model:
  provider: claude
  model: claude-sonnet-4-6
  max_tokens: {8192 if args.type == 'agent' else 2048}

trigger:
{trigger_block}

tools: {tools_line if '  -' not in tools_line else ''}
"""
    if "  -" in tools_line:
        config += f"tools:\n{tools_line}\n"

    if args.type == "agent":
        config += f"""
budget:
  max_turns: {args.max_turns or 15}
  max_cost_usd: {args.max_cost or 0.50}

memory:
  type: {args.memory_type or 'none'}
"""
        if args.memory_type and args.memory_type != "none":
            config += f"  # {args.memory_type}: "
            if args.memory_type == "file":
                config += "memory.md next to runner\n"
            elif args.memory_type == "supabase":
                config += "patterns stored in events table\n"
            elif args.memory_type == "hermes":
                config += "updates Hermes MEMORY.md\n"

        config += f"""
notify:
  on_complete: true
  silent_when: "nothing notable"
  channel: telegram
"""

    config += f"""
retry:
  parse_retries: 1
  retry_suffix: "\\nIMPORTANT: Respond with ONLY valid JSON."

output:
  destination: {args.output_dest or 'supabase'}
  table: {args.output_table or 'events'}
  event_type: {args.event_type or args.name.replace('-', '_') + '_completed'}
"""
    return config


def scaffold(args):
    """Create the worker/agent folder with all files."""
    output_dir = Path(args.path) / args.name
    output_dir.mkdir(parents=True, exist_ok=True)

    lang = args.language or "python"
    is_agent = args.type == "agent"

    # prompt.md
    (output_dir / "prompt.md").write_text(
        f"You are a {args.description or '[role]'}. Your job is to [purpose].\n\n"
        "## Rules\n- TODO: add specific rules\n\n"
        "## Context You Receive\n- TODO: describe input data\n\n"
        "## Behavior\n- TODO: add constraints and edge cases\n"
    )

    # output.md
    (output_dir / "output.md").write_text(
        "Respond with ONLY a JSON object. No markdown, no explanation.\n\n"
        "```json\n"
        "{\n"
        '  "example_field": "example_value",\n'
        '  "count": 0\n'
        "}\n"
        "```\n\n"
        "## Field Definitions\n"
        "- example_field: string -- TODO: describe\n"
        "- count: integer -- TODO: describe\n"
    )

    # config.yaml
    (output_dir / "config.yaml").write_text(create_worker_config(args))

    # state.json
    (output_dir / "state.json").write_text("{}\n")

    # runner
    if is_agent:
        runner_content = AGENT_RUNNER_TEMPLATE.format(
            name=args.name, description=args.description or "TODO"
        )
        (output_dir / "runner.py").write_text(runner_content)
    elif lang == "python":
        runner_content = PYTHON_RUNNER_TEMPLATE.format(
            name=args.name, description=args.description or "TODO"
        )
        (output_dir / "runner.py").write_text(runner_content)
    else:
        runner_content = TS_RUNNER_TEMPLATE.format(
            name=args.name, description=args.description or "TODO"
        )
        (output_dir / "runner.ts").write_text(runner_content)

    # prompt_builder.py (optional)
    if args.needs_prompt_builder:
        (output_dir / "prompt_builder.py").write_text(PROMPT_BUILDER_TEMPLATE)

    # memory.md (agents only)
    if is_agent and args.needs_memory:
        (output_dir / "memory.md").write_text(
            "# Agent Memory\n\nThis file is updated by the agent across runs.\n"
        )

    # Check for existing tools/
    tools_dir = Path(args.path) / "tools"
    existing_tools = []
    if tools_dir.exists():
        for d in tools_dir.iterdir():
            if d.is_dir() and (d / "server.py").exists():
                existing_tools.append(d.name)

    # Summary
    print(f"\nScaffolded {args.type}: {output_dir}")
    print(f"  Files created:")
    for f in sorted(output_dir.iterdir()):
        print(f"    {f.name}")

    if existing_tools:
        print(f"\n  Existing MCP servers in tools/:")
        for t in existing_tools:
            print(f"    - {t}")

    todos = []
    todos.append("Edit prompt.md with the actual system prompt")
    todos.append("Edit output.md with the actual output format")
    if lang == "python":
        todos.append("Implement gather_context() in runner.py")
        todos.append("Implement write_results() in runner.py")
    else:
        todos.append("Implement gatherContext() in runner.ts")
        todos.append("Add write logic in runner.ts main()")

    if args.needs_prompt_builder:
        todos.append("Implement build_prompt() in prompt_builder.py")

    print(f"\n  TODOs:")
    for t in todos:
        print(f"    - {t}")


def main():
    parser = argparse.ArgumentParser(description="Scaffold a worker or agent")
    parser.add_argument("--name", required=True, help="Worker/agent name (kebab-case)")
    parser.add_argument("--path", required=True, help="Output directory")
    parser.add_argument(
        "--type", choices=["worker", "agent"], default="worker", help="Type"
    )
    parser.add_argument("--description", default="", help="One-line description")
    parser.add_argument(
        "--trigger-type",
        choices=["cron", "api", "agent", "manual"],
        default="manual",
    )
    parser.add_argument("--schedule", default="", help="Cron expression")
    parser.add_argument("--called-by", default="", help="Calling agent name")
    parser.add_argument(
        "--output-dest",
        choices=["supabase", "agent", "file", "notification"],
        default="supabase",
    )
    parser.add_argument("--output-table", default="", help="Supabase table")
    parser.add_argument("--event-type", default="", help="Event type")
    parser.add_argument(
        "--language", choices=["python", "typescript"], default="python"
    )
    parser.add_argument("--tools", default="", help="Comma-separated MCP tools")
    parser.add_argument(
        "--needs-prompt-builder", action="store_true", help="Include prompt_builder.py"
    )
    parser.add_argument(
        "--needs-memory", action="store_true", help="Include memory.md (agents)"
    )
    parser.add_argument("--max-turns", type=int, default=15, help="Agent max turns")
    parser.add_argument(
        "--max-cost", type=float, default=0.50, help="Agent max cost USD"
    )
    parser.add_argument(
        "--memory-type",
        choices=["none", "file", "supabase", "hermes"],
        default="none",
    )
    args = parser.parse_args()

    scaffold(args)


if __name__ == "__main__":
    main()
