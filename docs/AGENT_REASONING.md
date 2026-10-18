# Validated suggestion service and optional Vertex reasoning

## Implemented vs connected

The default remains the credential-free deterministic agent and fixture calendar.
An optional `VertexADKProvider` runs a Google ADK `Agent` through an ADK `Runner`,
using Gemini on Vertex AI with Application Default Credentials (ADC). The backend's
opaque session ID is also the ADK in-memory session key and is deleted when the
backend session expires or closes. The backend remains the source of truth for its
30-minute expiry, schedule, permissions, constraints, proposals, and approvals. A
live ADK-to-Vertex smoke call was verified in project `climate-workforce-agent` using
`gemini-3.5-flash-lite`. Credentials and project configuration remain local and are
not stored in the repository. Runtime settings keep the provider deterministic by
default, so no model calls happen until `WORKFORCE_REASONING_PROVIDER=vertex` is set.
The project is read from ADC when available (or can be overridden), and the tested
model is the default Vertex model setting. Missing SDK, permissions, or valid output
fails closed.

`ReasoningProvider` is the injectable boundary. `ReasoningService` schema-validates
untrusted intent/candidates. `validate_model_candidates` is the reusable deterministic
candidate gate; `AgentService` supplies authorization, isolated session constraints,
source snapshots, review and approval. UI/REST/MCP use the same services; the browser
never receives provider credentials or calls Gemini. Existing tool discovery now
exposes typed affected activity evidence, suggestion validation checks/infeasibility
reasons, and provider measurements through `Reply`.

The MCP `climate_agent` tool remains the client-facing entry point. `AgentService`
routes clear supported phrases deterministically and invokes the ADK interpreter for
other language; it then applies the interpreted intent through the existing authorized
deterministic methods. This ADK agent does not call back into the same MCP server.
Adding ADK MCP tool calls would require a separate non-recursive tool endpoint and
delegated identity design; do not expose `climate_agent` to itself as an ADK tool.

## Request and candidate flow

1. Authenticate/site-authorize before accessing the calendar context. Snapshot the
   selected day and constraints under the service lock, then release the lock for
   inference. Send only IDs, pseudonymous employee IDs, site-local times, kinds,
   locations, warning/policy context and retained constraints. Do not send employee
   names, event notes, full transcripts, identity tokens or credentials.
2. Ask the ADK `LlmAgent` for JSON conforming to `ModelPlan`: action (`list_affected`, `propose`,
   `clarify`, `decline`), earliest/latest bounds, activity IDs, optional explicit
   candidate windows/explanations and unsupported constraints. ADK requests
   structured JSON using Vertex's supported schema subset; Pydantic independently
   rejects missing/extra fields, invented
   IDs, duplicate candidate IDs, invalid enums and naive/reversed intervals.
3. Ambiguous/unsupported constraints return clarification. A request with a clear
   time window but no explicit candidate timestamps uses the deterministic bounded
   planner. When Gemini identifies a specific eligible activity scope, planning is
   restricted to that scope; unrelated activities are not added silently.
4. Explicit candidates are checked against fresh application state: affected outdoor
   scope, original duration, retained/requested site-local window, policy/forecast
   result and employee/location conflicts. Candidates accepted earlier in the same
   batch reserve their slots. Failed checks produce `needs-review`, null proposed
   timestamps and machine-readable failure reasons. One rejected candidate is not
   proof there is no feasible slot elsewhere.
5. Only deterministic slot search can return `no-feasible-slot`, with explicit null
   timestamps and reasons. The search uses a bounded 15-minute grid and is not a
   global optimizer. Work-rest/free-form operational rules unsupported by this
   calendar evaluator conservatively require review; no model can override them.
6. Recheck ownership, expiry and permissions after inference. If session constraints
   changed while inference ran, discard the result and require review/retry.
   Persist proposals only, never apply event times. Approval still requires a new
   deterministic review, current availability and source-version compare-and-swap.

Current schedule/forecast inputs are **fixtures**, even when real Vertex reasoning
is enabled. Their evaluation time is explicit fixture time. The reusable candidate
validator requires `evaluation_time`; live adapters must supply current UTC time
and latest provider data, not the issue time to bypass aging. No live operational
safety integration is implied by enabling a reasoning provider.

## Structured contracts

- `AffectedActivity`: IDs, original timestamps/status/reason, typed warning intervals
  and `WarningMatch` intersections/severity/policy rationale.
- `Suggestion`: activity ID, proposed timestamps or null, deterministic rationale,
  warning/policy references, validation state, `validation_checks`, structured
  `infeasibility_reasons`, pending approval/source snapshot and eventual outcome.
- `model_explanation` is optional untrusted model text, separate from deterministic
  `rationale`. It is not used by validation or approval, and the UI does not render
  it as safety evidence. The service screens overt safety/approval claims.
- `Reply.request_status`: `not-evaluated`, `clarification`, `needs-review`, or
  `validated`. `validated` describes completed deterministic evaluation, **not**
  safety clearance; individual suggestions may explicitly be infeasible.
- `Reply.model`: provider, configured model, returned model version, latency, token
  counts, optional estimated cost and model-processing status. A model-processing
  `ready` status does not mean its candidates passed deterministic validation.

## Configuration and model/version policy

Install `pip install '.[api,vertex]'`. The optional ADK constraint is
`google-adk>=1.39,<2`; ADK 1.39.1 was used for local validation. For deployment,
lock the resolved package version. Environment variables:

| Variable | Default / meaning |
| --- | --- |
| `WORKFORCE_REASONING_PROVIDER` | `deterministic`; opt in with `vertex` |
| `WORKFORCE_VERTEX_PROJECT` | ADC project by default; set explicitly to override |
| `WORKFORCE_VERTEX_LOCATION` | `global`; select a supported approved location |
| `WORKFORCE_VERTEX_MODEL` | `gemini-3.5-flash-lite`; override to choose another available model/version |
| `WORKFORCE_MODEL_TIMEOUT_SECONDS` | 10; SDK HTTP deadline, maximum 30 |
| `WORKFORCE_MODEL_MAX_OUTPUT_TOKENS` | 2048; configurable 128–8192 |
| `WORKFORCE_MODEL_INPUT_USD_PER_MILLION` | unset; optional operator-supplied rate |
| `WORKFORCE_MODEL_OUTPUT_USD_PER_MILLION` | unset; optional operator-supplied rate |

The configured development default is `gemini-3.5-flash-lite`; it is only called when
Vertex reasoning is explicitly enabled. Operators can select another currently
available, region-compatible approved Gemini model/version; use a pinned/versioned
resource when supported. Record both the configured model ID and provider-returned
`model_version` for each call. Evaluation stubs use explicit
`fixture-model-v1` / `fixture-model-001`, never a claim of live Gemini execution.

On GCP use a dedicated least-privilege workload service account/ADC with Vertex
inference permission for the configured project. No API key is passed or embedded.
User/site authorization remains separate from the provider workload identity.
This change does not install enterprise OIDC/user login.

For Docker, set `WORKFORCE_PYTHON_EXTRAS=api,vertex` at build time, the reasoning
provider/project/location/model variables, and rebuild with `docker compose up
--build -d`. Supply ADC through an authorized workload identity or an explicit
local credential mount using a Compose override; credentials are not baked into
images or source. Standard Docker preview defaults to `api` extras/deterministic
mode and makes no live model calls. Optional rate variables can be supplied in
that environment override. No credentials or live calls are needed for tests.

## Fail-closed fallback and prompt injection

- Invalid/empty/truncated/blocked output, schema errors, unknown IDs, timeout, SDK
  failure, auth/quota errors or absent configuration yield `needs-review` with no
  newly feasible suggestions. Raw exceptions/output are not returned or logged.
- Failure does not silently switch a complex request to a weaker parser or invent
  a slot. Users can explicitly use the existing structured constraint endpoint or
  keep the deterministic default mode. Existing previously authorized proposals
  remain separate; a failed model response returns an empty suggestion list.
- Request screening rejects overt policy-bypass, approval and secret-disclosure
  attempts before inference. Output screening rejects overt safety/approval claims.
  These are heuristic defenses, not complete prompt-injection detection. Instruction
  boundaries alone are not a security guarantee: models have no write/approval
  capability, cannot select identities/policy, and every candidate is validated.
- Prompt/explanation text is always untrusted. Unsupported semantic constraints
  depend on model interpretation and human review; arbitrary natural language is
  not guaranteed perfectly understood. Approval reviews exact times/constraints.
- The input budget is 2,000 characters and serialized context is capped at 100 KB.
  One SDK attempt, temperature 0 and bounded output tokens limit retries/spend;
  temperature 0 does not guarantee deterministic real-model output.
- Model Armor is not connected. Evaluate inline screening for the chosen Vertex
  path before production, while preserving all deterministic and approval gates.

## Latency / cost measurement

The service measures wall time around the provider call with `perf_counter`,
including SDK/authentication overhead, and returns token metadata when available.
No production latency or cost figures are asserted here. ADC discovery and client
startup can add time outside the SDK HTTP timeout. Client abort is not proof the
provider stopped; no automatic calendar write follows an abandoned request.

For a real deployment, export non-sensitive counters/histograms for provider/model
version, status, end-to-end latency, validation failure category and token totals.
Compare p50/p95 latency and schema/constraint/unsafe-candidate rejection rates on
held-out requests. Do not log raw prompts, names, notes, model text or credentials.
Correlate request IDs with Cloud Billing/provider usage for authoritative cost.
The optional estimate is `(prompt_tokens * input_rate + (output_tokens +
thought_tokens) * output_rate) / 1e6`; it excludes caching/tier/region discounts,
other billable items and token-category differences. Missing rates/usage yields null,
never fabricated zero cost. Validate rates against current project pricing.

## Agent Engine/runtime assessment

The current FastAPI/container workflow runs an ADK agent locally/in-process and is
not an Agent Engine-deployed agent. ADK's in-memory conversation events are scoped to
the backend session ID and removed when its 30-minute lifetime ends. Agent Engine
deployment and managed sessions are not configured; that requires a deployed agent
resource and a verified mapping from the authenticated principal to Google `user_id`.
Managed conversation events must not replace schedule, proposal, audit, or
authorization data.

Google's [ADK documentation](https://google.github.io/adk-docs/),
[ADK MCP integration](https://google.github.io/adk-docs/tools/mcp-tools/), and
[structured output documentation](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/control-generated-output)
support this approach. See [Agent Engine/runtime](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
and [Cloud Run agent hosting](https://docs.cloud.google.com/run/docs/ai-agents) for
hosting options; none is evidence of a deployed integration in this repository.

## Evaluations and tests

`tests/fixtures/agent_evals/cases.json` contains recorded valid, malformed, ambiguous,
unsupported, unsafe, conflict, fabricated-ID, timezone, prompt-injection and no-slot
cases. Replay without credentials:

```bash
python scripts/evaluate_agent_reasoning.py
python scripts/evaluate_agent_reasoning.py --output /tmp/agent-evaluation.json
pytest tests/test_reasoning.py
```

Recorded-output replay evaluates application gates, **not live model quality**.
Adapter tests inject SDK responses; no paid inference runs in CI. Other tests cover
secret/error redaction, context minimization, expired/concurrently changed sessions,
policy/availability checks and unchanged calendar times. Add operator-approved,
held-out live-model evaluations before enabling Vertex in an operational deployment.
