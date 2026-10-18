# Complete single-day climate calendar demo

## Start / reset

Run `docker compose up --build -d`, then open http://localhost:5173. Keep
**Deterministic demo** selected. No live provider credentials are required.
Only day navigation exists; there is no week/month mode.

Use the bundled date **17 October 2026**, Vadodara Main plant, timezone
Asia/Kolkata. Other dates shift the same fixture scenario. All policy thresholds,
forecast values, employee records and integrations are illustrative. The agent
is deterministic; Gemini, Agent Engine, Model Armor, Google Calendar, remote MCP
and enterprise SSO are not connected. A local stdio MCP adapter is available.

Click **Start isolated demo session** to get a fresh schedule, independent of
other sessions. End the session and start another to reset the entire journey.
Restarting the backend also ends session access; audit/note snapshots persist in
Docker's `approval_data` volume. Session and demo identity expire after 30 minutes.

## Walkthrough (~3 minutes)

1. Inspect the four employee rows and the 06:00–18:00 day timeline. Read the
   clearly labeled demo forecast and illustrative site policy. The high-heat
   warning covers 12:00–16:00.
2. Show three affected outdoor activities: Panel maintenance (11:30–13:30),
   Site inspection (12:30–15:00), Pump inspection (15:30–17:00). First/last are
   partial overlaps. Workshop repairs is indoor and unflagged despite spanning
   the warning. Asset survey has unknown classification/location and needs review.
   Expand **Show all matching activities** to discover every warning match.
3. In supervisor chat ask `who is affected`, inspect **Affected activities &
   evidence**, then enter `reschedule before 12:00`. Structured proposals show
   warning/policy references and validation status. Try `move it earlier` to show
   clarification; unsupported constraints are not silently accepted.
4. For Panel maintenance choose **Select event & review**. Inspect current/proposed
   times, location/type, employee, warning/policy explanation, source version,
   policy and availability checks, and conflicts. Tick **I approve these exact
   times in the isolated demo calendar**, then **Approve & apply demo change**.
   The bar moves to 06:00–08:00, the affected count falls from three to two, and
   an `applied` result appears in **Decision history** with actor/time. Reject or
   Request revision records a decision without changing time.
5. Choose **Enable automatic notes**, then **Run warning pass now**. The same
   pass also runs every 30 seconds on the backend without the UI being open.
   Inspect the updated results for the two remaining affected outdoor events.
   Click one on the calendar, expand **Event notes**, and show the preserved
   supervisor note plus the delimited `[CLIMATE WORKFORCE NOTICE]` section.
   It includes severity, warning interval, forecast measure/source/update time,
   configured policy and an explicit informational/not-clearance disclaimer.
   Run the pass again: results say `unchanged`, with no duplicate section or
   event-time changes. Indoor, unknown and moved-outside-warning events receive
   no note action. Disabling automatic notes stops future passes.
6. Click **Show infeasible proposals**. It requests 12:00–13:00, inside the
   heat warning. The pump inspection needs 90 minutes, exceeding that 60-minute
   window; its result has null proposed times and an explicit explanation.
   No feasible time is invented, and there is no apply button for that result.

Annotation updates the event version. If notes are added before approval, an old
proposal correctly fails the version check; generate a fresh proposal and review
it again. Annotation permission/configuration is separate from approval. Approval
never invokes annotation automatically.

## Repeatable automated journey

With Docker running:

```bash
python scripts/demo_journey.py
```

Use the project's virtualenv Python (or install `httpx`). The script creates a
separate demo session, asserts the journey through the served Nginx/API, verifies
idempotent notes and the infeasible explanation, and ends its session. It never
modifies a real calendar or needs live credentials.

Run `pytest` for deterministic tests. `tests/test_demo_journey.py` additionally
verifies timed background execution without page requests, note failure reporting,
malformed note delimiters, independent permissions, and preservation of unrelated
notes/content and event times.

## Background configuration and limitations

- `WORKFORCE_BACKGROUND_CHECK_SECONDS` sets the positive polling interval
  (Docker default 30). Per-session note configuration defaults off and requires
  `annotate` permission. External credential grants must include that permission.
- Use the MCP `configure_warning_notes` and `annotate_warning_notes` tools through
  `/agent` to control and run the background note pass. Session results include
  updated/unchanged/failed per-event details.
- The backend process must be running; the page need not be open. Monitoring
  stops at session expiry and is not restored after restart. This is an MVP
  in-process scheduler for one worker, not a deployed Cloud Scheduler service.
- Disclaimer rendering is deterministic and replaces only its product-owned
  section. Malformed/multiple product markers require review and report failure.
  Unknown/stale data is skipped rather than annotated as cleared. Earlier notes
  on no-longer-affected events are preserved as informational history; automatic
  removal is not implemented.
- The bounded planner checks duration, forecast/policy, employee/location conflicts
  and a 15-minute candidate grid. It is not a global optimizer and does not model
  travel, equipment or arbitrary enterprise rules. Operational guidance requires
  verified site policy and live forecast/calendar adapters.
- Source-version compare-and-swap, terminal decisions, rollback and idempotent
  decisions protect demo writes. Real provider ETags, uncertain-outcome recovery,
  enterprise identity and multi-replica scheduling remain integration work.

See [agent boundaries](CLIMATE_AGENT.md) and
[approval details](RESCHEDULING_APPROVAL.md).
