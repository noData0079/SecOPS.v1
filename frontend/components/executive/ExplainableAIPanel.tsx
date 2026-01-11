"use client";

import {
  ArrowRightIcon,
  CpuChipIcon,
  CircleStackIcon,
  ShieldCheckIcon
} from "@heroicons/react/24/outline";
import { useMemo } from "react";

import { Card } from "@/components/shared/Card";

// Mock data trace
const MOCK_TRACE = {
  decisionId: "evt-9912",
  timestamp: "2023-10-27T14:32:00Z",
  action: "ISOLATE_POD",
  target: "payment-service-v2-pod-5f",
  reasoning: {
    policy: "Zero Trust Network Policy #42",
    memory: "Similar anomaly detected in incident #884 (98% confidence match)",
    observation: "Outbound traffic to unauthorized IP 192.168.x.x detected",
  },
};

export function ExplainableAIPanel() {
  const trace = useMemo(() => MOCK_TRACE, []);

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-neutral-100">
          Explainable AI Decision Trace
        </h2>
        <p className="text-sm text-neutral-400">
          Visualizing the logic path for high-stakes decision{" "}
          <span className="font-mono text-neutral-300">{trace.decisionId}</span>
        </p>
      </div>

      <div className="relative flex flex-col items-center gap-8 md:flex-row md:items-start md:justify-between">
        {/* Step 1: Observation/Trigger */}
        <div className="flex w-full flex-1 flex-col items-center text-center">
          <div className="mb-3 flex size-12 items-center justify-center rounded-full bg-neutral-800 ring-1 ring-neutral-700">
            <CircleStackIcon className="size-6 text-blue-400" />
          </div>
          <h3 className="text-sm font-medium text-neutral-200">Observation</h3>
          <p className="mt-1 text-xs text-neutral-400">
            {trace.reasoning.observation}
          </p>
        </div>

        {/* Connector */}
        <div className="hidden pt-4 md:block">
          <ArrowRightIcon className="size-5 text-neutral-600" />
        </div>

        {/* Step 2: Policy & Memory */}
        <div className="flex w-full flex-1 flex-col items-center text-center">
          <div className="mb-3 flex size-12 items-center justify-center rounded-full bg-neutral-800 ring-1 ring-neutral-700">
            <CpuChipIcon className="size-6 text-purple-400" />
          </div>
          <h3 className="text-sm font-medium text-neutral-200">AI Reasoning</h3>
          <div className="mt-2 space-y-2 text-xs">
            <div className="rounded bg-neutral-900 px-2 py-1 text-neutral-300 ring-1 ring-neutral-800">
              <span className="font-semibold text-purple-300">Policy:</span>{" "}
              {trace.reasoning.policy}
            </div>
            <div className="rounded bg-neutral-900 px-2 py-1 text-neutral-300 ring-1 ring-neutral-800">
              <span className="font-semibold text-amber-300">Memory:</span>{" "}
              {trace.reasoning.memory}
            </div>
          </div>
        </div>

        {/* Connector */}
        <div className="hidden pt-4 md:block">
          <ArrowRightIcon className="size-5 text-neutral-600" />
        </div>

        {/* Step 3: Action */}
        <div className="flex w-full flex-1 flex-col items-center text-center">
          <div className="mb-3 flex size-12 items-center justify-center rounded-full bg-neutral-800 ring-1 ring-neutral-700">
            <ShieldCheckIcon className="size-6 text-emerald-400" />
          </div>
          <h3 className="text-sm font-medium text-neutral-200">
            Action Taken
          </h3>
          <div className="mt-1 text-xs text-neutral-400">
            <p>
              <span className="font-mono font-bold text-emerald-300">
                {trace.action}
              </span>
            </p>
            <p className="mt-1 font-mono text-neutral-500">{trace.target}</p>
          </div>
        </div>
      </div>

      <div className="mt-8 rounded border border-neutral-800 bg-neutral-900/50 p-4">
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">
          Executive Summary
        </h4>
        <p className="text-sm text-neutral-300">
          The AI successfully identified an anomalous outbound connection pattern
          consistent with known exfiltration attempts (98% match). It
          autonomously enforced <strong>Policy #42</strong> to isolate the
          compromised pod, preventing potential data leakage. No human
          intervention was required.
        </p>
      </div>
    </Card>
  );
}
