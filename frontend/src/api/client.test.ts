import { describe, expect, it, vi } from "vitest";

import { ApiError, apiUrl, getJson, sendJson } from "./client";

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

describe("sendJson", () => {
  it("sends the body as JSON with the CSRF header", async () => {
    const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(Response.json({ user: null }));
    await expect(sendJson("POST", "/session", { username: "bob" })).resolves.toEqual({
      user: null,
    });
    const [url, init] = fetch.mock.calls[0]!;
    expect(url).toBe("/api/v1/session");
    expect(init?.method).toBe("POST");
    expect(init?.body).toBe('{"username":"bob"}');
    expect(new Headers(init?.headers).get("X-SBM-CSRF")).toBe("1");
    expect(new Headers(init?.headers).get("Content-Type")).toBe("application/json");
  });

  it("returns undefined for an answer without content", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(null, { status: 204 }));
    await expect(sendJson("DELETE", "/session")).resolves.toBeUndefined();
    const init = fetch.mock.calls[0]![1];
    expect(init?.body).toBeUndefined();
    expect(new Headers(init?.headers).has("Content-Type")).toBe(false);
  });

  it("keeps the invalid field of an error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json(
        { code: "invalid_parameter", message: "too short", field: "password" },
        { status: 400 },
      ),
    );
    await expect(sendJson("POST", "/invites/redeem", {})).rejects.toMatchObject({
      code: "invalid_parameter",
      status: 400,
      field: "password",
    });
  });
});
