# Policy explanations in the agent panel

Suggestion cards and the all-flagged activity list show backend activity reasons,
policy references, work location/type, and policy source when available. Fixture
data is explicitly labelled illustrative and requiring site confirmation. Missing
source/applicability and unknown location/type are shown as needs-review. Text and
warning icons accompany styling; explanatory text uses dark colors on a light
background.

The frontend accepts this optional `policy_context` on an activity:

```json
{
  "status": "configured",
  "name": "Site-configured policy",
  "version": "site-version",
  "source": "Site-approved policy document reference",
  "reason": "Backend explanation of why this policy applies to this activity",
  "illustrative": false,
  "applicable_work_rest_rules": [
    {
      "work_minutes": 37,
      "rest_minutes": 13,
      "cooling_required": true,
      "reason": "Backend-supplied explanation for this applicable requirement"
    }
  ]
}
```

These numbers are arbitrary contract-test examples, not guidance or fixture policy.
`name`, `source` and `reason` may be null; status also accepts `unknown` or
`needs-review`. Rules must already be selected for the activity by the backend.
The UI validates nonnegative integer minutes and boolean cooling flags, renders
the supplied values, and never selects a temperature band or infers safety.
`illustrative` is required whenever the context object is supplied.

Backend calendar analysis now emits this context, including the configured policy
source, version and illustrative status. It supplies only work/rest rules whose
configured metric band applies to that activity. Current demo fixtures configure
no work/rest rules, so their requirement list remains empty. Missing metadata from
other/older adapters remains explicit. See [deterministic window validation](POLICY_WINDOW_VALIDATION.md)
for enforcement semantics and limitations; no official-policy integration is claimed.

Verification: `npm test --prefix frontend`, `npm run lint --prefix frontend`, and
`npm run build --prefix frontend`. Tests cover supplied values/source/reasons,
illustrative labels, unknown data, missing requirements and malformed rule values.
