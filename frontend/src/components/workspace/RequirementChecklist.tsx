import type { RequirementChecklist } from "../../api/types";
import { CitationChip } from "./CitationChip";

const CATEGORY_ORDER = [
  "technical",
  "financial",
  "legal",
  "administrative",
  "submission",
] as const;

const CATEGORY_LABEL: Record<string, string> = {
  technical: "Technical",
  financial: "Financial",
  legal: "Legal",
  administrative: "Administrative",
  submission: "Submission",
};

interface Props {
  checklist: RequirementChecklist;
}

export function RequirementChecklistView({ checklist }: Props) {
  const byCategory = CATEGORY_ORDER.map((cat) => ({
    cat,
    items: checklist.items.filter((i) => i.category === cat),
  })).filter((g) => g.items.length > 0);

  return (
    <div className="space-y-4">
      {byCategory.map(({ cat, items }) => (
        <div key={cat}>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-[#8b93a0]">
            {CATEGORY_LABEL[cat]}
          </h4>
          <div className="space-y-2">
            {items.map((item) => (
              <div
                key={item.id}
                className="flex items-start gap-2 rounded-md border border-[#1e2530] bg-[#0f1117] p-3"
              >
                <span
                  className={`mt-0.5 shrink-0 text-xs font-medium ${
                    item.mandatory ? "text-red-400" : "text-[#8b93a0]"
                  }`}
                >
                  {item.mandatory ? "REQ" : "OPT"}
                </span>
                <div className="min-w-0">
                  <p className="text-xs text-[#e8eaed]">{item.text}</p>
                  <div className="mt-1">
                    <CitationChip
                      locator={item.citation.locator}
                      snippet={item.citation.snippet}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
