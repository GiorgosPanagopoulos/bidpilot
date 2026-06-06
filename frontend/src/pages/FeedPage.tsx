import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { CompanyPanel } from "../components/feed/CompanyPanel";
import { MatchCard } from "../components/feed/MatchCard";
import { Skeleton } from "../components/ui/Skeleton";
import { useCompanyStore } from "../store/companyStore";
import { useFeedStore } from "../store/feedStore";

export function FeedPage() {
  const { profile } = useCompanyStore();
  const {
    tenders,
    matches,
    isLoadingTenders,
    isRunningMatch,
    error,
    statusFilter,
    cpvFilter,
    setStatusFilter,
    setCpvFilter,
    fetchTenders,
    runMatch,
    fetchMatches,
  } = useFeedStore();
  const navigate = useNavigate();

  useEffect(() => {
    fetchTenders();
  }, [fetchTenders, statusFilter, cpvFilter]);

  useEffect(() => {
    if (profile) fetchMatches(profile.id);
  }, [profile, fetchMatches]);

  return (
    <div className="flex h-full gap-0">
      {/* Sidebar panel */}
      <div className="flex w-72 shrink-0 flex-col gap-4 border-r border-[#1e2530] p-4">
        <CompanyPanel />

        <div className="space-y-2">
          <label className="block text-xs text-[#8b93a0]">Status filter</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full rounded-md border border-[#1e2530] bg-[#0f1117] px-3 py-1.5 text-sm text-[#e8eaed]"
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="closed">Closed</option>
            <option value="awarded">Awarded</option>
          </select>

          <label className="block text-xs text-[#8b93a0]">CPV filter</label>
          <input
            type="text"
            value={cpvFilter}
            onChange={(e) => setCpvFilter(e.target.value)}
            placeholder="e.g. 45000000"
            className="w-full rounded-md border border-[#1e2530] bg-[#0f1117] px-3 py-1.5 text-sm text-[#e8eaed] outline-none focus:border-[#c9a84c]/50"
          />
        </div>

        {profile && (
          <button
            onClick={() => runMatch(profile.id)}
            disabled={isRunningMatch}
            className="rounded-md bg-[#c9a84c] px-4 py-2 text-sm font-medium text-[#0f1117] hover:bg-[#a07c34] disabled:opacity-50 transition-colors"
          >
            {isRunningMatch ? "Running…" : "Run match"}
          </button>
        )}

        <p className="text-xs text-[#8b93a0]">
          {tenders.length} tenders · {matches.length} matches
        </p>
      </div>

      {/* Match results */}
      <div className="flex-1 overflow-y-auto p-4">
        {error && (
          <div className="mb-4 rounded-md border border-red-800 bg-red-900/10 p-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {isLoadingTenders && (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-36 w-full" />
            ))}
          </div>
        )}

        {!isLoadingTenders && matches.length === 0 && (
          <div className="flex h-48 items-center justify-center text-sm text-[#8b93a0]">
            {profile ? "Run match to see results" : "Create a company profile to get started"}
          </div>
        )}

        <div className="space-y-3">
          {matches.map((m, i) => (
            <MatchCard
              key={`${m.tender_id}-${i}`}
              match={m}
              onOpen={() => navigate("/workspace")}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
