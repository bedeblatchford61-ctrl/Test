from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from src.models.property import Property

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base for all property data scrapers."""

    name: str = "base"

    @abstractmethod
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
        """Scrape properties matching the given criteria.

        Args:
            city: Target city name.
            state: Two-letter state code.
            property_types: Filter by property type names.
            min_value: Minimum assessed/market value.
            max_value: Maximum assessed/market value.
            limit: Max number of records to return.

        Returns:
            List of Property objects.
        """

    def validate_results(self, properties: list[Property]) -> list[Property]:
        """Drop records missing critical fields."""
        valid = []
        for p in properties:
            if not p.address or not p.owner_name:
                logger.warning("Dropping property %s: missing address or owner", p.parcel_id)
                continue
            valid.append(p)
        logger.info("%s: %d/%d records valid", self.name, len(valid), len(properties))
        return valid
