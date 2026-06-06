import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PricingStats } from "../../api/types";

interface Props {
  stats: PricingStats;
}

function fmt(n: number | null): string {
  if (n === null) return "—";
  return n >= 1_000_000
    ? `${(n / 1_000_000).toFixed(1)}M`
    : n >= 1_000
      ? `${(n / 1_000).toFixed(0)}K`
      : String(Math.round(n));
}

export function PricingChart({ stats }: Props) {
  if (stats.count === 0) {
    return (
      <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-[#1e2530] text-sm text-[#8b93a0]">
        No data available
      </div>
    );
  }

  const data = [
    { name: "Min", value: stats.min ?? 0 },
    { name: "P25", value: stats.p25 ?? 0 },
    { name: "Median", value: stats.median ?? 0 },
    { name: "P75", value: stats.p75 ?? 0 },
    { name: "Max", value: stats.max ?? 0 },
  ];

  return (
    <div>
      <div className="mb-3 flex items-baseline gap-3">
        <span className="text-2xl font-bold text-[#c9a84c]">{fmt(stats.mean)}</span>
        <span className="text-xs text-[#8b93a0]">
          mean · {stats.count} awards · {stats.currency}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2530" />
          <XAxis dataKey="name" tick={{ fill: "#8b93a0", fontSize: 11 }} />
          <YAxis tickFormatter={fmt} tick={{ fill: "#8b93a0", fontSize: 11 }} width={40} />
          <Tooltip
            formatter={(v: number) => [fmt(v), "Value"]}
            contentStyle={{ background: "#161a22", border: "1px solid #1e2530", borderRadius: 8 }}
            labelStyle={{ color: "#e8eaed" }}
          />
          <Bar dataKey="value" fill="#c9a84c" radius={[3, 3, 0, 0]} />
          {stats.mean !== null && (
            <ReferenceLine y={stats.mean} stroke="#a07c34" strokeDasharray="4 2" />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
