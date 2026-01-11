const assurances = [
  "Private cloud and on-prem deployment options",
  "SOC2-ready audit logging and immutable evidence",
  "SSO with Okta, Azure AD, or Google Workspace",
  "Dedicated customer success and 24/7 security response",
];

export default function Enterprise() {
  return (
    <div className="bg-slate-950 text-white min-h-screen p-20">
      <h1 className="text-5xl font-extrabold">Built for regulated enterprises</h1>
      <p className="text-lg text-slate-300 mt-4 max-w-3xl">
        Deploy T79AI into isolated environments with full control over data, identity, and operational
        governance. Pair AI autonomy with the auditability and compliance posture your board expects.
      </p>

      <div className="mt-10 grid md:grid-cols-2 gap-8">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8">
          <h2 className="text-2xl font-bold text-cyan-300">Enterprise assurance</h2>
          <ul className="mt-4 space-y-3 text-slate-200">
            {assurances.map((item) => (
              <li key={item} className="flex gap-2 items-start">
                <span className="text-cyan-400">◆</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8">
          <h2 className="text-2xl font-bold text-cyan-300">Security operations AI</h2>
          <p className="text-slate-200 leading-relaxed mt-3">
            Leverage autonomous agents for patch orchestration, Kubernetes repair, CI/CD diagnostics, and
            live runbooks backed by RAG-driven reasoning. Every action is traceable and reversible.
          </p>
        </div>
      </div>

      <div className="mt-12">
        <div className="bg-slate-900 p-8 rounded-xl border border-slate-800 max-w-2xl">
            <h3 className="text-xl font-bold text-white mb-4">Start your pilot</h3>
             <form className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-semibold text-slate-400 mb-1">Work Email</label>
                    <input
                    type="email"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2.5 focus:border-blue-500 focus:outline-none"
                    placeholder="you@company.com"
                    required
                    />
                </div>
                <div>
                    <label className="block text-sm font-semibold text-slate-400 mb-1">Company</label>
                    <input
                    type="text"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2.5 focus:border-blue-500 focus:outline-none"
                    placeholder="Your organization"
                    required
                    />
                </div>
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-400 mb-1">What do you want to secure?</label>
                <textarea
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2.5 focus:border-blue-500 focus:outline-none"
                  rows={3}
                  placeholder="Cloud footprint, CI/CD, Kubernetes, data stores, or all of the above"
                />
              </div>
              <button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 py-2.5 rounded-lg font-semibold transition"
              >
                Request a demo
              </button>
            </form>
        </div>
      </div>
    </div>
  );
}
