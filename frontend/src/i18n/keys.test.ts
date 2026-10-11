import { describe, expect, it } from "vitest";

import de from "./de.json";
import en from "./en.json";

function keys(node: unknown, prefix = ""): string[] {
  if (typeof node !== "object" || node === null) return [prefix];
  return Object.entries(node).flatMap(([key, value]) =>
    keys(value, prefix ? `${prefix}.${key}` : key),
  );
}

describe("translations", () => {
  it("have the same keys in German and English", () => {
    expect(keys(en).sort()).toEqual(keys(de).sort());
  });
});
