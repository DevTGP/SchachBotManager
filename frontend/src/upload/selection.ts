// What a folder selection uploads (verifikation.md): .py files outside data/ and files directly
// in data/. Everything else, such as .vscode/, README.md or __pycache__/, stays at home; the API
// checks the remaining rules and names the file to blame.

export const DATA_DIR = "data";
export const DEFAULT_ENTRY = "bot.py";
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

export function fileKind(path: string): FileKind | undefined {
  const parts = path.split("/");
  if (parts.some((part) => part.startsWith(".") || part === "__pycache__")) return undefined;
  if (parts[0] === DATA_DIR) return parts.length === 2 ? "data" : undefined;
  return path.endsWith(".py") ? "source" : undefined;
}

/** A file and its path inside the chosen or dropped folder. */
export interface FoundFile {
  path: string;
  file: File;
}

export function selectFiles(files: Iterable<File>): Selection {
  return selectPaths(Array.from(files, (file) => ({ path: relativePath(file), file })));
}

export function selectPaths(found: Iterable<FoundFile>): Selection {
  const selection: Selection = { files: [], ignored: [] };
  for (const { path, file } of found) {
    const kind = fileKind(path);
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

/** .py files in the top folder; bot.py first, since the template starts there. */
export function entryCandidates(files: PickedFile[]): string[] {
  const top = files
    .filter((file) => file.kind === "source" && !file.path.includes("/"))
    .map((file) => file.path)
    .sort();
  return top.includes(DEFAULT_ENTRY)
    ? [DEFAULT_ENTRY, ...top.filter((path) => path !== DEFAULT_ENTRY)]
    : top;
}
