import OpenAI from "openai";
import type {
  BuyerCriteria,
  ListingSummary,
  ScoredListing,
  ScoredListingWithSummary,
} from "../types/index";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

export interface LLMClientConfig {
  /** OpenAI API key. Defaults to process.env.OPENAI_API_KEY. */
  apiKey?: string;
  /** Model to use (default: "gpt-4o-mini"). */
  model?: string;
  /** Maximum tokens for each completion (default: 1024). */
  maxTokens?: number;
}

// ---------------------------------------------------------------------------
// Prompt builders
// ---------------------------------------------------------------------------

function buildSystemPrompt(): string {
  return [
    "You are an expert real estate analyst assisting a buyer's agent.",
    "Your job is to produce concise, objective, and grounded analyses of property listings relative to a buyer's search criteria.",
    "Always base your analysis strictly on the data provided — do not hallucinate amenities, prices, or neighbourhood facts.",
    "Return ONLY valid JSON matching the schema described in the user message.",
  ].join(" ");
}

function buildUserPrompt(
  scored: ScoredListing,
  criteria: BuyerCriteria,
): string {
  const { listing, overallScore, breakdown } = scored;

  const criteriaBlock = JSON.stringify(
    {
      maxBudget: criteria.maxBudget,
      minBudget: criteria.minBudget,
      minBedrooms: criteria.minBedrooms,
      minBathrooms: criteria.minBathrooms,
      minSquareFeet: criteria.minSquareFeet,
      preferredCities: criteria.preferredCities,
      mustHaveFeatures: criteria.mustHaveFeatures,
      niceToHaveFeatures: criteria.niceToHaveFeatures,
      dealbreakers: criteria.dealbreakers,
      freeformNotes: criteria.freeformNotes,
    },
    null,
    2,
  );

  const listingBlock = JSON.stringify(
    {
      id: listing.id,
      address: listing.address,
      city: listing.city,
      state: listing.state,
      listPrice: listing.listPrice,
      bedrooms: listing.bedrooms,
      bathrooms: listing.bathrooms,
      squareFeet: listing.squareFeet,
      yearBuilt: listing.yearBuilt,
      features: listing.features,
      description: listing.description,
      daysOnMarket: listing.daysOnMarket,
    },
    null,
    2,
  );

  const scoreBlock = JSON.stringify(
    {
      overallScore,
      breakdown: breakdown.map((b) => ({
        category: b.category,
        score: b.score,
        notes: b.notes,
      })),
    },
    null,
    2,
  );

  return [
    `## Buyer Criteria\n${criteriaBlock}`,
    `## Listing Data\n${listingBlock}`,
    `## Scoring Breakdown\n${scoreBlock}`,
    "---",
    "Produce a JSON object with exactly these fields:",
    '  "pros"          : string[]  — up to 5 positive attributes relevant to this buyer',
    '  "cons"          : string[]  — up to 5 negative attributes or unmet preferences',
    '  "risks"         : string[]  — up to 3 risks the agent or buyer should investigate',
    '  "matchRationale": string    — 2–4 sentence narrative explaining the match score',
    "",
    "Return ONLY the JSON object, no markdown fences.",
  ].join("\n\n");
}

// ---------------------------------------------------------------------------
// Response parser
// ---------------------------------------------------------------------------

interface RawSummaryResponse {
  pros?: unknown;
  cons?: unknown;
  risks?: unknown;
  matchRationale?: unknown;
}

function parseResponse(raw: string, listingId: string): ListingSummary {
  let parsed: RawSummaryResponse;
  try {
    parsed = JSON.parse(raw) as RawSummaryResponse;
  } catch {
    throw new Error(`LLM returned non-JSON response for listing ${listingId}: ${raw}`);
  }

  const toStringArray = (val: unknown, field: string): string[] => {
    if (!Array.isArray(val)) {
      throw new Error(`Expected array for "${field}" in LLM response for listing ${listingId}.`);
    }
    return val.map((item) => String(item));
  };

  return {
    listingId,
    pros: toStringArray(parsed.pros, "pros"),
    cons: toStringArray(parsed.cons, "cons"),
    risks: toStringArray(parsed.risks, "risks"),
    matchRationale:
      typeof parsed.matchRationale === "string"
        ? parsed.matchRationale
        : (() => {
            throw new Error(
              `Expected string for "matchRationale" in LLM response for listing ${listingId}.`,
            );
          })(),
  };
}

// ---------------------------------------------------------------------------
// LLM Client
// ---------------------------------------------------------------------------

export class LLMClient {
  private readonly openai: OpenAI;
  private readonly model: string;
  private readonly maxTokens: number;

  constructor(config: LLMClientConfig = {}) {
    this.openai = new OpenAI({
      apiKey: config.apiKey ?? process.env["OPENAI_API_KEY"],
    });
    this.model = config.model ?? "gpt-4o-mini";
    this.maxTokens = config.maxTokens ?? 1024;
  }

  /**
   * Generate a RAG-grounded listing summary for a single scored listing.
   */
  async summariseListing(
    scored: ScoredListing,
    criteria: BuyerCriteria,
  ): Promise<ListingSummary> {
    const response = await this.openai.chat.completions.create({
      model: this.model,
      max_tokens: this.maxTokens,
      temperature: 0.3,
      messages: [
        { role: "system", content: buildSystemPrompt() },
        { role: "user", content: buildUserPrompt(scored, criteria) },
      ],
    });

    const content = response.choices[0]?.message?.content ?? "";
    return parseResponse(content.trim(), scored.listing.id);
  }

  /**
   * Attach LLM-generated summaries to an array of scored listings.
   * Listings are processed concurrently up to `concurrency` at a time.
   */
  async summariseListings(
    scoredListings: ScoredListing[],
    criteria: BuyerCriteria,
    concurrency = 3,
  ): Promise<ScoredListingWithSummary[]> {
    const results: ScoredListingWithSummary[] = [];

    for (let i = 0; i < scoredListings.length; i += concurrency) {
      const batch = scoredListings.slice(i, i + concurrency);
      const summaries = await Promise.all(
        batch.map((s) => this.summariseListing(s, criteria)),
      );
      for (let j = 0; j < batch.length; j++) {
        results.push({ ...batch[j]!, summary: summaries[j]! });
      }
    }

    return results;
  }
}
