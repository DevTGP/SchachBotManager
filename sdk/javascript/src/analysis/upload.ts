// What an upload of a JavaScript bot may contain (verifikation.md, E207); the same rules as
// sbm.analysis.upload of the Python SDK, which the web API and the runner apply.
//
// Paths are relative and use /. Source files are .js and .mjs files outside data/; data files
// lie directly in data/, since loadData only takes plain names (E62). No part of a path may be
// node_modules: such a folder would come before the SDK when Node resolves "schachbotmanager".

export const SOURCE = "source";
export const DATA = "data";
export const DATA_DIR = "data";
export const SOURCE_SUFFIXES = [".js", ".mjs"] as const;
export const RESERVED_FOLDER = "node_modules";
export const MAX_SOURCE_FILES = 100;
export const MAX_SOURCE_BYTES = 1024 * 1024;
export const MAX_DATA_FILES = 100;
// E30: data files up to 1 MB in all.
export const MAX_DATA_BYTES = 1024 * 1024;
export const MAX_DEPTH = 8;
export const MAX_PATH_LENGTH = 200;
export const DEFAULT_ENTRY = "bot.js";
const COMPONENT = /^[A-Za-z0-9_][A-Za-z0-9_.-]*$/;

export type FileKind = typeof SOURCE | typeof DATA;

/** The upload breaks a rule; path names the file, if one is to blame. */
export class UploadError extends Error {
  readonly path: string | undefined;

  constructor(message: string, path?: string) {
    super(message);
    this.name = "UploadError";
    this.path = path;
  }
}

export interface UploadFile {
  readonly path: string;
  readonly kind: FileKind;
  readonly size: number;
}

export function isSource(path: string): boolean {
  return SOURCE_SUFFIXES.some((suffix) => path.endsWith(suffix));
}

/** SOURCE or DATA; throws UploadError for a path an upload may not contain. */
export function fileKind(path: string): FileKind {
  if (path.length > MAX_PATH_LENGTH) {
    throw new UploadError(`the path is longer than ${MAX_PATH_LENGTH} characters`, path);
  }
  const parts = path.split("/");
  if (parts.length > MAX_DEPTH) {
    throw new UploadError(`the path is deeper than ${MAX_DEPTH} levels`, path);
  }
  for (const part of parts) {
    if (!COMPONENT.test(part)) {
      throw new UploadError(
        "every part of a path must start with a letter, digit or _ and contain only " +
          "letters, digits, _, . and -",
        path,
      );
    }
    if (part.toLowerCase() === RESERVED_FOLDER) {
      throw new UploadError(`no part of a path may be ${RESERVED_FOLDER}`, path);
    }
  }
  if (parts[0] === DATA_DIR) {
    if (parts.length !== 2) {
      throw new UploadError(`data files must lie directly in ${DATA_DIR}/`, path);
    }
    return DATA;
  }
  if (!isSource(path)) {
    throw new UploadError(
      `only .js and .mjs files and data files in ${DATA_DIR}/ are allowed`,
      path,
    );
  }
  return SOURCE;
}

/** Checks paths, sizes and the entry file; files are [path, size in bytes]. */
export function checkUpload(
  files: Iterable<readonly [string, number]>,
  entry: string,
): UploadFile[] {
  const checked = [...files].map(([path, size]) => ({ path, kind: fileKind(path), size }));
  checkUnique(checked);
  const limits = [
    [SOURCE, MAX_SOURCE_FILES, MAX_SOURCE_BYTES],
    [DATA, MAX_DATA_FILES, MAX_DATA_BYTES],
  ] as const;
  for (const [kind, maxFiles, maxBytes] of limits) {
    const ofKind = checked.filter((file) => file.kind === kind);
    if (ofKind.length > maxFiles) {
      throw new UploadError(`more than ${maxFiles} ${kind} files`);
    }
    if (ofKind.reduce((sum, file) => sum + file.size, 0) > maxBytes) {
      throw new UploadError(`the ${kind} files are larger than ${maxBytes} bytes in all`);
    }
  }
  if (entry.includes("/") || !isSource(entry)) {
    throw new UploadError("the entry file must be a .js or .mjs file in the top folder", entry);
  }
  if (!checked.some((file) => file.path === entry && file.kind === SOURCE)) {
    throw new UploadError("the entry file is missing", entry);
  }
  return checked;
}

/** Also across case, since a bot written on Windows or macOS must not depend on it. */
function checkUnique(files: readonly UploadFile[]): void {
  const paths = new Set<string>();
  const folders = new Set<string>();
  for (const file of files) {
    const key = file.path.toLowerCase();
    if (paths.has(key) || folders.has(key)) {
      throw new UploadError("the path occurs twice", file.path);
    }
    paths.add(key);
    const parts = key.split("/");
    for (let end = 1; end < parts.length; end += 1) {
      folders.add(parts.slice(0, end).join("/"));
    }
  }
  const clashes = [...paths].filter((path) => folders.has(path)).sort();
  if (clashes.length > 0) {
    throw new UploadError("a file has the same name as a folder", clashes[0]);
  }
}
