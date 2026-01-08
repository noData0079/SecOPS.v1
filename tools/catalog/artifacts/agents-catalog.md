# Agents Catalog

Generated from: `agents`

Total agents: **1**

## example-agent — 0.1.0

Minimal, production-ready agent scaffold for SecOPS.v1 (health, metrics, config, graceful shutdown).

- Path: `agents/example_agent`
- Metrics: 3

### Metrics

| name | type | units | description |
|---|---|---|---|
| `example_agent_requests_total` | counter | requests/s | Total HTTP requests received by the agent, labeled by method and path. |
| `example_agent_errors_total` | counter | errors/s | Total application errors (exceptions captured). |
| `example_agent_uptime_seconds` | gauge | seconds | Agent process uptime in seconds. |

### Alerts

- example-agent-high-error-rate
- example-agent-no-metrics
