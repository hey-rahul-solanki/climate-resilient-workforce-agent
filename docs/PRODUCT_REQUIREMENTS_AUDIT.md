# MVP requirements audit

Reviewed against [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) after the
reference-style calendar update. This records implementation scope, not a claim
that production integrations or the design's illustrative values are live.

| Requirement | Implementation / verification |
| --- | --- |
| One day screen, selected site/date, employee rows (FR-01) | `CalendarPage`; only day navigation, site timezone, stable IDs, title/time/location/type and supplied role/team. Narrow screens scroll the timeline and stack the panel. |
| Timestamp-proportional cards and warning bands | All use `timelineGeometry`; overlapping events get separate lanes. Card padding is zero so tiny durations cannot be widened to fit content. Selecting a pending proposal adds a separate, labelled, site-local preview on the same scale; it does not move the original event. Geometry/timezone tests cover both. |
| Exhaustive warning flags and summary (FR-02–04) | Backend normalized forecast/policy matching, half-open intervals and deduplicated warning evidence; UI renders all flags independently of top suggestions. Banner retains severity, interval, measure, source, update time and computed count. Unknown/stale data is needs-review. |
| Suggestions and constraints (FR-05–06) | Structured suggestions retain employee/activity, current/proposed time, rationale, warning/policy evidence and validation. Additional proposals/evidence expand in place. Infeasible results have no invented time. Chat uses authenticated session context and requests clarification for unsupported demo grammar. |
| Approval and decision audit (FR-07) | Separate review supports approve/reject/revise. Checkbox and backend checks gate approval; final transactional policy/resource/version validation, terminal guards and idempotent decisions precede writes. Only backend-confirmed outcomes report an applied demo change. |
| Background checks and disclaimers (FR-08–09) | Configurable backend task runs without a page, operates only on affected outdoor events, preserves unowned notes and is idempotent. Notes and reschedule outcomes remain separate. Monitoring is session-scoped and ends at expiry/restart. |
| Reusable agent capability (FR-10) | MCP tools share application services and deterministic validation. Site permissions, session ownership and action permissions are enforced. Browser uses the MCP gateway with an HttpOnly demo cookie; no model/service secrets or trusted browser-supplied user IDs. |
| Deterministic demonstration (FR-11) | Bundled snapshot is generated from the backend fixture and compared in tests. Docker demo journey covers flags, chat, approval, idempotent notes and infeasibility without live credentials. |
| Policy explanations and safety | Backend policy ID/version/source and applicable work/rest context; unknown inputs fail closed. Illustrative labels are explicit. Browser does not select climate thresholds or validate safety. Rest/cooling gate is documented in `POLICY_WINDOW_VALIDATION.md`. |

## Production boundaries

The architecture in section 10 is the target architecture. The current connected
calendar is an isolated SQLite-backed demo calendar. Live Google Calendar writes,
Cloud Run/IAM deployment, Agent Engine and Model Armor are not verified live
integrations. Optional Vertex reasoning has a provider implementation with injected
tests; deterministic reasoning remains the default. The UI reports MCP connection
as unverified and never treats the architecture diagram as connection evidence.

Run one backend worker for the MVP. Sessions are process-local with a 30-minute
expiry; unattended durable multi-site monitoring needs a persistent job/session
store. Complex supervisor constraints such as crew grouping are clarified when
unsupported, not silently enforced. Work/rest checks use continuous work segments
and explicit recovery reservations, with documented conservative assumptions.

## Verification

- `npm test --prefix frontend`: timeline, warnings, needs-review states, structured
  suggestions, review decisions, policy explanations and proposed-time previews.
- `npm run build --prefix frontend` and `npm run lint --prefix frontend`.
- `python -m pytest`: schedule contract, interval/policy/rest boundaries, typed
  services/MCP, authorization, sessions, approval gating, rollback and annotations.
- Docker demo: `docker compose exec -T backend python - --base-url http://frontend < scripts/demo_journey.py`.

No browser was available for visual/interactive verification in this environment.
The 10-second discoverability success criterion and real keyboard/screen-reader
interaction remain manual acceptance checks; static markup and automated logic
tests do not establish those results.
