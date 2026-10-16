// sbm-check: checks a bot folder against the rules of the server before the upload (E228).
//
// Exit codes: 0 no findings, 1 findings, 2 invalid arguments.
import { statSync } from "node:fs";
import { parseArgs } from "node:util";

import { checkProject, selectFiles } from "./project.ts";
import { findingText, isOk, reportJson } from "./report.ts";
import { DEFAULT_ENTRY } from "./upload.ts";

export const EXIT_FINDINGS = 1;
export const EXIT_USAGE = 2;

const USAGE = `usage: sbm-check [folder] [--entry FILE] [--exclude GLOB]... [--json]

Checks a JavaScript bot as the server does after an upload: allowed files, sizes, imports and
forbidden names. The upload takes the .js and .mjs files outside hidden folders and
node_modules, and the files directly in data/.

  folder          the bot's folder (default .)
  --entry FILE    the main file (default ${DEFAULT_ENTRY})
  --exclude GLOB  leaves out matching paths, e.g. 'tests/*'; can be given more than once
  --json          prints the report as JSON
  --help          shows this text`;

export interface Output {
  out(line: string): void;
  err(line: string): void;
}

const CONSOLE: Output = {
  out: (line) => console.log(line),
  err: (line) => console.error(line),
};

export function main(argv: readonly string[], output: Output = CONSOLE): number {
  let parsed;
  try {
    parsed = parseArgs({
      args: [...argv],
      allowPositionals: true,
      options: {
        entry: { type: "string", default: DEFAULT_ENTRY },
        exclude: { type: "string", multiple: true, default: [] },
        json: { type: "boolean", default: false },
        help: { type: "boolean", default: false },
      },
    });
  } catch (error) {
    return usageError(output, (error as Error).message);
  }
  const { values, positionals } = parsed;
  if (values.help) {
    output.out(USAGE);
    return 0;
  }
  if (positionals.length > 1) {
    return usageError(output, "only one folder can be given");
  }
  const folder = positionals[0] ?? ".";
  if (!statSync(folder, { throwIfNoEntry: false })?.isDirectory()) {
    return usageError(output, `${folder} is not a folder`);
  }
  const selection = selectFiles(folder, values.exclude);
  const report = checkProject(selection, values.entry);
  if (values.json) {
    output.out(JSON.stringify(reportJson(report), null, 2));
  } else {
    if (selection.ignored.length > 0) {
      output.err(`ignored: ${selection.ignored.join(", ")}`);
    }
    for (const finding of report.findings) {
      output.out(findingText(finding));
    }
    if (report.truncated) {
      output.out("… more findings not shown");
    }
    const count = selection.files.size;
    output.out(
      isOk(report)
        ? `sbm-check: OK, ${count} files checked (${report.ruleset})`
        : `sbm-check: ${report.findings.length} problems in ${count} files (${report.ruleset})`,
    );
  }
  return isOk(report) ? 0 : EXIT_FINDINGS;
}

function usageError(output: Output, message: string): number {
  output.err(USAGE.split("\n")[0] ?? "");
  output.err(`sbm-check: error: ${message}`);
  return EXIT_USAGE;
}
