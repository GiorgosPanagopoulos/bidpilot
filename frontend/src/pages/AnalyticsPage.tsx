import { useEffect } from "react";
import { PricingChart } from "../components/analytics/PricingChart";
import { TrendsChart } from "../components/analytics/TrendsChart";
import { WinRatesChart } from "../components/analytics/WinRatesChart";
import { Skeleton } from "../components/ui/Skeleton";
import { useAnalyticsStore } from "../store/analyticsStore";

const INTERVALS = ["month", "quarter", "year"] as const;

export function AnalyticsPage() {
  const { cpv, authority, from, to, interval, pricing, winRates, trends, isLoading, error, setFilter, fetchAll } =
    useAnalyticsStore();

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  function applyFilters(e: React.FormEvent) {
    e.preventDefault();
    fetchAll();
  }

  return (
    <div className="p-6">
      <h1 className="mb-6 text-lg font-semibold text-[#e8eaed]">Award Analytics</h1>

      {/* Filters */}
      <form onSubmit={applyFilters} className="mb-6 flex flex-wrap items-end gap-3">
        {(
          [
            ["cpv", "CPV code", cpv],
            ["authority", "Contracting authority", authority],
            ["from", "From date", from],
            ["to", "To date", to],
          ] as const
        ).map(([key, label, val]) => (
          <div key={key}>
            <label className="mb-1 block text-xs text-[#8b93a0]">{label}</label>
            <input
              type="text"
              value={val}
              onChange={(e) => setFilter(key, e.target.value)}
              className="rounded-md border border-[#1e2530] bg-[#161a22] px-3 py-1.5 text-sm text-[#e8eaed] outline-none focus:border-[#c9a84c]/50"
            />
          </div>
        ))}

        <div>
          <label className="mb-1 block text-xs text-[#8b93a0]">Interval</label>
          <select
            value={interval}
            onChange={(e) => setFilter("interval", e.target.value as typeof interval)}
            className="rounded-md border border-[#1e2530] bg-[#161a22] px-3 py-1.5 text-sm text-[#e8eaed]"
          >
            {INTERVALS.map((i) => (
              <option key={i} value={i}>
                {i.charAt(0).toUpperCase() + i.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          className="rounded-md bg-[#c9a84c] px-4 py-2 text-sm font-medium text-[#0f1117] hover:bg-[#a07c34] transition-colors"
        >
          Apply
        </button>
      </form>

      {error && (
        <div className="mb-4 rounded-md border border-red-800 bg-red-900/10 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Pricing */}
        <div className="rounded-lg border border-[#1e2530] bg-[#161a22] p-4">
          <h2 className="mb-4 text-sm font-semibold text-[#e8eaed]">Pricing Statistics</h2>
          {isLoading ? <Skeleton className="h-48 w-full" /> : pricing ? <PricingChart stats={pricing} /> : null}
        </div>

        {/* Win rates */}
        <div className="rounded-lg border border-[#1e2530] bg-[#161a22] p-4">
          <h2 className="mb-4 text-sm font-semibold text-[#e8eaed]">Supplier Win Rates</h2>
          {isLoading ? <Skeleton className="h-48 w-full" /> : <WinRatesChart rates={winRates} />}
        </div>

        {/* Trends — full width */}
        <div className="rounded-lg border border-[#1e2530] bg-[#161a22] p-4 lg:col-span-2">
          <h2 className="mb-4 text-sm font-semibold text-[#e8eaed]">
            Award Trends ({interval})
          </h2>
          {isLoading ? <Skeleton className="h-48 w-full" /> : <TrendsChart series={trends} />}
        </div>
      </div>
    </div>
  );
}
