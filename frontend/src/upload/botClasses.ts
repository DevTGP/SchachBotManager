// The bot classes a C# upload offers for its entry (E202): classes deriving directly from Bot,
// with the namespace in effect before them. This is only a suggestion read from the text; the
// build on the server decides whether the class may start the bot.

import type { PickedFile } from "./selection";

const COMMENT = /\/\/[^\n]*|\/\*[\s\S]*?\*\//g;
const DECLARATION =
  /\bnamespace\s+([A-Za-z_][\w.]*)|((?:\b\w+\s+)*)class\s+([A-Za-z_]\w*)\s*:\s*(?:global::)?(?:Sbm\.)?Bot\b(?![.<\w])/g;
const NOT_STARTABLE = new Set(["abstract", "static"]);

/** Full names of the bot classes in one source file. */
export function botClasses(source: string): string[] {
  const classes: string[] = [];
  let namespace = "";
  for (const match of source.replace(COMMENT, "").matchAll(DECLARATION)) {
    const [, declared, modifiers, name] = match;
    if (declared !== undefined) {
      namespace = declared;
      continue;
    }
    if (modifiers?.split(/\s+/).some((modifier) => NOT_STARTABLE.has(modifier))) continue;
    if (name) classes.push(namespace ? `${namespace}.${name}` : name);
  }
  return classes;
}

/** The bot classes of all sources of the selection, sorted. */
export async function classCandidates(files: PickedFile[]): Promise<string[]> {
  const sources = files.filter((file) => file.kind === "source");
  const found = await Promise.all(sources.map(async (file) => botClasses(await file.file.text())));
  return [...new Set(found.flat())].sort();
}
