import { describe, expect, it } from "vitest";

import { droppedFiles } from "./dropped";

function fileEntry(fullPath: string): FileSystemEntry {
  const name = fullPath.split("/").at(-1)!;
  const file = new File(["x"], name);
  return {
    isFile: true,
    isDirectory: false,
    name,
    fullPath,
    file: (resolve: (file: File) => void) => resolve(file),
  } as unknown as FileSystemEntry;
}

function folderEntry(fullPath: string, children: FileSystemEntry[]): FileSystemEntry {
  return {
    isFile: false,
    isDirectory: true,
    name: fullPath.split("/").at(-1)!,
    fullPath,
    createReader: () => {
      // Two batches, then the empty one that ends the folder.
      const batches = [children.slice(0, 1), children.slice(1), []];
      return {
        readEntries: (resolve: (batch: FileSystemEntry[]) => void) => resolve(batches.shift()!),
      };
    },
  } as unknown as FileSystemEntry;
}

describe("droppedFiles", () => {
  it("reads a folder with paths inside it and skips hidden folders", async () => {
    const folder = folderEntry("/mybot", [
      fileEntry("/mybot/bot.py"),
      folderEntry("/mybot/lib", [fileEntry("/mybot/lib/eval.py")]),
      folderEntry("/mybot/.git", [fileEntry("/mybot/.git/HEAD")]),
      folderEntry("/mybot/__pycache__", [fileEntry("/mybot/__pycache__/bot.pyc")]),
    ]);

    const found = await droppedFiles([folder]);

    expect(found.map((item) => item.path)).toEqual(["bot.py", "lib/eval.py"]);
  });

  it("keeps the names of single files", async () => {
    const found = await droppedFiles([fileEntry("/bot.py"), fileEntry("/eval.py")]);
    expect(found.map((item) => item.path)).toEqual(["bot.py", "eval.py"]);
  });
});
