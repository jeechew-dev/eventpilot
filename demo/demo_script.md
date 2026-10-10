# EventPilot — Demo Script for Judges

**Duration:** ~5 minutes
**Setup:** WorkBuddy AI with EventPilot MCP server configured and trusted.

---

## Pre-Demo Setup (30 seconds)

1. Open WorkBuddy AI
2. In chat, type: **"reset demo"**
3. EventPilot resets all memory → confirms clean state
4. Type: **"show demo status"**
5. Confirm: 0 feedback, 0 playbooks, 0 proposals

> **Narrate:** "EventPilot is a self-improving event planning agent. I'll show you two runs — Run 1 from scratch, then the same request again after it's learned from feedback."

---

## Run 1 — Plan an Event (2 minutes)

### Step 1: The Brief (20 seconds)

Type:
> "Plan a grand product launch for ~150 guests in KL, mid-December, budget RM 25,000, theatre seating, lunch included, needs projector + wireless mics."

**What happens:**
- EventPilot loads the playbook for `product_launch/grand` → returns DEFAULT (no learned requirements)
- Brief Agent validates → all required fields are present
- No extra questions asked (no learned fields yet)

> **Narrate:** "One brief, one goal. EventPilot validates the brief and loads the event playbook — which is currently at its default state, no learned rules yet."

### Step 2: Venue Sourcing (30 seconds)

**What happens:**
- Venue Scout searches the venue database → finds 4 grand-tier KL hotels
- Checks Venue Memory for each → NO FEEDBACK (memory is empty)
- Shortlists all 4, no flags

> **Narrate:** "It searches for grand-tier venues in KL matching capacity, seating, and AV requirements. It also checks Venue Memory — but since this is the first run, there's no history yet."

### Step 3: RFQ + Quote Analysis (40 seconds)

**What happens:**
- Outreach Agent sends RFQs to all 4 venues
- Demo mode seeds simulated quotations (each with deliberately varied conditions)
- Quote Analyst analyses:
  - **Hotel A (Grand Hyatt):** RM 27,000 — OVER BUDGET, but nett pricing, good AV
  - **Hotel B (Westin):** RM 21,750 — within budget BUT minimum 200 pax trap (user has 150!)
  - **Hotel C (Hilton):** RM 120/pax looks cheap BUT ++ pricing (10% SC + 8% SST) + AV not included → actual total RM ~19,000 + AV extras
  - **Hotel E (Sheraton):** RM 23,250 — CLEAN WINNER, nett pricing, all-inclusive, within budget

> **Narrate:** "Watch the Quote Analyst catch the traps: Hotel B has a minimum-pax requirement that would cost extra. Hotel C uses ++ pricing that looks cheap but balloons with service charge and SST. Hotel E is the clean winner — nett pricing, everything included, under budget."

### Step 4: Recommendation + Invitation (20 seconds)

**What happens:**
- EventPilot recommends Hotel E with reasoning
- Invitation Designer generates an e-invite (parallel with quote analysis)

> **Narrate:** "Hotel E is recommended — within budget, no hidden conditions. The invitation designer ran in parallel and produced this e-invite."

### Step 5: Human Checkpoint (10 seconds)

EventPilot presents the recommendation and asks for approval.

> **Narrate:** "Human-in-the-loop: the user approves the venue and invitation before anything is sent to customers."

---

## The Learning Loop (1 minute)

### Step 6: Fast-Forward to Post-Event (20 seconds)

Type:
> "fast forward to post-event"

**What happens:**
- `seed_demo_feedback` populates Venue Memory:
  - Hotel A: ceiling_height = NEGATIVE/DEALBREAKER ("too low for grand launch")
  - Hotel A: av_quality = POSITIVE/minor ("excellent AV")
  - Hotel E: ceiling_height = POSITIVE/minor ("perfect for grand atmosphere")
  - Hotel E: service_quality = POSITIVE/minor ("impeccable service")
- Learning Agent analyzes feedback and proposes 2 playbook updates:
  1. Add `ceiling_height` as a required RFQ question for grand product launches
  2. Add ranking rule: down-rank venues flagged for low ceiling in grand launches

> **Narrate:** "After the event, the Learning Agent captures feedback. Hotel A's ceiling was too low — a dealbreaker for a grand launch. But the AV was excellent. It proposes adding ceiling height as a required question in future RFQs."

### Step 7: Approve Playbook Updates (10 seconds)

Type:
> "approve the playbook updates"

**What happens:**
- Both proposals are approved and merged into the playbook
- Future grand product launch plans will now ask about ceiling height

> **Narrate:** "The user approves the playbook update. This is the key innovation — the agent doesn't just learn, it proposes changes that a human approves, creating a traceable improvement loop."

---

## Run 2 — Same Request, Smarter Agent (1.5 minutes)

### Step 8: New Brief (10 seconds)

Type:
> "Plan another product launch, ~200 guests, KL, March."

**What happens:**
- EventPilot loads the playbook → NOW HAS LEARNED REQUIREMENTS
- Brief Agent asks about ceiling height (was NOT asked in Run 1!)

> **Narrate:** "Same type of request. But watch — the Brief Agent now asks about ceiling height. It learned this from the previous event's feedback."

### Step 9: Smarter Venue Search (30 seconds)

**What happens:**
- Venue Scout searches → same 4 venues
- BUT now Venue Memory has feedback:
  - Hotel A → FLAGGED with DEALBREAKER (low ceiling for grand launches)
  - Hotel E → BOOSTED with positive feedback (good ceiling, great service)
- Hotel A is down-ranked, Hotel E is boosted
- Source cited: "Flagged from feedback after Product Launch, Dec 2026"

> **Narrate:** "Hotel A is now flagged — the dealbreaker from last time is visible. Hotel E is boosted with positive feedback. The ranking has changed based on real experience."

### Step 10: Smarter RFQ (20 seconds)

**What happens:**
- RFQ email now includes: "Please state the ballroom ceiling height"
- This question was learned from the playbook update

> **Narrate:** "The RFQ now includes a ceiling height question — learned automatically from past feedback. Hotels must answer it, and the Quote Analyst will check the response."

### Step 11: Show the Difference (10 seconds)

| Aspect | Run 1 | Run 2 |
|---|---|---|
| Intake questions | Standard only | + ceiling height |
| Venue flags | None | Hotel A: dealbreaker |
| RFQ content | Standard | + ceiling height question |
| Ranking | By price/capacity | Hotel A down, Hotel E up |

> **Narrate:** "Same workflow, smarter agent. Every event makes the next one better — and every flag is traceable to its source."

---

## Key Points for Judges

1. **Real problem, clear user:** Malaysian event OCs spend days on pre-event admin. EventPilot does it in one brief + two approvals.
2. **Agentic workflow:** 7 agents with task decomposition, parallel execution (designer + outreach), tool calling (MCP), validation (quote checks), and dynamic adaptation (feedback loop).
3. **Self-improving:** The feedback → memory → playbook → smarter next run loop is the novel contribution. Every plan is better than the last.
4. **Human-in-the-loop:** Three checkpoints. Playbook changes require explicit approval. Every flag cites its source.
5. **WorkBuddy as platform:** Skill + MCP server + ImageGen + multi-agent delegation — WorkBuddy is the execution engine, not just a chat UI.
6. **One prompt → one goal → end-to-end:** Single brief in, full plan out.
