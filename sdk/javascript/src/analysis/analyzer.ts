// Analyzes all source files of a JavaScript bot at once (statische-analyse.md, E228).
//
// The analyzer only parses; it never imports or runs the bot. On the server it runs in the
// sandbox like the bot itself (E81).
import { parse, type Program } from "acorn";

import { FileChecker } from "./checker.ts";
import { ENCODING, SYNTAX_ERROR, makeReport, type Finding, type Report } from "./report.ts";
import { loadRules, type Rules } from "./rules.ts";

/** sources maps the paths of all .js and .mjs files (relative, with /) to their contents. */
export function analyze(
  sources: ReadonlyMap<string, Uint8Array>,
  rules: Rules = loadRules(),
): Report {
  const findings: Finding[] = [];
  const paths = new Set(sources.keys());
  for (const file of [...paths].sort()) {
    const program = parseFile(file, sources.get(file) ?? new Uint8Array(), findings);
    if (program !== null) {
      findings.push(...new FileChecker(file, paths, rules).check(program));
    }
  }
  return makeReport(rules.ruleset, findings, rules.maxFindings);
}

function parseFile(file: string, content: Uint8Array, findings: Finding[]): Program | null {
  let text: string;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(content);
  } catch {
    findings.push({ file, line: null, rule: ENCODING, message: "not valid UTF-8" });
    return null;
  }
  try {
    // As Node reads a file without package.json from its syntax: an ES module (E227).
    return parse(text, { ecmaVersion: "latest", sourceType: "module", locations: true });
  } catch (error) {
    if (error instanceof RangeError) {
      findings.push({
        file,
        line: null,
        rule: SYNTAX_ERROR,
        message: "the file is nested too deeply",
      });
      return null;
    }
    if (error instanceof SyntaxError) {
      const line = (error as SyntaxError & { loc?: { line: number } }).loc?.line ?? null;
      findings.push({ file, line, rule: SYNTAX_ERROR, message: error.message });
      return null;
    }
    throw error;
  }
}
