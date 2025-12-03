export default function Features() {
  const features = [
    "Full-stack automated scanning (CI/CD, K8s, Cloud, Code)",
    "AI-powered root cause analysis",
    "Zero-downtime security patching",
    "Database integrity monitoring & auto-repair",
    "Multi-model AI brain (GPT-4.1 | Claude | Gemini | Llama)",
    "Self-healing Kubernetes operators",
  ];

  return (
    <div className="px-20 py-20">
      <h1 className="text-6xl font-bold mb-10">Features</h1>

      <ul className="space-y-6 text-2xl text-gray-300">
        {features.map((feature) => (
          <li key={feature} className="border-l-4 border-blue-600 pl-6">
            {feature}
          </li>
        ))}
      </ul>
    </div>
  );
}
