import { api } from "./client";
import type { MatchResult } from "./types";

export const matchesApi = {
  run: (companyId: string) =>
    api.post<MatchResult[]>(`/matches/run?company_id=${encodeURIComponent(companyId)}`),
  list: (companyId: string) =>
    api.get<MatchResult[]>(`/matches?company_id=${encodeURIComponent(companyId)}`),
};
