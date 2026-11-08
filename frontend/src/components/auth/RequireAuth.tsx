import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isAuthenticated, useAuthStore } from "../../store/authStore";

export function RequireAuth({ children }: { children: ReactNode }) {
  // Subscribe so a logout (e.g. after a 401) re-renders and redirects.
  useAuthStore((s) => s.token);
  const location = useLocation();

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}
