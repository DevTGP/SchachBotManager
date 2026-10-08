import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { Bot } from "../api/types";
import { folderFile } from "../test/files";
import { ADMIN, BOTS, botDetail, CODER, SHARP_ID } from "../test/fixtures";
import { type ApiCall, mockApi, renderRoute } from "../test/render";

const OWN: Bot[] = [
  {
    id: "665f0000000000000000000d",
    name: "Sharp",
    version: "1.0.4",
    language: "python",
    status: "verified",
    builtin: false,
    created_at: "2026-05-01T10:00:00.000Z",
  },
];

const TEMPLATE = [".vscode/launch.json", "README.md", "bot.py", "lib/eval.py", "data/book.txt"];

describe("upload page", () => {
  it("uploads the sources of a folder as a new version", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: CODER },
      "/account/bots": { items: OWN },
      "/bots": (_url: URL, call: ApiCall) =>
        call.method === "POST" ? botDetail({ status: "uploaded" }) : { items: BOTS },
      [`/bots/${SHARP_ID}`]: botDetail({ status: "uploaded" }),
    });
    const { router } = renderRoute("/bots/new");

    expect(await screen.findByRole("link", { name: "Sharp" })).toHaveAttribute(
      "href",
      "/bots/665f0000000000000000000d",
    );
    const folder = screen.getByLabelText("Folder");
    expect(folder).toHaveAttribute("webkitdirectory");
    await user.upload(
      folder,
      TEMPLATE.map((path) => folderFile(path)),
    );
    expect(screen.getByText("3 files will be uploaded:")).toBeVisible();
    expect(screen.getByText("Not uploaded: .vscode/launch.json, README.md")).toBeVisible();
    expect(screen.getByRole("combobox", { name: "Entry file" })).toHaveValue("bot.py");
    await user.type(screen.getByLabelText(/^Name/), "sharp");
    expect(screen.getByLabelText(/^Version/)).toHaveValue("1.0.5");
    await user.click(screen.getByRole("button", { name: "Upload" }));

    expect(await screen.findByRole("heading", { name: "Sharp 1.0.0" })).toBeVisible();
    expect(router.state.location.pathname).toBe(`/bots/${SHARP_ID}`);
    expect(screen.getByText("The bot is being verified. This page updates itself.")).toBeVisible();
    const post = api.calls.find((call) => call.method === "POST");
    expect(post?.headers.get("X-SBM-CSRF")).toBe("1");
    const form = post?.form;
    expect([form?.get("name"), form?.get("version"), form?.get("entry")]).toEqual([
      "sharp",
      "1.0.5",
      "bot.py",
    ]);
    expect(form?.getAll("paths")).toEqual(["bot.py", "data/book.txt", "lib/eval.py"]);
    expect(form?.getAll("files")).toHaveLength(3);
  });

  it("checks the selection before sending", async () => {
    const user = userEvent.setup();
    const api = mockApi({ "/session": { user: CODER }, "/account/bots": { items: [] } });
    renderRoute("/bots/new");

    expect(await screen.findByText("You have not uploaded a bot yet.")).toBeVisible();
    await user.type(screen.getByLabelText(/^Name/), "Sharp");
    expect(screen.getByLabelText(/^Version/)).toHaveValue("1.0.0");
    await user.click(screen.getByRole("button", { name: "Upload" }));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Choose a folder or files with at least one .py file.",
    );

    await user.upload(screen.getByLabelText("Folder"), [folderFile("lib/eval.py")]);
    await user.click(screen.getByRole("button", { name: "Upload" }));
    expect(screen.getByRole("alert")).toHaveTextContent("The top folder needs a .py file");
    expect(api.calls.some((call) => call.method === "POST")).toBe(false);
  });

  it("names the file that breaks a rule", async () => {
    const user = userEvent.setup();
    mockApi({
      "/session": { user: CODER },
      "/account/bots": { items: [] },
      "/bots": Response.json(
        { code: "invalid_upload", message: "the path occurs twice", path: "Bot.py" },
        { status: 400 },
      ),
    });
    renderRoute("/bots/new");
    await user.upload(await screen.findByLabelText("Or single .py files"), [
      new File(["x"], "bot.py"),
    ]);
    await user.type(screen.getByLabelText(/^Name/), "Sharp");
    await user.click(screen.getByRole("button", { name: "Upload" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("The upload breaks a rule.");
    expect(alert).toHaveTextContent("Bot.py: the path occurs twice");
  });

  it("is only for accounts", async () => {
    mockApi({ "/session": { user: null } });
    const { router } = renderRoute("/bots/new");
    await screen.findByRole("button", { name: "Log in" });
    expect(router.state.location.pathname).toBe("/login");
  });
});

describe("bot page", () => {
  it("shows the owner the files and why the bot was rejected", async () => {
    mockApi({ "/session": { user: CODER }, [`/bots/${SHARP_ID}`]: botDetail() });
    renderRoute(`/bots/${SHARP_ID}`);

    expect(await screen.findByRole("heading", { name: "Sharp 1.0.0" })).toBeVisible();
    expect(screen.getByText("Rejected", { selector: "dd" })).toBeVisible();
    expect(screen.getByText("Static analysis: 1 finding")).toBeVisible();
    expect(screen.getByText("1,234 bytes")).toBeVisible();
    const findings = screen.getByRole("table", { name: "Findings" });
    expect(within(findings).getByText("bot.py:3")).toBeVisible();
    expect(within(findings).getByText("socket is not allowed")).toBeVisible();
    expect(screen.queryByRole("button", { name: "Disable" })).toBeNull();
  });

  it("shows others the public facts only", async () => {
    mockApi({
      "/session": { user: null },
      [`/bots/${SHARP_ID}`]: botDetail({ status: "verified", details: null }),
    });
    renderRoute(`/bots/${SHARP_ID}`);
    expect(await screen.findByText("Verified")).toBeVisible();
    expect(screen.getByRole("link", { name: "Games of this bot" })).toHaveAttribute(
      "href",
      `/matches?bot=${SHARP_ID}`,
    );
    expect(screen.queryByRole("heading", { name: "Files" })).toBeNull();
  });

  it("lets admins disable a verified bot", async () => {
    const user = userEvent.setup();
    let status: Bot["status"] = "verified";
    const api = mockApi({
      "/session": { user: ADMIN },
      [`/bots/${SHARP_ID}`]: () => botDetail({ status }),
      [`/admin/bots/${SHARP_ID}`]: (_url: URL, call: ApiCall) => {
        status = (call.body as { status: Bot["status"] }).status;
        return botDetail({ status });
      },
    });
    renderRoute(`/bots/${SHARP_ID}`);

    await user.click(await screen.findByRole("button", { name: "Disable" }));
    expect(await screen.findByRole("button", { name: "Enable" })).toBeVisible();
    expect(screen.getByText("Disabled", { selector: "dd" })).toBeVisible();
    const patch = api.calls.find((call) => call.method === "PATCH");
    expect(patch?.body).toEqual({ status: "disabled" });
  });
});

describe("bots page", () => {
  it("links each bot to its page and shows its version", async () => {
    mockApi({ "/bots": { items: BOTS } });
    renderRoute("/bots");
    expect(await screen.findByRole("link", { name: "Random" })).toHaveAttribute(
      "href",
      `/bots/${BOTS[0]!.id}`,
    );
    expect(screen.getAllByText("1.0.0")).toHaveLength(2);
  });
});
