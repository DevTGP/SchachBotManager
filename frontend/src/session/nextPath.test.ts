import { describe, expect, it } from "vitest";

import { nextPath } from "./nextPath";

describe("nextPath", () => {
  it("goes back to a page of this site", () => {
    expect(nextPath("?next=%2Fadmin%2Fusers%3Fx%3D1")).toBe("/admin/users?x=1");
  });

  it("goes to the start page without or with a foreign target", () => {
    expect(nextPath("")).toBe("/");
    expect(nextPath("?next=https%3A%2F%2Fevil.example")).toBe("/");
    expect(nextPath("?next=%2F%2Fevil.example")).toBe("/");
  });
});
