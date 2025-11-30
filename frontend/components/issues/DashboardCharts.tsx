"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Bar,
  BarChart,
  CartesianGrid,
} from "recharts";
import Card from "../shared/Card";
import Loader from "../shared/Loader";
import EmptyState from "../shared/EmptyState";

interface IssueTrendPoint {
  date: string;
  count: number;
}

interface SeverityDistribution {
  severity: "low" | "medium" | "high" | "critical";
  count: number;
}

interface DashboardChartsProps {
  loading: boolean;
  issueTrend: IssueTrendPoint[];
  severityStats: SeverityDistribution[];
}

const DashboardCharts: React.FC<DashboardChartsProps> = ({
  loading,
  issueTrend,
  severityStats,
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card><Loader /></Card>
        <Card><Loader /></Card>
      </div>
    );
  }

  if ((!issueTrend || issueTrend.length === 0) &&
      (!severityStats || severityStats.length === 0)) {
    return <EmptyState title="No Data Yet" description="Run checks to populate dashboard charts." />;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* ------------------------------------------------ */}
      {/* Issue Trend Over Time */}
      {/* ------------------------------------------------ */}
      <Card title="Issues Over Time">
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={issueTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2f2f2f" />
              <XAxis dataKey="date" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip
                contentStyle={{ backgroundColor: "#111", border: "1px solid #333" }}
                labelStyle={{ color: "#fff" }}
              />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#4f9fff"
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* ------------------------------------------------ */}
      {/* Severity Distribution */}
      {/* ------------------------------------------------ */}
      <Card title="Severity Distribution">
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={severityStats}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2f2f2f" />
              <XAxis dataKey="severity" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip
                contentStyle={{ backgroundColor: "#111", border: "1px solid #333" }}
                labelStyle={{ color: "#fff" }}
              />
              <Bar dataKey="count" fill="#ff5757" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
};

export default DashboardCharts;
