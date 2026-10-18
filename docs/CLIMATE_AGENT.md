# Climate agent: implemented contract and deployment boundaries

## Implemented

The calendar panel calls the root-level `calendar_backend` service through same-origin
`/agent` requests. That service discovers MCP tool schemas and invokes the requested
tool; the MCP server calls the shared agent service. Docker enables an **isolated demo
identity**, not an enterprise login.
Click **Start isolated demo session**. Ask `who is affected`, `reschedule before
12:00`, `after 08:00`, or `reschedule`. Combined earliest/latest constraints can be
submitted through the form. Unrecognized or ambiguous requests ask clarification;
they are never treated as successfully understood natural-language constraints.

The default deterministic agent identity is `climate-workforce/deterministic-v1`.
`AgentService` is reusable Python application logic. The unified `calendar_backend`
serves HTTP routes and acts as an MCP client gateway for browser agent calls. The stdio
MCP server calls the shared service directly. Proposal generation is not approval. It exposes
fresh proposal review and explicit approval-gated updates to the isolated demo calendar.
See [the approval workflow](RESCHEDULING_APPROVAL.md). External calendar integration
remains unconnected.

Existing fixture suggestions and session proposals use the same bounded planner:
15-minute candidates within the requested site-local window; preserved duration;
backend forecast/policy evaluation; employee and location availability; joint
reservation of proposed slots. No feasible slot returns null timestamps. Unknown
inputs require review. This demo does not model travel, equipment or arbitrary
site operational rules, and cannot certify an operational schedule. Warnings,
policy version, original times and validation rationale accompany each proposal.

## Agent transport

The agent is exposed to the frontend through the MCP gateway only. `GET /agent`
discovers MCP tool schemas, and `POST /agent` invokes a discovered tool with
`{name, arguments}`. The legacy `/api/agent/*` and `/api/v1/climate/*` REST adapters
are not registered by `calendar_backend`; agent requests use MCP instead. Other
calendar, weather, catalog, safety and planning HTTP routes remain under `/api`.

The local demo identity is enabled explicitly. The gateway login sets an HttpOnly,
SameSite=strict cookie. Use HTTPS beyond local development.

## Identity, permissions, session lifecycle

`WORKFORCE_AGENT_CREDENTIALS` is a server-only JSON map of opaque bearer tokens to
`{subject, permissions: ["read", "propose", "approve"], sites: ["VAD-PLANT-01"]}`. Provision a
separate high-entropy token/subject for each supervisor or workload, outside source
control. Do not put tokens in Vite variables or tool arguments. This is a minimal
local credential verifier, **not implemented Google IAM/OIDC or enterprise SSO**.
For a GCP deployment replace it with verified issuer/audience/expiry claims and
server-side role/site mapping; never trust user-supplied subject/role headers.

Authorization runs on every call. A different subject receives 404 even with a
valid session ID; a revoked permission/site returns 403. Random 256-bit session IDs
are not sufficient authorization by themselves. Multiple sessions for one subject
have separate constraints. Sessions have a fixed 30-minute lifetime and return 410
on access after expiry; a new session is required. Cleanup occurs on access/new
session, and capacity is bounded to 1,000 sessions. Explicit End session removes
constraints immediately. Conversational session memory is process-local and lost on restart. Approval
records and demo event/proposal snapshots are stored separately in SQLite. Run one
worker/replica for this MVP; shared encrypted TTL storage is required before scaling.

Only earliest/latest planning constraints are kept server-side. The bounded chat
transcript stays in component memory and clears on site/date/source change, session
end, expiry or authentication failure. Review details, input and constraints clear
with it. Late responses from an unmounted calendar panel are discarded. It is not
logged or persisted. Employee data is loaded from demo event snapshots when needed; approval audit
and snapshot persistence are documented in the separate workflow. No durable preference memory is implemented;
future durable preferences require an explicit user opt-in and deletion controls.

The chat has a labelled keyboard-accessible input, Enter-to-send, a focusable live
conversation log, backend-pending and clarification status, and retryable errors.
Proposals display current/proposed times, rationale and validation; selecting one
highlights its event and opens review. Only backend-confirmed outcomes report an
update. The frontend sends no user ID or service credential: application auth uses
the server-issued HttpOnly session cookie. Fixture mode supports the documented
time-window grammar; prompts such as “keep this crew together” request clarification
unless a configured reasoning provider can interpret them. Crew grouping is not
silently asserted or enforced by the demo planner.

Demo login is disabled by default. Docker explicitly sets
`WORKFORCE_AGENT_DEMO_ENABLED=true` and `WORKFORCE_AGENT_SECURE_COOKIES=false` for
local HTTP preview. Each login creates its own expiring principal. This is a public
fixture sandbox, never a way to access real workforce data. Disable demo login,
use Secure cookies, restrict CORS/origins and install real user auth before exposing
operational data. Default credentials are empty: no anonymous bearer API access.

## MCP

Install `pip install '.[mcp]'`. Run `workforce-agent-mcp` (or
`python -m workforce_agent.mcp_server`). The server uses the supported MCP Python
SDK v1 maintenance line with `<2` pinned; it uses stdio only, no public network
listener. Client configuration:

```json
{
  "mcpServers": {
    "climate-workforce": {
      "command": "workforce-agent-mcp",
      "env": {
        "WORKFORCE_AGENT_CREDENTIALS": "<configured principal mapping>",
        "WORKFORCE_AGENT_TOKEN": "<provisioned server-side credential>"
      }
    }
  }
}
```

The MCP process must have the matching credential mapping. Run a separate MCP process per
supervisor/workload identity; a process token represents that one identity. No tool
can select a different principal or receive secrets as arguments. The optional MCP
process is not automatically started or connected by the web app. The web UI does
not claim that another MCP client is connected.

Typed discovery exposes `create_supervisor_session`, `list_affected_activities`,
`get_climate_suggestions`, `create_rescheduling_proposal`, `supervisor_chat`, `configure_warning_notes`, and
`annotate_warning_notes`. Note tools require a separate `annotate` permission.
Read-only suggestion lookup returns existing proposals; proposal generation without sufficient constraints returns clarification. The stdio adapter
is a local bridge, not a deployed remote OAuth MCP server. Remote MCP/OAuth is future work; local annotation tools now use the separate monitoring API. See the
[official MCP SDK v1 documentation](https://py.sdk.modelcontextprotocol.io/v1/).

## GCP assessment: planned, not connected

| Component | Current implementation | Deployment decision |
| --- | --- | --- |
| Gemini on Vertex AI | Optional server-side provider implemented/tested with injected responses; no live connection verified | Configure an approved project/model and ADC; see AGENT_REASONING.md. Reject unknown schema fields; validate every candidate outside the model. Never permit model tools to bypass authorization/approval. |
| Cloud Run | Existing Docker-compatible FastAPI service; no verified deployment | Suitable first hackathon runtime; provision least-privilege service identity, secrets, auth gateway and shared session store before multiple replicas. |
| Vertex AI Agent Engine / Agent Runtime | Evaluated, not provisioned | Defer managed runtime migration until a real Gemini/ADK path is selected. Existing simple service does not need a managed runtime for deterministic fixtures. |
| Model Armor | Evaluated, not enabled or called | Screen untrusted prompts and generated output on a supported Vertex path. Confirm project/region/path support and configure enforcement; screening errors must not silently bypass the gate. |
| Google user/workload identity | No GCP verifier; local opaque tokens + demo principal | Verify authenticated end-user tokens and use a separate least-privilege workload identity for provider calls. |
| Durable memory | None | Keep constraints within session TTL; require opt-in for any durable preference. |

Google documents [Model Armor integration with Vertex Gemini](https://docs.cloud.google.com/model-armor/model-armor-vertex-integration)
and [gateway protection for supported ADK Agent Engine traffic](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/configure-model-armor).
These are deployment options, not evidence of a configured integration here.
Model screening is defense in depth: deterministic policy validation, ownership,
authorization, and explicit supervisor approval remain mandatory.

## Verification

`pytest tests/test_agent.py tests/test_agent_mcp.py tests/test_calendar.py` covers
ownership, permission/site denials, invalid credentials, isolation, fixed expiry,
explicit session deletion, clarification, retained constraints, traceable context,
feasible/no-slot proposals, unchanged source times, HTTP cookie behavior and MCP
schemas/shared results. The MCP tests require the optional `mcp` extra.


The complete fixture demo, scheduled note pass, and annotation MCP tools are
documented in [DEMO_WALKTHROUGH.md](DEMO_WALKTHROUGH.md).


Optional Gemini intent/candidate reasoning, typed contracts, fail-closed evaluation
and configuration are documented in [AGENT_REASONING.md](AGENT_REASONING.md).


Canonical MCP startup, schemas, permissions, errors, targeted annotation and GCP
status are documented in [MCP_SERVER.md](MCP_SERVER.md).
