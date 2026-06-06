interface ScoreBreakdownProps {
  semanticScore: number;
  ruleScore: number;
  finalScore: number;
}

function Bar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-16 shrink-0 text-[#8b93a0]">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-[#1e2530]">
        <div
          className="h-full rounded-full bg-[#c9a84c]"
          style={{ width: `${pct}%` }}
          data-testid={`bar-${label.toLowerCase().replace(/\s+/g, "-")}`}
        />
      </div>
      <span className="w-8 text-right text-[#8b93a0]">{pct}%</span>
    </div>
  );
}

export function ScoreBreakdown({ semanticScore, ruleScore, finalScore }: ScoreBreakdownProps) {
  return (
    <div className="space-y-1.5" data-testid="score-breakdown">
      <div className="mb-1 flex items-baseline gap-2">
        <span className="text-lg font-bold text-[#c9a84c]">
          {Math.round(finalScore * 100)}
        </span>
        <span className="text-xs text-[#8b93a0]">final score</span>
      </div>
      <Bar label="Semantic" value={semanticScore} />
      <Bar label="Rule" value={ruleScore} />
    </div>
  );
}
