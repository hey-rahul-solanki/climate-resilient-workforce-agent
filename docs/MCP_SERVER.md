# Climate planning MCP server

## Status and shared application boundary

Implemented: local stdio MCP transport using the official Python SDK (`mcp>=1.28,<2`),
an agent entry point, typed tool schemas and canonical schema/usage resources, authenticated REST bridge, shared deterministic
context/warning/suggestion services, session ownership/expiry, proposal-only actions and
separately enabled note annotation. No MCP approval or event-time write tool exists.

The stdio adapter does not duplicate forecasting, policy or scheduling logic. It
calls `/api/agent`, which uses `AgentService`, `analyze_calendar`, the suggestion
validator, and the same transactional demo calendar adapter as the UI. Custom
services may call these Python services or the
[versioned climate service API](CLIMATE_SERVICE_API_V1.md) directly.
Fixtures remain explicit. A local tool call does not imply Google Calendar,
Agent Engine, or Model Armor is connected. Gemini is used only when the backend
reasoning provider is explicitly set to Vertex; local ADC and one live Gemini call
have been verified for this development project.

## Local startup

1. Install the backend and optional MCP SDK: `pip install -e '.[api,mcp]'`.
2. Start the existing backend (`workforce-api`) or `docker compose up --build -d`.
3. Provision a high-entropy opaque token in the backend's server-only
   `WORKFORCE_AGENT_CREDENTIALS` JSON mapping. The value is a principal such as
   `{subject: "supervisor-1", permissions: ["read", "propose", "annotate"],
   sites: ["VAD-PLANT-01"]}`. Use valid JSON with quoted keys. Do not commit tokens.
4. Set that same token in the MCP process as `WORKFORCE_AGENT_TOKEN`. Set
   `WORKFORCE_AGENT_API_URL=http://127.0.0.1:8000` for local backend access.
5. Run `workforce-agent-mcp`, or `python -m workforce_agent.mcp_server`. It reads
   stdio protocol messages; do not expect a browser page or startup text on stdout.

For local Gemini-backed development, start the API with the following runtime settings
after installing `.[api,mcp,vertex]` and configuring ADC. The backend agent calls Vertex;
the MCP process itself needs only its backend URL and supervisor token.

```sh
export WORKFORCE_REASONING_PROVIDER=vertex
export WORKFORCE_VERTEX_PROJECT=climate-workforce-agent
export WORKFORCE_VERTEX_LOCATION=global
export WORKFORCE_VERTEX_MODEL=gemini-3.5-flash-lite
export WORKFORCE_AGENT_CREDENTIALS='{"<high-entropy-token>":{"subject":"local-supervisor","permissions":["read","propose"],"sites":["VAD-PLANT-01"]}}'
.venv/bin/workforce-api
```

Configure the same token in the MCP host's secret environment as
`WORKFORCE_AGENT_TOKEN`. The MCP host invokes `climate_agent` with a day/site on its
first turn and the returned session ID on follow-ups. Clear supported requests do not
call Gemini; other chat requests use Vertex and still pass deterministic validation.

Docker forwards `WORKFORCE_AGENT_CREDENTIALS` into the backend; recreate the backend
when changing grants. The MCP process runs locally against the exposed backend port.
Use HTTPS for non-loopback API hosts. URL userinfo/query/fragment credentials are
rejected; bearer tokens stay in the Authorization header, redirects are not followed,
and remote plaintext HTTP is rejected. Local Docker preview uses no live provider
credentials. A separate MCP process/credential represents one user or workload.

### One MCP host configuration

Use the absolute virtualenv Python path for your checkout:

```json
{
  "mcpServers": {
    "climate-workforce": {
      "command": "/absolute/path/to/project/.venv/bin/python",
      "args": ["-m", "workforce_agent.mcp_server"],
      "env": {
        "WORKFORCE_AGENT_API_URL": "http://127.0.0.1:8000",
        "WORKFORCE_AGENT_TOKEN": "<provisioned secret; use host secret storage>"
      }
    }
  }
}
```

The placeholder is not a functional credential. Provision it through the client's
secret facility/environment and matching backend grants. Start with read-only
permission and add propose/annotate only where explicitly needed.

A runnable SDK client example is `python scripts/mcp_client_example.py`. The primary
`climate_agent` tool starts or continues an authenticated planning conversation using
context loaded by the backend; the caller does not need to upload a schedule or policy.
Today that backend context is the explicitly labelled isolated demo fixture. No customer
calendar or employee data source is connected by default. A deployment must connect and
authorize its own operational data source before presenting results as customer-specific.
The separate `analyze_consumer_schedule` tool remains available for clients that explicitly
choose to submit their own schedule and policy; it is not required by `climate_agent`.

## Tool schemas and permissions

SDK discovery exposes JSON input/output schemas generated from annotations and
Pydantic models. `session_id` is a 43-character URL-safe opaque ID; it is never an
identity credential. HH:MM constraints use 24-hour site time. `activity_id` is a
nonempty stable event ID within the selected session/day (maximum 100 characters).

| Tool | Input | Permission | Output/action |
| --- | --- | --- | --- |
| `climate_agent` | message; day/site for a new session or session_id for follow-up | session owner + read; propose for proposals | primary entry point; backend loads its authorized context; deterministic path for clear requests, configured reasoning for interpretation; proposal-only |
| `analyze_consumer_schedule` | canonical `context` and applicable `policy` | read + submitted site | backend fetches weather and analyzes it against the supplied policy; returns exact warning overlaps and freshness evidence; no source writes |
| `create_supervisor_session` | ISO `day`, `site_id` | read + site | `Reply` with isolated expiring session |
| `list_affected_activities` | session_id | owner + read + site | all affected/review context with exact warning intersections |
| `get_climate_suggestions` | session_id | owner + read + site | existing structured suggestions, no proposal creation |
| `propose_reschedule` | session_id, `{earliest?, latest?}` constraints | owner + propose + site | validated pending proposals or explicit infeasible/review result; no time write |
| `annotate_affected_activity` | session_id, activity_id | owner + annotate + site; notes enabled | typed `AnnotationReply`; only target event notes may change |
| `supervisor_chat` | session_id, message (1–2000 chars) | owner + read; propose for proposals | structured answers/clarification or proposals |
| `configure_warning_notes` | session_id, enabled boolean | owner + annotate + site | explicit independent note configuration |

Compatibility aliases remain: `create_rescheduling_proposal` delegates to the same
proposal endpoint; `annotate_warning_notes` runs the configured full-session warning
pass. New integrations should use the initial tool names above for targeted actions.

`Reply` includes session/agent identity, mode, expiry, retained constraints, typed
`AffectedActivity` context, typed `Suggestion` results, calendar snapshot and audit.
Each suggestion includes current/proposed times, validation/checks, rationale,
warning/policy references, infeasibility reasons and pending/terminal approval state.
The model metadata distinguishes configured/returned model versions and verified
response status; none constitutes safety clearance.

Use `climate_agent` as the normal conversation entry point. On the first turn, provide
the site-local planning date and site; the backend creates the session and returns its
opaque `session_id`. Pass that ID on follow-up turns. The ID is only a handle: backend
authentication and session ownership checks remain authoritative. Sessions expire after
30 minutes. After expiry, start a new session and provide fresh request context; prior
conversation constraints are not restored. Clear requests supported by the deterministic
grammar do not call Gemini even when Vertex is configured. Requests needing language
interpretation use the configured reasoning provider. All candidate plans pass the same
deterministic validation and remain subject to the host supervisor's approval flow.

MCP resource discovery also publishes `climate://schemas/day-calendar-response`,
`climate://schemas/climate-evidence`, `climate://schemas/planning-responses`, and
`climate://schemas/usage`. These contain JSON Schemas derived from the canonical
Pydantic models, including `Reply`, `Suggestion`, and `AnnotationReply`. The usage resource
documents timezone-aware ISO-8601 timestamps, half-open `[start, end)` intervals,
site-local dates, classification/freshness semantics, warning evidence, required
read/site permissions, and stable error handling. `analyze_consumer_schedule` accepts the
existing `DayContextSubmission` envelope built from `DaySite`, `DayEmployee`, and
`CalendarActivity` source records, plus the applicable `SafetyPolicy`. Weather forecasts
remain backend-owned. It rejects caller-supplied derived warning/status
fields and returns the existing `DayCalendarResponse` with mode
`consumer-submitted`. Tool outputs remain typed MCP schemas as well.

`AnnotationReply.monitoring.last_run` is typed: timestamp, overall result and
per-event `{activity_id, result, message?}`. Results are `updated`, `unchanged`,
`skipped` or `failed`. Unknown/stale/indoor/unaffected events are skipped. Repeated
identical annotations return unchanged. Existing unowned notes and all event times
are preserved. Annotation is disabled by default and never enabled by a proposal.

The matching REST calls are session GET, POST `/proposals`, POST `/monitoring` and
POST `/annotations` with `{activity_id}` under `/api/agent/sessions/{id}`. No model
or tool can approve on behalf of a supervisor. The separate approval REST/UI flow
requires `approve` permission, explicit decision, fresh validation and source version.

## Useful protocol errors

MCP tool exceptions become SDK `isError` responses. The message begins with a stable
code; input validation also uses the SDK's schema error envelope. Raw exceptions,
Authorization headers, credential values and backend response bodies are not exposed.

| Code | Meaning / recovery |
| --- | --- |
| invalid-input | malformed session/date/constraints/ID; correct input |
| authentication-required / unauthenticated | configure a valid process credential |
| forbidden | missing site/action grant; request the appropriate permission |
| not-found | session/activity absent, evicted, or owned by another principal |
| conflict | annotation disabled or stale action state; explicitly configure/review |
| session-expired | create a new session (after eviction this may be not-found) |
| invalid-config | invalid URL or remote non-TLS destination |
| backend-timeout / backend-unavailable | inspect backend health; read state before retry |
| invalid-response | backend contract invalid; no success is asserted |

A successful protocol response can still contain validation failure or note-write
failure. Clients must inspect the structured result, not equate HTTP/tool success
or generated prose with feasibility or an applied change.

## Identity, sessions and retention

Every state-changing tool passes through the same current API authorization and
session ownership checks. User identity cannot be selected via tool input. Do not
share a process token across unrelated users or accept subject/role headers from
callers. A workload token only has its own configured subject/site/action grants;
end-user action delegation requires a verified supervisor credential, not an
unauthenticated user ID supplied to the tool.

Session constraints/context are isolated by random session ID and authenticated
subject. Lifetime is fixed at 30 minutes, with expiry checked on every access and
after model inference. Expired in-memory sessions are evicted on the next backend
background tick/new session; explicit End session removes memory immediately.
Only earliest/latest constraints and necessary operational context are retained;
no durable preferences are created. Raw model prompts/transcripts/credentials are
not logged or stored as session memory.

SQLite operational event/proposal snapshots and decision audit are separate from
session memory. For this local hackathon, those records persist until an operator
explicitly clears the local database/Docker volume; they are not restored as agent
memory and cannot be read with expired session IDs. Do not use that indefinite
local audit retention for real employee data: production activation requires an
approved audit retention/cleanup policy, encryption, access controls and shared
TTL session storage. One backend worker/replica is the supported MVP deployment.

## GCP implemented vs planned

| Component | Status |
| --- | --- |
| Gemini on Vertex AI | Optional provider implemented and smoke-tested live in the local project with `gemini-3.5-flash-lite` and ADC. Configure provider/project/location/model at runtime. Clear supported requests remain deterministic; Gemini interprets other requests when enabled. Structured output cannot override deterministic gates. |
| Vertex inference workload identity | Provider uses server-side ADC; no browser/provider API key. Actual IAM/service-account provisioning is deployment work. |
| Supervisor / MCP service identity | Local server-side opaque credential grants implemented. Google IAM/OIDC verification, remote MCP OAuth and verified end-user delegation are planned; no identity is inferred from tool arguments. |
| Agent Engine managed runtime/sessions | Not connected. The current 30-minute backend session remains the source of truth. Agent Engine session IDs are not created or accepted by this MCP service. A managed-session integration needs a deployed agent resource, verified mapping from authenticated subject to Google user ID, and expiry/deletion behavior aligned to the 30-minute backend session. Do not treat managed conversation history as schedule, proposal, audit, or authorization data. |
| Model Armor | Evaluated for supported Vertex input/output paths, not enabled. Local screening/schema checks are defense in depth, not a claim of Model Armor protection. |
| Secret Manager / IAM | No external calendar credentials are required or configured. Production credentials should be delivered via scoped Secret Manager access and least-privilege workload identity, never hardcoded files or model context. Secret Manager integration is planned, not provisioned. |
| External calendar | Not connected. Only the isolated transactional demo adapter updates approved times or independently authorized notes. |

See [reasoning/configuration/runtime assessment](AGENT_REASONING.md),
[approval workflow](RESCHEDULING_APPROVAL.md), and
[background demo](DEMO_WALKTHROUGH.md). Official [MCP SDK docs](https://py.sdk.modelcontextprotocol.io/v1/)
explain the local transport; these links do not imply any managed deployment.

## Tests

`pip install -e '.[dev,api,mcp]'` then `pytest`. MCP coverage includes actual stdio
initialization/discovery/SDK error envelopes plus tool-to-REST parity, typed schemas,
malformed IDs/constraints, missing credentials, sanitized timeout errors, remote TLS,
read/propose/annotate separation, cross-user denials, disabled/idempotent/indoor note
handling, stale/unavailable weather, infeasible proposals and injection attempts.
Reasoning evaluations additionally verify schema-invalid/unsafe model output cannot
become a feasible suggestion or override deterministic policy. All run without live
provider credentials.
