import { scoreListing, scoreListings } from "../src/scoring/index";
import type { BuyerCriteria, MLSListing } from "../src/types/index";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const baseCriteria: BuyerCriteria = {
  clientName: "Alice Smith",
  maxBudget: 600_000,
  minBudget: 400_000,
  minBedrooms: 3,
  minBathrooms: 2,
  minSquareFeet: 1500,
  preferredCities: ["Ottawa", "Nepean"],
  mustHaveFeatures: ["garage"],
  niceToHaveFeatures: ["pool", "fireplace"],
  dealbreakers: ["flood zone"],
};

const goodListing: MLSListing = {
  id: "mls-001",
  address: "123 Maple Ave",
  city: "Ottawa",
  state: "ON",
  zipCode: "K1A 0A1",
  listPrice: 550_000,
  bedrooms: 4,
  bathrooms: 2,
  squareFeet: 2000,
  yearBuilt: 2010,
  features: ["garage", "pool"],
  description: "Beautiful home in the heart of Ottawa with an attached garage and pool.",
};

// ---------------------------------------------------------------------------
// Budget scoring
// ---------------------------------------------------------------------------

describe("scoreListing — budget", () => {
  it("returns high score when price is within budget", () => {
    const result = scoreListing(goodListing, baseCriteria);
    const budgetBreakdown = result.breakdown.find((b) => b.category === "Budget");
    expect(budgetBreakdown).toBeDefined();
    expect(budgetBreakdown!.score).toBeGreaterThanOrEqual(80);
  });

  it("returns low score when price significantly exceeds budget", () => {
    const overBudget: MLSListing = { ...goodListing, listPrice: 900_000 };
    const result = scoreListing(overBudget, baseCriteria);
    const budgetBreakdown = result.breakdown.find((b) => b.category === "Budget");
    expect(budgetBreakdown!.score).toBe(0);
  });

  it("returns budget category score of 0 when price is more than 20% over budget", () => {
    const massivelyOverBudget: MLSListing = { ...goodListing, listPrice: 1_000_000 };
    const result = scoreListing(massivelyOverBudget, baseCriteria);
    const budgetBreakdown = result.breakdown.find((b) => b.category === "Budget");
    expect(budgetBreakdown!.score).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Location scoring
// ---------------------------------------------------------------------------

describe("scoreListing — location", () => {
  it("scores 100 when city is in preferred list", () => {
    const result = scoreListing(goodListing, baseCriteria);
    const loc = result.breakdown.find((b) => b.category === "Location");
    expect(loc!.score).toBe(100);
  });

  it("scores 0 when city is not in preferred list", () => {
    const wrongCity: MLSListing = { ...goodListing, city: "Toronto" };
    const result = scoreListing(wrongCity, baseCriteria);
    const loc = result.breakdown.find((b) => b.category === "Location");
    expect(loc!.score).toBe(0);
  });

  it("scores 80 when no preferred cities are specified", () => {
    const noCityCriteria: BuyerCriteria = { ...baseCriteria, preferredCities: [] };
    const result = scoreListing(goodListing, noCityCriteria);
    const loc = result.breakdown.find((b) => b.category === "Location");
    expect(loc!.score).toBe(80);
  });

  it("is case-insensitive for city matching", () => {
    const lowerCity: MLSListing = { ...goodListing, city: "ottawa" };
    const result = scoreListing(lowerCity, baseCriteria);
    const loc = result.breakdown.find((b) => b.category === "Location");
    expect(loc!.score).toBe(100);
  });
});

// ---------------------------------------------------------------------------
// Bedrooms / bathrooms scoring
// ---------------------------------------------------------------------------

describe("scoreListing — bedrooms", () => {
  it("scores 100 when bedrooms meet minimum", () => {
    const exact: MLSListing = { ...goodListing, bedrooms: 3 };
    const result = scoreListing(exact, baseCriteria);
    const beds = result.breakdown.find((b) => b.category === "Bedrooms");
    expect(beds!.score).toBe(100);
  });

  it("gives bonus score for extra bedrooms (capped at 100)", () => {
    const extra: MLSListing = { ...goodListing, bedrooms: 5 };
    const result = scoreListing(extra, baseCriteria);
    const beds = result.breakdown.find((b) => b.category === "Bedrooms");
    expect(beds!.score).toBe(100); // capped
  });

  it("penalises when bedrooms are below minimum", () => {
    const tooFew: MLSListing = { ...goodListing, bedrooms: 2 };
    const result = scoreListing(tooFew, baseCriteria);
    const beds = result.breakdown.find((b) => b.category === "Bedrooms");
    expect(beds!.score).toBeLessThan(100);
    expect(beds!.score).toBeGreaterThanOrEqual(0);
  });
});

// ---------------------------------------------------------------------------
// Must-have features scoring
// ---------------------------------------------------------------------------

describe("scoreListing — must-have features", () => {
  it("scores 100 when all must-have features are present", () => {
    const result = scoreListing(goodListing, baseCriteria);
    const feat = result.breakdown.find((b) => b.category === "Must-Have Features");
    expect(feat!.score).toBe(100);
  });

  it("scores 0 when no must-have features are present", () => {
    const noGarage: MLSListing = {
      ...goodListing,
      features: ["pool"],
      description: "Beautiful home.",
    };
    const result = scoreListing(noGarage, baseCriteria);
    const feat = result.breakdown.find((b) => b.category === "Must-Have Features");
    expect(feat!.score).toBe(0);
  });

  it("detects must-have features mentioned in the description", () => {
    const inDesc: MLSListing = { ...goodListing, features: [], description: "Has a garage." };
    const result = scoreListing(inDesc, baseCriteria);
    const feat = result.breakdown.find((b) => b.category === "Must-Have Features");
    expect(feat!.score).toBe(100);
  });

  it("scores 100 when no must-have features are specified", () => {
    const noCriteria: BuyerCriteria = { ...baseCriteria, mustHaveFeatures: [] };
    const result = scoreListing(goodListing, noCriteria);
    const feat = result.breakdown.find((b) => b.category === "Must-Have Features");
    expect(feat!.score).toBe(100);
  });
});

// ---------------------------------------------------------------------------
// Nice-to-have features scoring
// ---------------------------------------------------------------------------

describe("scoreListing — nice-to-have features", () => {
  it("scores based on proportion of matched features", () => {
    // goodListing has 'pool' but not 'fireplace'
    const result = scoreListing(goodListing, baseCriteria);
    const nth = result.breakdown.find((b) => b.category === "Nice-to-Have Features");
    expect(nth!.score).toBe(50); // 1/2
  });

  it("scores 100 when all nice-to-have features are present", () => {
    const allNice: MLSListing = {
      ...goodListing,
      features: ["garage", "pool", "fireplace"],
    };
    const result = scoreListing(allNice, baseCriteria);
    const nth = result.breakdown.find((b) => b.category === "Nice-to-Have Features");
    expect(nth!.score).toBe(100);
  });
});

// ---------------------------------------------------------------------------
// Dealbreaker
// ---------------------------------------------------------------------------

describe("scoreListing — dealbreakers", () => {
  it("returns overall score of 0 when a dealbreaker is present in features", () => {
    const db: MLSListing = { ...goodListing, features: ["garage", "flood zone"] };
    const result = scoreListing(db, baseCriteria);
    expect(result.overallScore).toBe(0);
    expect(result.breakdown[0]!.category).toBe("Dealbreaker");
  });

  it("returns overall score of 0 when a dealbreaker is mentioned in description", () => {
    const db: MLSListing = {
      ...goodListing,
      description: "This property is located in a flood zone area.",
    };
    const result = scoreListing(db, baseCriteria);
    expect(result.overallScore).toBe(0);
  });

  it("does not trigger dealbreaker when none are present", () => {
    const result = scoreListing(goodListing, baseCriteria);
    expect(result.overallScore).toBeGreaterThan(0);
    expect(result.breakdown.some((b) => b.category === "Dealbreaker")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// scoreListings — sorted order
// ---------------------------------------------------------------------------

describe("scoreListings", () => {
  it("returns listings sorted by overall score descending", () => {
    const listings: MLSListing[] = [
      { ...goodListing, id: "a", listPrice: 500_000 },
      { ...goodListing, id: "b", listPrice: 900_000 }, // over budget
      { ...goodListing, id: "c", listPrice: 480_000, bedrooms: 3 },
    ];
    const results = scoreListings(listings, baseCriteria);
    for (let i = 1; i < results.length; i++) {
      expect(results[i - 1]!.overallScore).toBeGreaterThanOrEqual(results[i]!.overallScore);
    }
  });

  it("handles an empty listing array", () => {
    expect(scoreListings([], baseCriteria)).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Overall score sanity
// ---------------------------------------------------------------------------

describe("scoreListing — overall score", () => {
  it("produces a score between 0 and 100", () => {
    const result = scoreListing(goodListing, baseCriteria);
    expect(result.overallScore).toBeGreaterThanOrEqual(0);
    expect(result.overallScore).toBeLessThanOrEqual(100);
  });

  it("produces higher score for good listing than poor one", () => {
    const poorListing: MLSListing = {
      id: "poor",
      address: "1 Bad St",
      city: "Toronto",
      state: "ON",
      zipCode: "M5V",
      listPrice: 850_000,
      bedrooms: 1,
      bathrooms: 1,
      squareFeet: 600,
      features: [],
      description: "Tiny condo.",
    };
    const goodScore = scoreListing(goodListing, baseCriteria).overallScore;
    const poorScore = scoreListing(poorListing, baseCriteria).overallScore;
    expect(goodScore).toBeGreaterThan(poorScore);
  });
});
