"""
EventPilot Database Layer
SQLite-based persistence for Venue Memory, Event Playbooks, and demo simulation state.
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

DB_PATH = os.environ.get(
    "EVENTPILOT_DB_PATH",
    str(Path(__file__).parent.parent / "data" / "eventpilot_memory.db"),
)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # --- Venue Memory ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS venue_feedback (
            id TEXT PRIMARY KEY,
            venue_id TEXT NOT NULL,
            venue_name TEXT NOT NULL,
            room_name TEXT,
            event_type TEXT NOT NULL,
            event_tier TEXT NOT NULL,
            event_ref TEXT,
            attribute TEXT NOT NULL,
            sentiment TEXT NOT NULL CHECK(sentiment IN ('positive','negative')),
            severity TEXT NOT NULL CHECK(severity IN ('minor','dealbreaker')),
            note TEXT NOT NULL,
            feedback_date TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # --- Event Playbooks ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playbooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            event_tier TEXT NOT NULL,
            content TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(event_type, event_tier)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playbook_proposals (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            event_tier TEXT NOT NULL,
            proposal_type TEXT NOT NULL CHECK(proposal_type IN ('add_requirement','add_ranking_rule','modify_requirement')),
            field_name TEXT,
            question TEXT,
            rfq_question TEXT,
            rule_description TEXT,
            applies_to_attribute TEXT,
            sentiment_filter TEXT,
            severity_filter TEXT,
            source_feedback_id TEXT,
            source_event_ref TEXT,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
            created_at TEXT NOT NULL,
            reviewed_at TEXT
        )
    """)

    # --- Simulated Email Inbox ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS simulated_emails (
            id TEXT PRIMARY KEY,
            from_email TEXT NOT NULL,
            to_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            attachments TEXT,
            received_at TEXT,
            is_read INTEGER DEFAULT 0,
            thread_id TEXT
        )
    """)

    # --- RFQ Tracking ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rfq_log (
            id TEXT PRIMARY KEY,
            venue_id TEXT NOT NULL,
            venue_name TEXT NOT NULL,
            requirements TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            status TEXT DEFAULT 'sent',
            quote_received INTEGER DEFAULT 0
        )
    """)

    # --- Demo State ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS demo_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Venue Memory Operations
# ---------------------------------------------------------------------------

def log_feedback(venue_id, venue_name, room_name, event_type, event_tier,
                 attribute, sentiment, severity, note, event_ref=None,
                 feedback_date=None):
    """Insert a feedback entry into venue memory."""
    conn = get_connection()
    import uuid
    fb_id = f"fb_{uuid.uuid4().hex[:12]}_{venue_id}"
    now = datetime.now().isoformat()
    if feedback_date is None:
        feedback_date = datetime.now().strftime('%Y-%m-%d')

    conn.execute(
        """INSERT INTO venue_feedback
           (id, venue_id, venue_name, room_name, event_type, event_tier,
            event_ref, attribute, sentiment, severity, note, feedback_date, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (fb_id, venue_id, venue_name, room_name, event_type, event_tier,
         event_ref, attribute, sentiment, severity, note, feedback_date, now)
    )
    conn.commit()
    conn.close()
    return fb_id


def get_venue_history(venue_id, event_type=None, event_tier=None):
    """Retrieve feedback for a venue, optionally filtered by event context."""
    conn = get_connection()
    query = "SELECT * FROM venue_feedback WHERE venue_id = ?"
    params = [venue_id]

    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)
    if event_tier:
        query += " AND event_tier = ?"
        params.append(event_tier)

    query += " ORDER BY feedback_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_venues_with_feedback(event_type=None, event_tier=None):
    """Get all distinct venues that have feedback, filtered by event context."""
    conn = get_connection()
    query = "SELECT DISTINCT venue_id, venue_name, room_name FROM venue_feedback WHERE 1=1"
    params = []

    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)
    if event_tier:
        query += " AND event_tier = ?"
        params.append(event_tier)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_venue_feedback_summary(venue_id, event_type, event_tier):
    """Get a human-readable summary of feedback for a venue in a specific event context."""
    history = get_venue_history(venue_id, event_type, event_tier)
    if not history:
        return None

    positives = [f for f in history if f["sentiment"] == "positive"]
    negatives = [f for f in history if f["sentiment"] == "negative"]
    dealbreakers = [f for f in negatives if f["severity"] == "dealbreaker"]

    summary_parts = []
    if dealbreakers:
        summary_parts.append(f"DEALBREAKERS ({len(dealbreakers)}):")
        for d in dealbreakers:
            summary_parts.append(f"  - {d['attribute']}: {d['note']} (from {d['event_ref'] or 'past event'})")
    if negatives and len(negatives) > len(dealbreakers):
        minor_negs = [f for f in negatives if f["severity"] == "minor"]
        if minor_negs:
            summary_parts.append(f"Minor issues ({len(minor_negs)}):")
            for m in minor_negs:
                summary_parts.append(f"  - {m['attribute']}: {m['note']}")
    if positives:
        summary_parts.append(f"Positives ({len(positives)}):")
        for p in positives:
            summary_parts.append(f"  - {p['attribute']}: {p['note']}")

    return "\n".join(summary_parts)


# ---------------------------------------------------------------------------
# Playbook Operations
# ---------------------------------------------------------------------------

def get_playbook(event_type, event_tier):
    """Retrieve the playbook for an event type + tier, or return default."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM playbooks WHERE event_type = ? AND event_tier = ?",
        (event_type, event_tier)
    ).fetchone()
    conn.close()

    if row:
        return json.loads(row["content"])

    # Return default playbook
    return _default_playbook(event_type, event_tier)


def save_playbook(event_type, event_tier, content):
    """Insert or update a playbook."""
    conn = get_connection()
    now = datetime.now().isoformat()
    conn.execute(
        """INSERT INTO playbooks (event_type, event_tier, content, updated_at)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(event_type, event_tier)
           DO UPDATE SET content = ?, updated_at = ?""",
        (event_type, event_tier, json.dumps(content), now,
         json.dumps(content), now)
    )
    conn.commit()
    conn.close()


def propose_playbook_update(event_type, event_tier, proposal_type, field_name=None,
                            question=None, rfq_question=None, rule_description=None,
                            applies_to_attribute=None, sentiment_filter=None,
                            severity_filter=None, source_feedback_id=None,
                            source_event_ref=None):
    """Create a playbook update proposal (pending user approval)."""
    conn = get_connection()
    import uuid
    proposal_id = f"prop_{uuid.uuid4().hex[:12]}"
    now = datetime.now().isoformat()

    conn.execute(
        """INSERT INTO playbook_proposals
           (id, event_type, event_tier, proposal_type, field_name, question,
            rfq_question, rule_description, applies_to_attribute, sentiment_filter,
            severity_filter, source_feedback_id, source_event_ref, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
        (proposal_id, event_type, event_tier, proposal_type, field_name,
         question, rfq_question, rule_description, applies_to_attribute,
         sentiment_filter, severity_filter, source_feedback_id,
         source_event_ref, now)
    )
    conn.commit()
    conn.close()
    return proposal_id


def list_proposals(event_type=None, event_tier=None, status="pending"):
    """List playbook proposals, optionally filtered."""
    conn = get_connection()
    query = "SELECT * FROM playbook_proposals WHERE status = ?"
    params = [status]

    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)
    if event_tier:
        query += " AND event_tier = ?"
        params.append(event_tier)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def apply_playbook_update(proposal_id):
    """Approve a proposal and merge it into the playbook."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM playbook_proposals WHERE id = ?", (proposal_id,)
    ).fetchone()

    if not row:
        conn.close()
        raise ValueError(f"Proposal {proposal_id} not found")

    proposal = dict(row)
    if proposal["status"] != "pending":
        conn.close()
        raise ValueError(f"Proposal {proposal_id} is already {proposal['status']}")

    # Get current playbook
    playbook = get_playbook(proposal["event_type"], proposal["event_tier"])

    # Apply the proposal based on type
    if proposal["proposal_type"] == "add_requirement":
        new_req = {
            "field": proposal["field_name"],
            "question": proposal["question"],
            "rfq_question": proposal["rfq_question"],
            "added_date": datetime.now().strftime('%Y-%m-%d'),
            "source_feedback": proposal["source_feedback_id"],
            "source_event": proposal["source_event_ref"],
            "status": "approved"
        }
        playbook["learned_requirements"].append(new_req)

    elif proposal["proposal_type"] == "add_ranking_rule":
        new_rule = {
            "rule_id": proposal["id"],
            "description": proposal["rule_description"],
            "applies_to_attribute": proposal["applies_to_attribute"],
            "sentiment_filter": proposal["sentiment_filter"],
            "severity_filter": json.loads(proposal["severity_filter"]) if proposal["severity_filter"] else [],
            "added_date": datetime.now().strftime('%Y-%m-%d'),
            "source_feedback": proposal["source_feedback_id"],
            "source_event": proposal["source_event_ref"],
            "status": "approved"
        }
        playbook["venue_ranking_rules"].append(new_rule)

    # Save updated playbook
    save_playbook(proposal["event_type"], proposal["event_tier"], playbook)

    # Mark proposal as approved
    now = datetime.now().isoformat()
    conn.execute(
        "UPDATE playbook_proposals SET status = 'approved', reviewed_at = ? WHERE id = ?",
        (now, proposal_id)
    )
    conn.commit()
    conn.close()
    return proposal_id


def reject_playbook_update(proposal_id):
    """Reject a proposal."""
    conn = get_connection()
    now = datetime.now().isoformat()
    conn.execute(
        "UPDATE playbook_proposals SET status = 'rejected', reviewed_at = ? WHERE id = ?",
        (now, proposal_id)
    )
    conn.commit()
    conn.close()
    return proposal_id


def _default_playbook(event_type, event_tier):
    """Return a default playbook with standard requirements and no learned rules."""
    return {
        "event_type": event_type,
        "event_tier": event_tier,
        "required_brief_fields": [
            "event_purpose", "date", "budget", "location",
            "room_type", "pax", "seating", "meals", "av_requirements"
        ],
        "learned_requirements": [],
        "venue_ranking_rules": []
    }


# ---------------------------------------------------------------------------
# Simulated Email Operations
# ---------------------------------------------------------------------------

def insert_email(email_id, from_email, to_email, subject, body,
                 attachments=None, thread_id=None):
    """Insert a simulated email into the inbox."""
    conn = get_connection()
    now = datetime.now().isoformat()
    att_json = json.dumps(attachments) if attachments else None
    conn.execute(
        """INSERT INTO simulated_emails
           (id, from_email, to_email, subject, body, attachments, received_at, is_read, thread_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)""",
        (email_id, from_email, to_email, subject, body, att_json, now, thread_id)
    )
    conn.commit()
    conn.close()


def check_inbox(since_timestamp=None):
    """Check for unread emails in the simulated inbox."""
    conn = get_connection()
    if since_timestamp:
        rows = conn.execute(
            "SELECT * FROM simulated_emails WHERE is_read = 0 AND received_at > ? ORDER BY received_at",
            (since_timestamp,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM simulated_emails WHERE is_read = 0 ORDER BY received_at"
        ).fetchall()

    # Mark as read
    for row in rows:
        conn.execute("UPDATE simulated_emails SET is_read = 1 WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()
    return [dict(r) for r in rows]


def log_rfq(rfq_id, venue_id, venue_name, requirements):
    """Log an RFQ that was sent."""
    conn = get_connection()
    now = datetime.now().isoformat()
    conn.execute(
        """INSERT INTO rfq_log (id, venue_id, venue_name, requirements, sent_at, status, quote_received)
           VALUES (?, ?, ?, ?, ?, 'sent', 0)""",
        (rfq_id, venue_id, venue_name, json.dumps(requirements), now)
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Demo State Operations
# ---------------------------------------------------------------------------

def set_demo_state(key, value):
    conn = get_connection()
    conn.execute(
        "INSERT INTO demo_state (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
        (key, str(value), str(value))
    )
    conn.commit()
    conn.close()


def get_demo_state(key, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM demo_state WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


# ---------------------------------------------------------------------------
# Reset (for demo)
# ---------------------------------------------------------------------------

def reset_memory():
    """Clear all memory tables (feedback, playbooks, proposals, emails, rfqs)."""
    conn = get_connection()
    for table in ["venue_feedback", "playbooks", "playbook_proposals",
                  "simulated_emails", "rfq_log", "demo_state"]:
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()
