// What a folder selection uploads (verifikation.md, E227): the sources of the language (.py,
// .js/.mjs or .cs) outside data/ and files directly in data/. Everything else, such as .vscode/,
// README.md, __pycache__/, node_modules/ or bin/ and obj/ of a C# build, stays at home; the API
// checks the remaining rules and names the file to blame.

export const DATA_DIR = "data";
export const LANGUAGES = ["python", "javascript", "csharp"] as const;
export type Language = (typeof LANGUAGES)[number];
const SUFFIXES: Record<Language, string[]> = {
  python: [".py"],
  javascript: [".js", ".mjs"],
  csharp: [".cs"],
};
/** The entry the template starts with; a C# bot has none (E203). */
const DEFAULT_ENTRY: Record<Language, string | undefined> = {
  python: "bot.py",
  javascript: "bot.js",
  csharp: undefined,
};
/** Folders of a local build, which hold nothing to upload. */
const SKIPPED: Record<Language, string[]> = {
  python: ["__pycache__"],
  javascript: [],
  csharp: ["bin", "obj"],
};
/** node_modules/ holds thousands of files, often with sources of other languages. */
const SKIPPED_EVERYWHERE = ["node_modules"];
/** The server writes the entry of a C# bot itself (E203), so the template's one stays home. */
const CSHARP_ENTRY_FILE = "Program.cs";
export const MAX_FILES = 100;
export const MAX_BYTES = 1024 * 1024;

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

/** Whether a folder of the selection is skipped as a whole, also while reading a drop. */
export function skippedFolder(name: string, language: Language): boolean {
  return (
    name.startsWith(".") || SKIPPED_EVERYWHERE.includes(name) || SKIPPED[language].includes(name)
  );
}

export function fileKind(path: string, language: Language = "python"): FileKind | undefined {
  const parts = path.split("/");
  if (parts.some((part) => part.startsWith("."))) return undefined;
  if (parts.slice(0, -1).some((part) => skippedFolder(part, language))) return undefined;
  if (parts[0] === DATA_DIR) return parts.length === 2 ? "data" : undefined;
  if (language === "csharp" && path === CSHARP_ENTRY_FILE) return undefined;
  return isSource(path, language) ? "source" : undefined;
}

function isSource(path: string, language: Language): boolean {
  return SUFFIXES[language].some((suffix) => path.endsWith(suffix));
}

/** The source suffixes for texts and the file input, e.g. ".js, .mjs". */
export function sourceSuffixes(language: Language): string {
  return SUFFIXES[language].join(", ");
}

/** A file and its path inside the chosen or dropped folder. */
export interface FoundFile {
  path: string;
  file: File;
}

export function foundFiles(files: Iterable<File>): FoundFile[] {
  return Array.from(files, (file) => ({ path: relativePath(file), file }));
}

export function selectFiles(files: Iterable<File>, language: Language = "python"): Selection {
  return selectPaths(foundFiles(files), language);
}

export function selectPaths(found: Iterable<FoundFile>, language: Language = "python"): Selection {
  const selection: Selection = { files: [], ignored: [] };
  for (const { path, file } of found) {
    const kind = fileKind(path, language);
    if (kind) selection.files.push({ path, kind, file });
    else {
      const ignored = ignoredPath(path, language);
      if (!selection.ignored.includes(ignored)) selection.ignored.push(ignored);
    }
  }
  selection.files.sort((a, b) => a.path.localeCompare(b.path));
  return selection;
}

/** A file in a skipped folder is listed as that folder, such as obj/ with its many files. */
function ignoredPath(path: string, language: Language): string {
  const parts = path.split("/");
  const folder = parts.slice(0, -1).findIndex((part) => skippedFolder(part, language));
  return folder < 0 ? path : `${parts.slice(0, folder + 1).join("/")}/`;
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
export function entryCandidates(files: PickedFile[], language: Language = "python"): string[] {
  const defaultEntry = DEFAULT_ENTRY[language];
  const top = files
    .filter((file) => file.kind === "source" && !file.path.includes("/"))
    .map((file) => file.path)
    .sort();
  return defaultEntry && top.includes(defaultEntry)
    ? [defaultEntry, ...top.filter((path) => path !== defaultEntry)]
    : top;
}

/** The only language with sources among the files, if there is one. */
export function detectLanguage(found: FoundFile[]): Language | undefined {
  const languages = LANGUAGES.filter((language) =>
    found.some(({ path }) => fileKind(path, language) === "source"),
  );
  return languages.length === 1 ? languages[0] : undefined;
}
