import { describe, expect, it } from "vitest";

import type { Bot } from "../api/types";
import { folderFile } from "../test/files";
import { entryCandidates, MAX_BYTES, selectFiles, selectionProblem } from "./selection";
import { parseVersion, suggestVersion } from "./version";

const TEMPLATE = [
  ".gitignore",
  ".vscode/launch.json",
  "README.md",
  "requirements.txt",
  "bot.py",
  "lib/eval.py",
  "lib/__pycache__/eval.cpython-312.pyc",
  "data/book.txt",
  "data/deep/table.bin",
].map((path) => folderFile(path));

describe("selectFiles", () => {
  it("keeps sources and data files and lists the rest", () => {
    const selection = selectFiles(TEMPLATE);
    expect(selection.files.map(({ path, kind }) => [path, kind])).toEqual([
      ["bot.py", "source"],
      ["data/book.txt", "data"],
      ["lib/eval.py", "source"],
    ]);
    expect(selection.ignored).toEqual([
      ".gitignore",
      ".vscode/launch.json",
      "README.md",
      "requirements.txt",
      "lib/__pycache__/eval.cpython-312.pyc",
      "data/deep/table.bin",
    ]);
  });

  it("takes single files by their name", () => {
    expect(selectFiles([new File(["x"], "bot.py")]).files[0]?.path).toBe("bot.py");
  });
});

describe("selectionProblem", () => {
  it("needs a file and keeps the limits of each kind", () => {
    expect(selectionProblem([])).toBe("upload.noFiles");
    expect(selectionProblem(selectFiles(TEMPLATE).files)).toBeUndefined();
    const many = Array.from({ length: 101 }, (_, index) => folderFile(`m${index}.py`));
    expect(selectionProblem(selectFiles(many).files)).toBe("upload.tooManyFiles");
    const big = [folderFile("bot.py"), folderFile("data/big.bin", new Uint8Array(MAX_BYTES + 1))];
    expect(selectionProblem(selectFiles(big).files)).toBe("upload.tooLarge");
  });
});

describe("entryCandidates", () => {
  it("offers top-level sources with bot.py first", () => {
    const files = selectFiles(["main.py", "bot.py", "lib/eval.py"].map((p) => folderFile(p)));
    expect(entryCandidates(files.files)).toEqual(["bot.py", "main.py"]);
  });
});

function own(name: string, version: string): Bot {
  return {
    id: `${name}-${version}`,
    name,
    version,
    language: "python",
    status: "verified",
    builtin: false,
    description: "",
    created_at: "2026-05-01T10:00:00.000Z",
  };
}

describe("suggestVersion", () => {
  it("raises the latest version of the name", () => {
    const bots = [own("Sharp", "1.2.0"), own("Sharp", "1.10.3"), own("Other", "5.0.0")];
    expect(suggestVersion(bots, "sharp")).toBe("1.10.4");
    expect(suggestVersion(bots, "New")).toBe("1.0.0");
    expect(suggestVersion([own("Sharp", "2.0.999")], "Sharp")).toBe("");
  });

  it("parses only X.Y.Z without leading zeros", () => {
    expect(parseVersion("10.0.999")).toEqual([10, 0, 999]);
    expect(parseVersion("01.0.0")).toBeUndefined();
    expect(parseVersion("1.0")).toBeUndefined();
  });
});
