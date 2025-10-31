"""Text parsing utilities for quote requests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import get_close_matches
from typing import Iterable, List, Optional

from data import PAPER_SUPPLIES


ITEM_PATTERN = re.compile(
    r"(?P<quantity>\d{1,6})\s*(?:sheets|sheet|rolls|roll|reams|ream|units|bags|covers|cups|plates|boards|tags|folders|tape)?\s*of\s+(?P<item>[^\n,]+)",
    re.IGNORECASE,
)


@dataclass
class ParsedItem:
    name: str
    quantity: int
    unit_price: float


def _canonical_item_name(raw_name: str) -> Optional[ParsedItem]:
    candidate = raw_name.strip().lower().replace("-", " ")
    options = [item["item_name"] for item in PAPER_SUPPLIES]
    best_match = get_close_matches(candidate, [opt.lower() for opt in options], n=1, cutoff=0.6)
    if not best_match:
        return None
    matched_name = next(opt for opt in options if opt.lower() == best_match[0])
    entry = next(item for item in PAPER_SUPPLIES if item["item_name"] == matched_name)
    return ParsedItem(name=matched_name, quantity=0, unit_price=entry["unit_price"])


def parse_request_items(request_text: str) -> List[ParsedItem]:
    items: List[ParsedItem] = []
    for match in ITEM_PATTERN.finditer(request_text):
        quantity = int(match.group("quantity"))
        raw_item = match.group("item")
        parsed = _canonical_item_name(raw_item)
        if parsed is None:
            continue
        parsed.quantity = quantity
        items.append(parsed)
    return items


def build_request_text(
    items: Iterable[ParsedItem],
    *,
    persona: str | None = None,
    event: str | None = None,
    closing: str | None = None,
) -> str:
    """Compose a customer request string from structured items.

    Args:
        items: Iterable of parsed items with name, quantity, and unit price.
        persona: Optional description of the requester to include in the intro.
        event: Optional event description that adds context to the request.
        closing: Optional closing sentence appended at the end.

    Returns:
        A multi-line string that can be fed back into the orchestrator as a
        natural-language customer request.
    """

    header_parts: List[str] = []
    if persona:
        header_parts.append(f"We are preparing on behalf of the {persona}.")
    if event:
        header_parts.append(f"The supplies are for an upcoming {event}.")
    intro = " ".join(header_parts) or "We would like to place an order for the following supplies."

    lines = [intro, "", "Please provide:"]
    for item in items:
        lines.append(f"- {item.quantity} units of {item.name}")

    if closing:
        lines.extend(["", closing])
    else:
        lines.extend(["", "Thank you for your assistance."])

    return "\n".join(lines)

