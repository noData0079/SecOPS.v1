// frontend/app/page.tsx

"use client";

import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  return (
    <div className="flex flex-col min-h-[calc(100vh-64px)] bg-gray-50">
      {/* Hero Section */}
      <section className="flex-1 border-b bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white">
        <div className="max-w-6xl mx-auto px-6 py-16 lg:py-24 grid gap-10 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] items-center">
          {/* Left: Copy */}
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/10 border border-emerald-400/40 px-3 py-1 text-xs text-emerald-100 mb-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Deployment-ready MVP • SecOpsAI Console</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight leading-tight">
              Autonomous{" "}
              <span className="text-emerald-400">DevSecOps intelligence</span>{" "}
              for real-world systems.
            </h1>

            <p className="text-sm sm:text-base text-slate-300 max-w-xl">
              Connect your GitHub, CI, and Kubernetes. SecOpsAI continuously
              scans, explains, and suggests fixes for security gaps, drift, and
              reliability issues – like having a senior DevSecOps engineer
              watching your stack 24/7.
            </p>

            <div className="flex flex-wrap items-center gap-4">
              <button
                onClick={() => router.push("/console")}
                className="inline-flex items-center justify-center rounded-md bg-emerald-500 px-5 py-2.5 text-sm font-medium text-slate-950 shadow-md shadow-emerald-500/30 hover:bg-emerald-400 transition"
              >
                Open SecOps Console
              </button>

              <button
                onClick={() => router.push("/console/issues")}
                className="inline-flex items-center justify-center rounded-md border border-slate-700 bg-slate-900/60 px-5 py-2.5 text-sm font-medium text-slate-100 hover:bg-slate-800 transition"
              >
                View sample issues
              </button>
            </div>

            <div className="flex flex-wrap gap-6 text-xs text-slate-400 pt-4">
              <div className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                <span>Multi-LLM RAG engine</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                <span>GitHub, CI, Kubernetes checks</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                <span>Cost-aware, usage-based compute</span>
              </div>
            </div>
          </div>

          {/* Right: “Live Console” Preview */}
          <div className="relative">
            <div className="absolute -inset-6 rounded-3xl bg-emerald-500/20 blur-3xl opacity-50" />
            <div className="relative border border-slate-700/70 bg-slate-900 rounded-2xl shadow-2xl shadow-black/40 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800/80 bg-slate-950">
                <span className="text-xs font-medium text-slate-200">
                  SecOpsAI • Issues Overview
                </span>
                <span className="flex gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  <span className="h-2 w-2 rounded-full bg-amber-400" />
                  <span className="h-2 w-2 rounded-full bg-red-400" />
                </span>
              </div>

              <div className="px-4 py-3 text-[11px] text-slate-300 border-b border-slate-800/60 bg-slate-900/70">
                <span className="font-medium text-emerald-300">Summary:</span>{" "}
                3 critical, 7 high, 14 medium issues across GitHub, CI/CD, and
                Kubernetes. Top recommendation: lock down public ingress,
                rotate leaked tokens, and enforce least-privilege in workflows.
              </div>

              <div className="divide-y divide-slate-800 text-xs">
                <IssueRow
                  severity="CRITICAL"
                  title="Public K8s ingress exposed with no auth"
                  source="Kubernetes"
                />
                <IssueRow
                  severity="HIGH"
                  title="Github Actions workflow can push to main without approvals"
                  source="GitHub Actions"
                />
                <IssueRow
                  severity="HIGH"
                  title="Outdated dependency with known RCE vulnerability"
                  source="Dependencies"
                />
                <IssueRow
                  severity="MEDIUM"
                  title="Missing resource limits on production workloads"
                  source="Kubernetes"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-6 py-12 lg:py-16">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
                Built for teams who can’t hire 20 DevSecOps engineers.
              </h2>
              <p className="mt-2 text-sm text-slate-600 max-w-xl">
                Connect your existing stack. SecOpsAI continuously analyzes your
                code, config, dependencies, CI, and clusters — then explains
                what’s wrong, why it matters, and how to fix it, step by step.
              </p>
            </div>
          </div>

          <div className="mt-8 grid gap-6 md:grid-cols-3">
            <FeatureCard
              label="01"
              title="Autonomous checks"
              body="Scheduled checks across GitHub, CI workflows, and Kubernetes. Zero setup beyond an API key and a few scopes."
            />
            <FeatureCard
              label="02"
              title="Explain + Fix"
              body="Every issue comes with plain-language explanation, code/config diff suggestions, and test hints to avoid regressions."
            />
            <FeatureCard
              label="03"
              title="Cost-aware brain"
              body="Usage is tracked in real time. You always know how much compute is burned and what your customers should be charged."
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-slate-950 text-slate-50">
        <div className="max-w-6xl mx-auto px-6 py-10 lg:py-12 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="text-lg font-semibold">
              Ready to see what SecOpsAI finds in your stack?
            </h3>
            <p className="mt-1 text-sm text-slate-300 max-w-xl">
              Start with a minimal integration: connect a single GitHub repo or
              a staging cluster. The console will show you a before/after view
              of your security and reliability posture.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => router.push("/console")}
              className="inline-flex items-center justify-center rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-slate-950 shadow-md shadow-emerald-500/30 hover:bg-emerald-400 transition"
            >
              Go to Console
            </button>
            <button
              onClick={() => router.push("/console/settings")}
              className="inline-flex items-center justify-center rounded-md border border-slate-500/70 bg-transparent px-4 py-2 text-sm font-medium text-slate-100 hover:bg-slate-800 transition"
            >
              Configure integrations
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

type IssueRowProps = {
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  title: string;
  source: string;
};

function IssueRow({ severity, title, source }: IssueRowProps) {
  const severityColor =
    severity === "CRITICAL"
      ? "bg-red-500/20 text-red-300 border-red-500/60"
      : severity === "HIGH"
      ? "bg-amber-500/20 text-amber-200 border-amber-500/60"
      : severity === "MEDIUM"
      ? "bg-emerald-500/15 text-emerald-200 border-emerald-500/40"
      : "bg-slate-600/20 text-slate-200 border-slate-500/60";

  return (
    <div className="flex items-start gap-3 px-4 py-3 bg-slate-900/70">
      <span
        className={`mt-0.5 inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold tracking-wide uppercase ${severityColor}`}
      >
        {severity}
      </span>
      <div className="flex-1 space-y-1">
        <p className="text-[11px] text-slate-100">{title}</p>
        <p className="text-[10px] text-slate-400">Source: {source}</p>
      </div>
    </div>
  );
}

type FeatureCardProps = {
  label: string;
  title: string;
  body: string;
};

function FeatureCard({ label, title, body }: FeatureCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-mono text-slate-400">#{label}</span>
      </div>
      <h3 className="text-sm font-semibold text-slate-900 mb-1">{title}</h3>
      <p className="text-xs text-slate-600">{body}</p>
    </div>
  );
}
