import fs from "fs";
import path from "path";
import PDFDocument from "pdfkit";
import type {
  BuyerCriteria,
  PacketConfig,
  PacketTemplate,
  ScoredListingWithSummary,
} from "../../types/index";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const DEFAULT_BRAND_COLOR = "#1a4b8c";

/** Convert a hex colour string to an r/g/b tuple. */
function hexToRgb(hex: string): [number, number, number] {
  const clean = hex.replace("#", "");
  const bigint = parseInt(clean, 16);
  return [(bigint >> 16) & 255, (bigint >> 8) & 255, bigint & 255];
}

function scoreLabel(score: number): string {
  if (score >= 85) return "Excellent Match";
  if (score >= 70) return "Strong Match";
  if (score >= 55) return "Moderate Match";
  if (score >= 40) return "Weak Match";
  return "Poor Match";
}

// ---------------------------------------------------------------------------
// Drawing primitives
// ---------------------------------------------------------------------------

function drawHeaderBand(
  doc: PDFKit.PDFDocument,
  config: PacketConfig,
  title: string,
): void {
  const color = config.brandColor ?? DEFAULT_BRAND_COLOR;
  const [r, g, b] = hexToRgb(color);
  doc
    .rect(0, 0, doc.page.width, 80)
    .fill(`rgb(${r},${g},${b})`);

  doc
    .fillColor("white")
    .fontSize(22)
    .font("Helvetica-Bold")
    .text(title, 40, 20, { width: doc.page.width - 80 });

  doc
    .fontSize(11)
    .font("Helvetica")
    .text(`${config.agentName} · ${config.agencyName}`, 40, 50);

  doc.fillColor("black");
}

function drawSectionHeader(
  doc: PDFKit.PDFDocument,
  text: string,
  color: string,
): void {
  const [r, g, b] = hexToRgb(color);
  doc
    .moveDown(0.5)
    .rect(doc.page.margins.left, doc.y, doc.page.width - doc.page.margins.left - doc.page.margins.right, 20)
    .fill(`rgb(${r},${g},${b})`);

  doc
    .fillColor("white")
    .fontSize(12)
    .font("Helvetica-Bold")
    .text(text, doc.page.margins.left + 6, doc.y - 16);

  doc.fillColor("black").moveDown(0.5);
}

function drawBulletList(
  doc: PDFKit.PDFDocument,
  items: string[],
  bulletChar = "•",
): void {
  doc.font("Helvetica").fontSize(10);
  for (const item of items) {
    const x = doc.page.margins.left + 12;
    const width =
      doc.page.width - doc.page.margins.left - doc.page.margins.right - 12;
    doc.text(`${bulletChar}  ${item}`, x, doc.y, { width });
  }
  doc.moveDown(0.3);
}

function drawKeyValue(
  doc: PDFKit.PDFDocument,
  label: string,
  value: string,
): void {
  const x = doc.page.margins.left;
  const width =
    doc.page.width - doc.page.margins.left - doc.page.margins.right;
  doc
    .font("Helvetica-Bold")
    .fontSize(10)
    .text(`${label}: `, x, doc.y, { continued: true, width })
    .font("Helvetica")
    .text(value);
}

// ---------------------------------------------------------------------------
// Cover page
// ---------------------------------------------------------------------------

function renderCoverPage(
  doc: PDFKit.PDFDocument,
  config: PacketConfig,
  criteria: BuyerCriteria,
  count: number,
): void {
  drawHeaderBand(doc, config, "Property Analysis Packet");

  doc.moveDown(4);

  doc
    .font("Helvetica-Bold")
    .fontSize(18)
    .fillColor("black")
    .text(`Prepared for: ${criteria.clientName}`, { align: "center" });

  doc.moveDown(0.5);

  const today = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  doc
    .font("Helvetica")
    .fontSize(12)
    .text(`Date: ${today}`, { align: "center" })
    .moveDown(0.3)
    .text(`Listings reviewed: ${count}`, { align: "center" });

  doc.moveDown(2);

  const color = config.brandColor ?? DEFAULT_BRAND_COLOR;
  drawSectionHeader(doc, "Search Criteria Summary", color);

  doc.moveDown(0.3);
  doc.font("Helvetica").fontSize(10);

  if (criteria.maxBudget) {
    drawKeyValue(
      doc,
      "Budget",
      criteria.minBudget
        ? `$${criteria.minBudget.toLocaleString()} – $${criteria.maxBudget.toLocaleString()}`
        : `Up to $${criteria.maxBudget.toLocaleString()}`,
    );
  }
  if (criteria.minBedrooms !== undefined)
    drawKeyValue(doc, "Min. Bedrooms", String(criteria.minBedrooms));
  if (criteria.minBathrooms !== undefined)
    drawKeyValue(doc, "Min. Bathrooms", String(criteria.minBathrooms));
  if (criteria.minSquareFeet !== undefined)
    drawKeyValue(doc, "Min. Sq Ft", criteria.minSquareFeet.toLocaleString());
  if (criteria.preferredCities?.length)
    drawKeyValue(doc, "Preferred Cities", criteria.preferredCities.join(", "));
  if (criteria.mustHaveFeatures?.length)
    drawKeyValue(doc, "Must-Have Features", criteria.mustHaveFeatures.join(", "));
  if (criteria.niceToHaveFeatures?.length)
    drawKeyValue(doc, "Nice-to-Have", criteria.niceToHaveFeatures.join(", "));
  if (criteria.dealbreakers?.length)
    drawKeyValue(doc, "Dealbreakers", criteria.dealbreakers.join(", "));
  if (criteria.freeformNotes)
    drawKeyValue(doc, "Additional Notes", criteria.freeformNotes);
}

// ---------------------------------------------------------------------------
// Listing page
// ---------------------------------------------------------------------------

function renderListingPage(
  doc: PDFKit.PDFDocument,
  config: PacketConfig,
  item: ScoredListingWithSummary,
  index: number,
): void {
  doc.addPage();

  const { listing, overallScore, breakdown, summary } = item;
  const color = config.brandColor ?? DEFAULT_BRAND_COLOR;

  // Mini header
  drawHeaderBand(
    doc,
    config,
    `Listing ${index + 1}: ${listing.address}, ${listing.city}`,
  );

  doc.moveDown(3);

  // Key stats row
  const statsY = doc.y;
  doc.font("Helvetica-Bold").fontSize(10).fillColor("black");

  const stats: [string, string][] = [
    ["List Price", `$${listing.listPrice.toLocaleString()}`],
    ["Beds / Baths", `${listing.bedrooms} bd / ${listing.bathrooms} ba`],
    ["Sq Ft", listing.squareFeet.toLocaleString()],
    ...(listing.yearBuilt ? ([["Year Built", String(listing.yearBuilt)]] as [string, string][]) : []),
    ...(listing.daysOnMarket !== undefined
      ? ([["Days on Market", String(listing.daysOnMarket)]] as [string, string][])
      : []),
  ];

  const colWidth = (doc.page.width - doc.page.margins.left - doc.page.margins.right) / stats.length;
  stats.forEach(([label, value], i) => {
    const x = doc.page.margins.left + i * colWidth;
    doc
      .font("Helvetica-Bold")
      .fontSize(9)
      .fillColor("grey")
      .text(label.toUpperCase(), x, statsY, { width: colWidth - 4 });
    doc
      .font("Helvetica-Bold")
      .fontSize(12)
      .fillColor("black")
      .text(value, x, statsY + 14, { width: colWidth - 4 });
  });

  // Overall score badge
  const badgeX = doc.page.width - doc.page.margins.right - 80;
  const [r, g, b] = hexToRgb(color);
  doc.rect(badgeX, statsY - 2, 80, 44).fill(`rgb(${r},${g},${b})`);
  doc
    .fillColor("white")
    .font("Helvetica-Bold")
    .fontSize(22)
    .text(`${overallScore}`, badgeX, statsY + 2, { width: 80, align: "center" });
  doc
    .fontSize(8)
    .text(scoreLabel(overallScore), badgeX, statsY + 28, { width: 80, align: "center" });
  doc.fillColor("black");

  doc.y = statsY + 52;
  doc.moveDown(0.5);

  // Match rationale
  drawSectionHeader(doc, "Match Rationale", color);
  doc.moveDown(0.3);
  doc
    .font("Helvetica")
    .fontSize(10)
    .text(summary.matchRationale, doc.page.margins.left, doc.y, {
      width: doc.page.width - doc.page.margins.left - doc.page.margins.right,
    });
  doc.moveDown(0.5);

  // Pros
  drawSectionHeader(doc, "Pros", color);
  doc.moveDown(0.3);
  drawBulletList(doc, summary.pros.length > 0 ? summary.pros : ["None identified."], "✓");

  // Cons
  drawSectionHeader(doc, "Cons", color);
  doc.moveDown(0.3);
  drawBulletList(doc, summary.cons.length > 0 ? summary.cons : ["None identified."], "✗");

  // Risks
  drawSectionHeader(doc, "Risks to Investigate", color);
  doc.moveDown(0.3);
  drawBulletList(doc, summary.risks.length > 0 ? summary.risks : ["None identified."], "⚠");

  // Score breakdown table
  drawSectionHeader(doc, "Score Breakdown", color);
  doc.moveDown(0.3);

  const tableX = doc.page.margins.left;
  const tableWidth =
    doc.page.width - doc.page.margins.left - doc.page.margins.right;
  const colWidths = [tableWidth * 0.35, tableWidth * 0.15, tableWidth * 0.5];

  // Table header
  doc.font("Helvetica-Bold").fontSize(9).fillColor("grey");
  ["Category", "Score", "Notes"].forEach((h, i) => {
    const x = tableX + colWidths.slice(0, i).reduce((a, c) => a + c, 0);
    doc.text(h.toUpperCase(), x, doc.y, { width: colWidths[i]! - 4 });
  });
  doc.moveDown(0.3);
  doc.moveTo(tableX, doc.y).lineTo(tableX + tableWidth, doc.y).stroke();
  doc.moveDown(0.2);

  // Table rows
  doc.fillColor("black").fontSize(9).font("Helvetica");
  for (const row of breakdown) {
    const rowY = doc.y;
    const cols = [row.category, String(row.score), row.notes];
    cols.forEach((text, i) => {
      const x = tableX + colWidths.slice(0, i).reduce((a, c) => a + c, 0);
      doc.text(text, x, rowY, { width: (colWidths[i] ?? 0) - 4 });
    });
    doc.y = Math.max(doc.y, rowY + 14);
    doc.moveDown(0.2);
  }
}

// ---------------------------------------------------------------------------
// Default template
// ---------------------------------------------------------------------------

export const defaultTemplate: PacketTemplate = {
  name: "default",

  async render(
    config: PacketConfig,
    criteria: BuyerCriteria,
    listings: ScoredListingWithSummary[],
  ): Promise<string> {
    return new Promise((resolve, reject) => {
      const outputDir = path.dirname(config.outputPath);
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }

      const doc = new PDFDocument({ margin: 40, size: "LETTER" });
      const stream = fs.createWriteStream(config.outputPath);

      doc.pipe(stream);

      // Cover page
      renderCoverPage(doc, config, criteria, listings.length);

      // One page per listing
      listings.forEach((item, i) => renderListingPage(doc, config, item, i));

      doc.end();

      stream.on("finish", () => resolve(config.outputPath));
      stream.on("error", reject);
    });
  },
};
