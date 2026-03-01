"""Pull incremental MLS/IDX data into the warehouse."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

import requests

LAST_RUN_FILE = ".openclaw/state/ingest_mls.json"
MLS_API_URL = os.getenv("MLS_API_URL", "https://api.example-mls.com/listings")
MLS_API_KEY = os.getenv("MLS_API_KEY", "demo-key")


def load_last_run() -> datetime:
    try:
        with open(LAST_RUN_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            return datetime.fromisoformat(data["last_run"])
    except FileNotFoundError:
        return datetime.now(timezone.utc) - timedelta(hours=1)


def save_last_run(moment: datetime) -> None:
    os.makedirs(os.path.dirname(LAST_RUN_FILE), exist_ok=True)
    with open(LAST_RUN_FILE, "w", encoding="utf-8") as handle:
        json.dump({"last_run": moment.isoformat()}, handle)


def fetch_listings(since: datetime) -> list[dict]:
    resp = requests.get(
        MLS_API_URL,
        params={"updated_since": since.isoformat()},
        headers={"Authorization": f"Bearer {MLS_API_KEY}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("listings", [])


def upsert_listings(listings: list[dict]) -> None:
    # Placeholder: integrate with real database layer
    print(f"[ingest_mls] Would upsert {len(listings)} listings")


def main() -> None:
    last_run = load_last_run()
    listings = fetch_listings(last_run)
    upsert_listings(listings)
    save_last_run(datetime.now(timezone.utc))


if __name__ == "__main__":
    main()
