"""Generate client-facing packets (PDF placeholder)."""
from __future__ import annotations

import json
from pathlib import Path

PACKET_QUEUE = Path(".openclaw/state/packet_queue.json")


def fetch_packets():
    if not PACKET_QUEUE.exists():
        return []
    return json.loads(PACKET_QUEUE.read_text())


def render_packet(packet):
    # TODO: integrate with template + PDF renderer
    print(f"[packet] Would render packet {packet['id']} for buyer {packet['buyer_id']}")


def main():
    for packet in fetch_packets():
        render_packet(packet)


if __name__ == "__main__":
    main()
