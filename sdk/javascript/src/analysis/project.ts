// Checks a bot folder as it would be uploaded: which files count, the upload rules, the analysis.
//
// sbm-check and the runner use it alike; in the runner the folder holds exactly the uploaded files.
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

import { analyze } from "./analyzer.ts";
import { UPLOAD, makeReport, type Finding, type Report } from "./report.ts";
import { loadRules, type Rules } from "./rules.ts";
import { DATA_DIR, RESERVED_FOLDER, SOURCE, UploadError, checkUpload, isSource } from "./upload.ts";

/** files maps upload paths to files on disk; ignored lists what an upload would leave out. */
export interface Selection {
  readonly files: ReadonlyMap<string, string>;
  readonly ignored: readonly string[];
}

/** .js and .mjs files outside hidden folders and node_modules, and the files directly in data/. */
export function selectFiles(root: string, excludes: readonly string[] = []): Selection {
  const patterns = excludes.map(globPattern);
  const excluded = (relative: string) => patterns.some((pattern) => pattern.test(relative));
  const files = new Map<string, string>();
  const ignored: string[] = [];
  const folders = [""];
  for (let prefix = folders.shift(); prefix !== undefined; prefix = folders.shift()) {
    const entries = readdirSync(path.join(root, prefix), { withFileTypes: true });
    for (const entry of entries.sort((a, b) => compare(a.name, b.name))) {
      const relative = `${prefix}${entry.name}`;
      if (entry.isDirectory()) {
        if (!entry.name.startsWith(".") && entry.name !== RESERVED_FOLDER && !excluded(relative)) {
          folders.push(`${relative}/`);
        }
        continue;
      }
      if (entry.name.startsWith(".") || excluded(relative)) {
        continue;
      }
      const inData = relative.startsWith(`${DATA_DIR}/`);
      const wanted = inData ? relative.split("/").length === 2 : isSource(entry.name);
      // A symbolic link is no Dirent file, so links stay out.
      if (wanted && entry.isFile()) {
        files.set(relative, path.join(root, relative));
      } else {
        ignored.push(relative);
      }
    }
  }
  return { files, ignored };
}

function compare(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

/** * matches any text, also /, and ? one character, like fnmatch in sbm-check for Python. */
function globPattern(glob: string): RegExp {
  const parts = [...glob].map((char) =>
    char === "*" ? ".*" : char === "?" ? "." : char.replace(/[\\^$.|+()[\]{}]/g, "\\$&"),
  );
  return new RegExp(`^${parts.join("")}$`, "s");
}

export function checkProject(
  selection: Selection,
  entry: string,
  rules: Rules = loadRules(),
): Report {
  const findings: Finding[] = [];
  let sources: string[];
  try {
    const sizes = [...selection.files].map(
      ([relative, file]) => [relative, statSync(file).size] as const,
    );
    sources = checkUpload(sizes, entry)
      .filter((file) => file.kind === SOURCE)
      .map((file) => file.path);
  } catch (error) {
    if (!(error instanceof UploadError)) {
      throw error;
    }
    findings.push({ file: error.path ?? entry, line: null, rule: UPLOAD, message: error.message });
    sources = [...selection.files.keys()].filter(
      (relative) => isSource(relative) && !relative.startsWith(`${DATA_DIR}/`),
    );
  }
  const contents = new Map(sources.map((relative) => [relative, readSource(selection, relative)]));
  const report = analyze(contents, rules);
  return makeReport(rules.ruleset, [...findings, ...report.findings], rules.maxFindings);
}

function readSource(selection: Selection, relative: string): Uint8Array {
  const content = readFileSync(selection.files.get(relative) ?? relative);
  return new Uint8Array(content.buffer, content.byteOffset, content.byteLength);
}
