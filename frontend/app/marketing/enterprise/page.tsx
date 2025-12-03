import EnterpriseBlock from "../components/EnterpriseBlock";

export default function Enterprise() {
  return (
    <div className="px-20 py-20">
      <h1 className="text-6xl font-bold">Enterprise</h1>
      <p className="mt-10 text-2xl text-gray-300 max-w-3xl">
        SecOpsAI is built for global-scale companies requiring high availability,
        custom compliance, on-premise deployment, and private LLM execution.
      </p>

      <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-12">
        <EnterpriseBlock title="Private Cloud / On-Prem" desc="Deploy inside your firewalls." />
        <EnterpriseBlock
          title="Dedicated LLM Compute"
          desc="Run custom tuned models isolated per client."
        />
        <EnterpriseBlock
          title="SOC2, GDPR, HIPAA readiness"
          desc="Fully compliant auditing and privacy controls."
        />
        <EnterpriseBlock title="24/7 Autonomous Agent Monitoring" desc="AI agents that never sleep." />
      </div>
    </div>
  );
}
