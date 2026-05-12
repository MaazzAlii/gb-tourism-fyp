import re
from difflib import get_close_matches
from typing import Any


KNOWN_DESTINATIONS = [
    "Hunza Valley",
    "Skardu",
    "Gilgit",
    "Fairy Meadows",
    "Naltar Valley",
    "Naran",
    "Kaghan",
    "Astore",
    "Ghizer",
    "Chilas",
    "Khaplu",
    "Shigar",
]


def _extract_budget(raw_text: str, fallback_budget: float | None) -> float | None:
    budget_patterns = [
        r"(?:under|below|max|budget)\s*(?:pkr|rs\.?)?\s*([\d,]+)",
        r"(?:pkr|rs\.?)\s*([\d,]+)",
        r"\b(\d+)\s*k\b",
    ]
    for pattern in budget_patterns:
        match = re.search(pattern, raw_text, flags=re.IGNORECASE)
        if not match:
            continue
        value = match.group(1).replace(",", "")
        amount = float(value)
        if pattern.endswith(r"\b(\d+)\s*k\b"):
            amount *= 1000
        return amount
    return fallback_budget


def _extract_days(raw_text: str, fallback_days: int | None) -> int | None:
    match = re.search(r"(\d+)\s*(?:day|days|d)\b", raw_text, flags=re.IGNORECASE)
    if match:
        return max(1, int(match.group(1)))
    return fallback_days


def _extract_destination(raw_text: str, fallback_destination: str) -> tuple[str, str | None]:
    lowered = raw_text.lower()
    for destination in KNOWN_DESTINATIONS:
        if destination.lower() in lowered:
            return destination, None

    fuzzy = get_close_matches(
        fallback_destination.strip().lower(),
        [d.lower() for d in KNOWN_DESTINATIONS],
        n=1,
        cutoff=0.65,
    )
    if fuzzy:
        corrected = next(d for d in KNOWN_DESTINATIONS if d.lower() == fuzzy[0])
        return corrected, corrected

    return fallback_destination, None


def parse_user_query(
    destination: str,
    duration_days: int,
    total_budget: float,
    budget_tier: str,
) -> dict[str, Any]:
    raw_text = f"{destination} for {duration_days} days under PKR {int(total_budget)}"
    parsed_destination, corrected = _extract_destination(raw_text, destination)
    parsed_days = _extract_days(raw_text, duration_days) or duration_days
    parsed_budget = _extract_budget(raw_text, total_budget) or total_budget

    group_type = "family" if parsed_days >= 3 else "solo"
    preferences = []
    if budget_tier == "budget":
        preferences.append("affordable")
    if budget_tier == "luxury":
        preferences.append("premium")

    return {
        "destination": parsed_destination,
        "days": parsed_days,
        "budget": parsed_budget,
        "preferences": preferences,
        "group_type": group_type,
        "destination_corrected_to": corrected,
        "raw_query": raw_text,
    }

