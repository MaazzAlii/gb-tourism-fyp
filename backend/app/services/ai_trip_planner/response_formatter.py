from typing import Any


def format_trip_planner_response(
    destination: str,
    duration_days: int,
    budget_tier: str,
    total_budget: float,
    destination_info: dict[str, Any],
    merged_categories: dict[str, list[dict[str, Any]]],
    db_results_found: bool,
    fallback_triggered: bool,
    web_error: bool,
    destination_corrected_to: str | None = None,
) -> dict[str, Any]:
    db_hotels = [item for item in merged_categories.get("hotels", []) if item.get("source") == "database"]
    db_transport = [item for item in merged_categories.get("transport", []) if item.get("source") == "database"]
    db_activities = [item for item in merged_categories.get("activities", []) if item.get("source") == "database"]

    hotel = db_hotels[0] if db_hotels else None
    transport = db_transport[0] if db_transport else None
    activities = db_activities[:3]
    alt_hotels = db_hotels[1:5]
    alt_transport = db_transport[1:4]
    alt_activities = db_activities[3:7]

    hotel_cost = (hotel.get("price_per_night", 0) if hotel else 0) * duration_days
    transport_cost = transport.get("price_per_night", 0) if transport else 0
    activity_cost = sum(a.get("price_per_night", 0) for a in activities)
    estimated_cost = hotel_cost + transport_cost + activity_cost

    external = []
    for category in ("hotels", "restaurants", "activities", "transport", "guides"):
        external.extend([i for i in merged_categories.get(category, []) if i.get("source") == "web"])

    return {
        "destination": destination,
        "duration_days": duration_days,
        "budget_tier": budget_tier,
        "total_budget": total_budget,
        "estimated_cost": estimated_cost,
        "budget_remaining": total_budget - estimated_cost,
        "db_results_found": db_results_found,
        "destination_info": destination_info,
        "hotel": hotel,
        "transport": transport,
        "activities": activities,
        "alternatives": {
            "hotels": alt_hotels,
            "transports": alt_transport,
            "activities": alt_activities,
        },
        "breakdown": {
            "hotel": hotel_cost,
            "transport": transport_cost,
            "activities": activity_cost,
        },
        "available_on_gb_tourism": {
            "hotels": db_hotels,
            "restaurants": [i for i in merged_categories.get("restaurants", []) if i.get("source") == "database"],
            "activities": db_activities,
            "transport": db_transport,
            "guides": [i for i in merged_categories.get("guides", []) if i.get("source") == "database"],
        },
        "web_suggestions": external,
        "fallback_triggered": fallback_triggered,
        "limited_results": web_error,
        "empty_state_message": (
            f"No direct listings found in our database. Showing verified web suggestions for {destination}."
            if fallback_triggered
            else ""
        ),
        "destination_corrected_to": destination_corrected_to,
    }

