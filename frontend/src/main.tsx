import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router";

import "./i18n";
import { routes } from "./routes";
import "./styles/base.css";
import "./styles/bot.css";
import "./styles/forms.css";
import "./styles/layout.css";
import "./styles/viewer.css";

const root = document.getElementById("root");
if (!root) throw new Error("missing #root");

createRoot(root).render(
  <StrictMode>
    <RouterProvider router={createBrowserRouter(routes)} />
  </StrictMode>,
);
