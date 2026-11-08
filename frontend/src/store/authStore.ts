import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthUser, TokenResponse } from "../api/types";

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  expiresAt: number | null;
  setSession: (res: TokenResponse) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      expiresAt: null,
      setSession: (res) =>
        set({
          token: res.access_token,
          user: res.user,
          expiresAt: Date.now() + res.expires_in * 1000,
        }),
      logout: () => set({ token: null, user: null, expiresAt: null }),
    }),
    { name: "bidpilot-auth" },
  ),
);

export function getValidToken(): string | null {
  const { token, expiresAt } = useAuthStore.getState();
  if (!token || !expiresAt || expiresAt <= Date.now()) return null;
  return token;
}

export function isAuthenticated(): boolean {
  return getValidToken() !== null;
}
