"use client";

import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card } from "@/components/shared/Card";

// Mock data for Risk Burn-down
const RISK_DATA = [
  { day: "Mon", riskScore: 85 },
  { day: "Tue", riskScore: 82 },
  { day: "Wed", riskScore: 78 },
  { day: "Thu", riskScore: 72 },
  { day: "Fri", riskScore: 68 },
  { day: "Sat", riskScore: 66 },
  { day: "Sun", riskScore: 66 }, // Flattened out
];

export function StrategicRoadmap() {
  // Mock data for Autonomous ROI
  // "I saved 420 man-hours this month by resolving 1,400 incidents without human intervention."
  const roiStats = useMemo(
    () => ({
      manHoursSaved: 420,
      incidentsResolved: 1400,
      riskReduction: 22, // percent
    }),
    []
  );

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* Risk Burn-down Chart */}
      <Card className="col-span-2 flex flex-col justify-between p-6">
        <div>
          <h2 className="text-lg font-semibold text-neutral-100">
            Risk Burn-down
          </h2>
          <p className="text-sm text-neutral-400">
            &quot;I have reduced our attack surface by {roiStats.riskReduction}%
            this week.&quot;
          </p>
        </div>
        <div className="mt-6 h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={RISK_DATA}
              margin={{
                top: 10,
                right: 30,
                left: 0,
                bottom: 0,
              }}
            >
              <defs>
                <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
              <XAxis dataKey="day" stroke="#a3a3a3" fontSize={12} />
              <YAxis stroke="#a3a3a3" fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#171717",
                  border: "1px solid #404040",
                  color: "#f5f5f5",
                }}
              />
              <Area
                type="monotone"
                dataKey="riskScore"
                stroke="#f43f5e"
                fillOpacity={1}
                fill="url(#colorRisk)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Autonomous ROI Stats */}
      <div className="flex flex-col gap-4">
        <Card className="flex flex-1 flex-col justify-center p-6">
          <h3 className="text-sm font-medium text-neutral-400">
            Man-Hours Saved (This Month)
          </h3>
          <div className="mt-2 text-4xl font-bold text-emerald-400">
            {roiStats.manHoursSaved} h
          </div>
          <p className="mt-1 text-xs text-neutral-500">
            Equivalent to ~{(roiStats.manHoursSaved / 160).toFixed(1)} full-time
            engineers.
          </p>
        </Card>
        <Card className="flex flex-1 flex-col justify-center p-6">
          <h3 className="text-sm font-medium text-neutral-400">
            Incidents Resolved Autonomously
          </h3>
          <div className="mt-2 text-4xl font-bold text-blue-400">
            {roiStats.incidentsResolved.toLocaleString()}
          </div>
          <p className="mt-1 text-xs text-neutral-500">
            Zero human intervention required.
          </p>
        </Card>
      </div>
    </div>
  );
}
