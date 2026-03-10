import json
import tempfile
from pathlib import Path

from src.scrapers.public_records import PublicRecordsScraper
from src.scrapers.listings import ListingsScraper


SAMPLE_RECORD = {
    "parcel_id": "SCRAPE-001",
    "address": "100 Test St",
    "city": "Austin",
    "state": "TX",
    "zip_code": "78701",
    "property_type": "office",
    "square_feet": 10000,
    "owner_name": "Test Owner",
    "assessed_value": 2000000,
}


def _write_temp_json(records: list[dict]) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(records, tmp)
    tmp.close()
    return Path(tmp.name)


def test_public_records_scraper_loads_data():
    path = _write_temp_json([SAMPLE_RECORD])
    scraper = PublicRecordsScraper(data_path=path)
    results = scraper.scrape("Austin", "TX")
    assert len(results) == 1
    assert results[0].parcel_id == "SCRAPE-001"


def test_public_records_scraper_filters_city():
    path = _write_temp_json([SAMPLE_RECORD])
    scraper = PublicRecordsScraper(data_path=path)
    results = scraper.scrape("Dallas", "TX")
    assert len(results) == 0


def test_listings_scraper_loads_data():
    record = {**SAMPLE_RECORD, "parcel_id": "LIST-001", "is_listed": True, "list_price": 2500000}
    path = _write_temp_json([record])
    scraper = ListingsScraper(data_path=path)
    results = scraper.scrape("Austin", "TX")
    assert len(results) == 1
    assert results[0].is_listed is True


def test_scraper_missing_file_returns_empty():
    scraper = PublicRecordsScraper(data_path="/nonexistent/path.json")
    results = scraper.scrape("Austin", "TX")
    assert results == []
