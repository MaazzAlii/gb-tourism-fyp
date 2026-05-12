import logging
from typing import Any

from sqlalchemy.orm import Session

from app.services.ai_trip_planner.db_search import search_database
from app.services.ai_trip_planner.parser import parse_user_query
from app.services.ai_trip_planner.recommendation_engine import merge_recommendations
from app.services.ai_trip_planner.response_formatter import format_trip_planner_response
from app.services.ai_trip_planner.web_search import WebSearchService

logger = logging.getLogger(__name__)


class PlannerService:
    def __init__(self, web_search_service: WebSearchService | None = None):
        self.web_search_service = web_search_service or WebSearchService()

    async def generate_plan(
        self,
        db: Session,
        destination: str,
        duration_days: int,
        budget_tier: str,
        total_budget: float,
        destination_info: dict[str, Any],
    ) -> dict[str, Any]:
        logger.info("[AI Planner] incoming query for %s", destination)
        parsed = parse_user_query(destination, duration_days, total_budget, budget_tier)
        db_result = search_database(
            db=db,
            destination=parsed["destination"],
            days=parsed["days"],
            budget=parsed["budget"],
        )
        logger.info("[DB Search] items=%s fallback=%s", db_result["total_items"], db_result["fallback_needed"])

        fallback_triggered = db_result["fallback_needed"]
        web_error = False
        web_categories = {k: [] for k in ("hotels", "restaurants", "activities", "transport", "guides")}
        if fallback_triggered:
            logger.info("[Fallback Triggered] destination=%s", parsed["destination"])
            web_categories = await self.web_search_service.search(parsed["destination"])
            if not any(web_categories.values()):
                web_error = True
            logger.info(
                "[External Results Parsed] hotels=%s activities=%s",
                len(web_categories["hotels"]),
                len(web_categories["activities"]),
            )

        merged = merge_recommendations(db_result["categories"], web_categories, parsed["destination"])
        return format_trip_planner_response(
            destination=parsed["destination"],
            duration_days=duration_days,
            budget_tier=budget_tier,
            total_budget=total_budget,
            destination_info=destination_info,
            merged_categories=merged,
            db_results_found=db_result["total_items"] > 0,
            fallback_triggered=fallback_triggered,
            web_error=web_error,
            destination_corrected_to=parsed.get("destination_corrected_to"),
        )

