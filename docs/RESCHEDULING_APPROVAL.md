# Supervisor rescheduling approval

Implemented for an **isolated demo calendar**. Google Calendar and other external
calendar writes are not connected. Every outcome identifies the integration; an
`applied` result means only the session's demo events were updated.

## Review and decisions

Start an isolated demo session on the day calendar. Existing suggestions become
server-owned proposals. Open **Select event & review** to inspect current/proposed times,
source version, employee, location/type, climate rationale, policy/warning references,
validation checks, and employee/location conflicts. Tick the explicit approval
checkbox, then **Approve & apply demo change**. Reject and Request revision record
backend decisions; a revision request does not silently generate or approve a new
proposal. Submit revised chat/time constraints to generate a fresh proposal batch.

Review shows the backend's original warning overlap intervals and rationale, plus
named weather/policy, source-version and employee/location resource checks. Missing
overlap evidence is explicit; the browser does not reconstruct climate matches.
A failed source-version check displays a stale-proposal alert and disables approval;
reject and revision remain available for a pending proposal. API failures invalidate
the displayed review and clear the approval checkbox. Select the event again to
refresh review before deciding.

Pending, rejected and superseded proposals are labelled as such. An applied result
is displayed only when returned by the backend. Current event notes/disclaimers are
shown in a separate review section; note presence never confirms a time change or
successful automatic annotation. The current resource check covers employee and
location conflicts, not a separate equipment inventory.

`read` and a site grant are required for review. `approve`, ownership, and the site
grant are additionally required for every approve/reject/revision decision. Demo
principals receive these permissions; external bearer principals must be provisioned
explicitly. Creating proposals or reading suggestions cannot change event times.
MCP tools continue to expose only reads/proposals/chat, never approval or writes.

Supervisor review and decisions are performed through the application UI. The old
`/api/agent/*` REST endpoints are no longer registered; agent operations are routed
through the MCP gateway.

Clients submit a proposal ID and decision, not replacement timestamps. Unknown
fields are rejected. The immutable snapshot includes source version, original
activity metadata and exact proposed times. Every newly generated batch supersedes
previous pending proposals, so older review screens cannot apply obsolete proposals.

## Apply gate and concurrency

Within the shared service lock, approval reads the current calendar and obtains the
latest configured forecast/policy inputs again. It checks source event version,
forecast completeness/freshness and policy evaluation, policy version, duration,
visible site window, employee availability and location conflicts. Any failed check
records `blocked` and makes no calendar change. Missing source events also block.
Demo forecast freshness is evaluated at its explicit fixture evaluation time;
audit timestamps use the actual UTC server clock. This is not a live-weather claim.

The SQLite demo adapter then uses compare-and-swap on the source version. An update
changes only start/end and increments version; notes, attendees and unrelated fields
are preserved. A transaction commits the demo event change, terminal proposal state
and audit record together. Write failures roll back to a savepoint and record
`integration-failed`. Failed proposals require a fresh proposal/review rather than
silently retrying a stale calendar update. Repeating the same decision returns the
recorded outcome without a second write/audit entry. A different subsequent decision
returns 409. Pending, rejected, revision-requested, superseded, blocked and failed
proposals cannot apply later.

Each decision record includes proposal ID, actor subject, actual timestamp,
decision, validation checks, result, integration and message. The UI displays
success/failure and refreshes the day calendar from the returned backend snapshot.
A failed approval is an HTTP-successful recorded decision with result `blocked` or
`integration-failed`, never an asserted calendar success.

Persisted proposals and typed agent responses also distinguish `decision_state`
(`pending`, `approved`, `rejected`, `revision-requested`) from
`calendar_update_state` (`not-requested`, `applied`, `failed`). The existing
`approval` field retains its detailed lifecycle values for compatibility. An
approved decision can therefore have a failed calendar result. Legacy records are
interpreted from their stored outcome rather than falsely shown as pending.

Approval records an `approved` audit transition followed by the update outcome,
atomically with the demo update. Both carry actor, timestamp and proposal ID;
`approved` alone never means the calendar changed. Storage reloads the authoritative
proposal inside a SQLite write transaction and refuses terminal/superseded proposals.
The service reruns weather/policy, employee/location availability, duration, day
window and source-version validation inside that same transaction immediately
before writing. Missing or non-boolean required check results fail closed. The
event write additionally compares source version. Retrying the same decision
returns its stored result without a second write or duplicate audit; changing a
terminal decision is rejected.

## Persistence and operational limits

`WORKFORCE_APPROVAL_DB_PATH` defaults to `data/approvals.sqlite3`. Docker mounts
`approval_data` at `/app/data`, preserving audit and demo event/proposal snapshots
across container recreation. Sessions/identity are still ephemeral and cannot be
resumed after a process restart; operators can inspect retained audit through
SQLite. No durable user preferences are stored. The new durable records contain
only the operational proposal/event evidence necessary for review and audit; a
production deployment needs an organization-approved retention/access policy.

This MVP supports one backend worker/replica. The service lock and SQLite write
transaction serialize final validation and local writes; compare-and-swap also
protects the event version. A live
calendar adapter must fetch fresh provider data, enforce provider ETag/If-Match,
handle uncertain write outcomes using idempotent operation IDs/reconciliation, and
persist decisions/audit with suitable transactional guarantees before activation.
No real provider write is represented as implemented here.

## Warning notes are a separate action

Rescheduling approval never calls warning-note annotation. Annotations are enabled separately through the monitoring controls, as described
in [the full demo walkthrough](DEMO_WALKTHROUGH.md); approval does not enable them. An external annotation integration requires separate
permission/configuration, a product-owned idempotent note section, and independent
result reporting; it must never alter event time. Approval changes only times in
the demo event and preserves existing notes.

## Verification

`pytest tests/test_approval.py` covers explicit approval, audit persistence,
idempotency, permission/ownership denials, superseded/rejected/revision states,
changed source versions, stale weather, changed policy, new conflicts, rollback on
a partially failed write, and rejection of client-supplied timestamps. The full
suite also checks warning intervals and agent session isolation/expiry.
Additional tests cover durable decision/update state separation, storage-level
terminal guards, incomplete checks, tampered proposal snapshots, concurrent duplicate
approvals, and a conflict arriving after initial review but before final validation.
