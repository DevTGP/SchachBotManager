// What a folder selection uploads (verifikation.md, E207): the source files of the language
// outside data/ and files directly in data/. Everything else, such as .vscode/, README.md or
// __pycache__/, stays at home; node_modules/ is left out without a word, since it holds thousands
// of files. The API checks the remaining rules and names the file to blame.

export const DATA_DIR = "data";
export const MAX_FILES = 100;
export const MAX_BYTES = 1024 * 1024;
const SKIPPED_FOLDERS = ["__pycache__", "node_modules"];

/** The languages of an upload so far; the server runs no others yet. */
export const UPLOAD_LANGUAGES = ["python", "javascript"] as const;
export type UploadLanguage = (typeof UPLOAD_LANGUAGES)[number];

interface LanguageRules {
  suffixes: readonly string[];
  /** The entry the template starts with. */
  defaultEntry: string;
}

export const LANGUAGE_RULES: Record<UploadLanguage, LanguageRules> = {
  python: { suffixes: [".py"], defaultEntry: "bot.py" },
  javascript: { suffixes: [".js", ".mjs"], defaultEntry: "bot.js" },
};

/** The source suffixes for texts and the file input, e.g. ".js, .mjs". */
export function sourceSuffixes(language: UploadLanguage): string {
  return LANGUAGE_RULES[language].suffixes.join(", ");
}

function isSource(path: string, language: UploadLanguage): boolean {
  return LANGUAGE_RULES[language].suffixes.some((suffix) => path.endsWith(suffix));
}

export type FileKind = "source" | "data";

export interface PickedFile {
  path: string;
  kind: FileKind;
  file: File;
}

export interface Selection {
  files: PickedFile[];
  /** Paths left out, in the order of the selection. */
  ignored: string[];
}

/** A path without the chosen folder in front; a plain name stays as it is. */
export function insideFolder(path: string): string {
  const parts = path.split("/");
  return parts.length > 1 ? parts.slice(1).join("/") : path;
}

/** The path inside the chosen folder, or the plain name of a single file. */
export function relativePath(file: File): string {
  // Some environments, such as jsdom, do not know the attribute at all.
  const relative: string | undefined = file.webkitRelativePath;
  return relative ? insideFolder(relative) : file.name;
}

function skipped(path: string): boolean {
  return path.split("/").includes("node_modules");
}

export function fileKind(path: string, language: UploadLanguage): FileKind | undefined {
  const parts = path.split("/");
  if (parts.some((part) => part.startsWith(".") || SKIPPED_FOLDERS.includes(part))) {
    return undefined;
  }
  if (parts[0] === DATA_DIR) return parts.length === 2 ? "data" : undefined;
  return isSource(path, language) ? "source" : undefined;
}

/** A file and its path inside the chosen or dropped folder. */
export interface FoundFile {
  path: string;
  file: File;
}

export function foundFiles(files: Iterable<File>): FoundFile[] {
  return Array.from(files, (file) => ({ path: relativePath(file), file }));
}

export function selectFiles(files: Iterable<File>, language: UploadLanguage): Selection {
  return selectPaths(foundFiles(files), language);
}

export function selectPaths(found: Iterable<FoundFile>, language: UploadLanguage): Selection {
  const selection: Selection = { files: [], ignored: [] };
  for (const { path, file } of found) {
    if (skipped(path)) continue;
    const kind = fileKind(path, language);
    if (kind) selection.files.push({ path, kind, file });
    else selection.ignored.push(path);
  }
  selection.files.sort((a, b) => a.path.localeCompare(b.path));
  return selection;
}

/** The translation key of a broken limit, checked before anything is sent. */
export function selectionProblem(files: PickedFile[]): string | undefined {
  if (files.length === 0) return "upload.noFiles";
  for (const kind of ["source", "data"] as const) {
    const ofKind = files.filter((file) => file.kind === kind);
    if (ofKind.length > MAX_FILES) return "upload.tooManyFiles";
    if (ofKind.reduce((sum, file) => sum + file.file.size, 0) > MAX_BYTES) return "upload.tooLarge";
  }
  return undefined;
}

/** Sources in the top folder; bot.py or bot.js first, since the template starts there. */
export function entryCandidates(files: PickedFile[], language: UploadLanguage): string[] {
  const { defaultEntry } = LANGUAGE_RULES[language];
  const top = files
    .filter((file) => file.kind === "source" && !file.path.includes("/"))
    .map((file) => file.path)
    .sort();
  return top.includes(defaultEntry)
    ? [defaultEntry, ...top.filter((path) => path !== defaultEntry)]
    : top;
}

/** The only language with sources among the files, if there is one. */
export function detectLanguage(found: FoundFile[]): UploadLanguage | undefined {
  const languages = UPLOAD_LANGUAGES.filter((language) =>
    found.some(({ path }) => fileKind(path, language) === "source"),
  );
  return languages.length === 1 ? languages[0] : undefined;
}
