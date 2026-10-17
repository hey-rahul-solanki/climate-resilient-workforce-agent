# Selected-site day schedule API

`GET /api/calendar/day?site_id=VAD-PLANT-01&date=2026-10-17`

The response is `DayCalendarResponse`, published in `/openapi.json` and `/docs`.
This endpoint currently uses deterministic fixture data, explicitly returns
`mode: "fixture"`, and needs no weather/calendar/model provider credentials. It is
a read-only schedule endpoint: it does not generate proposals, optimize schedules,
annotate notes, or change event times. Proposal and approval APIs remain separate.

## Authentication and errors

Uses the existing server-side identity verifier with `read` permission and a site
grant. Use a provisioned bearer credential, or an explicitly enabled isolated demo
identity cookie from POST `/api/agent/demo-login` (JSON `{}`). That HttpOnly,
SameSite=strict cookie now has `/api` scope to authorize both agent and day reads.
Secure cookies remain the default outside the local Docker preview configuration.
Responses are non-cacheable.

- 401: missing/invalid identity.
- 403: missing read permission or site grant.
- 404: authorized site has no configured schedule source.
- 422: missing/invalid ISO date or required query parameter.

Only `VAD-PLANT-01` has a fixture source. There are no week/month endpoints.
The older public `/api/calendar/demo` fixture remains available for standalone
preview; it is not a live provider or enterprise-authenticated schedule.

## Response fields

| Field | Meaning |
| --- | --- |
| `site` | Stable site ID, display name, IANA timezone |
| `date` | Selected site-local ISO date |
| `window` | Visible timeline start/end as timezone-aware timestamps |
| `employees` | Stable ID, operational name, role, optional team |
| `activities` | Stable ID, employee ID, title, start/end, site/work location, indoor/outdoor/unknown kind, version and source reference |
| `warnings` | Backend-generated warning intervals and policy context |
| `weather` | Explicit fixture source/freshness/update metadata |
| `integrations` | Truthful agent/MCP/calendar labels |
| `suggestions` | Empty on this read endpoint; use the proposal service separately |
| `mode` | `fixture`; no live calendar integration is implied |

Activities also retain backend-computed status/reason/warning references, optional
notes and exposure classification. Unknown/missing classification normalizes to
`unknown`; absent, blank or placeholder location becomes null and requires review.
Location names never determine whether an activity is indoors. Employee-role/team
projections intentionally avoid unrelated skill, certification and personal data.

## Identity and interval semantics

Activity IDs are stable across repeated reads for a selected site/date. A logical
fixture activity key is `(site_id, date, activity.id)`. `source_event_id` provides
an unambiguous stable namespace, for example
`fixture:VAD-PLANT-01:2026-10-17:event-1`. Different fixture dates get distinct source
references; IDs are not regenerated randomly on reads. `version` starts at 1 for
the immutable baseline fixture.

Annotation/update operations must retain this source identity and version and use
the separate authorized session/approval workflow. The day endpoint returns the
baseline fixture, not the mutable state of another supervisor's session. A real
calendar adapter will map `source_event_id` to provider IDs/ETags; this endpoint
does not claim such a connection.

All intervals use inclusive start/exclusive end: `[start,end)`. Timestamps require
UTC `Z` or an explicit numeric offset, with `end > start`; naive, zero-length and
reversed intervals are rejected by Pydantic. Returned timestamps preserve their
instants/offsets. Clients format them in `site.timezone`, never the browser's local
timezone. IANA names are validated using the existing shared helper.

The selected date means local midnight through the next local midnight, computed
with `zoneinfo` (23/25-hour DST days are valid). Activities are included when their
interval overlaps that local day, including cross-midnight work. Activities
outside the selected local day, duplicate IDs, missing employee references or a
conflicting site are rejected. The timeline window must fall inside the day;
fixture operating hours are 06:00–18:00, distinct from the full-day selection.

The response reuses `CalendarActivity`, `TimeWindow`, `ExposureType`, and the shared
IANA validator. Typed employee/site projections avoid requiring unrelated catalog
or worker fields. Deterministic climate assessment is reused; browser risk
inference and optimization are not introduced here.

## Tests

`pytest tests/test_day_schedule.py` covers classifications, repeatable IDs/source
references, read authorization, invalid parameters/intervals, UTC offsets,
site-local cross-midnight overlap, DST transitions, OpenAPI typing and a guard
against invoking the suggestion planner from the schedule read.

## Deterministic warning-match evidence

Each activity now includes typed `warning_matches`, while retaining `warning_ids`
for existing consumers. A match contains:

```json
{
  "warning_id": "heat-warning-1",
  "overlap": {
    "start": "2026-10-17T12:00:00+05:30",
    "end": "2026-10-17T13:30:00+05:30"
  },
  "severity": "High",
  "rationale": "Outdoor activity overlaps the configured heat warning.",
  "policy": "Illustrative demo policy v1"
}
```

The intersection is `[max(activity.start, warning.start),
min(activity.end, warning.end))`, with a match only if its end exceeds its start.
Exact touching endpoints do not overlap. Comparison uses timezone-aware instants.
Indoor activities have no outdoor-weather matches. Unknown type/location and
stale/incomplete/unsupported inputs require review; known outdoor overlaps may
retain evidence alongside `needs-review`, never as clearance.

The reusable `match_warning_intervals` service accepts activity dictionaries and
already policy-scoped warning dictionaries with offset-aware ISO timestamps.
It returns `activities`, a deduplicated `affected_activities` list,
`needs_review_activities`, and `affected_activity_count`. It accepts an optional
configured policy for site/location/exposure applicability. Without that argument,
callers must supply already applicable warnings and an authoritative freshness
state; the matcher does not invent policy thresholds or infer freshness.
`analyze_calendar` supplies these decisions from normalized forecasts and policy,
and returns the same evidence plus generated warnings and forecast metadata.

Each `(site_id, activity.id)` appears once. Repeated identical input records and
warning IDs are deduplicated; conflicting definitions for the same activity or
warning ID are rejected rather than silently losing evidence. An activity crossing
multiple warning windows retains every distinct warning match while contributing
once to the total affected count. The day response and agent/MCP context both
expose this evidence. See `tests/test_warning_matching.py` for deterministic boundary,
multiple-warning, classification, unknown/stale data, timezone and deduplication tests.
