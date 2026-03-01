/**
 * realtor-ai-copilot
 *
 * Public API re-exports for the three core modules:
 *   - scoring  : Score MLS listings against structured + freeform buyer criteria.
 *   - llm      : Generate RAG-grounded summaries (pros, cons, risks, match rationale).
 *   - packet   : Assemble branded PDF packets using a template system.
 */

// Types
export type {
  BuyerCriteria,
  ListingSummary,
  MLSListing,
  PacketConfig,
  PacketTemplate,
  ScoreBreakdown,
  ScoredListing,
  ScoredListingWithSummary,
} from "./types/index";

// Scoring engine
export { scoreListing, scoreListings } from "./scoring/index";

// LLM client
export { LLMClient } from "./llm/index";
export type { LLMClientConfig } from "./llm/index";

// Packet builder
export { PacketBuilder, registerTemplate } from "./packet/index";
export type { PacketBuilderOptions } from "./packet/index";
