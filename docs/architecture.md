# EventPilot Architecture

## System Overview

EventPilot is a multi-agent agentic workflow built on WorkBuddy AI. It uses a **Combo approach**: a Skill (orchestrator) + MCP server (tools) + multi-agent delegation pattern.

```
┌────────────────────────────────────────────────────────────────────┐
│                         WorkBuddy AI                               │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  EventPilot Skill (SKILL.md) — Orchestrator                  │  │
│  │                                                               │  │
│  │  Phase 1: Brief Agent     → validate, load playbook           │  │
│  │  Phase 2: Venue Scout     → search, check memory, shortlist   │  │
│  │  Phase 3: Outreach Agent  → send RFQs, monitor inbox          │  │
│  │  Phase 4: Quote Analyst   → parse, normalise, compare, rank   │  │
│  │  Phase 5: Invitation Designer → generate e-invite (parallel)  │  │
│  │  Phase 6: RSVP Agent      → form, invites, reminders, track   │  │
│  │  Phase 7: Learning Agent  → feedback → memory → playbook      │  │
│  │                                                               │  │
│  │  Human Checkpoints:                                          │  │
│  │    ✋ Approve shortlist + RFQ                                  │  │
│  │    ✋ Approve venue + invitation                               │  │
│  │    ✋ Approve playbook updates                                 │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                              │ MCP (stdio)                          │
│  ┌───────────────────────────▼──────────────────────────────────┐  │
│  │  EventPilot MCP Server (Python / FastMCP)                     │  │
│  │                                                               │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │  │
│  │  │ Memory  │ │ Venue   │ │ Email   │ │ Quote   │ │ Demo   │ │  │
│  │  │ Tools   │ │ Tools   │ │ Tools   │ │ Tools   │ │ Tools  │ │  │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────────┘ │  │
│  │       │           │           │           │                   │  │
│  │  ┌────▼───────────▼───────────▼───────────▼──────────────┐  │  │
│  │  │              SQLite (eventpilot_memory.db)              │  │  │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌────────────────┐  │  │  │
│  │  │  │ Venue       │ │ Playbooks + │ │ Simulated      │  │  │  │
│  │  │  │ Feedback    │ │ Proposals   │ │ Emails + RFQs  │  │  │  │
│  │  │  └─────────────┘ └─────────────┘ └────────────────┘  │  │  │
│  │  └───────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Static Data                                                  │  │
│  │  ┌─────────────┐  ┌──────────────────┐                       │  │
│  │  │ venues.json │  │ customers.csv    │                       │  │
│  │  │ (5 KL hotels)│  │ (20 customers)   │                       │  │
│  │  └─────────────┘  └──────────────────┘                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

## Agent Interaction Diagram

```
User sends brief
     │
     ▼
[Orchestrator]
     │
     ├─► [Brief Agent]
     │      │ calls get_playbook()
     │      │ calls log_feedback (if parsing feedback)
     │      │ asks user for missing fields
     │      ▼
     ├─► [Venue Scout]
     │      │ calls search_venues()
     │      │ calls get_venue_feedback_flags() per venue
     │      │ calls get_all_flagged_venues()
     │      │ shortlists + ranks
     │      ▼
     ✋ HUMAN CHECKPOINT 1: Approve shortlist + RFQ
     │
     ├─► [Outreach Agent]
     │      │ calls send_rfq() per venue
     │      │ calls seed_quote_replies() [demo]
     │      │ calls check_inbox()
     │      ▼
     ├─► [Quote Analyst]          ┌─► [Invitation Designer]
     │      │ calls analyze_quotes()│   (parallel — runs while
     │      │ checks Venue Memory   │    waiting for quotes)
     │      │ produces comparison   │   uses ImageGen tool
     │      ▼                       ▼
     ✋ HUMAN CHECKPOINT 2: Approve venue + invitation
     │
     ├─► [RSVP Agent]
     │      │ calls get_customers()
     │      │ creates RSVP form (described for demo)
     │      ▼
     │
     ═══ EVENT HAPPENS ═══
     │
     ├─► [Learning Agent]
     │      │ prompts user for feedback
     │      │ parses free text → structured entries
     │      │ calls log_feedback() per attribute
     │      │ analyzes patterns
     │      │ calls propose_playbook_update()
     │      │ calls list_playbook_proposals()
     │      ▼
     ✋ HUMAN CHECKPOINT 3: Approve playbook updates
     │
     │   calls apply_playbook_update() / reject_playbook_update()
     │
     ▼
  NEXT RUN IS SMARTER
```

## Feedback & Adaptation Loop

```
┌─────────────────────────────────────────────────────┐
│                   RUN 1                             │
│                                                     │
│  Brief → Venue Search (no flags) → RFQ → Quotes    │
│  → Recommendation → Event → Feedback               │
│                                                     │
│  Feedback: "Hotel A ceiling too low, AV great"     │
│      │                                              │
│      ▼                                              │
│  [Learning Agent]                                   │
│      │ parses into structured feedback              │
│      │ logs to Venue Memory                         │
│      │ proposes playbook updates                    │
│      ▼                                              │
│  ✋ User approves                                   │
│      │                                              │
│      ▼                                              │
│  Playbook updated:                                  │
│    + ceiling_height as required RFQ question        │
│    + ranking rule: down-rank low-ceiling venues     │
│                                                     │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                   RUN 2                             │
│                                                     │
│  Brief → Load Playbook (NOW HAS LEARNED RULES)     │
│      │ asks about ceiling height (didn't before)   │
│      │ includes ceiling height in RFQ              │
│      ▼                                              │
│  Venue Search:                                      │
│    Hotel A → FLAGGED (dealbreaker: low ceiling)    │
│    Hotel E → BOOSTED (positive: good ceiling)      │
│      │                                              │
│      ▼                                              │
│  Recommendation cites feedback sources              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Two Memory Layers

### Venue Memory
- **What:** Facts about specific venues, tagged by event context
- **Storage:** SQLite `venue_feedback` table
- **Read pattern:** During venue scouting, `get_venue_feedback_flags(venue_id, event_type, event_tier)`
- **Write pattern:** After event, `log_feedback(...)` per attribute
- **Context-aware:** Feedback only applies to matching event_type + event_tier

### Event Playbooks
- **What:** Evolving rules and checklists per event type + tier
- **Storage:** SQLite `playbooks` table (JSON content)
- **Read pattern:** At brief intake, `get_playbook(event_type, event_tier)` → check `learned_requirements` and `venue_ranking_rules`
- **Write pattern:** `propose_playbook_update()` → user approves → `apply_playbook_update()` merges into playbook
- **Human-approved:** Venue notes save automatically; playbook changes require explicit approval

## MCP Tool Inventory

| Category | Tool | Purpose |
|---|---|---|
| Memory | `log_feedback` | Store structured venue feedback |
| Memory | `get_venue_history` | Full feedback history for a venue |
| Memory | `get_venue_feedback_flags` | Concise flag summary for shortlisting |
| Memory | `get_all_flagged_venues` | All venues with feedback for an event context |
| Playbook | `get_playbook` | Retrieve playbook (with learned rules) |
| Playbook | `propose_playbook_update` | Propose a new rule/requirement |
| Playbook | `list_playbook_proposals` | Show pending proposals |
| Playbook | `apply_playbook_update` | Approve and merge a proposal |
| Playbook | `reject_playbook_update` | Reject a proposal |
| Venue | `search_venues` | Search venue database by criteria |
| Venue | `get_venue_details` | Full details for one venue |
| Email | `send_rfq` | Log an RFQ sent to a hotel |
| Email | `check_inbox` | Check for simulated replies |
| Quote | `seed_quote_replies` | [Demo] Seed hotel quotation emails |
| Quote | `get_all_quotes` | Retrieve all quotes |
| Quote | `analyze_quotes` | Compare + flag + recommend |
| Customer | `get_customers` | Retrieve customer database |
| Learning | `trigger_post_event_feedback` | Process free-text feedback |
| Learning | `seed_demo_feedback` | [Demo] Seed Run 1 feedback |
| Demo | `reset_memory` | Clear all state |
| Demo | `get_demo_status` | Check current state |

## WorkBuddy Native Capabilities Used

| Capability | How it's used |
|---|---|
| Skills (SKILL.md) | Orchestrator workflow definition |
| MCP Server | All tools (memory, venue, email sim, quotes) |
| Agent tool | Parallel sub-agents (Invitation Designer) |
| ImageGen | Invitation/e-invite generation |
| Bash execution | Running Python MCP server |

## WorkBuddy Limitations & Workarounds

| Limitation | Workaround |
|---|---|
| No native email send/receive | MCP server simulates email inbox (demo mode) |
| No real-time inbox polling | `check_inbox` tool called by skill at appropriate step |
| No Google Forms creation | RSVP form described in demo; can be built as HTML + cloud-service for production |
| No Slack/Teams integration | WorkBuddy chat IS the notification surface (it's the demo platform) |
| No scheduled reminders | Automations API can handle this for production; demo uses "fast-forward" |
