"""Send notifications when new matches or packets are ready."""
from __future__ import annotations

import os
from typing import List

import requests

WEBHOOK_URL = os.getenv("NOTIFICATION_WEBHOOK_URL", "")


def fetch_events() -> List[dict]:
    # Placeholder for DB query
    return [
        {"type": "match", "agent": "agent-1", "message": "New match scored 92"}
    ]


def send_notification(event: dict) -> None:
    if not WEBHOOK_URL:
        print(f"[notify] {event['agent']}: {event['message']}")
        return
    requests.post(WEBHOOK_URL, json={"text": event["message"]}, timeout=10)


def main() -> None:
    for event in fetch_events():
        send_notification(event)


if __name__ == "__main__":
    main()
