"""Deterministic work/rest gate for continuous outdoor calendar activities.

Breaks are trusted calendar inputs, never model assertions. Long work must be split
into separate activities; this gate does not silently shorten work or insert breaks.
"""
from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictBool

from workforce_agent.schemas.common import TimeWindow


class RestInterval(TimeWindow):
    model_config = ConfigDict(extra='forbid')
    cooling_available: StrictBool | None = None


class PolicyBlock(BaseModel):
    code: str
    reason: str
    policy_id: str | None
    policy_version: str | None
    policy_source: str | None


class WindowPolicyResult(BaseModel):
    status: Literal['valid','blocked','needs-review']
    policy_id: str | None
    policy_version: str | None
    policy_source: str | None
    blocks: list[PolicyBlock]


def policy_source(policy):
    return (policy.source or f'Configured policy {policy.policy_id} v{policy.version}') if policy else None


def check_rest_intervals(activity, forecast, policy, activities):
    """Return applicable rules and reasons; caller establishes weather coverage first.

    Any overlapping hourly sample can activate a half-open configured metric band.
    Each continuous activity must fit every active work limit and have a contiguous
    post-task rest interval. This conservative per-task rule avoids assuming prior
    recovery or treating unscheduled idle time as approved cooling.
    """
    start,end=map(datetime.fromisoformat,(activity['start'],activity['end']))
    blocks=[]
    applicable=[]
    review=False
    def block(code,reason,unknown=False):
        nonlocal review
        review |= unknown
        blocks.append(PolicyBlock(code=code,reason=reason,policy_id=policy.policy_id,
            policy_version=policy.version,policy_source=policy_source(policy)).model_dump())
    for window in activity.get('mandatory_rest_intervals',[]):
        rest=TimeWindow.model_validate(window)
        if start < rest.end and end > rest.start:
            block('mandatory-rest-overlap','Move work outside the reserved mandatory rest/cooling interval.')
    for rule in policy.work_rest_rules:
        hours=[h for h in forecast.hourly if h.valid_at < end and h.valid_at+timedelta(hours=1)>start]
        values=[getattr(h,rule.metric.value) for h in hours]
        if any(value is None for value in values):
            block('missing-rest-metric',f'Provide {rule.metric.value} forecast data to evaluate the configured work/rest band.',True)
            continue
        if not any(rule.min_c <= value < rule.max_c for value in values):
            continue
        if not activity.get('employee_id'):
            block('unknown-employee','Identify the assigned employee before validating recovery conflicts.',True)
        applicable.append(dict(work_minutes=rule.work_minutes,rest_minutes=rule.rest_minutes,
            cooling_required=rule.cooling_required,reason=f'Configured {rule.metric.value} band [{rule.min_c:g}, {rule.max_c:g}) applies.'))
        if rule.required_action.value not in ('proceed','notify','extra_breaks'):
            block('rest-rule-action',f'Configured work/rest rule requires {rule.required_action.value}; obtain a revised plan or policy review.',rule.required_action.value=='require_review')
        if rule.work_minutes==0 or end-start>timedelta(minutes=rule.work_minutes):
            block('continuous-work-limit',f'Split or shorten the continuous work segment to at most {rule.work_minutes} minutes and reserve the configured recovery interval.')
        if not rule.rest_minutes and not rule.cooling_required:
            continue
        if rule.cooling_required and rule.rest_minutes==0:
            block('unspecified-cooling-duration','Configure a positive cooling duration before validating this activity.',True)
            continue
        recovery_end=end+timedelta(minutes=rule.rest_minutes)
        rests=[RestInterval.model_validate(r) for r in activity.get('scheduled_rest',[])]
        covering=[r for r in rests if r.start==end and r.end>=recovery_end]
        if not covering:
            block('missing-recovery',f'Reserve at least {rule.rest_minutes} uninterrupted minutes of rest immediately after this work segment.')
            continue
        if rule.cooling_required and not any(r.cooling_available is True for r in covering):
            unknown=any(r.cooling_available is None for r in covering)
            block('cooling-unverified' if unknown else 'cooling-unavailable','Provide a verified cooling facility for the entire required recovery interval.',unknown)
        if any(a['id']!=activity['id'] and activity.get('employee_id') is not None and a.get('employee_id')==activity.get('employee_id')
               and end<datetime.fromisoformat(a['end']) and recovery_end>datetime.fromisoformat(a['start']) for a in activities):
            block('break-conflict','Move conflicting employee work out of the mandatory post-task recovery interval.')
    return applicable,blocks,review


def evaluate_proposed_window(activity, forecast, policy, *, now, activities=None):
    """Typed reusable gate shared through calendar analysis with REST/MCP/approval."""
    from workforce_agent.calendar import analyze_calendar
    schedule=[activity]+[a for a in (activities or []) if a['id']!=activity['id']]
    item=analyze_calendar(schedule,forecast,policy,now=now)['activities'][0]
    blocks=list(item.get('policy_blocks',[]))
    status=item['policy_validation_status']
    if item.get('warning_ids'):
        blocks.extend(dict(code='climate-warning',reason=w['rationale'],policy_id=policy.policy_id if policy else None,
            policy_version=policy.version if policy else None,policy_source=policy_source(policy)) for w in item.get('warning_matches',[]))
    if status=='needs-review' or (status=='blocked' and not blocks):
        blocks.append(dict(code='climate-warning' if status=='blocked' else 'unknown-inputs',
            reason=item['reason'],policy_id=policy.policy_id if policy else None,
            policy_version=policy.version if policy else None,policy_source=policy_source(policy)))
    return WindowPolicyResult(status=status,
        policy_id=policy.policy_id if policy else None,policy_version=policy.version if policy else None,
        policy_source=policy_source(policy),blocks=blocks)
