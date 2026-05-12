from typing import Any

from sqlalchemy.orm import Session

from app.models.listing import Listing


HOTEL_TYPES = {"hotel"}
RESTAURANT_TYPES = {"restaurant", "dining"}
ACTIVITY_TYPES = {"tour", "activity", "horse_riding", "boat_trip", "camping"}
TRANSPORT_TYPES = {"transport", "car_rental", "bike_rental", "jeep_safari"}
GUIDE_TYPES = {"guide"}


def _location_matches(destination: str, location: str | None) -> bool:
    if not location:
        return False
    dest = destination.lower()
    loc = location.lower()
    return dest in loc or loc in dest or any(part in loc for part in dest.split() if len(part) > 3)


def _price_value(listing: Listing) -> float:
    return float(getattr(listing, "price_per_night", None) or getattr(listing, "price", None) or 0)


def _compute_score(listing: Listing, destination: str, budget_limit: float) -> float:
    relevance = 1.0 if _location_matches(destination, listing.location) else 0.0
    price = _price_value(listing)
    budget_match = 1.0 if price <= budget_limit else max(0.0, 1 - ((price - budget_limit) / max(budget_limit, 1)))
    rating = 0.75
    popularity = 0.6 if listing.is_featured else 0.4
    return relevance + budget_match + rating + popularity


def _to_unified_item(listing: Listing) -> dict[str, Any]:
    price = _price_value(listing)
    return {
        "id": listing.id,
        "name": listing.title,
        "title": listing.title,
        "type": listing.service_type,
        "service_type": listing.service_type,
        "location": listing.location or "",
        "price": price,
        "price_per_night": price,
        "total_price": price,
        "rating": "",
        "image": listing.image_url or "",
        "image_url": listing.image_url,
        "description": listing.description or "",
        "source": "database",
        "booking_supported": True,
        "external_url": "",
    }


def search_database(
    db: Session,
    destination: str,
    days: int,
    budget: float,
) -> dict[str, Any]:
    listings = db.query(Listing).all()
    matched = [l for l in listings if _location_matches(destination, l.location)]

    categorized: dict[str, list[dict[str, Any]]] = {
        "hotels": [],
        "restaurants": [],
        "activities": [],
        "transport": [],
        "guides": [],
    }
    total_score = 0.0

    for listing in matched:
        score = _compute_score(listing, destination, budget / max(days, 1))
        total_score += score
        item = _to_unified_item(listing)
        item["score"] = score
        if listing.service_type in HOTEL_TYPES:
            categorized["hotels"].append(item)
        elif listing.service_type in RESTAURANT_TYPES:
            categorized["restaurants"].append(item)
        elif listing.service_type in ACTIVITY_TYPES:
            categorized["activities"].append(item)
        elif listing.service_type in TRANSPORT_TYPES:
            categorized["transport"].append(item)
        elif listing.service_type in GUIDE_TYPES:
            categorized["guides"].append(item)

    for key in categorized:
        categorized[key] = sorted(categorized[key], key=lambda x: x.get("score", 0), reverse=True)

    total_items = sum(len(v) for v in categorized.values())
    average_score = (total_score / total_items) if total_items else 0.0
    return {
        "categories": categorized,
        "total_items": total_items,
        "average_score": average_score,
        "fallback_needed": len(categorized["hotels"]) < 2
        or len(categorized["activities"]) == 0
        or average_score < 1.8,
    }

