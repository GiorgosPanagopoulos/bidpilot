import type { GapReport, RequirementChecklist } from "../../api/types";

const STATUS_COLOR: Record<string, string> = {
  met: "text-green-400",
  partial: "text-amber-400",
  unmet: "text-red-400",
};

const STATUS_BG: Record<string, string> = {
  met: "bg-green-900/20",
  partial: "bg-amber-900/20",
  unmet: "bg-red-900/20",
};

interface Props {
  report: GapReport;
  checklist: RequirementChecklist;
}

export function GapReportView({ report, checklist }: Props) {
  const pct = Math.round(report.coverage_ratio * 100);
  const reqMap = Object.fromEntries(checklist.items.map((i) => [i.id, i.text]));

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <div className="relative h-16 w-16">
          <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36">
            <circle cx="18" cy="18" r="15" fill="none" stroke="#1e2530" strokeWidth="3" />
            <circle
              cx="18"
              cy="18"
              r="15"
              fill="none"
              stroke="#c9a84c"
              strokeWidth="3"
              strokeDasharray={`${pct * 0.942} 94.2`}
              strokeLinecap="round"
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-[#c9a84c]">
            {pct}%
          </span>
        </div>
        <div>
          <p className="text-sm font-medium text-[#e8eaed]">Coverage ratio</p>
          <p className="text-xs text-[#8b93a0]">
            {report.items.filter((i) => i.status === "met").length} of {report.items.length}{" "}
            requirements met
          </p>
        </div>
      </div>

      <div className="space-y-2">
        {report.items.map((item) => (
          <div
            key={item.requirement_id}
            className={`rounded-md border border-[#1e2530] p-3 ${STATUS_BG[item.status] ?? ""}`}
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-xs text-[#e8eaed]">
                {reqMap[item.requirement_id] ?? item.requirement_id}
              </p>
              <span className={`shrink-0 text-xs font-medium capitalize ${STATUS_COLOR[item.status] ?? ""}`}>
                {item.status}
              </span>
            </div>
            {item.note && <p className="mt-1 text-xs text-[#8b93a0]">{item.note}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
