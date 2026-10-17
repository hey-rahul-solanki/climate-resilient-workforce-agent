# Deterministic outdoor window validation

`workforce_agent.policy_windows.evaluate_proposed_window(activity, forecast, policy,
now=..., activities=...)` returns typed `WindowPolicyResult`: `valid`, `blocked`, or
`needs-review`, policy ID/version/source, and actionable `PolicyBlock` entries.
Every block carries code, reason and policy provenance; absent policy provenance
is null and requires review. A source not explicitly configured is identified as
the configured policy ID/version, never as an official external authority.

Calendar analysis, deterministic slot search, model-candidate validation and final
supervisor approval share the rest/cooling checks. The approval transaction reruns
the typed window gate and persists its result with the calendar update outcome.
REST/MCP affected-activity context includes policy context and rest blocks. The
browser/model cannot supply new policy thresholds or approve breaks; model candidate
schemas accept only activity IDs, timestamps and explanations. No live weather or
calendar provider integration is implied.

## Inputs and interval semantics

`SafetyPolicy` provides versioned heat thresholds and `work_rest_rules`, plus optional
`source` and explicit `illustrative` metadata. The fixture policy is labelled demo.
Rules apply when **any** overlapping normalized hourly sample falls in their
half-open metric band `[min_c, max_c)`. Partial hours count. All applicable rules
are enforced; a more restrictive requirement is never discarded by averaging or
selecting only the peak sample. Existing warning thresholds still block work;
adding cooling does not override a climate warning.

Trusted activity/calendar data can include:

```json
{
  "mandatory_rest_intervals": [
    {"start":"2026-10-17T12:00:00+05:30","end":"2026-10-17T12:15:00+05:30"}
  ],
  "scheduled_rest": [
    {"start":"2026-10-17T09:00:00+05:30","end":"2026-10-17T09:15:00+05:30","cooling_available":true}
  ]
}
```

These are contract examples, not prescribed break times. Pass all relevant employee
activities to validate recovery conflicts. Intervals require increasing, offset-aware
timestamps. Work overlapping a mandatory rest reservation is blocked; exact touching
boundaries do not overlap. Rest must begin exactly at the work segment's end and
cover the configured recovery duration. Conflicting employee work during recovery
blocks the candidate. Cooling must be explicitly verified where required; absent
cooling evidence requires review, and unavailable cooling blocks it.

## Conservative scheduling assumptions

Each calendar activity is one **continuous work segment**. It may not exceed an
active rule's `work_minutes`; longer tasks require an explicit split/revised plan.
Every segment under a rest/cooling rule requires its own immediate post-task
recovery reservation, even when shorter than the maximum work duration. This
conservative MVP convention avoids inventing prior recovery or cumulative exposure
history. A zero work limit blocks outdoor work. Cooling with unspecified/zero
duration requires policy review. Stop/reschedule/block/review rule actions are
honored rather than treated as permission to proceed.

Rest intervals are supplied by a trusted calendar adapter; this implementation
does not automatically create breaks, split tasks, prove cooling facility capacity,
or model physiological recovery, travel or cumulative multi-day exposure. A `valid`
result means these configured checks passed, not medical safety clearance or approval
to mutate a calendar. Existing supervisor approval and event-version checks remain.
Unsupported freeform policy rules and missing/stale/incomplete weather, unknown
location/type or unavailable policy fail closed to `needs-review`.

The day/agent responses now supply `policy_context` with backend reason/source,
illustrative status and applicable work/rest requirements for the existing frontend
display. Rest-only blocks are needs-review on calendar cards and do not fabricate
weather warning IDs or increase weather-affected counts. The typed window result
distinguishes a known block from unknown inputs.

Tests: `python -m pytest tests/test_policy_windows.py`. Cases include valid windows,
continuous work limits, cooling/rest reservations, employee conflicts, exact band
and interval boundaries, partial hours, unknown inputs, model-text bypass attempts,
and policy changes detected during final approval.
