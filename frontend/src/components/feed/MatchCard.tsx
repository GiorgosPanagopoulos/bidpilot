import { FileText } from "lucide-react";
import { useDraftStore } from "../../store/draftStore";
import { useFeedStore } from "../../store/feedStore";
import type { MatchResult } from "../../api/types";
import { EligibilityBadge } from "./EligibilityBadge";
import { ScoreBreakdown } from "./ScoreBreakdown";

interface MatchCardProps {
  match: MatchResult;
  onOpen: () => void;
}

export function MatchCard({ match, onOpen }: MatchCardProps) {
  const tender = useFeedStore((s) => s.getTender(match.tender_id));
  const selectTender = useDraftStore((s) => s.selectTender);
  const dimmed = !match.eligibility.passed;

  function handleOpen() {
    if (tender) selectTender(tender);
    onOpen();
  }

  return (
    <div
      className={`rounded-lg border bg-[#161a22] p-4 transition-colors hover:border-[#c9a84c]/30 ${
        dimmed ? "border-[#1e2530] opacity-60" : "border-[#1e2530]"
      }`}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-medium text-[#e8eaed]">
            {tender?.title ?? match.tender_id}
          </h3>
          {tender && (
            <p className="mt-0.5 text-xs text-[#8b93a0]">
              {tender.source} · {tender.cpv_codes.slice(0, 2).join(", ")}
            </p>
          )}
        </div>
        <EligibilityBadge
          passed={match.eligibility.passed}
          failedCriteria={match.eligibility.failed_criteria}
          warnings={match.eligibility.warnings}
        />
      </div>

      <ScoreBreakdown
        semanticScore={match.semantic_score}
        ruleScore={match.rule_score}
        finalScore={match.score}
      />

      {match.reasons.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {match.reasons.map((r, i) => (
            <span
              key={i}
              className="rounded-full bg-[#1e2530] px-2 py-0.5 text-xs text-[#8b93a0]"
            >
              {r}
            </span>
          ))}
        </div>
      )}

      {match.eligibility.passed && (
        <button
          onClick={handleOpen}
          className="mt-3 flex items-center gap-1.5 text-xs font-medium text-[#c9a84c] hover:text-[#a07c34] transition-colors"
        >
          <FileText size={12} />
          Open in Workspace
        </button>
      )}
    </div>
  );
}
