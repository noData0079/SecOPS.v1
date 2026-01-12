
const tiers = [
  {
    name: "Starter",
    price: "$199/mo",
    highlights: ["Up to 5 services", "CI/CD diagnostics", "Weekly security reports"],
  },
  {
    name: "Growth",
    price: "$899/mo",
    highlights: ["Unlimited services", "Autonomous remediation", "24/7 on-call insights"],
  },
  {
    name: "Enterprise",
    price: "Custom",
    highlights: ["Dedicated enclave", "SSO & RBAC", "Named customer success team"],
  },
];

export default function Pricing() {
  return (
    <div className="bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white min-h-screen p-20">
      <h1 className="text-5xl font-extrabold text-center">Choose your command tier</h1>
      <p className="text-lg text-slate-300 mt-4 max-w-2xl mx-auto text-center">
        Straightforward pricing with enterprise security, governance, and observability included.
      </p>

      <div className="grid md:grid-cols-3 gap-8 mt-12">
        {tiers.map((tier) => (
          <div key={tier.name} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8 shadow-xl hover:border-slate-700 transition">
            <h2 className="text-2xl font-bold text-white">{tier.name}</h2>
            <p className="text-4xl font-extrabold mt-4 text-emerald-400">{tier.price}</p>
            <ul className="mt-6 space-y-3 text-slate-300">
              {tier.highlights.map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <span className="text-cyan-400">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <button className="mt-8 w-full bg-blue-600 hover:bg-blue-700 py-3 rounded-lg font-semibold transition text-white">
              Talk to sales
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
