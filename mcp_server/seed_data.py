"""
EventPilot Demo Seed Data
Seeds quotation replies with deliberately varied conditions for a compelling demo.

Quote variations:
  - Hotel A: Over budget (RM 32k for 150 pax), clean pricing (nett), good AV
  - Hotel B: Within budget BUT minimum 200 pax trap (user has 150)
  - Hotel C: "++" pricing (hidden service charge + SST), appears cheap upfront
  - Hotel E: Clean winner — within budget, no traps, excellent AV + F&B
  - Hotel D: Standard tier (excluded from grand search, shown as contrast)
"""

import json
import os
from datetime import datetime, timedelta
from . import db

VENUES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "venues.json")


def load_venues():
    with open(VENUES_FILE) as f:
        return json.load(f)


def seed_demo_quotes(event_brief):
    """
    Seed simulated quotation emails from hotels based on the event brief.
    Each quote has deliberately varied conditions for the demo narrative.

    Args:
        event_brief: dict with at least pax, budget, event_type, event_tier

    Returns:
        dict mapping venue_id -> quote data
    """
    pax = event_brief.get("pax", 150)
    budget = event_brief.get("budget", 25000)

    quotes = {
        "hotel_a": {
            "venue_id": "hotel_a",
            "venue_name": "Grand Hyatt Kuala Lumpur",
            "room_name": "Grand Ballroom",
            "pricing_type": "nett",
            "price_per_pax": 180,
            "total_price": 180 * pax,
            "minimum_pax": None,
            "service_charge_pct": 0,
            "sst_pct": 0,
            "av_included": True,
            "av_details": "4K projector, 6 wireless mics, stage lighting, LED wall",
            "meals_included": ["lunch", "tea_break"],
            "room_fit": "Excellent - high ceiling, column-free",
            "special_conditions": "30% deposit required upon confirmation",
            "validity": "30 days",
            "notes": "Premium option. All-inclusive nett pricing with full AV."
        },
        "hotel_b": {
            "venue_id": "hotel_b",
            "venue_name": "Westin Kuala Lumpur",
            "room_name": "Marble Ballroom",
            "pricing_type": "nett",
            "price_per_pax": 145,
            "total_price": 145 * pax,
            "minimum_pax": 200,
            "service_charge_pct": 0,
            "sst_pct": 0,
            "av_included": True,
            "av_details": "Projector, 4 wireless mics, basic stage lighting",
            "meals_included": ["lunch", "tea_break"],
            "room_fit": "Good - modern layout",
            "special_conditions": "Minimum 200 pax for this package. Below 200 pax, surcharge of RM 3,000 applies.",
            "validity": "14 days",
            "notes": "MINIMUM PAX TRAP: quoted per-pax looks affordable, but requires 200 pax minimum."
        },
        "hotel_c": {
            "venue_id": "hotel_c",
            "venue_name": "Hilton Kuala Lumpur",
            "room_name": "Grand Ballroom",
            "pricing_type": "plusplus",
            "price_per_pax": 120,
            "total_price": 120 * pax,
            "minimum_pax": None,
            "service_charge_pct": 10,
            "sst_pct": 8,
            "av_included": False,
            "av_details": "AV not included. Basic projector available at RM 2,500/day. Wireless mics at RM 150/each/day.",
            "meals_included": ["lunch"],
            "room_fit": "Spacious, column-free",
            "special_conditions": "Pricing is subject to 10% service charge and 8% SST. Tea break not included in base package.",
            "validity": "21 days",
            "notes": "++ PRICING TRAP: low per-pax price but service charge + SST + AV extra pushes total well above budget."
        },
        "hotel_e": {
            "venue_id": "hotel_e",
            "venue_name": "Sheraton Imperial KL",
            "room_name": "Imperial Ballroom",
            "pricing_type": "nett",
            "price_per_pax": 155,
            "total_price": 155 * pax,
            "minimum_pax": None,
            "service_charge_pct": 0,
            "sst_pct": 0,
            "av_included": True,
            "av_details": "4K projector, 6 wireless mics, concert-grade lighting, professional sound system",
            "meals_included": ["lunch", "tea_break"],
            "room_fit": "Excellent - high ceiling, grand entrance foyer",
            "special_conditions": "Complimentary parking for 100 guests. Free 1-night stay in suite for OC.",
            "validity": "30 days",
            "notes": "CLEAN WINNER: nett pricing, all-inclusive, within budget, excellent AV, no hidden conditions."
        }
    }

    return quotes


def seed_feedback_run1():
    """
    Seed post-event feedback for Run 1 demo.
    This is the feedback that triggers the learning loop for Run 2.
    """
    feedback_entries = [
        {
            "venue_id": "hotel_a",
            "venue_name": "Grand Hyatt Kuala Lumpur",
            "room_name": "Grand Ballroom",
            "event_type": "product_launch",
            "event_tier": "grand",
            "event_ref": "product_launch_dec_2026",
            "attribute": "ceiling_height",
            "sentiment": "negative",
            "severity": "dealbreaker",
            "note": "Ballroom ceiling was too low for a grand product launch. Could not create the dramatic atmosphere we needed with suspended installations.",
            "feedback_date": "2026-12-20"
        },
        {
            "venue_id": "hotel_a",
            "venue_name": "Grand Hyatt Kuala Lumpur",
            "room_name": "Grand Ballroom",
            "event_type": "product_launch",
            "event_tier": "grand",
            "event_ref": "product_launch_dec_2026",
            "attribute": "av_quality",
            "sentiment": "positive",
            "severity": "minor",
            "note": "AV system was excellent. 4K projector and wireless mics worked flawlessly.",
            "feedback_date": "2026-12-20"
        },
        {
            "venue_id": "hotel_e",
            "venue_name": "Sheraton Imperial KL",
            "room_name": "Imperial Ballroom",
            "event_type": "product_launch",
            "event_tier": "grand",
            "event_ref": "product_launch_dec_2026",
            "attribute": "ceiling_height",
            "sentiment": "positive",
            "severity": "minor",
            "note": "High ceiling was perfect for our suspended light installations. Created the grand atmosphere we wanted.",
            "feedback_date": "2026-12-20"
        },
        {
            "venue_id": "hotel_e",
            "venue_name": "Sheraton Imperial KL",
            "room_name": "Imperial Ballroom",
            "event_type": "product_launch",
            "event_tier": "grand",
            "event_ref": "product_launch_dec_2026",
            "attribute": "service_quality",
            "sentiment": "positive",
            "severity": "minor",
            "note": "Impeccable service throughout. Staff was proactive and attentive.",
            "feedback_date": "2026-12-20"
        }
    ]

    for entry in feedback_entries:
        db.log_feedback(**entry)

    return len(feedback_entries)


def generate_proposed_playbook_updates():
    """
    Based on seeded feedback, generate playbook update proposals.
    These show the learning agent's proposals that the user must approve.
    """
    # Proposal 1: Add ceiling height as a required RFQ question for grand product launches
    prop1_id = db.propose_playbook_update(
        event_type="product_launch",
        event_tier="grand",
        proposal_type="add_requirement",
        field_name="ceiling_height",
        question="What is the minimum ceiling height required for your event?",
        rfq_question="Please state the ballroom ceiling height (in meters).",
        source_feedback_id="fb_hotel_a_ceiling",
        source_event_ref="product_launch_dec_2026"
    )

    # Proposal 2: Add ranking rule to down-rank venues with low ceiling feedback
    prop2_id = db.propose_playbook_update(
        event_type="product_launch",
        event_tier="grand",
        proposal_type="add_ranking_rule",
        rule_description="Down-rank venues flagged for low ceiling height in past grand product launches.",
        applies_to_attribute="ceiling_height",
        sentiment_filter="negative",
        severity_filter=json.dumps(["dealbreaker"]),
        source_feedback_id="fb_hotel_a_ceiling",
        source_event_ref="product_launch_dec_2026"
    )

    return [prop1_id, prop2_id]


def seed_simulated_quote_emails(event_brief, quotes):
    """
    Insert simulated quotation emails into the inbox as if hotels replied.
    """
    now = datetime.now()
    timestamp = now.isoformat()

    for venue_id, quote in quotes.items():
        email_id = f"email_quote_{venue_id}_{now.strftime('%Y%m%d%H%M%S')}"
        subject = f"Re: RFQ - {event_brief.get('event_purpose', 'Event')} - Quotation from {quote['venue_name']}"

        # Build email body from quote data
        body_parts = [
            f"Dear Event Organising Committee,",
            f"",
            f"Thank you for your enquiry. Please find our quotation below for your {event_brief.get('event_purpose', 'event')}:",
            f"",
            f"Venue: {quote['venue_name']} - {quote['room_name']}",
            f"Date: {event_brief.get('date', 'TBC')}",
            f"Estimated pax: {event_brief.get('pax', 'TBC')}",
            f"",
            f"--- QUOTATION ---",
            f"Price per pax: RM {quote['price_per_pax']}",
            f"Total (base): RM {quote['total_price']:.2f}",
        ]

        if quote["pricing_type"] == "plusplus":
            sc = quote["total_price"] * quote["service_charge_pct"] / 100
            sst = (quote["total_price"] + sc) * quote["sst_pct"] / 100
            grand_total = quote["total_price"] + sc + sst
            body_parts.extend([
                f"Service charge ({quote['service_charge_pct']}%): RM {sc:.2f}",
                f"SST ({quote['sst_pct']}%): RM {sst:.2f}",
                f"GRAND TOTAL: RM {grand_total:.2f}",
            ])
        else:
            body_parts.append(f"GRAND TOTAL (nett): RM {quote['total_price']:.2f}")

        body_parts.extend([
            f"",
            f"AV: {'Included' if quote['av_included'] else 'NOT included'} - {quote['av_details']}",
            f"Meals included: {', '.join(quote['meals_included'])}",
            f"Room fit: {quote['room_fit']}",
        ])

        if quote["minimum_pax"]:
            body_parts.append(f"Minimum pax: {quote['minimum_pax']}")

        body_parts.extend([
            f"Special conditions: {quote['special_conditions']}",
            f"Quotation validity: {quote['validity']}",
            f"",
            f"Best regards,",
            f"Events Team, {quote['venue_name']}",
        ])

        body = "\n".join(body_parts)

        db.insert_email(
            email_id=email_id,
            from_email=f"{venue_id}@eventpilot.test",
            to_email="oc@eventpilot.test",
            subject=subject,
            body=body,
            attachments={"quote_data": quote},
            thread_id=f"rfq_{venue_id}"
        )

    return len(quotes)
