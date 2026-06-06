import { create } from "zustand";
import { analyticsApi } from "../api/analytics";
import type { PricingStats, SupplierWinRate, TrendSeries } from "../api/types";

interface AnalyticsFilters {
  cpv: string;
  authority: string;
  from: string;
  to: string;
  interval: "month" | "quarter" | "year";
}

interface AnalyticsState extends AnalyticsFilters {
  pricing: PricingStats | null;
  winRates: SupplierWinRate[];
  trends: TrendSeries | null;
  isLoading: boolean;
  error: string | null;
  setFilter: <K extends keyof AnalyticsFilters>(key: K, value: AnalyticsFilters[K]) => void;
  fetchAll: () => Promise<void>;
}

export const useAnalyticsStore = create<AnalyticsState>((set, get) => ({
  cpv: "",
  authority: "",
  from: "",
  to: "",
  interval: "month",
  pricing: null,
  winRates: [],
  trends: null,
  isLoading: false,
  error: null,

  setFilter: (key, value) => set({ [key]: value } as Partial<AnalyticsState>),

  fetchAll: async () => {
    set({ isLoading: true, error: null });
    const { cpv, authority, from, to, interval } = get();
    const filters = {
      cpv: cpv || undefined,
      authority: authority || undefined,
      from: from || undefined,
      to: to || undefined,
      interval,
    };
    try {
      const [pricing, winRates, trends] = await Promise.all([
        analyticsApi.pricing(filters),
        analyticsApi.winRates(filters),
        analyticsApi.trends(filters),
      ]);
      set({ pricing, winRates, trends });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : "Analytics fetch failed" });
    } finally {
      set({ isLoading: false });
    }
  },
}));
