"""Deterministic gate for untrusted model candidates. No calendar writes."""
from datetime import datetime
from zoneinfo import ZoneInfo

from workforce_agent.calendar import analyze_calendar


def warning_overlap_minutes(activity):
    return sum(max(0, (datetime.fromisoformat(match['overlap']['end']) -
                       datetime.fromisoformat(match['overlap']['start'])).total_seconds() / 60)
               for match in activity.get('warning_matches', []))


def validate_model_candidates(plan, calendar, forecast, policy, constraints, *, evaluation_time):
    reservations = [dict(a) for a in calendar['activities']]
    results = []
    zone = ZoneInfo(calendar['site']['timezone'])
    def bound(value, fallback):
        return datetime.fromisoformat(f"{calendar['date']}T{value}:00").replace(tzinfo=zone) if value else datetime.fromisoformat(fallback)
    lower=max(bound(constraints.earliest,calendar['window']['start']),datetime.fromisoformat(calendar['window']['start']))
    upper=min(bound(constraints.latest,calendar['window']['end']),datetime.fromisoformat(calendar['window']['end']))
    for candidate in plan.candidates:
        original = next(a for a in reservations if a['id']==candidate.activity_id)
        allowed = original['kind']=='outdoor' and bool(original['warning_ids']) and original['status']!='needs-review'
        checks = dict(activity_scope=allowed and (not plan.activity_ids or original['id'] in plan.activity_ids),
            duration=candidate.end-candidate.start == datetime.fromisoformat(original['end'])-datetime.fromisoformat(original['start']),
            requested_window=lower <= candidate.start < candidate.end <= upper,
            availability=not any(a['id']!=original['id'] and (a['employee_id']==original['employee_id'] or a['location']==original['location'])
                and candidate.start<datetime.fromisoformat(a['end']) and candidate.end>datetime.fromisoformat(a['start']) for a in reservations),
            weather_policy=False)
        proposed={**original,'start':candidate.start.isoformat(),'end':candidate.end.isoformat()}
        analysis=analyze_calendar([proposed]+[a for a in reservations if a['id']!=original['id']],forecast,policy,now=evaluation_time)
        analyzed=analysis['activities'][0]
        remaining_overlap=warning_overlap_minutes(analyzed)
        original_overlap=warning_overlap_minutes(original)
        # A supervisor may accept residual warning overlap when the move
        # materially reduces exposure. Hard policy/rest blocks still fail.
        hard_blocks=[b for b in analyzed.get('policy_blocks',[]) if b.get('code') != 'climate-warning']
        reduced=remaining_overlap < original_overlap
        checks['weather_policy']=(analyzed['status']=='unflagged' or
                                  (analyzed['status']=='affected' and reduced and not hard_blocks))
        risk_reduced=checks['weather_policy'] and analyzed['status']!='unflagged'
        valid=all(checks.values())
        if valid:
            reservations=[proposed if a['id']==original['id'] else a for a in reservations]
        results.append(dict(id=f"candidate-{original['id']}",activity_id=original['id'],
            start=proposed['start'] if valid else None,end=proposed['end'] if valid else None,
            candidate_window=dict(start=proposed['start'],end=proposed['end']),
            rationale=(f'{candidate.explanation} ' + (f'The move reduces climate-warning overlap from {original_overlap:g} to {remaining_overlap:g} minutes; residual overlap remains and requires supervisor acknowledgement and a reason. '
                       if risk_reduced else 'Deterministic validation accepted this candidate; supervisor approval and fresh revalidation remain required. ')
                       if valid else f'{candidate.explanation} The candidate failed deterministic checks; review or revision is required.'),
            validation='risk-reduced' if valid and risk_reduced else 'demo-validated' if valid else 'needs-review',validation_checks=checks,
            infeasibility_reasons=[key for key,passed in checks.items() if not passed],
            policy_blocks=analysis['activities'][0].get('policy_blocks',[]),policy_context=analysis['activities'][0].get('policy_context'),
            model_explanation=candidate.explanation,warning_ids=original['warning_ids'],
            warning_matches=original.get('warning_matches',[]),policy=f'{policy.policy_id} v{policy.version}' if policy else 'Unknown policy',approval='pending'))
    return results
