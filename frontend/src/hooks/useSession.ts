import { useCallback, useEffect } from "react";
import { ApiError } from "../api/client";
import { companiesApi } from "../api/companies";
import type { TokenResponse } from "../api/types";
import { useAuthStore } from "../store/authStore";
import { useCompanyStore } from "../store/companyStore";

/** Keeps the cached company profile in step with the company in the token. */
export function useCompanyBootstrap() {
  const user = useAuthStore((s) => s.user);
  const { profile, setCompany, clearCompany } = useCompanyStore();

  useEffect(() => {
    if (!user) return;
    if (profile?.id === user.company_id) return;
    clearCompany();
    companiesApi
      .get(user.company_id)
      .then(setCompany)
      .catch((e: unknown) => {
        // 404 just means the admin hasn't filled in the profile yet.
        if (!(e instanceof ApiError && e.status === 404)) console.error(e);
      });
  }, [user, profile?.id, setCompany, clearCompany]);
}

export function useSessionActions() {
  const setSession = useAuthStore((s) => s.setSession);
  const clearSession = useAuthStore((s) => s.logout);
  const clearCompany = useCompanyStore((s) => s.clearCompany);

  const start = useCallback(
    (res: TokenResponse) => {
      clearCompany();
      setSession(res);
    },
    [clearCompany, setSession],
  );

  const logout = useCallback(() => {
    clearSession();
    clearCompany();
  }, [clearSession, clearCompany]);

  return { start, logout };
}
