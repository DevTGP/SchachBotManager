// The versioned rule set of the JavaScript analyzer (statische-analyse.md, E208), read from JSON.
import data from "./javascript-rules.json" with { type: "json" };

export interface Rules {
  readonly ruleset: string;
  /** Bare module names a bot may import; everything else must be a file of the upload. */
  readonly modules: ReadonlySet<string>;
  readonly forbiddenGlobals: ReadonlySet<string>;
  readonly forbiddenProperties: ReadonlySet<string>;
  /** The only properties of import.meta a bot may read. */
  readonly importMeta: ReadonlySet<string>;
  readonly maxFindings: number;
}

export function loadRules(): Rules {
  return {
    ruleset: data.ruleset,
    modules: new Set(data.modules),
    forbiddenGlobals: new Set(data.forbidden_globals),
    forbiddenProperties: new Set(data.forbidden_properties),
    importMeta: new Set(data.import_meta),
    maxFindings: data.max_findings,
  };
}
