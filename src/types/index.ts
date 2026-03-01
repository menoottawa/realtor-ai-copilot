/**
 * Structured buyer preferences provided by a real estate agent on behalf of a client.
 */
export interface BuyerCriteria {
  /** Client's name for personalised output. */
  clientName: string;
  /** Maximum purchase price the buyer can afford. */
  maxBudget: number;
  /** Minimum purchase price (optional; used to exclude ultra-low listings). */
  minBudget?: number;
  /** Minimum number of bedrooms required. */
  minBedrooms?: number;
  /** Minimum number of bathrooms required. */
  minBathrooms?: number;
  /** Minimum livable square footage. */
  minSquareFeet?: number;
  /** List of city names the buyer would consider. Empty = no restriction. */
  preferredCities?: string[];
  /** Features the listing MUST have (e.g. "garage", "pool"). */
  mustHaveFeatures?: string[];
  /** Features the buyer would like but aren't mandatory. */
  niceToHaveFeatures?: string[];
  /** Characteristics that immediately disqualify a listing. */
  dealbreakers?: string[];
  /** Free-form notes from the agent (e.g. "prefers a quiet street near good schools"). */
  freeformNotes?: string;
}

/**
 * An MLS/IDX listing snapshot.
 */
export interface MLSListing {
  /** Unique MLS identifier. */
  id: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  listPrice: number;
  bedrooms: number;
  bathrooms: number;
  squareFeet: number;
  lotSizeSqFt?: number;
  yearBuilt?: number;
  /** Amenity / feature tags from the MLS feed. */
  features: string[];
  /** Full marketing description. */
  description: string;
  daysOnMarket?: number;
  pricePerSqFt?: number;
}

/**
 * Score for a single dimension of the buyer's criteria.
 */
export interface ScoreBreakdown {
  /** Human-readable category name. */
  category: string;
  /** Score for this category from 0 (worst) to 100 (best). */
  score: number;
  /** Weight applied when computing the overall score (0–1, all weights should sum to 1). */
  weight: number;
  /** Short explanation of why this score was assigned. */
  notes: string;
}

/**
 * A listing that has been scored against a buyer's criteria.
 */
export interface ScoredListing {
  listing: MLSListing;
  /** Weighted average of all category scores (0–100). */
  overallScore: number;
  breakdown: ScoreBreakdown[];
}

/**
 * RAG-grounded narrative analysis of a listing for a specific buyer.
 */
export interface ListingSummary {
  listingId: string;
  /** Positive attributes relevant to the buyer. */
  pros: string[];
  /** Negative attributes or unmet preferences. */
  cons: string[];
  /** Potential risks the agent or buyer should investigate. */
  risks: string[];
  /** Narrative explanation of how well the listing matches the buyer's brief. */
  matchRationale: string;
}

/**
 * A scored listing combined with its LLM-generated narrative summary.
 */
export interface ScoredListingWithSummary extends ScoredListing {
  summary: ListingSummary;
}

/**
 * Configuration for building a client-ready PDF packet.
 */
export interface PacketConfig {
  /** Agent's display name. */
  agentName: string;
  /** Brokerage or agency name. */
  agencyName: string;
  /** Path or URL to the agency logo (optional). */
  logoPath?: string;
  /** Absolute file path where the PDF should be written. */
  outputPath: string;
  /** Brand accent colour as a hex string (default: "#1a4b8c"). */
  brandColor?: string;
}

/**
 * Abstract interface every packet template must implement.
 */
export interface PacketTemplate {
  /** Human-readable template name. */
  name: string;
  /**
   * Render the PDF for the given buyer and listings.
   * @param config    Branding / output configuration.
   * @param criteria  The buyer's search criteria.
   * @param listings  Scored + summarised listings to include.
   * @returns Resolves with the absolute path to the written PDF.
   */
  render(
    config: PacketConfig,
    criteria: BuyerCriteria,
    listings: ScoredListingWithSummary[],
  ): Promise<string>;
}
