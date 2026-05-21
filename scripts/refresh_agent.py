"""
CDes AI Tools Matrix — Daily Refresh Agent
Calls Claude API with web search to surface new/changed AI design tools.
Results are written to data/pending_submissions.json for human review.
Nothing is promoted to the master list without a human approving it first.
"""

import os
import json
import datetime
import urllib.request

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-opus-4-20250514"
TODAY = datetime.date.today().isoformat()


def load_known_tools(path="data/known_tools.json"):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def call_claude(known_tools: list) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable not set")

    known_names = [t["name"] for t in known_tools]
    known_list_str = "\n".join(f"- {n}" for n in known_names)

    system_prompt = """You are a research assistant maintaining the College of Design (University of Minnesota) AI Tools Matrix.
Your job is to identify AI tools relevant to design disciplines that are either new, updated, or not yet in the matrix.

Disciplines: Architecture, Interior Design, Landscape Architecture, Product Design,
Graphic Design, Apparel Design, Retail Merchandising, Human Factors & Ergonomics, UX Design.

Process stages: Research, Analysis, Ideation, Prototyping, Production, Presentation, Collaboration.

You must respond ONLY with valid JSON — no preamble, no markdown fences, no explanation outside the JSON."""

    user_prompt = f"""Today is {TODAY}.

Tools already in the matrix (do not re-suggest unless there is a significant update):
{known_list_str}

Task: Use web search to find AI tools relevant to the design disciplines above that have been
released, significantly updated, or gained notable adoption in the past 30 days.

Return a JSON object with this exact structure:
{{
  "new_tools": [
    {{
      "tool_name": "string",
      "vendor": "string",
      "url": "string",
      "tool_type": "string",
      "primary_disciplines": ["string"],
      "process_stages": ["string"],
      "key_ai_capability": "string",
      "pricing": "string",
      "reason_for_suggestion": "string",
      "confidence": "high|medium|low"
    }}
  ],
  "updates_to_existing": [
    {{
      "tool_name": "string",
      "change_description": "string",
      "change_type": "pricing|new_feature|discontinuation|rebranding|other",
      "source_url": "string",
      "confidence": "high|medium|low"
    }}
  ],
  "scan_date": "{TODAY}",
  "summary": "1-2 sentence summary of what was found"
}}

Only include items with confidence medium or high.
If nothing notable was found, return empty arrays and explain in summary."""

    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 4000,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = json.loads(resp.read().decode("utf-8"))

    # Extract text blocks from response (ignore tool_use blocks)
    text_blocks = [b["text"] for b in raw.get("content", []) if b.get("type") == "text"]
    text = "\n".join(text_blocks).strip()

    # Strip markdown fences if the model added them despite instructions
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    return json.loads(text)


def write_pending(results: dict, path="data/pending_submissions.json"):
    existing = []
    if os.path.exists(path):
        with open(path) as f:
            existing = json.load(f)

    new_count = 0
    update_count = 0

    for tool in results.get("new_tools", []):
        existing.append({
            "type": "new_tool",
            "status": "pending",
            "scan_date": results["scan_date"],
            **tool
        })
        new_count += 1

    for update in results.get("updates_to_existing", []):
        existing.append({
            "type": "update",
            "status": "pending",
            "scan_date": results["scan_date"],
            **update
        })
        update_count += 1

    with open(path, "w") as f:
        json.dump(existing, f, indent=2)

    return new_count, update_count


def write_run_log(results: dict, new_count: int, update_count: int,
                  log_path="data/run_log.json"):
    log = []
    if os.path.exists(log_path):
        with open(log_path) as f:
            log = json.load(f)

    log.append({
        "date": results["scan_date"],
        "new_tools_found": new_count,
        "updates_found": update_count,
        "summary": results.get("summary", ""),
    })

    log = log[-90:]  # Keep last 90 days

    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)


if __name__ == "__main__":
    print(f"CDes AI Matrix Refresh Agent — {TODAY}")
    known = load_known_tools()
    print(f"  Loaded {len(known)} known tools from data/known_tools.json")
    print("  Calling Claude API (web search enabled)...")

    results = call_claude(known)
    new_count, update_count = write_pending(results)
    write_run_log(results, new_count, update_count)

    print(f"  New tools found:    {new_count}")
    print(f"  Updates found:      {update_count}")
    print(f"  Summary: {results.get('summary', 'n/a')}")
    print("  Written to data/pending_submissions.json")
    print("  Review and approve before promoting to known_tools.json")
