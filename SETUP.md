# EventPilot — Teammate Setup Guide

This guide gets a new teammate from clone to demo in ~10 minutes.

---

## Prerequisites

- **WorkBuddy AI** installed (desktop app)
- **Python 3.11+** on your machine
- **GitHub CLI** (`gh`) or Git installed
- **macOS or Linux** (Windows not tested)

---

## Step 1: Clone the Repo

```bash
git clone https://github.com/jeechew-dev/eventpilot.git
cd eventpilot
```

## Step 2: Install Python Dependencies

You need a Python virtual environment with the `mcp` package.

### Option A: Use WorkBuddy's managed Python (recommended)

```bash
# Create the venv (skip if already exists)
~/.workbuddy-ai/binaries/python/versions/3.13.12/bin/python3 -m venv ~/.workbuddy-ai/binaries/python/envs/default

# Install deps
~/.workbuddy-ai/binaries/python/envs/default/bin/pip install -r requirements.txt
```

Your Python path will be: `~/.workbuddy-ai/binaries/python/envs/default/bin/python3`

### Option B: Use your own Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Your Python path will be: `./venv/bin/python3` (relative to the repo root)

## Step 3: Configure WorkBuddy MCP Server

Copy the template and edit it with your paths:

```bash
cp mcp.json.example ~/.workbuddy-ai/mcp.json
```

Open `~/.workbuddy-ai/mcp.json` and replace:
- `<PYTHON_PATH>` → your Python path from Step 2
- `<REPO_PATH>` → absolute path to the cloned repo

**Example (Option A):**
```json
{
  "mcpServers": {
    "eventpilot": {
      "command": "/Users/yourusername/.workbuddy-ai/binaries/python/envs/default/bin/python3",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/Users/yourusername/projects/eventpilot",
      "env": {
        "PYTHONPATH": "/Users/yourusername/projects/eventpilot"
      }
    }
  }
}
```

**Example (Option B):**
```json
{
  "mcpServers": {
    "eventpilot": {
      "command": "/Users/yourusername/projects/eventpilot/venv/bin/python3",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/Users/yourusername/projects/eventpilot",
      "env": {
        "PYTHONPATH": "/Users/yourusername/projects/eventpilot"
      }
    }
  }
}
```

## Step 4: Restart WorkBuddy & Trust the Server

1. **Quit WorkBuddy completely** (Cmd+Q on Mac)
2. **Reopen WorkBuddy**
3. Open the `eventpilot` folder as your workspace
4. Look for the **connector notification** (top-right or bottom-left `+` menu)
5. Click **Trust** on the `eventpilot` MCP server

## Step 5: Verify It Works

Type this in WorkBuddy chat:

```
Show demo status
```

You should see:
```
Venue feedback entries: 0
Active playbooks: 0
Pending proposals: 0
Approved proposals: 0
Simulated emails: 0
RFQs sent: 0
```

If that works, try the full demo prompt:

```
Reset the demo, then plan a grand product launch for ~150 guests in KL, mid-December, budget RM 25,000, theatre seating, lunch included, needs projector + wireless mics.
```

---

## Project Structure

```
eventpilot/
├── mcp_server/              ← Python MCP server (the "backend")
│   ├── server.py            ← 21 MCP tools (entry point)
│   ├── db.py                ← SQLite database layer
│   ├── seed_data.py         ← Demo data (quotes, feedback)
│   └── __init__.py
├── .workbuddy-ai/
│   └── skills/
│       └── eventpilot/
│           └── SKILL.md     ← Orchestrator skill (the "business logic")
├── data/
│   ├── venues.json          ← 5 mock KL hotels
│   └── customers.csv        ← 20 mock customers
├── docs/
│   └── architecture.md      ← System architecture diagrams
├── demo/
│   └── demo_script.md       ← Step-by-step judge demo script
├── mcp.json.example         ← Template for MCP config
├── SETUP.md                 ← This file
├── requirements.txt         ← Python dependencies
├── .gitignore
└── README.md
```

## What Each Person Can Work On

The project splits cleanly into parallel workstreams:

### Workstream A — Skill Refinement
- Improve `SKILL.md` prompt engineering
- Test the full Run 1 → Run 2 demo flow in WorkBuddy chat
- Refine how the agent presents results (formatting, timing, narration)
- Add the ImageGen invitation design step
- Practice the demo script

### Workstream B — MCP Server Features
- Add new tools or refine existing ones in `mcp_server/server.py`
- Extend `seed_data.py` with more demo scenarios
- Add real web search for venue discovery (replace mock JSON)
- Add RSVP form creation (HTML + cloud-service)
- Improve the quote analysis output format

Both workstreams can proceed independently — Skill changes don't require server changes and vice versa. Just coordinate on tool names/parameters if adding new tools.

---

## Troubleshooting

### "Tool not found" in WorkBuddy chat
→ MCP server not trusted. Repeat Step 4 (restart + trust).

### Python import errors
→ PYTHONPATH not set correctly in mcp.json. Make sure it points to the repo root.

### SQLite database errors
→ Delete `data/eventpilot_memory.db` and restart. The DB auto-creates on first run.

### Server won't start
→ Test manually: `cd /path/to/eventpilot && PYTHONPATH=. python3 -m mcp_server.server`
→ It should start and wait for input (no errors). Ctrl+C to stop.
