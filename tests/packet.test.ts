import fs from "fs";
import path from "path";
import { PacketBuilder, registerTemplate } from "../src/packet/index";
import type {
  BuyerCriteria,
  PacketConfig,
  PacketTemplate,
  ScoredListingWithSummary,
} from "../src/types/index";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const config: PacketConfig = {
  agentName: "Jane Realtor",
  agencyName: "Acme Realty",
  outputPath: "/tmp/realtor-ai-copilot-test/packet-test.pdf",
  brandColor: "#2d6a4f",
};

const criteria: BuyerCriteria = {
  clientName: "Carol White",
  maxBudget: 750_000,
  minBedrooms: 3,
  preferredCities: ["Ottawa"],
};

const listing: ScoredListingWithSummary = {
  listing: {
    id: "mls-99",
    address: "99 Elm Rd",
    city: "Ottawa",
    state: "ON",
    zipCode: "K1N 5T8",
    listPrice: 699_000,
    bedrooms: 4,
    bathrooms: 2,
    squareFeet: 2100,
    yearBuilt: 2005,
    features: ["garage", "central air"],
    description: "Well-maintained Ottawa home.",
    daysOnMarket: 5,
  },
  overallScore: 90,
  breakdown: [
    { category: "Budget", score: 92, weight: 0.3, notes: "Within budget." },
    { category: "Location", score: 100, weight: 0.2, notes: "Preferred city." },
  ],
  summary: {
    listingId: "mls-99",
    pros: ["Spacious backyard", "Renovated kitchen"],
    cons: ["Dated bathrooms"],
    risks: ["Verify HVAC age"],
    matchRationale:
      "This property is a strong match for Carol White. Budget, location, and bedroom count all align with stated preferences.",
  },
};

// ---------------------------------------------------------------------------
// PacketBuilder + default template
// ---------------------------------------------------------------------------

describe("PacketBuilder", () => {
  afterAll(() => {
    // Clean up generated PDF
    try {
      fs.unlinkSync(config.outputPath);
      fs.rmdirSync(path.dirname(config.outputPath));
    } catch {
      // ignore
    }
  });

  it("throws when an unknown template is requested", () => {
    expect(() => new PacketBuilder({ template: "non-existent" })).toThrow(
      /not registered/,
    );
  });

  it("uses the default template when no template option is specified", () => {
    expect(() => new PacketBuilder()).not.toThrow();
  });

  it("generates a PDF file at the specified outputPath", async () => {
    const builder = new PacketBuilder();
    const resultPath = await builder.build(config, criteria, [listing]);

    expect(resultPath).toBe(config.outputPath);
    expect(fs.existsSync(config.outputPath)).toBe(true);

    const stat = fs.statSync(config.outputPath);
    expect(stat.size).toBeGreaterThan(1000); // non-trivial PDF
  });

  it("creates the output directory if it does not exist", async () => {
    const uniquePath = `/tmp/realtor-ai-copilot-test-nested/${Date.now()}/packet.pdf`;
    const nestedConfig: PacketConfig = { ...config, outputPath: uniquePath };

    const builder = new PacketBuilder();
    await builder.build(nestedConfig, criteria, [listing]);

    expect(fs.existsSync(uniquePath)).toBe(true);
    fs.unlinkSync(uniquePath);
    fs.rmdirSync(path.dirname(uniquePath));
    fs.rmdirSync(path.dirname(path.dirname(uniquePath)));
  });

  it("handles an empty listings array (cover page only)", async () => {
    const emptyPath = `/tmp/realtor-ai-copilot-empty-${Date.now()}.pdf`;
    const emptyConfig: PacketConfig = { ...config, outputPath: emptyPath };

    const builder = new PacketBuilder();
    const result = await builder.build(emptyConfig, criteria, []);

    expect(fs.existsSync(emptyPath)).toBe(true);
    fs.unlinkSync(emptyPath);
  });
});

// ---------------------------------------------------------------------------
// registerTemplate
// ---------------------------------------------------------------------------

describe("registerTemplate", () => {
  it("allows registering and using a custom template", async () => {
    const rendered: string[] = [];

    const customTemplate: PacketTemplate = {
      name: "custom-test",
      async render(cfg, _crit, _listings): Promise<string> {
        rendered.push(cfg.agentName);
        return cfg.outputPath;
      },
    };

    registerTemplate(customTemplate);

    const builder = new PacketBuilder({ template: "custom-test" });
    const result = await builder.build(config, criteria, [listing]);

    expect(rendered).toContain("Jane Realtor");
    expect(result).toBe(config.outputPath);
  });
});
