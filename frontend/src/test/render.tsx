import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { vi } from "vitest";

import { routes } from "../routes";

/** One request as the API saw it. */
export interface ApiCall {
  url: URL;
  method: string;
  headers: Headers;
  /** The parsed JSON body, if any. */
  body: unknown;
  /** A multipart body, if any. */
  form: FormData | undefined;
}

/** A response per API path (without /api/v1 and query); a function sees the whole request. */
export type ApiResponses = Record<string, unknown | ((url: URL, call: ApiCall) => unknown)>;

export interface MockedApi {
  /** Every requested URL, in order. */
  requests: URL[];
  /** Every request with method, headers and body, in order. */
  calls: ApiCall[];
}

/** Answers fetch from `responses`; unknown paths get the API's 404. */
export function mockApi(responses: ApiResponses): MockedApi {
  const requests: URL[] = [];
  const calls: ApiCall[] = [];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = new URL(String(input), "http://localhost");
    const call: ApiCall = {
      url,
      method: init?.method ?? "GET",
      headers: new Headers(init?.headers),
      body: typeof init?.body === "string" ? JSON.parse(init.body) : undefined,
      form: init?.body instanceof FormData ? init.body : undefined,
    };
    requests.push(url);
    calls.push(call);
    const path = url.pathname.replace(/^\/api\/v1/, "");
    if (!(path in responses)) {
      return Response.json({ code: "not_found", message: "not found" }, { status: 404 });
    }
    const response = responses[path];
    const body = typeof response === "function" ? response(url, call) : response;
    return body instanceof Response ? body : Response.json(body);
  });
  return { requests, calls };
}

/** Renders the app's routes at `path`; the router shows where navigation led. */
export function renderRoute(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  const view = render(<RouterProvider router={router} />);
  return { router, ...view };
}
