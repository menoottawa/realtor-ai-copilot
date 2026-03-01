"""Worker that generates AI analyses for matches needing summaries."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import requests

from realtor_ai.services import prompts

QUEUE_FILE = Path(".openclaw/state/ai_queue.json")
LLM_API_URL = "https://api.openai.com/v1/responses"
LLM_API_KEY = os.getenv("LLM_API_KEY", "demo")


def fetch_pending_matches() -> list[Dict[str, Any]]:
    if not QUEUE_FILE.exists():
        return []
    return json.loads(QUEUE_FILE.read_text())


def build_context(match: Dict[str, Any]) -> Dict[str, str]:
    return {
        "buyer_summary": match["buyer_summary"],
        "listing_facts": match["listing_facts"],
        "neighborhood_data": match.get("neighborhood_data", "N/A"),
        "match_breakdown": match["criterion_breakdown"],
        "match_score": match["score"],
    }


def call_llm(prompt: str) -> Dict[str, Any]:
    resp = requests.post(
        LLM_API_URL,
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        json={
            "model": "gpt-4.1-mini",
            "input": prompt,
            "response_format": {"type": "json_object"},
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def process_match(match: Dict[str, Any]) -> None:
    context = build_context(match)
    prompt = prompts.PROPERTY_ANALYSIS_PROMPT.format(**context)
    llm_response = call_llm(prompt)
    # TODO: Persist ai_sections to DB
    print(f"[ai] Generated analysis for match {match['id']}")


def main() -> None:
    matches = fetch_pending_matches()
    for match in matches:
        process_match(match)


if __name__ == "__main__":
    main()
