import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrendSeries } from "../../api/types";

interface Props {
  series: TrendSeries | null;
}

export function TrendsChart({ series }: Props) {
  if (!series || series.points.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-[#1e2530] text-sm text-[#8b93a0]">
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={series.points} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="goldGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#c9a84c" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#c9a84c" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e2530" />
        <XAxis dataKey="period" tick={{ fill: "#8b93a0", fontSize: 11 }} />
        <YAxis tick={{ fill: "#8b93a0", fontSize: 11 }} width={40} />
        <Tooltip
          contentStyle={{ background: "#161a22", border: "1px solid #1e2530", borderRadius: 8 }}
          labelStyle={{ color: "#e8eaed" }}
        />
        <Area
          type="monotone"
          dataKey="count"
          stroke="#c9a84c"
          fill="url(#goldGradient)"
          strokeWidth={2}
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
