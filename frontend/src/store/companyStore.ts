import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { CompanyProfile } from "../api/types";

interface CompanyState {
  companyId: string | null;
  profile: CompanyProfile | null;
  setCompany: (profile: CompanyProfile) => void;
  clearCompany: () => void;
}

export const useCompanyStore = create<CompanyState>()(
  persist(
    (set) => ({
      companyId: null,
      profile: null,
      setCompany: (profile) => set({ companyId: profile.id, profile }),
      clearCompany: () => set({ companyId: null, profile: null }),
    }),
    { name: "bidpilot-company" },
  ),
);
