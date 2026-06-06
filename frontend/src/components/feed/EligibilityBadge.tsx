import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import { useState } from "react";

interface EligibilityBadgeProps {
  passed: boolean;
  failedCriteria: string[];
  warnings: string[];
}

export function EligibilityBadge({ passed, failedCriteria, warnings }: EligibilityBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  if (passed && warnings.length === 0) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-900/30 px-2 py-0.5 text-xs font-medium text-green-400">
        <CheckCircle size={12} />
        Passed
      </span>
    );
  }

  if (!passed) {
    return (
      <div className="relative inline-block">
        <button
          className="inline-flex items-center gap-1 rounded-full bg-red-900/30 px-2 py-0.5 text-xs font-medium text-red-400"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          aria-label={`Eligibility failed: ${failedCriteria.join(", ")}`}
        >
          <XCircle size={12} />
          Failed
        </button>
        {showTooltip && failedCriteria.length > 0 && (
          <div className="absolute bottom-full left-0 mb-1 w-48 rounded-md border border-[#1e2530] bg-[#161a22] p-2 text-xs text-[#8b93a0] shadow-xl z-10">
            {failedCriteria.map((c) => (
              <div key={c} className="py-0.5">
                {c}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-amber-900/30 px-2 py-0.5 text-xs font-medium text-amber-400">
      <AlertTriangle size={12} />
      Warnings
    </span>
  );
}
