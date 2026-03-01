import type {
  BuyerCriteria,
  MLSListing,
  ScoreBreakdown,
  ScoredListing,
} from "../types/index";

// ---------------------------------------------------------------------------
// Category weights — must sum to 1.0
// ---------------------------------------------------------------------------
const WEIGHTS = {
  budget: 0.3,
  location: 0.2,
  bedrooms: 0.15,
  bathrooms: 0.1,
  squareFeet: 0.1,
  mustHaveFeatures: 0.1,
  niceToHaveFeatures: 0.05,
} as const;

// ---------------------------------------------------------------------------
// Individual category scorers (each returns 0–100)
// ---------------------------------------------------------------------------

function scoreBudget(listing: MLSListing, criteria: BuyerCriteria): ScoreBreakdown {
  const { listPrice } = listing;
  const { maxBudget, minBudget = 0 } = criteria;

  let score: number;
  let notes: string;

  if (listPrice > maxBudget) {
    // Over budget — penalise proportionally (hard cap at 0 if >20% over)
    const overRatio = (listPrice - maxBudget) / maxBudget;
    score = Math.max(0, Math.round(100 - overRatio * 500));
    notes = `$${listPrice.toLocaleString()} is ${(overRatio * 100).toFixed(1)}% over the $${maxBudget.toLocaleString()} budget.`;
  } else if (listPrice < minBudget) {
    // Unusually cheap — flag as moderate concern
    score = 60;
    notes = `$${listPrice.toLocaleString()} is below the minimum expected price of $${minBudget.toLocaleString()}.`;
  } else {
    // Within range — reward listings closer to (but not at) the ceiling
    const usedRatio = (listPrice - minBudget) / (maxBudget - minBudget || maxBudget);
    score = Math.round(100 - usedRatio * 20); // 80–100
    notes = `$${listPrice.toLocaleString()} fits within the $${minBudget.toLocaleString()}–$${maxBudget.toLocaleString()} budget range.`;
  }

  return { category: "Budget", score, weight: WEIGHTS.budget, notes };
}

function scoreLocation(listing: MLSListing, criteria: BuyerCriteria): ScoreBreakdown {
  const preferred = criteria.preferredCities ?? [];

  if (preferred.length === 0) {
    return {
      category: "Location",
      score: 80,
      weight: WEIGHTS.location,
      notes: "No city preference specified — listing city accepted.",
    };
  }

  const listingCity = listing.city.toLowerCase().trim();
  const match = preferred.some((c) => c.toLowerCase().trim() === listingCity);

  return {
    category: "Location",
    score: match ? 100 : 0,
    weight: WEIGHTS.location,
    notes: match
      ? `${listing.city} is in the preferred city list.`
      : `${listing.city} is not in the preferred city list (${preferred.join(", ")}).`,
  };
}

function scoreBedrooms(listing: MLSListing, criteria: BuyerCriteria): ScoreBreakdown {
  const min = criteria.minBedrooms ?? 0;
  const actual = listing.bedrooms;

  let score: number;
  let notes: string;

  if (actual >= min) {
    // Bonus for extras, capped at 100
    score = Math.min(100, 100 + (actual - min) * 5);
    notes =
      actual === min
        ? `Meets the minimum of ${min} bedroom(s).`
        : `${actual} bedrooms — ${actual - min} more than the required ${min}.`;
  } else {
    const shortfall = min - actual;
    score = Math.max(0, 100 - shortfall * 30);
    notes = `Only ${actual} bedroom(s); ${shortfall} short of the required ${min}.`;
  }

  return { category: "Bedrooms", score, weight: WEIGHTS.bedrooms, notes };
}

function scoreBathrooms(listing: MLSListing, criteria: BuyerCriteria): ScoreBreakdown {
  const min = criteria.minBathrooms ?? 0;
  const actual = listing.bathrooms;

  let score: number;
  let notes: string;

  if (actual >= min) {
    score = Math.min(100, 100 + (actual - min) * 5);
    notes =
      actual === min
        ? `Meets the minimum of ${min} bathroom(s).`
        : `${actual} bathrooms — ${actual - min} more than the required ${min}.`;
  } else {
    const shortfall = min - actual;
    score = Math.max(0, 100 - shortfall * 25);
    notes = `Only ${actual} bathroom(s); ${shortfall} short of the required ${min}.`;
  }

  return { category: "Bathrooms", score, weight: WEIGHTS.bathrooms, notes };
}

function scoreSquareFeet(listing: MLSListing, criteria: BuyerCriteria): ScoreBreakdown {
  const min = criteria.minSquareFeet ?? 0;
  const actual = listing.squareFeet;

  if (min === 0) {
    return {
      category: "Square Footage",
      score: 80,
      weight: WEIGHTS.squareFeet,
      notes: "No minimum square footage specified.",
    };
  }

  let score: number;
  let notes: string;

  if (actual >= min) {
    const ratio = actual / min;
    score = Math.min(100, Math.round(80 + (ratio - 1) * 40));
    notes = `${actual.toLocaleString()} sq ft meets or exceeds the ${min.toLocaleString()} sq ft minimum.`;
  } else {
    const deficitRatio = (min - actual) / min;
    score = Math.max(0, Math.round(100 - deficitRatio * 150));
    notes = `${actual.toLocaleString()} sq ft is below the ${min.toLocaleString()} sq ft minimum.`;
  }

  return { category: "Square Footage", score, weight: WEIGHTS.squareFeet, notes };
}

function scoreMustHaveFeatures(
  listing: MLSListing,
  criteria: BuyerCriteria,
): ScoreBreakdown {
  const required = criteria.mustHaveFeatures ?? [];

  if (required.length === 0) {
    return {
      category: "Must-Have Features",
      score: 100,
      weight: WEIGHTS.mustHaveFeatures,
      notes: "No must-have features specified.",
    };
  }

  const listingFeatureSet = new Set(listing.features.map((f) => f.toLowerCase().trim()));
  const descLower = listing.description.toLowerCase();

  const missing: string[] = [];
  const present: string[] = [];

  for (const feature of required) {
    const featureLower = feature.toLowerCase().trim();
    if (
      listingFeatureSet.has(featureLower) ||
      descLower.includes(featureLower)
    ) {
      present.push(feature);
    } else {
      missing.push(feature);
    }
  }

  const score = Math.round((present.length / required.length) * 100);
  const notes =
    missing.length === 0
      ? `All ${required.length} must-have feature(s) confirmed: ${present.join(", ")}.`
      : `Missing must-have feature(s): ${missing.join(", ")}.`;

  return { category: "Must-Have Features", score, weight: WEIGHTS.mustHaveFeatures, notes };
}

function scoreNiceToHaveFeatures(
  listing: MLSListing,
  criteria: BuyerCriteria,
): ScoreBreakdown {
  const wanted = criteria.niceToHaveFeatures ?? [];

  if (wanted.length === 0) {
    return {
      category: "Nice-to-Have Features",
      score: 80,
      weight: WEIGHTS.niceToHaveFeatures,
      notes: "No nice-to-have features specified.",
    };
  }

  const listingFeatureSet = new Set(listing.features.map((f) => f.toLowerCase().trim()));
  const descLower = listing.description.toLowerCase();

  let matched = 0;
  const matchedNames: string[] = [];

  for (const feature of wanted) {
    const featureLower = feature.toLowerCase().trim();
    if (listingFeatureSet.has(featureLower) || descLower.includes(featureLower)) {
      matched++;
      matchedNames.push(feature);
    }
  }

  const score = Math.round((matched / wanted.length) * 100);
  const notes =
    matched === 0
      ? "None of the nice-to-have features are present."
      : `${matched}/${wanted.length} nice-to-have feature(s) matched: ${matchedNames.join(", ")}.`;

  return {
    category: "Nice-to-Have Features",
    score,
    weight: WEIGHTS.niceToHaveFeatures,
    notes,
  };
}

// ---------------------------------------------------------------------------
// Dealbreaker check — returns true if a dealbreaker is detected
// ---------------------------------------------------------------------------

function hasDealbreaker(listing: MLSListing, criteria: BuyerCriteria): string | null {
  const dealbreakers = criteria.dealbreakers ?? [];
  if (dealbreakers.length === 0) return null;

  const listingFeatureSet = new Set(listing.features.map((f) => f.toLowerCase().trim()));
  const descLower = listing.description.toLowerCase();

  for (const db of dealbreakers) {
    const dbLower = db.toLowerCase().trim();
    if (listingFeatureSet.has(dbLower) || descLower.includes(dbLower)) {
      return db;
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Score a single MLS listing against the buyer's criteria.
 *
 * If a dealbreaker is detected the listing receives an overall score of 0
 * and the breakdown contains a single "Dealbreaker" entry explaining why.
 */
export function scoreListing(
  listing: MLSListing,
  criteria: BuyerCriteria,
): ScoredListing {
  const dealbreaker = hasDealbreaker(listing, criteria);

  if (dealbreaker !== null) {
    return {
      listing,
      overallScore: 0,
      breakdown: [
        {
          category: "Dealbreaker",
          score: 0,
          weight: 1,
          notes: `Dealbreaker detected: "${dealbreaker}" found in listing features or description.`,
        },
      ],
    };
  }

  const breakdown: ScoreBreakdown[] = [
    scoreBudget(listing, criteria),
    scoreLocation(listing, criteria),
    scoreBedrooms(listing, criteria),
    scoreBathrooms(listing, criteria),
    scoreSquareFeet(listing, criteria),
    scoreMustHaveFeatures(listing, criteria),
    scoreNiceToHaveFeatures(listing, criteria),
  ];

  const overallScore = Math.round(
    breakdown.reduce((sum, b) => sum + b.score * b.weight, 0),
  );

  return { listing, overallScore, breakdown };
}

/**
 * Score multiple listings and return them sorted by overall score (descending).
 */
export function scoreListings(
  listings: MLSListing[],
  criteria: BuyerCriteria,
): ScoredListing[] {
  return listings
    .map((l) => scoreListing(l, criteria))
    .sort((a, b) => b.overallScore - a.overallScore);
}
