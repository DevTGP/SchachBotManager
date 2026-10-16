// Findings and the report of an analysis; the JSON form is what the runner reads (E90, E208).

export const UPLOAD = "upload";
export const ENCODING = "encoding";
export const SYNTAX_ERROR = "syntax_error";
export const NOT_MODULE = "not_module";
export const IMPORT_NOT_ALLOWED = "import_not_allowed";
export const DYNAMIC_IMPORT = "dynamic_import";
export const IMPORT_META = "import_meta";
export const FORBIDDEN_NAME = "forbidden_name";
export const FORBIDDEN_PROPERTY = "forbidden_property";

export interface Finding {
  readonly file: string;
  readonly line: number | null;
  readonly rule: string;
  readonly message: string;
}

export interface Report {
  readonly ruleset: string;
  readonly findings: readonly Finding[];
  readonly truncated: boolean;
}

export function isOk(report: Report): boolean {
  return report.findings.length === 0;
}

export function reportJson(report: Report): object {
  return {
    ruleset: report.ruleset,
    ok: isOk(report),
    truncated: report.truncated,
    findings: report.findings.map(({ rule, file, line, message }) => ({
      rule,
      file,
      line,
      message,
    })),
  };
}

export function findingText(finding: Finding): string {
  const place = finding.line === null ? finding.file : `${finding.file}:${finding.line}`;
  return `${place}: ${finding.rule}: ${finding.message}`;
}

function compare(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

/** Sorted by file and line without duplicates, at most limit findings. */
export function makeReport(ruleset: string, findings: readonly Finding[], limit: number): Report {
  const unique = new Map<string, Finding>();
  for (const finding of findings) {
    unique.set(
      JSON.stringify([finding.file, finding.line, finding.rule, finding.message]),
      finding,
    );
  }
  const ordered = [...unique.values()].sort(
    (a, b) =>
      compare(a.file, b.file) ||
      (a.line ?? 0) - (b.line ?? 0) ||
      compare(a.rule, b.rule) ||
      compare(a.message, b.message),
  );
  return {
    ruleset,
    findings: ordered.slice(0, limit),
    truncated: ordered.length > limit,
  };
}
