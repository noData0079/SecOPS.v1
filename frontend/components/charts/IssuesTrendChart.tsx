"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

export type IssueTrendPoint = {
  date: string;     // e.g. "2025-01-02"
  issues: number;   // number of issues on that day
};

type IssuesTrendChartProps = {
  data: IssueTrendPoint[];
};

/**
 * IssuesTrendChart
 *
 * Displays issue trends over time.
 * Uses Recharts for smooth, responsive visualization.
 *
 * Example data:
 * [
 *   { date: "2025-01-01", issues: 2 },
 *   { date: "2025-01-02", issues: 6 },
 *   { date: "2025-01-03", issues: 3 }
 * ]
 */

export default function IssuesTrendChart({ data }: IssuesTrendChartProps) {
  return (
    <div className="w-full h-64 rounded-xl border bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-800 mb-3">
        Issues Trend Over Time
      </h3>

      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 15, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="issuesGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0f172a" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#0f172a" stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />

          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={false}
            tickLine={false}
          />

          <YAxis
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={false}
            tickLine={false}
            width={30}
          />

          <Tooltip
            contentStyle={{
              backgroundColor: "white",
              borderRadius: "8px",
              border: "1px solid #e2e8f0",
              fontSize: "12px",
            }}
          />

          <Area
            type="monotone"
            dataKey="issues"
            stroke="#0f172a"
            fill="url(#issuesGradient)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
