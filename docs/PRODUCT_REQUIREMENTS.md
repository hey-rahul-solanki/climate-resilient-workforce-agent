# Product Requirements: Climate-Resilient Workforce Planning

**Status:** MVP product brief  
**Product:** Climate-Resilient Workforce Planning  
**Repository:** `hey-rahul-solanki/climate-resilient-workforce-agent`  
**Primary experience:** Day-view workforce schedule with a climate-agent side panel  
**Audience:** Operations managers, EHS leads, and industrial field-maintenance planners

## 1. Product vision
Help industrial operations teams see which planned outdoor tasks overlap with hazardous weather, understand why they are flagged, and review safer schedule proposals without losing operational context or bypassing safety policy.

The product is a decision-support system. It must make risks and trade-offs understandable; it must not claim that work is safe solely because an AI agent says so.

## 2. MVP problem
Managers currently need to cross-reference worker schedules, outdoor task locations, weather forecasts, resource constraints, and site safety rules. This is error-prone and slow, especially when several tasks overlap a high-heat period.

## 3. MVP goals
- Show a single site's daily schedule by worker and time.
- Visually distinguish outdoor tasks, indoor tasks, climate-risk periods, and flagged assignments.
- Summarize the number of affected tasks and the relevant forecast window.
- Present a short ranked list of actionable schedule suggestions with a reason and suggested time.
- Let a manager inspect a proposal, compare current and proposed times, and approve, reject, or request revision.
- Surface required cooling/rest periods and explain the policy basis.
- Support conversational questions such as “Who is affected?” and “Suggest safer times.”
- Clearly show whether data is simulated, fixture-based, or live; display forecast freshness.
- Keep all schedule changes as proposals until an authorized manager approves them.

## 4. Non-goals for the MVP
- Global optimal schedule search, objective-function scoring, or OR-Tools-based optimization.
- Autonomous calendar writes or agent-controlled safety overrides.
- Multi-site portfolio analytics and workforce performance scoring.
- Historical insights, advanced notification delivery, and MCP integration (future phase).
- Treating a blank/missing forecast as safe.

## 5. Primary user and key journey
**Primary user:** Site operations manager responsible for daily field-maintenance work.

1. Open the day view for a site and date.
2. See the schedule, forecast risk window, affected outdoor tasks, and data freshness.
3. Select a flagged task or suggestion.
4. Inspect the reason, source forecast, policy rule, resource constraints, and proposed alternative window.
5. Review the change list, including tasks that cannot be safely rescheduled.
6. Approve, reject, or request a revision.
7. If approved, apply the change only through the authorized calendar integration; show a clear success/failure result and audit trail.

## 6. Main page requirements

### A. Schedule header
- Show selected site, date, worker count, and navigation to previous/next day and Today.
- Changing site/date refreshes schedule and weather data.
- Show a clear loading, empty, and error state.

### B. Day timeline
- Rows represent workers; each row shows worker name and role/team.
- Horizontal axis shows local site time and scheduled task duration.
- Task cards show task name, time range, and indoor/outdoor classification.
- Outdoor tasks overlapping a risk window receive a high-contrast warning state and explicit risk label.
- Indoor tasks are visually distinct and are not flagged solely because they occur during the heat window.
- Show the climate-risk interval as a background band with a legend.
- Avoid relying on color alone: pair colors with icons/text and provide accessible contrast.
- Support overlapping/conflicting tasks without hiding either task; on narrow screens, provide a usable alternative layout.

### C. Climate summary banner
- Show severity, start/end time, relevant measure (for example, feels-like temperature), and count of affected tasks.
- Explain that the banner is forecast-based and display the forecast issue/update time.
- If data is stale, incomplete, or unavailable, show that status explicitly and do not assert safe conditions.

### D. Climate agent panel
- Show connection/data status honestly (for example, “Demo data”, “Weather connected”, “Agent unavailable”); do not imply MCP is connected unless it is.
- Show total flagged events and top suggestions.
- Each suggestion includes affected worker/task, reason, suggested time, and a Review action.
- “View more” opens the full flagged-task list.
- Quick prompts include “Who is affected?” and “Suggest safer times.”
- Answers cite the task, forecast window, and applicable policy in plain language.
- Agent output is advisory; it cannot bypass deterministic policy validation.

### E. Cooling periods and policy
- Show applicable work/rest rules and the source/configuration of the policy.
- Mark whether a rule is informational or requires review/approval.
- Proposed schedules must respect mandatory breaks and prohibited work windows.
- Do not invent medical thresholds or present demo values as official policy.

### F. Proposal review and approval
- Show current versus proposed time, affected workers/resources, climate rationale, policy rationale, and validation results.
- Offer Approve, Reject, and Request revision actions with confirmation where appropriate.
- Revalidate policy, worker/resource availability, and source-event version at approval time.
- Never apply pending/rejected proposals. Show audit status and any integration error.

## 7. Functional requirements
- FR-01: Retrieve workers, tasks, site configuration, weather, and policy through typed API contracts.
- FR-02: Evaluate climate risk deterministically from configured policy and normalized forecast data.
- FR-03: Identify impacted tasks by outdoor classification and overlap between task window and risk window.
- FR-04: Generate simple feasible time suggestions respecting duration, skills, shift, dependencies, resources, and breaks.
- FR-05: Preserve an immutable baseline snapshot for each planning run.
- FR-06: Return structured proposals and explicit reasons when no feasible safe slot exists.
- FR-07: Keep proposal approval separate from proposal generation and calendar writes.
- FR-08: Make simulated versus live integrations unmistakable in the UI.
- FR-09: Record proposal decisions and integration outcomes for auditability.
- FR-10: Provide deterministic fixtures so the main demo works without live API dependencies.

## 8. Safety, privacy, and reliability
- Deterministic policy validation is authoritative; the LLM is never the safety enforcement layer.
- Unknown or stale weather must result in “unknown / needs review”, not “safe”.
- The system must not schedule work in a prohibited window or violate mandatory cooling/rest rules.
- Do not infer health status or use the system for worker discipline.
- Minimize personal data; show only operationally necessary worker information.
- Clearly separate recommendations from applied schedule changes.
- All times use the site's timezone; handle daylight-saving transitions where applicable.

## 9. MVP success criteria
- A reviewer can identify affected tasks and the risk window within 10 seconds of opening the day view.
- Every flagged task has a visible, understandable reason.
- Every proposed change shows current time, proposed time, and validation outcome.
- Tests prove unsafe proposals are blocked and unapproved changes never write to a calendar.
- Demo works repeatably with fixed fixture data and explicitly labels simulated integrations.
- No critical schedule content is hidden behind color alone.

## 10. MVP scope and sequencing
1. **Data and baseline:** schemas, synthetic fixture, immutable baseline.
2. **Risk and feasibility:** weather normalization, deterministic climate policy, resource and cooling-break validation.
3. **Planning:** simple safe-window suggestions; no optimizer.
4. **Review UI:** timeline, risk banner, agent panel, flagged list, proposal comparison and decision controls.
5. **Integration:** calendar read and approval-gated writes; clearly simulated when credentials are absent.
6. **Hardening:** safety tests, accessibility, demo scenarios and limitations.

## 11. Design reference
The supplied product screenshot is the visual reference: a wide day timeline on the left and a climate-agent panel on the right, with a site/date header, heat-risk banner, worker rows, event cards, top suggestions, cooling periods, and conversational prompts. Treat the screenshot as a direction for hierarchy and interaction, not as proof that the displayed values or integrations are real.

## 12. Open product decisions
- Confirm the initial screen uses synthetic/demo data until all API contracts are wired.
- Confirm the authoritative site policy and source for heat thresholds before presenting values as operational guidance.
- Confirm whether calendar integration is a required hackathon demo path or whether a simulated approval/write flow is sufficient.
- Confirm the minimum supported viewport and accessibility target.
