import type { RouteObject } from "react-router";

import { Layout } from "./components/Layout";
import { AccountPage } from "./pages/account/AccountPage";
import { InvitePage } from "./pages/account/InvitePage";
import { LoginPage } from "./pages/account/LoginPage";
import { ResetPasswordPage } from "./pages/account/ResetPasswordPage";
import { AdminInvitesPage } from "./pages/admin/AdminInvitesPage";
import { AdminLayout } from "./pages/admin/AdminLayout";
import { AdminMatchesPage } from "./pages/admin/AdminMatchesPage";
import { AdminUsersPage } from "./pages/admin/AdminUsersPage";
import { BotsPage } from "./pages/BotsPage";
import { MatchesPage } from "./pages/MatchesPage";
import { MatchPage } from "./pages/MatchPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { QueuePage } from "./pages/QueuePage";
import { StartPage } from "./pages/StartPage";
import { RequireRole } from "./session/RequireRole";
import { SessionProvider } from "./session/SessionProvider";

export const routes: RouteObject[] = [
  {
    element: (
      <SessionProvider>
        <Layout />
      </SessionProvider>
    ),
    children: [
      { index: true, element: <StartPage /> },
      { path: "matches", element: <MatchesPage /> },
      { path: "matches/:id", element: <MatchPage /> },
      { path: "queue", element: <QueuePage /> },
      { path: "bots", element: <BotsPage /> },
      { path: "login", element: <LoginPage /> },
      { path: "invite", element: <InvitePage /> },
      { path: "reset-password", element: <ResetPasswordPage /> },
      {
        path: "account",
        element: (
          <RequireRole>
            <AccountPage />
          </RequireRole>
        ),
      },
      {
        path: "admin",
        element: <AdminLayout />,
        children: [
          { index: true, element: <AdminMatchesPage /> },
          { path: "users", element: <AdminUsersPage /> },
          { path: "invites", element: <AdminInvitesPage /> },
        ],
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];
