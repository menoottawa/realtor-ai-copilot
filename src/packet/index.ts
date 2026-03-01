import type {
  BuyerCriteria,
  PacketConfig,
  PacketTemplate,
  ScoredListingWithSummary,
} from "../types/index";
import { defaultTemplate } from "./templates/default";

export type { PacketTemplate };

// ---------------------------------------------------------------------------
// Template registry
// ---------------------------------------------------------------------------

const templateRegistry = new Map<string, PacketTemplate>();
templateRegistry.set(defaultTemplate.name, defaultTemplate);

/**
 * Register a custom packet template under the given name.
 * A registered template can be selected via {@link PacketBuilderOptions.template}.
 */
export function registerTemplate(template: PacketTemplate): void {
  templateRegistry.set(template.name, template);
}

// ---------------------------------------------------------------------------
// Packet builder
// ---------------------------------------------------------------------------

export interface PacketBuilderOptions {
  /**
   * Name of the registered template to use.
   * Defaults to `"default"`.
   */
  template?: string;
}

export class PacketBuilder {
  private readonly template: PacketTemplate;

  constructor(options: PacketBuilderOptions = {}) {
    const name = options.template ?? "default";
    const tpl = templateRegistry.get(name);
    if (!tpl) {
      throw new Error(
        `Packet template "${name}" is not registered. ` +
          `Available templates: ${[...templateRegistry.keys()].join(", ")}.`,
      );
    }
    this.template = tpl;
  }

  /**
   * Build a branded PDF packet and write it to `config.outputPath`.
   * @returns Resolves with the absolute path to the generated PDF.
   */
  async build(
    config: PacketConfig,
    criteria: BuyerCriteria,
    listings: ScoredListingWithSummary[],
  ): Promise<string> {
    return this.template.render(config, criteria, listings);
  }
}
