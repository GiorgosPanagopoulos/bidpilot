import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { FeedPage } from "./pages/FeedPage";
import { WorkspacePage } from "./pages/WorkspacePage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <FeedPage /> },
      { path: "workspace", element: <WorkspacePage /> },
      { path: "analytics", element: <AnalyticsPage /> },
    ],
  },
]);

export function App() {
  return <RouterProvider router={router} />;
}
