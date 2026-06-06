import { api } from "./client";
import type { CompanyProfile } from "./types";

export const companiesApi = {
  create: (profile: Partial<CompanyProfile> & { name: string }) =>
    api.post<CompanyProfile>("/companies", profile),
  get: (id: string) => api.get<CompanyProfile>(`/companies/${id}`),
};
