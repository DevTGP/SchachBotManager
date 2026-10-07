import { describe, expect, it, vi } from "vitest";

import { ApiError, apiUrl, getJson } from "./client";

describe("apiUrl", () => {
  it("leaves out missing parameters", () => {
    expect(apiUrl("/matches", { status: "running", bot_id: undefined, limit: 5 })).toBe(
      "/api/v1/matches?status=running&limit=5",
    );
    expect(apiUrl("/queue")).toBe("/api/v1/queue");
  });
});

describe("getJson", () => {
  it("returns the body of a successful response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(Response.json({ status: "ok" }));
    await expect(getJson("/health")).resolves.toEqual({ status: "ok" });
  });

  it("throws the API's error code", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json({ code: "unavailable", message: "database" }, { status: 503 }),
    );
    const error = await getJson("/matches").catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ code: "unavailable", status: 503 });
  });

  it("reports a missing server or a non-JSON answer as network", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new TypeError("Failed to fetch"));
    await expect(getJson("/matches")).rejects.toMatchObject({ code: "network", status: 0 });

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response("<html>Bad Gateway</html>", { status: 502 }),
    );
    await expect(getJson("/matches")).rejects.toMatchObject({ code: "network", status: 502 });
  });
});
