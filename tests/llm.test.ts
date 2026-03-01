import { LLMClient } from "../src/llm/index";
import type { BuyerCriteria, ScoredListing } from "../src/types/index";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

jest.mock("openai", () => {
  const mockCreate = jest.fn();
  return {
    __esModule: true,
    default: jest.fn().mockImplementation(() => ({
      chat: {
        completions: {
          create: mockCreate,
        },
      },
    })),
    _mockCreate: mockCreate,
  };
});

// Helper to get the mocked `create` function
function getMockCreate(): jest.Mock {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const openaiModule = require("openai") as { _mockCreate: jest.Mock };
  return openaiModule._mockCreate;
}

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const criteria: BuyerCriteria = {
  clientName: "Bob Jones",
  maxBudget: 700_000,
  preferredCities: ["Ottawa"],
  mustHaveFeatures: ["garage"],
};

const scoredListing: ScoredListing = {
  listing: {
    id: "mls-42",
    address: "42 Oak St",
    city: "Ottawa",
    state: "ON",
    zipCode: "K2P 1L3",
    listPrice: 650_000,
    bedrooms: 3,
    bathrooms: 2,
    squareFeet: 1800,
    features: ["garage", "deck"],
    description: "Charming Ottawa home with garage and large deck.",
    daysOnMarket: 10,
  },
  overallScore: 87,
  breakdown: [
    { category: "Budget", score: 90, weight: 0.3, notes: "Within budget." },
    { category: "Location", score: 100, weight: 0.2, notes: "Preferred city." },
  ],
};

// Valid LLM JSON response
const validLLMResponse = JSON.stringify({
  pros: ["Great location", "Garage included", "Spacious deck"],
  cons: ["Near main road"],
  risks: ["Check roof age"],
  matchRationale:
    "This property ticks all key boxes for Bob Jones. The garage and preferred city align perfectly with stated criteria.",
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("LLMClient.summariseListing", () => {
  beforeEach(() => {
    getMockCreate().mockReset();
  });

  it("returns a valid ListingSummary from a well-formed LLM response", async () => {
    getMockCreate().mockResolvedValue({
      choices: [{ message: { content: validLLMResponse } }],
    });

    const client = new LLMClient({ apiKey: "test-key" });
    const summary = await client.summariseListing(scoredListing, criteria);

    expect(summary.listingId).toBe("mls-42");
    expect(summary.pros).toEqual(["Great location", "Garage included", "Spacious deck"]);
    expect(summary.cons).toEqual(["Near main road"]);
    expect(summary.risks).toEqual(["Check roof age"]);
    expect(typeof summary.matchRationale).toBe("string");
    expect(summary.matchRationale.length).toBeGreaterThan(0);
  });

  it("trims whitespace/newlines around the JSON response", async () => {
    getMockCreate().mockResolvedValue({
      choices: [{ message: { content: `\n\n${validLLMResponse}\n` } }],
    });

    const client = new LLMClient({ apiKey: "test-key" });
    const summary = await client.summariseListing(scoredListing, criteria);
    expect(summary.listingId).toBe("mls-42");
  });

  it("throws when the LLM returns non-JSON", async () => {
    getMockCreate().mockResolvedValue({
      choices: [{ message: { content: "Sorry, I cannot help with that." } }],
    });

    const client = new LLMClient({ apiKey: "test-key" });
    await expect(client.summariseListing(scoredListing, criteria)).rejects.toThrow(
      /non-JSON response/,
    );
  });

  it("throws when a required array field is missing", async () => {
    const bad = JSON.stringify({
      pros: ["Good location"],
      // cons is missing
      risks: [],
      matchRationale: "OK",
    });
    getMockCreate().mockResolvedValue({
      choices: [{ message: { content: bad } }],
    });

    const client = new LLMClient({ apiKey: "test-key" });
    await expect(client.summariseListing(scoredListing, criteria)).rejects.toThrow(/cons/);
  });

  it("throws when matchRationale is not a string", async () => {
    const bad = JSON.stringify({
      pros: [],
      cons: [],
      risks: [],
      matchRationale: 42,
    });
    getMockCreate().mockResolvedValue({
      choices: [{ message: { content: bad } }],
    });

    const client = new LLMClient({ apiKey: "test-key" });
    await expect(client.summariseListing(scoredListing, criteria)).rejects.toThrow(
      /matchRationale/,
    );
  });

  it("passes the correct model to the OpenAI API", async () => {
    getMockCreate().mockResolvedValue({
      choices: [{ message: { content: validLLMResponse } }],
    });

    const client = new LLMClient({ apiKey: "test-key", model: "gpt-4-turbo" });
    await client.summariseListing(scoredListing, criteria);

    expect(getMockCreate()).toHaveBeenCalledWith(
      expect.objectContaining({ model: "gpt-4-turbo" }),
    );
  });
});

describe("LLMClient.summariseListings", () => {
  beforeEach(() => {
    getMockCreate().mockReset();
  });

  it("returns ScoredListingWithSummary objects for each input", async () => {
    getMockCreate().mockResolvedValue({
      choices: [{ message: { content: validLLMResponse } }],
    });

    const client = new LLMClient({ apiKey: "test-key" });
    const listings = [scoredListing, { ...scoredListing, listing: { ...scoredListing.listing, id: "mls-43" } }];
    const results = await client.summariseListings(listings, criteria);

    expect(results).toHaveLength(2);
    expect(results[0]).toHaveProperty("summary");
    expect(results[0]!.summary.listingId).toBe("mls-42");
    expect(results[1]!.summary.listingId).toBe("mls-43");
  });

  it("handles an empty listings array", async () => {
    const client = new LLMClient({ apiKey: "test-key" });
    const results = await client.summariseListings([], criteria);
    expect(results).toEqual([]);
    expect(getMockCreate()).not.toHaveBeenCalled();
  });
});
