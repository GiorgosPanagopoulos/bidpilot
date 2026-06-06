import { Upload } from "lucide-react";
import { useDraftStore } from "../../store/draftStore";

export function IngestDocButton({ tenderId }: { tenderId: string }) {
  const { isIngesting, ingestError, ingestDoc } = useDraftStore();

  return (
    <div className="rounded-lg border border-dashed border-[#1e2530] bg-[#161a22] p-6 text-center">
      <Upload size={24} className="mx-auto mb-3 text-[#8b93a0]" />
      <p className="mb-1 text-sm text-[#e8eaed]">Tender document not ingested</p>
      <p className="mb-4 text-xs text-[#8b93a0]">
        Ingest the PDF to enable RAG-powered bid drafting
      </p>
      <button
        onClick={() => ingestDoc(tenderId)}
        disabled={isIngesting}
        className="rounded-md bg-[#c9a84c] px-4 py-2 text-sm font-medium text-[#0f1117] hover:bg-[#a07c34] disabled:opacity-50 transition-colors"
      >
        {isIngesting ? "Ingesting…" : "Ingest tender document"}
      </button>
      {ingestError && <p className="mt-2 text-xs text-red-400">{ingestError}</p>}
    </div>
  );
}
