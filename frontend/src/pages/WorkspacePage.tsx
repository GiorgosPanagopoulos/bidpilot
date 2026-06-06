import { useCompanyStore } from "../store/companyStore";
import { useDraftStore } from "../store/draftStore";
import { AgentWorking } from "../components/workspace/AgentWorking";
import { BidDraftView } from "../components/workspace/BidDraftView";
import { IngestDocButton } from "../components/workspace/IngestDocButton";

export function WorkspacePage() {
  const profile = useCompanyStore((s) => s.profile);
  const { selectedTender, isDrafting, draft, draftError, runDraft } = useDraftStore();

  if (!selectedTender) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-[#8b93a0]">Select a tender from the Feed to open it here</p>
      </div>
    );
  }

  const hasDoc = Boolean(selectedTender.raw_doc_uri);

  return (
    <div className="mx-auto max-w-4xl p-6">
      {/* Tender header */}
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-[#e8eaed]">{selectedTender.title}</h1>
        <p className="mt-1 text-xs text-[#8b93a0]">
          {selectedTender.source} · {selectedTender.cpv_codes.join(", ")}
          {selectedTender.budget && ` · Budget: ${selectedTender.budget.toLocaleString()} EUR`}
        </p>
      </div>

      {/* Ingest or draft */}
      {!hasDoc ? (
        <IngestDocButton tenderId={selectedTender.id} />
      ) : isDrafting ? (
        <AgentWorking />
      ) : draft ? (
        <BidDraftView draft={draft} />
      ) : (
        <div className="text-center">
          {draftError && (
            <p className="mb-4 text-sm text-red-400">{draftError}</p>
          )}
          <button
            onClick={() => profile && runDraft(profile.id, selectedTender.id)}
            disabled={!profile}
            className="rounded-md bg-[#c9a84c] px-6 py-2.5 text-sm font-medium text-[#0f1117] hover:bg-[#a07c34] disabled:opacity-50 transition-colors"
          >
            Generate draft
          </button>
          {!profile && (
            <p className="mt-2 text-xs text-[#8b93a0]">Set a company profile first</p>
          )}
        </div>
      )}
    </div>
  );
}
