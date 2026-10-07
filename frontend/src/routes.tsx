import type { RouteObject } from "react-router";

import { Layout } from "./components/Layout";
import { BotsPage } from "./pages/BotsPage";
import { MatchesPage } from "./pages/MatchesPage";
import { MatchPage } from "./pages/MatchPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { QueuePage } from "./pages/QueuePage";
import { StartPage } from "./pages/StartPage";

export const routes: RouteObject[] = [
  {
    element: <Layout />,
    children: [
      { index: true, element: <StartPage /> },
      { path: "matches", element: <MatchesPage /> },
      { path: "matches/:id", element: <MatchPage /> },
      { path: "queue", element: <QueuePage /> },
      { path: "bots", element: <BotsPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];
