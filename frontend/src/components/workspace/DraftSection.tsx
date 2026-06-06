import { CheckCircle, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import type { BidDraftSection } from "../../api/types";
import { CitationChip } from "./CitationChip";

export function DraftSectionView({ section }: { section: BidDraftSection }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="rounded-lg border border-[#1e2530] bg-[#161a22]">
      <button
        className="flex w-full items-center justify-between p-4 text-left"
        onClick={() => setCollapsed((v) => !v)}
      >
        <div className="flex items-center gap-2">
          {section.self_check_status === "ok" ? (
            <CheckCircle size={14} className="text-green-400" />
          ) : (
            <AlertTriangle size={14} className="text-amber-400" />
          )}
          <span className="text-sm font-medium text-[#e8eaed]">{section.title}</span>
        </div>
        {collapsed ? <ChevronDown size={14} className="text-[#8b93a0]" /> : <ChevronUp size={14} className="text-[#8b93a0]" />}
      </button>

      {!collapsed && (
        <div className="border-t border-[#1e2530] p-4">
          <div className="prose prose-invert prose-sm max-w-none text-[#e8eaed]">
            <ReactMarkdown>{section.content}</ReactMarkdown>
          </div>

          {section.citations.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {section.citations.map((c, i) => (
                <CitationChip key={i} locator={c.locator} snippet={c.snippet} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
