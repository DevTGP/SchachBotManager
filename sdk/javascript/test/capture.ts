// Collects the lines of Log during a test instead of writing them to stderr.
import { after, before, beforeEach } from "node:test";

import { configure, setOutput, setPly } from "../src/log.ts";
import { INFO } from "../src/constants.ts";

/** The lines written in the current test; registers its hooks in the calling file. */
export function captureLog(): string[] {
  const lines: string[] = [];
  before(() => setOutput((line) => lines.push(line)));
  beforeEach(() => {
    lines.length = 0;
    configure(INFO, undefined);
    setPly(undefined);
  });
  after(() => setOutput(undefined));
  return lines;
}
