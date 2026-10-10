# EventPilot — Self-Improving Pre-Event Planning Agent

**A multi-agent workflow that takes ONE event brief and runs pre-event planning end-to-end — then learns from feedback to make every future plan better than the last.**

Built for the hackathon. Runs on [WorkBuddy AI](https://www.workbuddy.ai/) as the primary execution platform.

---

## The Problem

Businesses that host customer events (product launches, seminars, appreciation nights) lose days on pre-event admin: emailing hotels one by one, chasing quotes, checking for hidden conditions, comparing by hand, designing invitations, managing RSVPs.

Worse, **lessons learned are lost**. When a venue disappoints, that knowledge lives in one person's head. The next organiser repeats the same mistake.

## What EventPilot Does

1. **One brief in → full plan out.** Give it the event details and a customer database. It sources venues, sends RFQs, analyses quotes, recommends a venue, designs the invitation, and sets up RSVP.

2. **Learns from feedback.** After the event, it captures structured feedback about the venue, stores it in Venue Memory, and proposes playbook updates (new RFQ questions, ranking rules) that make the next plan smarter.

3. **Context-aware memory.** A low-ceiling flag counts against a venue for grand launches, not for 50-pax seminars. Positive feedback boosts rankings.

4. **Human-in-the-loop.** Three checkpoints: approve hotel shortlist + RFQ, approve venue + invitation, approve playbook updates.

---

## Architecture

```
User Brief (chat)
       │
       ▼
┌─────────────────┐
│  Orchestrator   │  ← EventPilot Skill (SKILL.md)
│  (Skill Layer)  │
└────────┬────────┘
         │ delegates to
    ┌────┴────┬─────────┬───────────┬──────────┐
    ▼         ▼         ▼           ▼          ▼
┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Brief  │ │Venue │ │Outreach│ │ Quote  │ │Learning│
│ Agent  │ │Scout │ │ Agent  │ │Analyst │ │ Agent  │
└────┬───┘ └──┬───┘ └───┬────┘ └───┬────┘ └───┬────┘
     │        │         │          │          │
     ▼        ▼         ▼          ▼          ▼
┌──────────────────────────────────────────────────┐
│              MCP Server (Python)                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │  Venue   │ │  Email   │ │  Memory Store    │ │
│  │  Search  │ │  Sim     │ │  (SQLite)        │ │
│  └──────────┘ └──────────┘ │  - Venue Memory  │ │
│                              │  - Playbooks     │ │
│                              │  - Proposals     │ │
│                              └──────────────────┘ │
└──────────────────────────────────────────────────┘
```

### Components

| Component | Technology | Purpose |
|---|---|---|
| **Orchestrator Skill** | WorkBuddy SKILL.md | Defines the workflow, delegates to agents, manages checkpoints |
| **MCP Server** | Python + FastMCP | Exposes tools for memory, venue search, email simulation, quote analysis |
| **Memory Store** | SQLite | Venue Memory (feedback), Event Playbooks (learned rules), Proposals |
| **Venue Database** | JSON | 5 mock KL hotels with varied conditions |
| **Customer Database** | CSV | 20 mock customers with segments (VIP/Premium/Standard) |

### Agents (7 + Orchestrator)

| # | Agent | Responsibility |
|---|---|---|
| 0 | Orchestrator | Owns the plan, delegates, tracks state, notifies at checkpoints |
| 1 | Brief Agent | Validates brief, loads playbook, asks for missing + learned fields |
| 2 | Venue Scout | Searches venues, checks Venue Memory, flags/re-ranks, shortlists |
| 3 | Outreach Agent | Drafts RFQ emails (with learned questions), sends, monitors inbox |
| 4 | Quote Analyst | Parses quotes, normalises pricing, checks traps, scores vs budget |
| 5 | Invitation Designer | Runs in parallel with outreach; generates e-invite via ImageGen |
| 6 | RSVP Agent | Creates RSVP form, sends invites, schedules reminders, tracks |
| 7 | Learning Agent | Post-event feedback → structured memory → playbook proposals |

---

## Setup

### Prerequisites
- Python 3.11+
- WorkBuddy AI (desktop app)
- Git

### 1. Clone the repo
```bash
git clone <repo-url>
cd eventpilot
```

### 2. Install Python dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure WorkBuddy MCP

Add the EventPilot MCP server to WorkBuddy's MCP config at `~/.workbuddy-ai/mcp.json`:

```json
{
  "mcpServers": {
    "eventpilot": {
      "command": "python3",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/eventpilot"
    }
  }
}
```

Replace `/absolute/path/to/eventpilot` with the actual path to this repo.

After saving, open WorkBuddy → Connector Management → trust the `eventpilot` server.

### 4. Verify
In a WorkBuddy chat, type:
> "Show demo status"

EventPilot should respond with the current memory state.

---

## Demo Walkthrough

### Run 1 — Plan an event (fresh)

1. **Reset:** Type "reset demo"
2. **Brief:** "Plan a grand product launch for ~150 guests in KL, mid-December, budget RM 25,000, theatre seating, lunch included, needs projector + wireless mics."
3. EventPilot:
   - Loads playbook (default — no learned requirements yet)
   - Searches venues → shortlists 4 grand-tier KL hotels
   - No venue feedback flags (memory is empty)
   - Sends RFQs → seeds simulated quotes
   - Analyses quotes → flags minimum-pax trap (Hotel B), ++ pricing (Hotel C), over-budget (Hotel A)
   - Recommends Hotel E (Sheraton) — clean winner, nett pricing, all-inclusive
   - Generates invitation design
4. **Fast-forward:** Type "fast forward to post-event"
5. EventPilot:
   - Seeds feedback: Hotel A ceiling too low (dealbreaker), AV great; Hotel E ceiling perfect, service excellent
   - Proposes playbook updates: add ceiling_height to RFQ, down-rank low-ceiling venues
6. **Approve:** Type "approve the playbook updates"
7. Playbook now has learned requirements.

### Run 2 — Same request, smarter agent

1. **Brief:** "Plan another product launch, ~200 guests, KL, March."
2. EventPilot:
   - Loads playbook → NOW has ceiling_height as a learned requirement
   - Asks about ceiling height (was NOT asked in Run 1)
   - Searches venues → Hotel A FLAGGED with dealbreaker
   - Hotel E BOOSTED with positive feedback
   - RFQ includes "Please state ballroom ceiling height"
   - Recommendation cites feedback sources

### Visible before/after difference
| Aspect | Run 1 | Run 2 |
|---|---|---|
| Intake questions | Standard fields only | + ceiling height question |
| Venue flags | None | Hotel A: dealbreaker, Hotel E: positive |
| RFQ content | Standard requirements | + ceiling height question |
| Ranking | By price/capacity | Hotel A down-ranked, Hotel E boosted |

---

## Data Schema

### Venue Memory (venue_feedback table)
```json
{
  "id": "fb_20261220120000_hotel_a",
  "venue_id": "hotel_a",
  "venue_name": "Grand Hyatt Kuala Lumpur",
  "room_name": "Grand Ballroom",
  "event_type": "product_launch",
  "event_tier": "grand",
  "event_ref": "product_launch_dec_2026",
  "attribute": "ceiling_height",
  "sentiment": "negative",
  "severity": "dealbreaker",
  "note": "Ceiling too low for grand atmosphere",
  "feedback_date": "2026-12-20"
}
```

### Event Playbook
```json
{
  "event_type": "product_launch",
  "event_tier": "grand",
  "required_brief_fields": ["event_purpose", "date", "budget", ...],
  "learned_requirements": [
    {
      "field": "ceiling_height",
      "question": "What is the minimum ceiling height required?",
      "rfq_question": "Please state the ballroom ceiling height (in meters).",
      "source_feedback": "fb_...",
      "source_event": "product_launch_dec_2026",
      "status": "approved"
    }
  ],
  "venue_ranking_rules": [
    {
      "rule_id": "prop_...",
      "description": "Down-rank venues flagged for low ceiling height",
      "applies_to_attribute": "ceiling_height",
      "sentiment_filter": "negative",
      "severity_filter": ["dealbreaker"],
      "status": "approved"
    }
  ]
}
```

---

## Tech Stack
- **Platform:** WorkBuddy AI
- **MCP Server:** Python 3.13, FastMCP
- **Database:** SQLite
- **Skill:** WorkBuddy SKILL.md
- **Image Generation:** WorkBuddy ImageGen (for invitations)

## Team
- Built at [hackathon name] by [team members]

## License
MIT
