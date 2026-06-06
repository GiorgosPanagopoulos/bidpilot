import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SupplierWinRate } from "../../api/types";

interface Props {
  rates: SupplierWinRate[];
}

export function WinRatesChart({ rates }: Props) {
  if (rates.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-[#1e2530] text-sm text-[#8b93a0]">
        No data available
      </div>
    );
  }

  const top = rates.slice(0, 10);
  const maxWins = top[0]?.awards_won ?? 1;

  return (
    <ResponsiveContainer width="100%" height={Math.max(160, top.length * 36)}>
      <BarChart
        layout="vertical"
        data={top}
        margin={{ top: 4, right: 60, bottom: 0, left: 0 }}
      >
        <XAxis type="number" tick={{ fill: "#8b93a0", fontSize: 11 }} />
        <YAxis
          type="category"
          dataKey="supplier_name"
          tick={{ fill: "#8b93a0", fontSize: 11 }}
          width={120}
        />
        <Tooltip
          formatter={(v: number, name: string) => [v, name]}
          contentStyle={{ background: "#161a22", border: "1px solid #1e2530", borderRadius: 8 }}
          labelStyle={{ color: "#e8eaed" }}
        />
        <Bar dataKey="awards_won" radius={[0, 3, 3, 0]}>
          {top.map((entry, i) => (
            <Cell
              key={entry.supplier_name}
              fill={`rgba(201,168,76,${0.9 - (i / Math.max(top.length - 1, 1)) * 0.5})`}
            />
          ))}
        </Bar>
        {/* win_share label on bars */}
        <text />
      </BarChart>
    </ResponsiveContainer>
  );
  void maxWins;
}
