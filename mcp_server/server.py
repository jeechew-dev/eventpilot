"""
EventPilot MCP Server
Exposes tools for venue memory, event playbooks, simulated email/RFQ,
quote management, and demo control.

Run with: python -m mcp_server.server
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Ensure parent dir is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # MCP v2.x
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    # MCP v1.x fallback
    from mcp.server.fastmcp import FastMCP

from mcp_server import db, seed_data

# Initialize database on startup
db.init_db()

mcp = FastMCP("eventpilot")

# Load venue data
VENUES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "venues.json")
CUSTOMERS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "customers.csv")


def _load_venues():
    with open(VENUES_FILE) as f:
        return json.load(f)


# ===========================================================================
# VENUE MEMORY TOOLS
# ===========================================================================

@mcp.tool()
def log_feedback(
    venue_id: str,
    venue_name: str,
    room_name: str,
    event_type: str,
    event_tier: str,
    attribute: str,
    sentiment: str,
    severity: str,
    note: str,
    event_ref: str = "",
    feedback_date: str = ""
) -> str:
    """
    Log post-event feedback about a venue into Venue Memory.

    Args:
        venue_id: Unique venue identifier (e.g. "hotel_a")
        venue_name: Display name of the venue
        room_name: Name of the specific room/ballroom
        event_type: Type of event (e.g. "product_launch", "seminar", "appreciation_night")
        event_tier: Tier of event ("grand" or "standard")
        attribute: What the feedback is about (e.g. "ceiling_height", "av_quality", "service_quality")
        sentiment: "positive" or "negative"
        severity: "minor" or "dealbreaker"
        note: The free-text feedback note
        event_ref: Reference to the event (e.g. "product_launch_dec_2026")
        feedback_date: Date of feedback (YYYY-MM-DD), defaults to today

    Returns:
        Confirmation with the feedback ID
    """
    fb_id = db.log_feedback(
        venue_id=venue_id, venue_name=venue_name, room_name=room_name,
        event_type=event_type, event_tier=event_tier, attribute=attribute,
        sentiment=sentiment, severity=severity, note=note,
        event_ref=event_ref or None,
        feedback_date=feedback_date or None
    )
    return f"Feedback logged successfully. ID: {fb_id}\nVenue: {venue_name} ({room_name})\nAttribute: {attribute} ({sentiment}, {severity})"


@mcp.tool()
def get_venue_history(
    venue_id: str,
    event_type: str = "",
    event_tier: str = ""
) -> str:
    """
    Retrieve feedback history for a specific venue, optionally filtered by event context.
    Feedback is context-aware: a low ceiling flag for grand product launches won't show for standard seminars.

    Args:
        venue_id: The venue to look up
        event_type: Filter to this event type (optional)
        event_tier: Filter to this event tier (optional)

    Returns:
        Human-readable summary of all feedback for this venue in the given context
    """
    history = db.get_venue_history(
        venue_id,
        event_type=event_type or None,
        event_tier=event_tier or None
    )

    if not history:
        return f"No feedback history found for venue {venue_id}" + (
            f" (filtered by {event_type}/{event_tier})" if event_type or event_tier else ""
        ) + "."

    lines = [f"=== Venue Feedback History: {history[0]['venue_name']} ==="]
    if event_type or event_tier:
        lines.append(f"Context filter: {event_type or 'any type'} / {event_tier or 'any tier'}")
    lines.append("")

    for entry in history:
        icon = "+" if entry["sentiment"] == "positive" else ("!!!" if entry["severity"] == "dealbreaker" else "!")
        lines.append(f"[{icon}] {entry['attribute'].upper()} ({entry['sentiment']}, {entry['severity']})")
        lines.append(f"    Note: {entry['note']}")
        lines.append(f"    Event: {entry['event_type']}/{entry['event_tier']} | Ref: {entry['event_ref'] or 'N/A'} | Date: {entry['feedback_date']}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def get_venue_feedback_flags(
    venue_id: str,
    event_type: str,
    event_tier: str
) -> str:
    """
    Get a concise summary of feedback flags for a venue in a specific event context.
    Use this during venue shortlisting to flag risks and positives.

    Returns a structured summary with dealbreakers, minor issues, and positives.
    Returns "NO_FEEDBACK" if there is no feedback for this venue in this context.
    """
    summary = db.get_venue_feedback_summary(venue_id, event_type, event_tier)
    if summary is None:
        return "NO_FEEDBACK"
    return summary


@mcp.tool()
def get_all_flagged_venues(
    event_type: str,
    event_tier: str
) -> str:
    """
    Get all venues that have feedback for a specific event context.
    Use this at the start of venue scouting to know which venues have history.

    Returns a list of venue_id -> venue_name mappings with feedback.
    """
    venues = db.get_all_venues_with_feedback(event_type, event_tier)
    if not venues:
        return f"No venues with feedback found for {event_type}/{event_tier}."

    lines = [f"=== Venues with feedback for {event_type}/{event_tier} ==="]
    for v in venues:
        lines.append(f"  {v['venue_id']}: {v['venue_name']} ({v['room_name']})")
    return "\n".join(lines)


# ===========================================================================
# EVENT PLAYBOOK TOOLS
# ===========================================================================

@mcp.tool()
def get_playbook(
    event_type: str,
    event_tier: str
) -> str:
    """
    Retrieve the Event Playbook for a given event type and tier.
    The playbook contains required brief fields, learned requirements (from past feedback),
    and venue ranking rules.

    Use this at the start of brief intake to know what questions to ask,
    and during venue ranking to apply learned rules.

    Args:
        event_type: e.g. "product_launch", "seminar", "appreciation_night"
        event_tier: "grand" or "standard"

    Returns:
        JSON string of the playbook
    """
    playbook = db.get_playbook(event_type, event_tier)
    return json.dumps(playbook, indent=2)


@mcp.tool()
def propose_playbook_update(
    event_type: str,
    event_tier: str,
    proposal_type: str,
    field_name: str = "",
    question: str = "",
    rfq_question: str = "",
    rule_description: str = "",
    applies_to_attribute: str = "",
    sentiment_filter: str = "",
    severity_filter: str = "",
    source_feedback_id: str = "",
    source_event_ref: str = ""
) -> str:
    """
    Propose a new playbook update based on feedback analysis.
    The proposal is saved as 'pending' and must be approved by the user before it takes effect.

    Proposal types:
    - "add_requirement": Add a new required field to brief intake + RFQ
    - "add_ranking_rule": Add a rule that affects venue ranking based on feedback

    Args:
        event_type, event_tier: Which playbook to update
        proposal_type: "add_requirement" or "add_ranking_rule"
        field_name: Name of the new requirement field (for add_requirement)
        question: Intake question to ask the user (for add_requirement)
        rfq_question: Question to include in hotel RFQs (for add_requirement)
        rule_description: Human-readable rule (for add_ranking_rule)
        applies_to_attribute: Which venue attribute this rule checks (for add_ranking_rule)
        sentiment_filter: Filter by sentiment ("negative" or "positive")
        severity_filter: JSON array of severities to filter (e.g. '["dealbreaker"]')
        source_feedback_id: ID of the feedback that triggered this proposal
        source_event_ref: Reference to the source event
    """
    prop_id = db.propose_playbook_update(
        event_type=event_type, event_tier=event_tier,
        proposal_type=proposal_type, field_name=field_name or None,
        question=question or None, rfq_question=rfq_question or None,
        rule_description=rule_description or None,
        applies_to_attribute=applies_to_attribute or None,
        sentiment_filter=sentiment_filter or None,
        severity_filter=severity_filter or None,
        source_feedback_id=source_feedback_id or None,
        source_event_ref=source_event_ref or None
    )
    return f"Playbook update proposed. ID: {prop_id}\nType: {proposal_type}\nStatus: pending user approval"


@mcp.tool()
def list_playbook_proposals(
    event_type: str = "",
    event_tier: str = "",
    status: str = "pending"
) -> str:
    """
    List playbook proposals, by default only pending ones awaiting user approval.

    Args:
        event_type: Filter by event type (optional)
        event_tier: Filter by event tier (optional)
        status: "pending", "approved", "rejected", or "" for all
    """
    proposals = db.list_proposals(
        event_type=event_type or None,
        event_tier=event_tier or None,
        status=status
    )

    if not proposals:
        return f"No {status} proposals found."

    lines = [f"=== Playbook Proposals ({status}) ==="]
    for p in proposals:
        lines.append(f"\nID: {p['id']}")
        lines.append(f"  Event: {p['event_type']}/{p['event_tier']}")
        lines.append(f"  Type: {p['proposal_type']}")
        if p["field_name"]:
            lines.append(f"  Field: {p['field_name']}")
        if p["question"]:
            lines.append(f"  Question: {p['question']}")
        if p["rfq_question"]:
            lines.append(f"  RFQ Question: {p['rfq_question']}")
        if p["rule_description"]:
            lines.append(f"  Rule: {p['rule_description']}")
        lines.append(f"  Source: {p['source_event_ref'] or 'N/A'}")
        lines.append(f"  Status: {p['status']}")
    return "\n".join(lines)


@mcp.tool()
def apply_playbook_update(proposal_id: str) -> str:
    """
    Approve a pending playbook proposal. This merges the change into the active playbook.
    The user must explicitly approve proposals before they take effect.
    """
    try:
        db.apply_playbook_update(proposal_id)
        return f"Playbook update {proposal_id} has been APPROVED and applied to the playbook."
    except ValueError as e:
        return f"Error: {e}"


@mcp.tool()
def reject_playbook_update(proposal_id: str) -> str:
    """Reject a pending playbook proposal."""
    try:
        db.reject_playbook_update(proposal_id)
        return f"Playbook update {proposal_id} has been REJECTED."
    except ValueError as e:
        return f"Error: {e}"


# ===========================================================================
# VENUE SEARCH TOOLS
# ===========================================================================

@mcp.tool()
def search_venues(
    location: str = "",
    event_tier: str = "",
    min_capacity: int = 0,
    room_type: str = "",
    seating: str = ""
) -> str:
    """
    Search the venue database for hotels matching the given criteria.
    Returns matching venues with full details.

    Args:
        location: City/area (e.g. "Kuala Lumpur", "KL")
        event_tier: "grand" or "standard"
        min_capacity: Minimum number of guests the venue must accommodate
        room_type: "ballroom", "main_hall", "lecture_theatre"
        seating: Required seating option ("theatre", "classroom", "cluster", "u-shape")
    """
    venues = _load_venues()
    results = []

    for v in venues:
        if location and location.lower() not in v["location"].lower():
            # Also check "KL" as alias for Kuala Lumpur
            if not (location.upper() == "KL" and "kuala lumpur" in v["location"].lower()):
                continue
        if event_tier and v["tier"] != event_tier:
            continue
        if min_capacity and v["max_capacity"] < min_capacity:
            continue
        if room_type and room_type not in v["room_types"]:
            continue
        if seating and seating not in v["seating_options"]:
            continue
        results.append(v)

    if not results:
        return f"No venues found matching criteria: location={location}, tier={event_tier}, min_capacity={min_capacity}, room_type={room_type}, seating={seating}"

    lines = [f"=== Venue Search Results ({len(results)} found) ===\n"]
    for v in results:
        lines.append(f"ID: {v['venue_id']}")
        lines.append(f"  Name: {v['venue_name']} - {v['room_name']}")
        lines.append(f"  Location: {v['location']}")
        lines.append(f"  Capacity: up to {v['max_capacity']} pax")
        lines.append(f"  Tier: {v['tier']}")
        lines.append(f"  AV: {'Yes' if v['has_av'] else 'No'} - {v['av_details']}")
        lines.append(f"  Meals: {', '.join(v['meals_available'])}")
        lines.append(f"  Seating options: {', '.join(v['seating_options'])}")
        lines.append(f"  Contact: {v['contact_email']}")
        lines.append(f"  Base price/pax: RM {v['base_price_per_pax']}")
        lines.append(f"  Description: {v['description']}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def get_venue_details(venue_id: str) -> str:
    """Get full details for a specific venue by ID."""
    venues = _load_venues()
    for v in venues:
        if v["venue_id"] == venue_id:
            return json.dumps(v, indent=2)
    return f"Venue not found: {venue_id}"


# ===========================================================================
# SIMULATED EMAIL / RFQ TOOLS
# ===========================================================================

@mcp.tool()
def send_rfq(
    venue_id: str,
    venue_name: str,
    requirements: str
) -> str:
    """
    Log an RFQ email sent to a hotel. In demo mode, this triggers a simulated reply.

    Args:
        venue_id: Target venue ID
        venue_name: Display name
        requirements: JSON string of the full requirements sent in the RFQ
    """
    import uuid
    rfq_id = f"rfq_{venue_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    try:
        req_dict = json.loads(requirements) if isinstance(requirements, str) else requirements
    except json.JSONDecodeError:
        req_dict = {"raw": requirements}

    db.log_rfq(rfq_id, venue_id, venue_name, req_dict)
    return f"RFQ sent to {venue_name} ({venue_id}).\nRFQ ID: {rfq_id}\nIn demo mode, a simulated reply will be available via check_inbox."


@mcp.tool()
def check_inbox() -> str:
    """
    Check the simulated email inbox for new hotel quotation replies.
    Returns all unread emails and marks them as read.

    In demo mode, call seed_quote_replies first to populate the inbox with test quotes.
    """
    emails = db.check_inbox()

    if not emails:
        return "No new emails in inbox."

    lines = [f"=== Inbox: {len(emails)} new email(s) ===\n"]
    for email in emails:
        lines.append(f"From: {email['from_email']}")
        lines.append(f"Subject: {email['subject']}")
        lines.append(f"Received: {email['received_at']}")
        lines.append(f"Body:\n{email['body']}")

        if email.get("attachments"):
            att = json.loads(email["attachments"])
            if "quote_data" in att:
                lines.append(f"\n[Structured Quote Data]:")
                lines.append(json.dumps(att["quote_data"], indent=2))
        lines.append("\n" + "=" * 60 + "\n")
    return "\n".join(lines)


# ===========================================================================
# QUOTE MANAGEMENT TOOLS
# ===========================================================================

@mcp.tool()
def seed_quote_replies(
    pax: int = 150,
    budget: int = 25000,
    event_purpose: str = "Product Launch",
    event_date: str = "December 2026",
    event_type: str = "product_launch",
    event_tier: str = "grand"
) -> str:
    """
    [DEMO MODE] Seed simulated quotation replies from hotels into the inbox.
    This simulates hotels responding to RFQs with varied quote conditions.

    Call this after sending RFQs to simulate hotel replies arriving.

    Args:
        pax: Number of guests
        budget: Budget in RM
        event_purpose: Purpose of the event
        event_date: Event date string
        event_type: Event type for context
        event_tier: Event tier
    """
    event_brief = {
        "pax": pax, "budget": budget, "event_purpose": event_purpose,
        "date": event_date, "event_type": event_type, "event_tier": event_tier
    }

    quotes = seed_data.seed_demo_quotes(event_brief)
    count = seed_data.seed_simulated_quote_emails(event_brief, quotes)

    # Store quotes in demo state for later retrieval
    db.set_demo_state("last_quotes", json.dumps(quotes))

    return f"Seeded {count} simulated quotation replies from hotels. Use check_inbox to retrieve them."


@mcp.tool()
def get_all_quotes() -> str:
    """
    Retrieve all quotes that have been received (from the last seeded batch).
    Returns structured quote data for comparison by the Quote Analyst.
    """
    quotes_json = db.get_demo_state("last_quotes")
    if not quotes_json:
        return "No quotes available. Call seed_quote_replies first."

    quotes = json.loads(quotes_json)
    return json.dumps(quotes, indent=2)


@mcp.tool()
def analyze_quotes(
    pax: int,
    budget: int,
    event_type: str = "",
    event_tier: str = ""
) -> str:
    """
    Analyze all received quotes and produce a comparison table with risk flags.
    Checks for: minimum pax traps, ++ pricing hidden costs, AV exclusions, budget overrun.
    Also checks Venue Memory for past feedback flags.

    Args:
        pax: Expected number of guests
        budget: Budget in RM
        event_type: For venue memory lookup
        event_tier: For venue memory lookup

    Returns:
        Structured comparison table with scores, risk flags, and recommendation
    """
    quotes_json = db.get_demo_state("last_quotes")
    if not quotes_json:
        return "No quotes to analyze. Call seed_quote_replies first."

    quotes = json.loads(quotes_json)

    lines = ["=== QUOTE COMPARISON & ANALYSIS ===\n"]
    lines.append(f"Budget: RM {budget:,.2f} | Expected pax: {pax}\n")
    lines.append(f"{'Venue':<35} {'Total (RM)':<15} {'Pricing':<10} {'Min Pax':<10} {'AV':<8} {'Budget':<8} {'Risk Level'}")
    lines.append("-" * 110)

    analyzed = []
    for q in quotes.values():
        # Calculate true total
        if q["pricing_type"] == "plusplus":
            sc = q["total_price"] * q["service_charge_pct"] / 100
            sst = (q["total_price"] + sc) * q["sst_pct"] / 100
            true_total = q["total_price"] + sc + sst
        else:
            true_total = q["total_price"]

        # Check risks
        risks = []
        risk_level = "LOW"

        if q["minimum_pax"] and pax < q["minimum_pax"]:
            risks.append(f"MINIMUM PAX TRAP: requires {q['minimum_pax']} pax, you have {pax}")
            risk_level = "HIGH"

        if q["pricing_type"] == "plusplus":
            risks.append(f"++ PRICING: base RM {q['total_price']:,.0f} + SC {q['service_charge_pct']}% + SST {q['sst_pct']}% = RM {true_total:,.0f}")
            if risk_level != "HIGH":
                risk_level = "MEDIUM"

        if not q["av_included"]:
            risks.append("AV NOT INCLUDED - extra cost required")
            if risk_level != "HIGH":
                risk_level = "MEDIUM"

        if true_total > budget:
            risks.append(f"OVER BUDGET by RM {true_total - budget:,.0f}")
            risk_level = "HIGH"

        # Check venue memory
        feedback_summary = db.get_venue_feedback_summary(q["venue_id"], event_type, event_tier) if event_type else None
        if feedback_summary:
            risks.append(f"PAST FEEDBACK: {feedback_summary[:100]}...")

        budget_status = "OVER" if true_total > budget else "OK"
        min_pax_str = f"{q['minimum_pax']}" if q["minimum_pax"] else "None"

        lines.append(f"{q['venue_name']:<35} {true_total:>12,.0f}  {q['pricing_type']:<10} {min_pax_str:<10} {'Yes' if q['av_included'] else 'NO':<8} {budget_status:<8} {risk_level}")

        analyzed.append({
            "venue_id": q["venue_id"],
            "venue_name": q["venue_name"],
            "true_total": true_total,
            "risk_level": risk_level,
            "risks": risks,
            "quote": q
        })

    lines.append("")

    # Detailed risk breakdown
    lines.append("=== RISK DETAILS ===\n")
    for a in analyzed:
        lines.append(f"[{a['risk_level']}] {a['venue_name']} - RM {a['true_total']:,.0f}")
        for risk in a["risks"]:
            lines.append(f"  ! {risk}")
        lines.append("")

    # Recommendation
    lines.append("=== RECOMMENDATION ===\n")
    safe = [a for a in analyzed if a["risk_level"] == "LOW"]
    if safe:
        best = min(safe, key=lambda x: x["true_total"])
        lines.append(f"RECOMMENDED: {best['venue_name']}")
        lines.append(f"  Total: RM {best['true_total']:,.0f} (within budget)")
        lines.append(f"  Reasons: nett pricing, no minimum pax, AV included, no hidden costs")
        if best["true_total"] < budget:
            lines.append(f"  Savings: RM {budget - best['true_total']:,.0f} under budget")
    else:
        lines.append("No low-risk options found. Consider negotiating or adjusting requirements.")

    return "\n".join(lines)


# ===========================================================================
# CUSTOMER DATABASE TOOLS
# ===========================================================================

@mcp.tool()
def get_customers(segment: str = "") -> str:
    """
    Retrieve customers from the customer database, optionally filtered by segment.

    Args:
        segment: Filter by segment ("VIP", "Premium", "Standard"), empty for all
    """
    import csv
    customers = []
    with open(CUSTOMERS_FILE, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if segment and row["segment"] != segment:
                continue
            customers.append(row)

    if not customers:
        return f"No customers found" + f" in segment {segment}" if segment else "."

    lines = [f"=== Customer Database ({len(customers)} customers) ===\n"]
    for c in customers:
        lines.append(f"{c['customer_id']}: {c['name']} | {c['company']} | {c['segment']} | {c['email']}")
    return "\n".join(lines)


# ===========================================================================
# LEARNING / FEEDBACK LOOP TOOLS
# ===========================================================================

@mcp.tool()
def trigger_post_event_feedback(
    venue_id: str,
    venue_name: str,
    room_name: str,
    event_type: str,
    event_tier: str,
    event_ref: str,
    feedback_text: str,
    feedback_date: str = ""
) -> str:
    """
    Process free-text post-event feedback from the OC and:
    1. Parse it into structured feedback entries (logged to Venue Memory)
    2. Analyze feedback for potential playbook updates
    3. Generate playbook update proposals (pending user approval)

    This is the core of the learning loop. Call this after an event when the OC provides feedback.

    Args:
        venue_id, venue_name, room_name: Which venue the feedback is about
        event_type, event_tier, event_ref: Event context
        feedback_text: Free-text feedback from the OC (e.g. "ceiling was too low, AV was great")
        feedback_date: Date of feedback (YYYY-MM-DD)

    Returns:
        Summary of logged feedback and proposed playbook updates
    """
    # In a real implementation, the LLM in the skill would parse the free text.
    # For the MCP server, we accept the raw text and return guidance.
    # The actual parsing happens in the skill layer (the LLM).

    lines = ["=== Post-Event Feedback Processing ===\n"]
    lines.append(f"Venue: {venue_name} ({room_name})")
    lines.append(f"Event: {event_type}/{event_tier} ({event_ref})")
    lines.append(f"Feedback text: \"{feedback_text}\"")
    lines.append("")
    lines.append("NOTE: The Learning Agent (skill layer) should parse this free text into structured")
    lines.append("feedback entries using log_feedback, then analyze patterns and use")
    lines.append("propose_playbook_update to suggest playbook changes.")
    lines.append("")
    lines.append("After parsing, call list_playbook_proposals to show the user what was proposed.")

    return "\n".join(lines)


@mcp.tool()
def seed_demo_feedback() -> str:
    """
    [DEMO MODE] Seed post-event feedback for the Run 1 -> Run 2 demo.
    This populates Venue Memory with feedback about Hotel A (ceiling too low, AV great)
    and Hotel E (ceiling good, service excellent), then generates playbook proposals.

    Call this to simulate the "fast-forward to post-event" step.
    """
    count = seed_data.seed_feedback_run1()
    proposal_ids = seed_data.generate_proposed_playbook_updates()

    lines = [f"=== Demo Feedback Seeded ==="]
    lines.append(f"Seeded {count} feedback entries into Venue Memory.")
    lines.append(f"Generated {len(proposal_ids)} playbook update proposals (pending approval).")
    lines.append("")
    lines.append("Feedback summary:")
    lines.append("  Hotel A (Grand Hyatt):")
    lines.append("    - ceiling_height: NEGATIVE / DEALBREAKER (too low for grand launch)")
    lines.append("    - av_quality: POSITIVE / minor (excellent AV)")
    lines.append("  Hotel E (Sheraton Imperial):")
    lines.append("    - ceiling_height: POSITIVE / minor (perfect for grand atmosphere)")
    lines.append("    - service_quality: POSITIVE / minor (impeccable service)")
    lines.append("")
    lines.append("Proposals generated:")
    lines.append("  1. Add 'ceiling_height' as required RFQ question for grand product launches")
    lines.append("  2. Add ranking rule: down-rank venues flagged for low ceiling in grand launches")
    lines.append("")
    lines.append("Use list_playbook_proposals to view them, then apply_playbook_update to approve.")

    return "\n".join(lines)


# ===========================================================================
# DEMO CONTROL TOOLS
# ===========================================================================

@mcp.tool()
def reset_memory() -> str:
    """
    [DEMO MODE] Reset all memory: clears venue feedback, playbooks, proposals, emails, and RFQ logs.
    Use this to reset the demo between runs.
    """
    db.reset_memory()
    db.init_db()
    return "All memory reset. Venue Memory, Playbooks, Proposals, Emails, and RFQ logs cleared."


@mcp.tool()
def get_demo_status() -> str:
    """Get current demo state: feedback count, playbook status, proposal count, email count."""
    conn = db.get_connection()

    fb_count = conn.execute("SELECT COUNT(*) as c FROM venue_feedback").fetchone()["c"]
    pb_count = conn.execute("SELECT COUNT(*) as c FROM playbooks").fetchone()["c"]
    prop_pending = conn.execute("SELECT COUNT(*) as c FROM playbook_proposals WHERE status='pending'").fetchone()["c"]
    prop_approved = conn.execute("SELECT COUNT(*) as c FROM playbook_proposals WHERE status='approved'").fetchone()["c"]
    email_count = conn.execute("SELECT COUNT(*) as c FROM simulated_emails").fetchone()["c"]
    rfq_count = conn.execute("SELECT COUNT(*) as c FROM rfq_log").fetchone()["c"]

    conn.close()

    lines = ["=== EventPilot Demo Status ==="]
    lines.append(f"  Venue feedback entries: {fb_count}")
    lines.append(f"  Active playbooks: {pb_count}")
    lines.append(f"  Pending proposals: {prop_pending}")
    lines.append(f"  Approved proposals: {prop_approved}")
    lines.append(f"  Simulated emails: {email_count}")
    lines.append(f"  RFQs sent: {rfq_count}")
    return "\n".join(lines)


# ===========================================================================
# RUN
# ===========================================================================

if __name__ == "__main__":
    mcp.run()
