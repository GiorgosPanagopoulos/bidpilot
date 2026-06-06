import { AlertCircle } from "lucide-react";
import { useEffect } from "react";
import type { BidDraft } from "../../api/types";
import { useDraftStore } from "../../store/draftStore";
import { DraftSectionView } from "./DraftSection";
import { GapReportView } from "./GapReportView";
import { RequirementChecklistView } from "./RequirementChecklist";
import { TracePanel } from "./TracePanel";

export function BidDraftView({ draft }: { draft: BidDraft }) {
  const { trace, fetchTrace } = useDraftStore();

  useEffect(() => {
    fetchTrace(draft.id);
  }, [draft.id, fetchTrace]);

  return (
    <div className="space-y-6">
      {/* Human review banner */}
      <div className="flex items-start gap-3 rounded-lg border border-amber-800/50 bg-amber-900/10 p-4">
        <AlertCircle size={16} className="mt-0.5 shrink-0 text-amber-400" />
        <p className="text-sm text-amber-300">{draft.notice}</p>
      </div>

      {/* Requirements */}
      <section>
        <h3 className="mb-3 text-sm font-semibold text-[#e8eaed]">Requirement Checklist</h3>
        <RequirementChecklistView checklist={draft.checklist} />
      </section>

      {/* Gap report */}
      <section>
        <h3 className="mb-3 text-sm font-semibold text-[#e8eaed]">Gap Report</h3>
        <GapReportView report={draft.gap_report} checklist={draft.checklist} />
      </section>

      {/* Draft sections */}
      <section>
        <h3 className="mb-3 text-sm font-semibold text-[#e8eaed]">Draft Sections</h3>
        <div className="space-y-3">
          {draft.sections.map((section, i) => (
            <DraftSectionView key={i} section={section} />
          ))}
        </div>
      </section>

      {/* Trace */}
      {trace && trace.length > 0 && (
        <section>
          <TracePanel steps={trace} />
        </section>
      )}

      <p className="text-xs text-[#8b93a0]">
        Prompt version: {draft.prompt_version} · Generated:{" "}
        {new Date(draft.created_at).toLocaleString()}
      </p>
    </div>
  );
}
