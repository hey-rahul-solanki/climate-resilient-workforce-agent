# Customer Target Strategy & Pitch Notes

## Purpose
This document captures the initial target-customer hypothesis and pitch framing for the Climate-Resilient Workforce Planning Agent. It is intended to support the MVP, pitch deck, and future customer conversations.

**Status:** Initial strategy draft. These are prospective target accounts, not confirmed buyers. Public disclosures indicate relevant operations and safety/climate-risk programmes, but do not establish quantified unmet demand for this product.

## The customer problem
Extreme weather can affect the safety and execution of planned outdoor work. Companies with recurring field maintenance, inspections, and infrastructure operations need to balance:
- Worker safety and applicable safety policies
- Planned work orders, task urgency, and dependencies
- Worker availability and site location
- Weather forecasts and changing conditions
- Operational continuity, delays, and rescheduling costs

The opportunity is not simply to forecast dangerous weather. It is to translate weather and operational context into actionable, safety-aware schedule proposals before crews begin work.

## Ideal customer profile
Prioritise organisations that have:
1. Recurring, planned fieldwork rather than purely on-demand dispatch.
2. Workers regularly operating outdoors or at exposed infrastructure sites.
3. Work orders that can sometimes be reordered or rescheduled safely.
4. Formal worker-safety processes and operational scheduling.
5. Multiple sites, crews, or assets where weather-aware coordination may be valuable.

On-demand delivery businesses are not the initial focus: an order may arrive only moments before dispatch, leaving less opportunity for advance schedule optimisation.

## Initial target-account shortlist

| Priority | Company | Relevant recurring work hypothesis | Potential product fit | Validation still needed |
|---|---|---|---|---|
| 1 | Tata Power | Electrical network maintenance, inspections, renewable-asset operations | Weather-aware scheduling of planned maintenance crews | Which teams face material weather-driven rescheduling, current workflow, and measurable costs |
| 2 | Adani Energy Solutions | Transmission infrastructure inspections and maintenance; related field operations | Prioritising and scheduling exposed infrastructure work within safety constraints | Frequency and cost of weather-related disruptions and tools already used |
| 3 | IndianOil | Pipeline inspections, refinery maintenance, and infrastructure operations | Coordinating planned outdoor inspections and maintenance | Which tasks are weather-sensitive and whether existing systems already address the problem |
| 4 | Adani Green Energy | Solar and wind asset inspections and maintenance | Planning site visits and maintenance windows around weather and safety constraints | Site-level scheduling needs, operational constraints, and potential value |
| 5 | Tata Projects | Planned construction and infrastructure project work | Adjusting work sequences when weather affects site safety or execution | Project-specific scheduling flexibility and buying decision owner |

This is a prioritised hypothesis list, not a ranking of confirmed demand or willingness to pay. Tata Power is the proposed reference-customer scenario for the MVP; the other four are expansion prospects, not dependencies.

## Proposed MVP workflow
1. Load synthetic workers, sites, work orders, weather forecasts, and safety policies.
2. Identify planned tasks whose timing or execution may conflict with forecast conditions or safety rules.
3. Use scheduling/optimisation logic to evaluate feasible alternatives, respecting task dependencies, urgency, worker availability, and operational constraints.
4. Have the agent explain the risks and propose schedule changes.
5. Require supervisor approval before changes are written to the operational calendar.
6. Show the approved proposal and rationale in the web app.

**Safety boundary:** The agent supports decision-making; it does not override site safety procedures, guarantee that conditions are safe, or autonomously change the operational calendar. Applicable safety rules and human judgement take precedence.

## Demonstration scenario
Use a clearly labelled synthetic scenario based on a power utility maintenance crew:
- A crew has several planned outdoor maintenance work orders at different sites.
- Weather forecasts indicate a potentially unsafe period for one planned activity.
- The agent identifies the conflict, explains the forecast and policy constraints, and proposes an alternative sequence or time.
- A supervisor reviews and approves or rejects the proposal.
- The web app shows the resulting plan and rationale.

Do not imply that synthetic data came from Tata Power or that Tata Power has endorsed the product.

## Evaluation metrics
Compare the baseline schedule with the proposed schedule using:
- Safety-policy compliance
- Number of tasks completed within the planning horizon
- Weather-conflicted work identified before dispatch
- Schedule changes and delay minutes
- Estimated overtime or rescheduling cost, if assumptions are supplied
- Worker and equipment constraint violations
- Supervisor approval rate and reasons for rejection

Use synthetic data to demonstrate the method, not to claim real-world savings. Clearly label estimated benefits as illustrative and document assumptions.

## Value proposition

**One-line pitch**
> Help field operations teams plan safer, more resilient workdays by turning weather forecasts, work orders, worker availability, and safety policies into explainable schedule proposals that supervisors approve.

**Short pitch**
> Companies operating power, energy, and industrial infrastructure depend on crews performing planned work outdoors. Weather can create safety constraints and force last-minute changes. The Climate-Resilient Workforce Planning Agent combines forecasts with operational work orders and safety policies to flag conflicts and recommend feasible schedule adjustments before crews are dispatched. Supervisors retain control over approvals and calendar updates. The goal is to improve safety-aware planning and operational continuity; the size of the benefit must be validated with real operational data.

## Business case: knowns and unknowns

**Supported by the current research direction**
- The target companies operate infrastructure or project environments involving field work.
- Worker safety and climate-related operational risks are relevant themes in these industries.
- Planned maintenance and inspections provide a plausible setting for advance scheduling support.

**Not yet established**
- Annual financial cost of weather-driven field-schedule disruption at any named company
- The proportion of disruption the agent could prevent
- A reduction in injuries, insurance premiums, or claims
- A target company's active purchasing intent, budget, or integration requirements

Do not claim quantified savings or insurance reductions without evidence. A future validation exercise should seek anonymised work orders, forecast/actual weather, completion and delay records, rescheduling/overtime costs, and safety interventions. If access is unavailable, continue with a transparent synthetic-data demonstration and present the business case as a hypothesis.

## Initial discovery questions
When time permits, ask a field operations, maintenance, asset management, or EHS leader:
1. Which recurring field activities are most affected by extreme weather?
2. How are work orders rescheduled today when weather creates a safety concern?
3. Who makes the decision, and which scheduling systems are involved?
4. What costs or operational impacts are tracked: delays, overtime, repeat visits, or backlog?
5. What constraints must never be violated?
6. What evidence would justify a small pilot?

## Suggested pitch-deck structure
1. Problem: Planned fieldwork faces changing weather and safety constraints.
2. Target customer: Infrastructure operators with recurring outdoor maintenance and inspections.
3. Solution: Weather-aware workforce planning and explainable schedule proposals.
4. Workflow: Forecast + work orders + workers/sites + safety policies → proposed schedule → supervisor approval.
5. Demo: A synthetic power-utility maintenance scenario.
6. Evaluation: Baseline versus proposed schedule with transparent metrics.
7. Business-value hypothesis: Safer planning and fewer avoidable disruptions; quantify only after validation.
8. Initial target accounts: Tata Power first, then Adani Energy Solutions, IndianOil, Adani Green Energy, and Tata Projects.
9. Pilot plan: Define one workflow, baseline metrics, safety boundaries, and success criteria.
10. Ask: A short discussion with field operations or EHS to validate the workflow and identify pilot data.

## Positioning guardrails
- Refer to named companies as prospective target accounts, not customers or partners.
- Do not imply that a company endorsed the product.
- Do not claim measured reductions in injuries, costs, insurance premiums, or delays without evidence.
- Distinguish the synthetic MVP demonstration from real operational results.
- Keep supervisor approval before calendar updates as an explicit design principle.

## Research references to revisit
These links were identified during initial research and should be checked again before external publication or a pitch:
- Tata Power annual report: https://www.tatapower.com/html/integrated-annual-report-2026/
- Adani Energy Solutions annual report: https://www.adanienergysolutions.com/digital-reports/energy-solution/2026/index.html
- IndianOil: https://www.iocl.com/
- Adani Green Energy annual report: https://www.adanigreenenergy.com/digital-reports/green-energy/2026/index.html
- Tata Projects: https://tataprojects.com/

*Document status: Initial strategy draft for MVP and pitch-deck planning. Company-specific disruption costs and buyer demand have not been validated.*
