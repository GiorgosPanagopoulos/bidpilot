import { api } from "./client";
import type { AuthUser, TokenResponse } from "./types";

export const authApi = {
  login: (email: string, password: string) =>
    api.post<TokenResponse>("/auth/login", { email, password }),
  demo: () => api.post<TokenResponse>("/auth/demo"),
  me: () => api.get<AuthUser>("/auth/me"),
};
