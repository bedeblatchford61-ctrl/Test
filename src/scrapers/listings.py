from __future__ import annotations

import json
import logging
from pathlib import Path

from src.models.property import Property
from src.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ListingsScraper(BaseScraper):
    """Scraper for commercial real estate listing platforms.

    In production, this would integrate with listing APIs (e.g., LoopNet,
    Crexi, or a commercial MLS feed). For development it reads from a
    local JSON file.
    """

    name = "listings"

    def __init__(self, data_path: str | Path | None = None) -> None:
        self.data_path = Path(data_path) if data_path else Path("data/sample_listings.json")

    def _fetch_raw(self, city: str, state: str, limit: int = 100) -> list[dict]:
        if not self.data_path.exists():
            logger.warning("Listings file not found: %s", self.data_path)
            return []
        with open(self.data_path) as f:
            records = json.load(f)
        filtered = [
            r
            for r in records
            if r.get("city", "").lower() == city.lower()
            and r.get("state", "").upper() == state.upper()
        ]
        return filtered[:limit]

    def scrape(
        self,
        city: str,
        state: str,
        *,
        property_types: list[str] | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        limit: int = 100,
    ) -> list[Property]:
        raw = self._fetch_raw(city, state, limit=limit)
        properties = []
        for record in raw:
            record.setdefault("is_listed", True)
            try:
                prop = Property(**record)
            except Exception:
                logger.debug("Skipping malformed listing: %s", record.get("parcel_id"))
                continue

            if property_types and prop.property_type.value not in property_types:
                continue
            if min_value and prop.market_value and prop.market_value < min_value:
                continue
            if max_value and prop.market_value and prop.market_value > max_value:
                continue
            properties.append(prop)

        return self.validate_results(properties[:limit])
