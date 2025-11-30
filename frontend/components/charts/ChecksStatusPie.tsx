"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export type ChecksStatusData = {
  label: string;      // "Passed" | "Warning" | "Failed"
  value: number;      // count
};

type ChecksStatusPieProps = {
  data: ChecksStatusData[];
};

/**
 * ChecksStatusPie
 *
 * Displays a pie chart showing the distribution of check results:
 * Passed | Warning | Failed.
 *
 * Example:
 * [
 *   { label: "Passed", value: 12 },
 *   { label: "Warning", value: 4 },
 *   { label: "Failed", value: 2 }
 * ]
 */

export default function ChecksStatusPie({ data }: ChecksStatusPieProps) {
  const COLORS = ["#16a34a", "#facc15", "#dc2626"]; // green, yellow, red

  return (
    <div className="w-full h-64 rounded-xl border bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-800 mb-3">
        Checks Status Distribution
      </h3>

      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={40}
            outerRadius={70}
            dataKey="value"
            paddingAngle={3}
            cornerRadius={4}
          >
            {data.map((entry, index) => (
              <Cell key={`${entry.label}-${index}`} fill={COLORS[index]} />
            ))}
          </Pie>

          <Tooltip
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
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
