import { describe, expect, it } from "vitest";

import type { Bot } from "../api/types";
import { folderFile } from "../test/files";
import { botClasses, classCandidates } from "./botClasses";
import {
  detectLanguage,
  entryCandidates,
  foundFiles,
  MAX_BYTES,
  selectFiles,
  selectionProblem,
} from "./selection";
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
    const selection = selectFiles(TEMPLATE, "python");
    expect(selection.files.map(({ path, kind }) => [path, kind])).toEqual([
      ["bot.py", "source"],
      ["data/book.txt", "data"],
      ["lib/eval.py", "source"],
    ]);
    expect(selection.ignored).toEqual([
      ".gitignore",
      ".vscode/",
      "README.md",
      "requirements.txt",
      "lib/__pycache__/",
      "data/deep/table.bin",
    ]);
  });

  it("takes single files by their name", () => {
    expect(selectFiles([new File(["x"], "bot.py")], "python").files[0]?.path).toBe("bot.py");
  });
});

const JS_TEMPLATE = [
  "package.json",
  "bot.js",
  "lib/eval.mjs",
  "start.py",
  "node_modules/schachbotmanager/dist/index.js",
  "data/book.txt",
].map((path) => folderFile(path));

describe("a JavaScript selection", () => {
  it("keeps .js and .mjs files and lists node_modules as one folder", () => {
    const selection = selectFiles(JS_TEMPLATE, "javascript");
    expect(selection.files.map(({ path, kind }) => [path, kind])).toEqual([
      ["bot.js", "source"],
      ["data/book.txt", "data"],
      ["lib/eval.mjs", "source"],
    ]);
    expect(selection.ignored).toEqual(["package.json", "start.py", "node_modules/"]);
    expect(entryCandidates(selection.files, "javascript")).toEqual(["bot.js"]);
  });

  it("names the language of the files if only one has sources", () => {
    expect(detectLanguage(foundFiles(JS_TEMPLATE.filter((file) => file.name !== "start.py")))).toBe(
      "javascript",
    );
    expect(detectLanguage(foundFiles(TEMPLATE))).toBe("python");
    expect(detectLanguage(foundFiles(JS_TEMPLATE))).toBeUndefined();
    expect(detectLanguage([])).toBeUndefined();
  });
});

const CSHARP_TEMPLATE = [
  ".vscode/launch.json",
  "MyBot.csproj",
  "Program.cs",
  "TemplateBot.cs",
  "Engine/Search.cs",
  "Engine/Program.cs",
  "bin/Release/net10.0/MyBot.dll",
  "obj/project.assets.json",
  "obj/Release/MyBot.AssemblyInfo.cs",
  "data/book.txt",
  "bot.py",
].map((path) => folderFile(path));

describe("selectFiles for C#", () => {
  it("keeps .cs sources outside the build folders and leaves the entry file home", () => {
    const selection = selectFiles(CSHARP_TEMPLATE, "csharp");
    expect(selection.files.map(({ path, kind }) => [path, kind])).toEqual([
      ["data/book.txt", "data"],
      ["Engine/Program.cs", "source"],
      ["Engine/Search.cs", "source"],
      ["TemplateBot.cs", "source"],
    ]);
    expect(selection.ignored).toEqual([
      ".vscode/",
      "MyBot.csproj",
      "Program.cs",
      "bin/",
      "obj/",
      "bot.py",
    ]);
  });

  it("keeps folders named bin or obj in a Python bot", () => {
    const files = ["bot.py", "bin/tool.py", "Bot.cs"].map((path) => folderFile(path));
    expect(selectFiles(files).files.map((file) => file.path)).toEqual(["bin/tool.py", "bot.py"]);
  });
});

describe("botClasses", () => {
  it("names classes deriving from Bot with their namespace", () => {
    const source = `using Sbm;

namespace MyBot;

// class Old : Bot
public sealed class TemplateBot : Bot { }
internal class Helper : Sbm.Bot { }
public abstract class Base : Bot { }
public class Other : BotBase { }
public class Generic<T> : Bot { }
`;
    expect(botClasses(source)).toEqual(["MyBot.TemplateBot", "MyBot.Helper"]);
  });

  it("follows block namespaces and classes without one", () => {
    expect(botClasses("class Top : global::Sbm.Bot {}")).toEqual(["Top"]);
    expect(botClasses("namespace A.B { /* x */ class C : Bot {} }")).toEqual(["A.B.C"]);
  });

  it("reads the sources of a selection", async () => {
    const files = selectFiles(
      [
        folderFile("TemplateBot.cs", "namespace MyBot; class TemplateBot : Bot {}"),
        folderFile("Engine/Second.cs", "namespace MyBot.Engine; class Second : Bot {}"),
        folderFile("data/notes.cs", "class Data : Bot {}"),
      ],
      "csharp",
    );
    expect(await classCandidates(files.files)).toEqual([
      "MyBot.Engine.Second",
      "MyBot.TemplateBot",
    ]);
  });
});

describe("selectionProblem", () => {
  it("needs a file and keeps the limits of each kind", () => {
    expect(selectionProblem([])).toBe("upload.noFiles");
    expect(selectionProblem(selectFiles(TEMPLATE, "python").files)).toBeUndefined();
    const many = Array.from({ length: 101 }, (_, index) => folderFile(`m${index}.py`));
    expect(selectionProblem(selectFiles(many, "python").files)).toBe("upload.tooManyFiles");
    const big = [folderFile("bot.py"), folderFile("data/big.bin", new Uint8Array(MAX_BYTES + 1))];
    expect(selectionProblem(selectFiles(big, "python").files)).toBe("upload.tooLarge");
  });
});

describe("entryCandidates", () => {
  it("offers top-level sources with bot.py first", () => {
    const files = selectFiles(
      ["main.py", "bot.py", "lib/eval.py"].map((p) => folderFile(p)),
      "python",
    );
    expect(entryCandidates(files.files, "python")).toEqual(["bot.py", "main.py"]);
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
    owner: "bob",
    description: "",
    rating: { value: 2500, games: 0 },
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
