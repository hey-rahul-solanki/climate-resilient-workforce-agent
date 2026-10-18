# Climate planning service API v1

Custom schedulers can consume typed JSON without an MCP client. This adapter and
the MCP adapter both call `AgentService`; warning matching, policy checks and slot
validation remain in the shared deterministic services. Current data and calendar
storage are demo fixtures. `mode: "fixture"` and `demo-validated` do not claim a live
weather, calendar or GCP connection.

## Contract and permissions

Base path: `/api/v1/climate`. OpenAPI schemas are served at `/openapi.json` and
interactive documentation at `/docs`. Breaking contract changes require a new
major path; clients should tolerate additive response fields.

| Method/path | Required permission | Result |
| --- | --- | --- |
| POST `/sessions` | read, authorized site | Create isolated site/date context; 201 |
| GET `/sessions/{id}/affected-activities` | read | Affected activities and existing proposals |
| GET `/sessions/{id}/suggestions` | read | Existing proposals; no generation |
| POST `/sessions/{id}/suggestions` | propose | Generate proposals using typed time constraints |
| DELETE `/sessions/{id}` | read | Close the caller's context; 204 |

All operations require `Authorization: Bearer <service-token>`. Browser demo
cookies are insufficient. Provision a unique high-entropy token per caller using
the server-only `WORKFORCE_AGENT_CREDENTIALS` JSON mapping. Each entry specifies
`subject`, `permissions` and `sites`. A scheduler usually needs only `read` and
`propose`; a reporting client needs only `read`. Do not grant `approve` or
`annotate` to suggestion consumers. Store credentials outside source control.

Site access is checked on creation and every subsequent operation; session
ownership is also checked. Another subject cannot reuse a session, even with site
access. Sessions expire after 30 minutes; recreate expired context. Missing/invalid
identity returns 401, insufficient permission/site access 403, another owner's
session 404, expired context 410, and invalid input 422. Expired contexts already
evicted from memory return 404. Extra request fields are rejected.

`PlanningResponse` includes version, fixture mode, site/timezone/date, expiry,
affected activities and structured actions. Actions carry stable activity IDs,
proposal IDs, current/proposed timestamp windows, warning IDs and overlap evidence,
policy references, rationale, validation checks/status, infeasibility reasons,
`requires_supervisor_approval` and `approval_state`. A null proposed window is
explicitly review/infeasibility, never an invented safe slot. Times use ISO 8601
offsets and site-local constraints; intervals use half-open overlap semantics.

POST returns the newly generated batch. GET includes proposal history, including
superseded or decided proposals; inspect `approval_state` before showing an action
as pending. A pending proposal is not an applied change. No endpoint in this API
changes event times or approves a proposal. Supervisor approval and final
revalidation remain in the separate [approval workflow](RESCHEDULING_APPROVAL.md).

## Example

Start the existing backend locally or with `docker compose up --build -d` and
configure the credential mapping in that backend process/container. Compose does
not provision a service token automatically. With `CLIMATE_SERVICE_TOKEN` set in
the caller's environment:

```bash
curl --fail-with-body http://localhost:8000/api/v1/climate/sessions \
  -H "Authorization: Bearer $CLIMATE_SERVICE_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"site_id":"VAD-PLANT-01","date":"2026-10-17"}'

curl --fail-with-body "http://localhost:8000/api/v1/climate/sessions/$SESSION_ID/suggestions" \
  -H "Authorization: Bearer $CLIMATE_SERVICE_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"latest":"12:00"}'
```

Set `SESSION_ID` from the first response. A complete schema-valid fixture response
is in [climate-suggestions-v1.json](examples/climate-suggestions-v1.json); session
and proposal IDs are illustrative and cannot be replayed. `earliest` and `latest`
accept `HH:MM` in the site's timezone. Missing/ambiguous constraints request
clarification. Infeasible windows return explicit `no-feasible-slot` actions;
missing forecasts fail closed to review.

Contract and authorization tests: `python -m pytest tests/test_planning_api.py`.
They verify typed responses/OpenAPI, parity with the shared service, unchanged
event times, cross-site/owner isolation, read-only credentials, malformed input,
infeasible windows and missing forecasts.

## Cloud Run / IAM deployment assumptions

Implemented authentication is application bearer-token validation, not Google ID
token validation. Cloud Run deployment and IAM identity integration are planned;
this API has not been deployed or verified against live IAM in this change.

A GCP deployment should require authenticated Cloud Run ingress and grant invocation
only to explicitly permitted caller service accounts. Map a verified service
identity to application site/permission grants; infrastructure invocation permission
alone is not site authorization. A gateway/token exchange or verified Google token
adapter is required to reconcile ingress authentication with the application's
bearer contract. Do not trust caller-supplied subject/site headers or treat a Google
token as an application token without verification.

Use a dedicated runtime service account, workload identity/ADC for GCP access and
Secret Manager for application/calendar credentials with narrowly scoped access.
Do not distribute runtime keys or model credentials to browsers. Current session
memory and SQLite demo storage assume a single backend process; scaling replicas
requires shared session/proposal storage and transactional concurrency guarantees.
