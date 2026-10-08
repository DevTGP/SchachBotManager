import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ADMIN, CODER } from "../test/fixtures";
import { mockApi, renderRoute } from "../test/render";

const NO_CONTENT = () => new Response(null, { status: 204 });

describe("login", () => {
  it("sends guests from a protected page to the login and back", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": (_url: URL, call: { method: string }) =>
        call.method === "POST" ? { user: CODER } : { user: null },
    });
    const { router } = renderRoute("/account");

    await user.type(await screen.findByLabelText("Name"), "bob");
    expect(router.state.location.pathname).toBe("/login");
    expect(router.state.location.search).toBe("?next=%2Faccount");
    await user.type(screen.getByLabelText("Password"), "correct horse");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByText("Logged in as bob")).toBeVisible();
    expect(router.state.location.pathname).toBe("/account");
    const post = api.calls.find((call) => call.method === "POST");
    expect(post?.body).toEqual({ username: "bob", password: "correct horse" });
    expect(post?.headers.get("X-SBM-CSRF")).toBe("1");
  });

  it("shows wrong credentials", async () => {
    const user = userEvent.setup();
    mockApi({
      "/session": (_url: URL, call: { method: string }) =>
        call.method === "POST"
          ? Response.json(
              { code: "invalid_credentials", message: "wrong name or password" },
              { status: 401 },
            )
          : { user: null },
    });
    renderRoute("/login");
    await user.type(await screen.findByLabelText("Name"), "bob");
    await user.type(screen.getByLabelText("Password"), "wrong password");
    await user.click(screen.getByRole("button", { name: "Log in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Wrong name or password.");
  });

  it("links guests to the login and admins to the admin pages", async () => {
    mockApi({ "/session": { user: null } });
    const guest = renderRoute("/login");
    expect(await screen.findByRole("link", { name: "Log in" })).toHaveAttribute("href", "/login");
    guest.unmount();

    mockApi({ "/session": { user: ADMIN } });
    renderRoute("/account");
    expect(await screen.findByRole("link", { name: "Admin" })).toHaveAttribute("href", "/admin");
    expect(screen.getByRole("link", { name: "admin" })).toHaveAttribute("href", "/account");
  });
});

describe("invite page", () => {
  it("takes the token from the link and creates the account", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: null },
      "/invites/redeem": { user: { ...CODER, username: "carol" } },
    });
    const { router } = renderRoute("/invite#secret-token");

    const name = await screen.findByLabelText(/^Name/);
    await waitFor(() => expect(router.state.location.hash).toBe(""));
    await user.type(name, "carol");
    await user.type(screen.getByLabelText(/^New password/), "long enough secret");
    await user.type(screen.getByLabelText("Repeat password"), "long enough typo");
    await user.click(screen.getByRole("button", { name: "Create account" }));
    expect(screen.getByRole("alert")).toHaveTextContent("The passwords do not match.");
    expect(api.calls.some((call) => call.method === "POST")).toBe(false);

    await user.clear(screen.getByLabelText("Repeat password"));
    await user.type(screen.getByLabelText("Repeat password"), "long enough secret");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByText("Logged in as carol")).toBeVisible();
    expect(router.state.location.pathname).toBe("/account");
    const post = api.calls.find((call) => call.url.pathname === "/api/v1/invites/redeem");
    expect(post?.body).toEqual({
      token: "secret-token",
      username: "carol",
      password: "long enough secret",
    });
  });

  it("names a taken name", async () => {
    const user = userEvent.setup();
    mockApi({
      "/session": { user: null },
      "/invites/redeem": Response.json(
        { code: "username_taken", message: "the name is taken", field: "username" },
        { status: 409 },
      ),
    });
    renderRoute("/invite#secret-token");
    await user.type(await screen.findByLabelText(/^Name/), "carol");
    await user.type(screen.getByLabelText(/^New password/), "long enough secret");
    await user.type(screen.getByLabelText("Repeat password"), "long enough secret");
    await user.click(screen.getByRole("button", { name: "Create account" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("The name is taken.");
  });

  it("explains a link without token", async () => {
    mockApi({ "/session": { user: null } });
    renderRoute("/invite");
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The link is invalid, expired or already used.",
    );
  });
});

describe("password reset page", () => {
  it("sets the new password and logs in", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": { user: null },
      "/password-resets/redeem": { user: CODER },
    });
    const { router } = renderRoute("/reset-password#reset-token");
    await user.type(await screen.findByLabelText(/^New password/), "another long secret");
    await user.type(screen.getByLabelText("Repeat password"), "another long secret");
    await user.click(screen.getByRole("button", { name: "Set password" }));

    expect(await screen.findByText("Logged in as bob")).toBeVisible();
    expect(router.state.location.pathname).toBe("/account");
    // The account page then loads the API tokens, so the redeem call is not the last one.
    const redeem = api.calls.find((call) => call.url.pathname.endsWith("/password-resets/redeem"));
    expect(redeem?.body).toEqual({
      token: "reset-token",
      password: "another long secret",
    });
  });
});

describe("account page", () => {
  it("changes the password", async () => {
    const user = userEvent.setup();
    const api = mockApi({ "/session": { user: CODER }, "/account/password": NO_CONTENT });
    renderRoute("/account");
    await user.type(await screen.findByLabelText("Current password"), "old long secret");
    await user.type(screen.getByLabelText(/^New password/), "new long secret");
    await user.type(screen.getByLabelText("Repeat password"), "new long secret");
    await user.click(screen.getByRole("button", { name: "Save password" }));

    expect(await screen.findByRole("status")).toHaveTextContent("The password is changed.");
    const put = api.calls.find((call) => call.method === "PUT");
    expect(put?.body).toEqual({
      current_password: "old long secret",
      new_password: "new long secret",
    });
    expect(screen.getByLabelText("Current password")).toHaveValue("");
  });

  it("shows the own rating", async () => {
    mockApi({
      "/session": { user: { ...CODER, role: "player" } },
      "/account/rating": { value: 2547, games: 1 },
    });
    renderRoute("/account");

    expect(await screen.findByText("2547 after 1 rated game")).toBeVisible();
    expect(screen.queryByRole("heading", { name: "API tokens" })).toBeNull();
  });

  it("logs out to the start page", async () => {
    const user = userEvent.setup();
    const api = mockApi({
      "/session": (_url: URL, call: { method: string }) =>
        call.method === "DELETE" ? NO_CONTENT() : { user: CODER },
      "/matches": { items: [], total: 0 },
    });
    const { router } = renderRoute("/account");
    await user.click(await screen.findByRole("button", { name: "Log out" }));

    expect(await screen.findByRole("link", { name: "Log in" })).toBeVisible();
    expect(router.state.location.pathname).toBe("/");
    expect(api.calls.some((call) => call.method === "DELETE")).toBe(true);
  });
});
