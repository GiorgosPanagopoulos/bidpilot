import { api } from "./client";
import type { PricingStats, SupplierWinRate, TrendSeries } from "./types";

export interface AnalyticsFilters {
  cpv?: string;
  authority?: string;
  from?: string;
  to?: string;
  interval?: "month" | "quarter" | "year";
  top_n?: number;
}

function buildParams(filters: AnalyticsFilters): string {
  const params = new URLSearchParams();
  if (filters.cpv) params.set("cpv", filters.cpv);
  if (filters.authority) params.set("authority", filters.authority);
  if (filters.from) params.set("from", filters.from);
  if (filters.to) params.set("to", filters.to);
  if (filters.interval) params.set("interval", filters.interval);
  if (filters.top_n !== undefined) params.set("top_n", String(filters.top_n));
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export const analyticsApi = {
  pricing: (filters: AnalyticsFilters = {}) =>
    api.get<PricingStats>(`/analytics/pricing${buildParams(filters)}`),
  winRates: (filters: AnalyticsFilters = {}) =>
    api.get<SupplierWinRate[]>(`/analytics/win-rates${buildParams(filters)}`),
  trends: (filters: AnalyticsFilters = {}) =>
    api.get<TrendSeries>(`/analytics/trends${buildParams(filters)}`),
};
