import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { vi } from "vitest";

import { routes } from "../routes";

/** A response per API path (without /api/v1 and query); a function sees the whole URL. */
export type ApiResponses = Record<string, unknown | ((url: URL) => unknown)>;

export interface MockedApi {
  /** Every requested URL, in order. */
  requests: URL[];
}

/** Answers fetch from `responses`; unknown paths get the API's 404. */
export function mockApi(responses: ApiResponses): MockedApi {
  const requests: URL[] = [];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = new URL(String(input), "http://localhost");
    requests.push(url);
    const path = url.pathname.replace(/^\/api\/v1/, "");
    if (!(path in responses)) {
      return Response.json({ code: "not_found", message: "not found" }, { status: 404 });
    }
    const response = responses[path];
    const body = typeof response === "function" ? response(url) : response;
    return body instanceof Response ? body : Response.json(body);
  });
  return { requests };
}

/** Renders the app's routes at `path`; the router shows where navigation led. */
export function renderRoute(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  const view = render(<RouterProvider router={router} />);
  return { router, ...view };
}
