"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

export type CostBreakdownPoint = {
  label: string;   // e.g. "Jan 2025" or "This month"
  infra: number;   // infra / hosting / k8s / supabase
  llm: number;     // LLM API usage
  storage: number; // object/vectordb/storage
  other: number;   // misc, monitoring, etc.
};

type CostBreakdownBarChartProps = {
  data: CostBreakdownPoint[];
  currency?: string; // default "₹"
};

/**
 * CostBreakdownBarChart
 *
 * Stacked bar chart displaying cost breakdown per period (e.g. month).
 *
 * Example data:
 * [
 *   { label: "Jan", infra: 40, llm: 25, storage: 5, other: 10 },
 *   { label: "Feb", infra: 42, llm: 30, storage: 6, other: 8 }
 * ]
 */

export default function CostBreakdownBarChart({
  data,
  currency = "₹",
}: CostBreakdownBarChartProps) {
  const formatCurrency = (value: number) =>
    `${currency}${value.toLocaleString(undefined, {
      maximumFractionDigits: 0,
    })}`;

  return (
    <div className="w-full h-72 rounded-xl border bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-800 mb-3">
        Monthly Cost Breakdown
      </h3>

      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />

          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={false}
            tickLine={false}
          />

          <YAxis
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={false}
            tickLine={false}
            width={48}
            tickFormatter={formatCurrency}
          />

          <Tooltip
            formatter={(value: any) => formatCurrency(Number(value))}
            contentStyle={{
              backgroundColor: "white",
              borderRadius: "8px",
              border: "1px solid #e2e8f0",
              fontSize: "12px",
            }}
          />

          <Legend
            verticalAlign="bottom"
            height={36}
            wrapperStyle={{
              fontSize: "11px",
              paddingTop: "10px",
              color: "#475569",
            }}
          />

          <Bar
            dataKey="infra"
            stackId="cost"
            name="Infra / Hosting"
            fill="#0f172a"
          />
          <Bar
            dataKey="llm"
            stackId="cost"
            name="LLM Usage"
            fill="#3b82f6"
          />
          <Bar
            dataKey="storage"
            stackId="cost"
            name="Storage"
            fill="#22c55e"
          />
          <Bar
            dataKey="other"
            stackId="cost"
            name="Other"
            fill="#eab308"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
