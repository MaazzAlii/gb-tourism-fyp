from typing import Any

from app.services.ai_trip_planner.parser_utils import sanitize_text


def _normalize_web_item(item: dict[str, Any], category: str, destination: str) -> dict[str, Any] | None:
    name = sanitize_text(item.get("name"))
    if not name:
        return None

    searchable = f"{name} {sanitize_text(item.get('description', ''))}".lower()
    if destination.lower() not in searchable:
        return None

    mapped_type = category[:-1] if category.endswith("s") else category
    return {
        "id": None,
        "name": name,
        "title": name,
        "type": mapped_type,
        "service_type": mapped_type,
        "location": destination,
        "price": "",
        "price_per_night": 0,
        "total_price": 0,
        "rating": "",
        "image": "",
        "image_url": "",
        "description": sanitize_text(item.get("description", "")),
        "source": "web",
        "booking_supported": False,
        "external_url": item.get("external_url", ""),
    }


def merge_recommendations(
    db_categories: dict[str, list[dict[str, Any]]],
    web_categories: dict[str, list[dict[str, Any]]],
    destination: str,
) -> dict[str, list[dict[str, Any]]]:
    merged: dict[str, list[dict[str, Any]]] = {}
    for category, db_items in db_categories.items():
        web_items = [
            _normalize_web_item(item, category, destination)
            for item in web_categories.get(category, [])
        ]
        merged[category] = db_items + [item for item in web_items if item]
    return merged

from typing import Any

from app.services.ai_trip_planner.parser_utils import sanitize_text


def _normalize_web_item(item: dict[str, Any], category: str, destination: str) -> dict[str, Any] | None:
    name = sanitize_text(item.get("name"))
    if not name:
        return None

    # Keep relevance strict and avoid unrelated cities.
    searchable = f"{name} {sanitize_text(item.get('description', ''))}".lower()
    if destination.lower() not in searchable:
        return None

    return {
        "id": None,
        "name": name,
        "title": name,
        "type": category[:-1] if category.endswith("s") else category,
        "service_type": category[:-1] if category.endswith("s") else category,
        "location": destination,
        "price": "",
        "price_per_night": 0,
        "total_price": 0,
        "rating": "",
        "image": "",
        "image_url": "",
        "description": sanitize_text(item.get("description", "")),
        "source": "web",
        "booking_supported": False,
        "external_url": item.get("external_url", ""),
    }


def merge_recommendations(
    db_categories: dict[str, list[dict[str, Any]]],
    web_categories: dict[str, list[dict[str, Any]]],
    destination: str,
) -> dict[str, list[dict[str, Any]]]:
    merged: dict[str, list[dict[str, Any]]] = {}
    for category, db_items in db_categories.items():
        web_items = [
            _normalize_web_item(item, category, destination)
            for item in web_categories.get(category, [])
        ]
        merged[category] = db_items + [item for item in web_items if item]
    return merged

