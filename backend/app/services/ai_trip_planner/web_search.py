import asyncio
import logging
import time
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.services.ai_trip_planner.parser_utils import is_safe_url, sanitize_text

logger = logging.getLogger(__name__)


class WebSearchService:
    _cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
    _semaphore = asyncio.Semaphore(4)

    async def _fetch(self, client: httpx.AsyncClient, query: str) -> list[dict[str, Any]]:
        cache_key = query.strip().lower()
        now = time.time()
        cached = self._cache.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]

        search_url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
        async with self._semaphore:
            response = await client.get(search_url, timeout=settings.WEB_SEARCH_TIMEOUT_SECONDS)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        parsed: list[dict[str, Any]] = []
        for item in soup.select(".result")[: settings.WEB_SEARCH_MAX_RESULTS_PER_TYPE]:
            anchor = item.select_one(".result__a")
            snippet = item.select_one(".result__snippet")
            if not anchor:
                continue
            source_url = anchor.get("href", "")
            if not is_safe_url(source_url):
                continue
            parsed.append(
                {
                    "name": sanitize_text(anchor.get_text(strip=True)),
                    "description": sanitize_text(snippet.get_text(strip=True) if snippet else ""),
                    "external_url": source_url,
                }
            )

        ttl = now + settings.WEB_SEARCH_CACHE_TTL_SECONDS
        self._cache[cache_key] = (ttl, parsed)
        return parsed

    async def search(self, destination: str) -> dict[str, list[dict[str, Any]]]:
        logger.info("[Web Search] searching external sources for %s", destination)
        query_map = {
            "hotels": f"Best hotels in {destination} Pakistan",
            "restaurants": f"Best restaurants in {destination} Pakistan",
            "activities": f"Top attractions in {destination}",
            "transport": f"Transport options in {destination}",
            "guides": f"Travel guides in {destination}",
        }
        try:
            async with httpx.AsyncClient(headers={"User-Agent": settings.WEB_SEARCH_USER_AGENT}) as client:
                tasks = {key: asyncio.create_task(self._fetch(client, q)) for key, q in query_map.items()}
                return {key: await task for key, task in tasks.items()}
        except Exception as exc:
            logger.warning("[Web Search] failed: %s", exc)
            return {k: [] for k in query_map}

