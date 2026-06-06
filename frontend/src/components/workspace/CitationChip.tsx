import { useState } from "react";
import { BookOpen } from "lucide-react";

interface CitationChipProps {
  locator: string;
  snippet: string;
}

export function CitationChip({ locator, snippet }: CitationChipProps) {
  const [open, setOpen] = useState(false);

  return (
    <span className="relative inline-block">
      <button
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-1 rounded border border-[#c9a84c]/30 bg-[#c9a84c]/10 px-1.5 py-0.5 text-xs font-mono text-[#c9a84c] hover:bg-[#c9a84c]/20 transition-colors"
        aria-expanded={open}
        aria-label={`Citation ${locator}`}
      >
        <BookOpen size={10} />
        {locator}
      </button>
      {open && (
        <div className="absolute bottom-full left-0 z-20 mb-1 w-72 rounded-lg border border-[#c9a84c]/20 bg-[#161a22] p-3 text-xs text-[#8b93a0] shadow-xl">
          <p className="mb-1 font-medium text-[#c9a84c]">{locator}</p>
          <p className="leading-relaxed">{snippet}</p>
        </div>
      )}
    </span>
  );
}
