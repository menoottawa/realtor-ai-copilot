# Skill: real-estate-search

## Purpose
Search residential listings for buyer clients using structured filters (location, price, beds/baths, must-haves) and return a concise ranked list with AI-ready metadata for summaries or packet creation.

## When to Use
- A buyer asks for property options matching specific criteria
- Need to refresh matches after a criteria tweak (price bump, add "office", etc.)
- Prepping a packet/intake form where structured listing data is required

## Inputs
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `location` | string | ✓ | City/ZIP/neighborhood keyword (e.g., "Lakeway, TX") |
| `min_price` | number |  | Defaults to 0 |
| `max_price` | number |  | Defaults to +inf |
| `beds` | number |  | Minimum bedrooms |
| `baths` | number |  | Minimum bathrooms |
| `must_haves` | array[string] |  | Keywords like `"office"`, `"lake"`, `"yard"` |
| `nice_to_haves` | array[string] |  | Lower weight keywords |
| `max_results` | integer |  | Defaults to 5 |

## Outputs
Array of up to `max_results` listings:
```
[
  {
    "mls_id": "A123",
    "address": "123 Oak Meadow Dr, Austin, TX 78735",
    "price": 745000,
    "beds": 3,
    "baths": 3,
    "sqft": 2680,
    "lot_sqft": 7405,
    "hoa": 68,
    "dom": 6,
    "style_tags": ["modern", "office"],
    "match_score": 0.92,
    "summary": "Circle C home w/ dedicated office, greenbelt view",
    "detail_url": "https://example.com/listings/A123",
    "notes": "Lake Travis ISD, covered patio"
  }
]
```

## Implementation Notes
- For now, the script reads `sample-data.json`. Swap in an MLS/IDX client later.
- Match score boosts listings that contain all `must_haves`. Partial credit for `nice_to_haves`.
- DOM under 15 days + price within 10% of budget get bonus.

## Agent Guidance
- After retrieving results, summarize top 3 and ask the buyer if they want to refine, save, or request a tour.
- If no results, suggest loosening one constraint (price, neighborhood, feature).
- Always remind the buyer a licensed agent will confirm availability before scheduling tours.
