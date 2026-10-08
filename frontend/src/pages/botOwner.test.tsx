import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { Bot } from "../api/types";
import { ADMIN, botDetail, CODER, SHARP_ID } from "../test/fixtures";
import { type ApiCall, mockApi, renderRoute } from "../test/render";

const OLDER: Bot = {
  id: "665f0000000000000000000e",
  name: "Sharp",
  version: "0.9.0",
  language: "python",
  status: "retired",
  builtin: false,
  description: "",
  created_at: "2026-04-01T10:00:00.000Z",
};

describe("bot page for the owner", () => {
  it("edits the description", async () => {
    const user = userEvent.setup();
    let description = "Plays e4.";
    const api = mockApi({
      "/session": { user: CODER },
      [`/bots/${SHARP_ID}`]: (_url: URL, call: ApiCall) => {
        if (call.method === "PATCH")
          description = (call.body as { description: string }).description;
        return botDetail({ status: "verified", description });
      },
    });
    renderRoute(`/bots/${SHARP_ID}`);

    expect(await screen.findByText("Plays e4.")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Edit description" }));
    const field = screen.getByRole("textbox", { name: /^Description/ });
    expect(field).toHaveAttribute("maxlength", "500");
    await user.clear(field);
    await user.type(field, "Plays d4.{Enter}Never resigns.");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText(/Plays d4\./)).toHaveClass("description");
    const patch = api.calls.find((call) => call.method === "PATCH");
    expect(patch?.body).toEqual({ description: "Plays d4.\nNever resigns." });
    expect(patch?.headers.get("X-SBM-CSRF")).toBe("1");
  });

  it("withdraws a verified bot and reactivates it", async () => {
    const user = userEvent.setup();
    let status: Bot["status"] = "verified";
    const api = mockApi({
      "/session": { user: CODER },
      [`/bots/${SHARP_ID}`]: (_url: URL, call: ApiCall) => {
        if (call.method === "PATCH") status = (call.body as { status: Bot["status"] }).status;
        return botDetail({ status });
      },
    });
    renderRoute(`/bots/${SHARP_ID}`);

    await user.click(await screen.findByRole("button", { name: "Withdraw" }));
    expect(await screen.findByRole("button", { name: "Reactivate" })).toBeVisible();
    expect(screen.getByText("Withdrawn", { selector: "dd" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Reactivate" }));
    expect(await screen.findByRole("button", { name: "Withdraw" })).toBeVisible();
    const bodies = api.calls.filter((call) => call.method === "PATCH").map((call) => call.body);
    expect(bodies).toEqual([{ status: "retired" }, { status: "verified" }]);
    // Coders have no admin switch.
    expect(screen.queryByRole("button", { name: "Disable" })).toBeNull();
  });

  it("shows each file and offers all of them as a ZIP file", async () => {
    const user = userEvent.setup();
    mockApi({
      "/session": { user: CODER },
      [`/bots/${SHARP_ID}`]: botDetail(),
      [`/bots/${SHARP_ID}/file`]: (url: URL) =>
        url.searchParams.get("path") === "bot.py"
          ? new Response("<b>import sbm</b>\n")
          : new Response(new Uint8Array([0, 255, 254])),
    });
    renderRoute(`/bots/${SHARP_ID}`);

    expect(await screen.findByRole("link", { name: "Download all files (ZIP)" })).toHaveAttribute(
      "href",
      `/api/v1/bots/${SHARP_ID}/source`,
    );
    await user.click(screen.getByRole("button", { name: "bot.py" }));
    const source = await screen.findByRole("region", { name: "bot.py" });
    // Shown as text, not as markup.
    expect(await within(source).findByText("<b>import sbm</b>")).toBeVisible();
    expect(within(source).getByRole("link", { name: "Download file" })).toHaveAttribute(
      "href",
      `/api/v1/bots/${SHARP_ID}/file?path=bot.py`,
    );

    await user.click(screen.getByRole("button", { name: "data/book.txt" }));
    const data = await screen.findByRole("region", { name: "data/book.txt" });
    expect(await within(data).findByText("This file is not text.")).toBeVisible();
  });
});

describe("bot page for everyone", () => {
  it("shows the description and the visible versions", async () => {
    mockApi({
      "/session": { user: null },
      [`/bots/${SHARP_ID}`]: botDetail({
        status: "verified",
        description: "Plays e4.",
        details: null,
        versions: [botDetail({ status: "verified" }), OLDER],
      }),
    });
    renderRoute(`/bots/${SHARP_ID}`);

    expect(await screen.findByText("Plays e4.")).toBeVisible();
    const versions = screen.getByRole("table");
    expect(within(versions).getByText("1.0.0")).toHaveAttribute("aria-current", "page");
    expect(within(versions).getByRole("link", { name: "0.9.0" })).toHaveAttribute(
      "href",
      `/bots/${OLDER.id}`,
    );
    expect(within(versions).getByText("Withdrawn")).toBeVisible();
    expect(screen.queryByRole("button", { name: "Edit description" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Withdraw" })).toBeNull();
  });

  it("lets admins disable a withdrawn bot", async () => {
    mockApi({
      "/session": { user: ADMIN },
      [`/bots/${SHARP_ID}`]: botDetail({ status: "retired" }),
    });
    renderRoute(`/bots/${SHARP_ID}`);

    expect(await screen.findByRole("button", { name: "Disable" })).toBeVisible();
    // The admin does not own the bot.
    expect(screen.queryByRole("button", { name: "Reactivate" })).toBeNull();
  });
});
