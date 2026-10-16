// The files of a drop on the upload area (G16). A dropped folder is read through the entries API;
// hidden folders, __pycache__ and node_modules are skipped on the way, since nothing in them is
// uploaded.

import { type FoundFile, insideFolder } from "./selection";

function skipped(name: string): boolean {
  return name.startsWith(".") || name === "__pycache__" || name === "node_modules";
}

function fileOf(entry: FileSystemFileEntry): Promise<File> {
  return new Promise((resolve, reject) => entry.file(resolve, reject));
}

function readBatch(reader: FileSystemDirectoryReader): Promise<FileSystemEntry[]> {
  return new Promise((resolve, reject) => reader.readEntries(resolve, reject));
}

async function collect(entry: FileSystemEntry, found: FoundFile[]): Promise<void> {
  if (entry.isFile) {
    const file = await fileOf(entry as FileSystemFileEntry);
    found.push({ path: insideFolder(entry.fullPath.replace(/^\//, "")), file });
    return;
  }
  if (!entry.isDirectory || skipped(entry.name)) return;
  const reader = (entry as FileSystemDirectoryEntry).createReader();
  // readEntries gives a folder in batches and an empty one at the end.
  for (let batch = await readBatch(reader); batch.length > 0; batch = await readBatch(reader)) {
    for (const child of batch) await collect(child, found);
  }
}

/**
 * The entries must be taken while the drop event lasts; reading them may take longer. Paths are
 * relative to a dropped folder, single files keep their name, as with the file inputs.
 */
export function droppedEntries(items: DataTransferItemList): FileSystemEntry[] {
  return Array.from(items, (item) => item.webkitGetAsEntry()).filter(
    (entry): entry is FileSystemEntry => entry !== null,
  );
}

export async function droppedFiles(entries: FileSystemEntry[]): Promise<FoundFile[]> {
  const found: FoundFile[] = [];
  for (const entry of entries) await collect(entry, found);
  return found;
}
