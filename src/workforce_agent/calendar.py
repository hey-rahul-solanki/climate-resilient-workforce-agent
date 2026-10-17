"""Deterministic calendar demo and interval classification; no model safety decisions."""
from datetime import date, datetime, timedelta

from workforce_agent.schemas import SafetyPolicy, WeatherForecast
from workforce_agent.schemas.calendar import CalendarActivity, WarningMatch
from workforce_agent.schemas.common import TimeWindow


def policy_applies(activity, policy):
    if policy is None:
        return False
    if policy.applies_to_site_ids and activity.get('site_id') not in policy.applies_to_site_ids:
        return False
    if policy.applies_to_work_locations and activity.get('location') not in policy.applies_to_work_locations:
        return False
    exposure = activity.get('exposure_type')
    if exposure:
        return exposure in policy.applies_to_exposure_types and not (activity.get('kind') == 'outdoor' and exposure == 'indoor_controlled')
    return any(e in ('outdoor_heat','outdoor_storm') for e in policy.applies_to_exposure_types)


def classify_activity(activity, warnings, *, weather_fresh=True, policy_applicable=True):
    start, end = datetime.fromisoformat(activity['start']), datetime.fromisoformat(activity['end'])
    if start.tzinfo is None or end.tzinfo is None or end <= start:
        raise ValueError('Activity requires an increasing, timezone-aware interval')
    matches = []
    seen = {}
    for warning in warnings:
        window = TimeWindow.model_validate({'start':warning['start'],'end':warning['end']})
        if warning['id'] in seen:
            if seen[warning['id']] != warning:
                raise ValueError('Conflicting definitions for the same warning ID')
            continue
        seen[warning['id']] = warning
        if (activity.get('kind') == 'outdoor'
            and (not warning.get('site_id') or warning['site_id'] == activity.get('site_id'))
            and (not warning.get('work_locations') or activity.get('location') in warning['work_locations'])
            and policy_applicable and start < window.end and end > window.start):
            matches.append(warning)
    evidence = [WarningMatch(warning_id=w['id'],
        overlap=TimeWindow(start=max(start,datetime.fromisoformat(w['start'])),end=min(end,datetime.fromisoformat(w['end']))),
        severity=w.get('severity','Unknown'), policy=w.get('policy'),
        rationale=f"Outdoor activity at {activity.get('location') or 'unknown work location'} overlaps {w.get('title','climate warning')}; {w.get('policy','configured policy context unavailable')}."
                  + (' Current forecast requires review; this match is not clearance.' if not weather_fresh else '')
    ).model_dump(mode='json') for w in matches]
    review = not weather_fresh or activity.get('kind') not in ('indoor', 'outdoor') or not str(activity.get('location') or '').strip() or (activity.get('kind') == 'outdoor' and not policy_applicable)
    issues = []
    if activity.get('kind') not in ('indoor','outdoor'): issues.append('Indoor/outdoor classification is unknown')
    if not str(activity.get('location') or '').strip(): issues.append('Work location is unknown')
    if not weather_fresh: issues.append('Forecast/site coverage or policy data is missing, stale, or incomplete')
    if activity.get('kind') == 'outdoor' and not policy_applicable: issues.append('No applicable configured policy for this site, work location and exposure')
    reason = (('; '.join(issues) + '; needs review.') if review else
              '; '.join(f"{w.get('title', 'Climate warning')}: {w.get('policy', 'Configured policy')}" for w in matches) if matches else
              'Indoor activity: outdoor weather alone does not trigger a flag; this is not safety clearance.' if activity.get('kind') == 'indoor' else 'No overlapping applicable climate warning; this is not safety clearance.')
    return {'status': 'needs-review' if review else 'affected' if matches else 'unflagged',
            'reason': reason, 'warning_ids': [w['id'] for w in matches], 'warning_matches':evidence}


def _normalize_activities(activities):
    unique = {}
    for raw in activities:
        model = CalendarActivity.model_validate(raw)
        activity = {**raw,'start':model.start.isoformat(),'end':model.end.isoformat(),
                    'kind':model.kind,'location':model.location,'site_id':model.site_id}
        key = (model.site_id,model.id)
        if key in unique and unique[key] != activity:
            raise ValueError('Conflicting activity records for the same site/activity ID')
        unique[key] = activity
    return list(unique.values())


def match_warning_intervals(activities, warnings, *, weather_fresh=True, policy=None):
    """Match supplied warning intervals once per activity; preserve all evidence.

    Without a policy argument, warnings must already be policy-scoped by the caller.
    This function does not invent thresholds or evaluate forecast freshness.
    """
    results = []
    for activity in _normalize_activities(activities):
        results.append({**activity,**classify_activity(activity,warnings,weather_fresh=weather_fresh,
                        policy_applicable=policy_applies(activity,policy) if policy else True)})
    affected = [a for a in results if a['warning_ids']]
    return dict(activities=results, affected_activities=affected,
                needs_review_activities=[a for a in results if a['status']=='needs-review'],
                affected_activity_count=len(affected))


def analyze_calendar(activities, forecast: WeatherForecast | None, policy: SafetyPolicy | None,
                     *, now: datetime, stale_after_minutes=180):
    """Derive site-scoped warning intervals and matches from normalized hourly inputs.

    Hourly samples cover [valid_at, valid_at + 1h). Adjacent intervals from the
    same policy rule/severity are merged. Unknown inputs never yield clearance.
    """
    if now.tzinfo is None:
        raise ValueError('now must be timezone-aware')
    fresh = bool(forecast and policy and not forecast.quality.is_stale
                 and forecast.quality.is_complete and forecast.quality.covers_requested_window
                 and not policy.rules and not policy.operational_constraints
                 and not any(h.missing_fields() or any(getattr(h, t.metric.value) is None for t in policy.heat_thresholds) for h in forecast.hourly)
                 and timedelta(0) <= now - forecast.issued_at <= timedelta(minutes=stale_after_minutes))
    warnings = []
    if forecast and policy and (not policy.applies_to_site_ids or forecast.site_id in policy.applies_to_site_ids):
        groups = {}
        for hour in forecast.hourly:
            start = max(hour.valid_at, forecast.valid_from)
            end = min(hour.valid_at + timedelta(hours=1), forecast.valid_until)
            if end <= start:
                continue
            triggers = []
            for threshold in policy.heat_thresholds:
                value = getattr(hour, threshold.metric.value)
                if value is None:
                    continue
                severity = ('Critical' if value >= threshold.prohibitive_c else
                            'High' if value >= threshold.high_c else
                            'Caution' if value >= threshold.caution_c else None)
                if severity:
                    triggers.append((threshold.metric.value, 'Heat warning', severity, value, '°C'))
            if policy.max_wind_speed_ms is not None and hour.wind_speed_ms is not None and hour.wind_speed_ms > policy.max_wind_speed_ms:
                triggers.append(('wind_speed_ms', 'High wind', 'High', hour.wind_speed_ms, 'm/s'))
            if policy.max_precipitation_mm is not None and hour.precipitation_mm is not None and hour.precipitation_mm > policy.max_precipitation_mm:
                triggers.append(('precipitation_mm', 'Heavy precipitation', 'High', hour.precipitation_mm, 'mm'))
            if hour.weather_code in policy.prohibited_weather_codes or (policy.lightning_prohibits_work and hour.weather_code in (95, 96, 99)):
                triggers.append(('weather_code', 'Prohibited weather', 'Critical', hour.weather_code, 'WMO'))
            for metric, title, severity, value, unit in triggers:
                key = (metric, severity)
                previous = groups.get(key)
                if previous and previous['end'] == start.isoformat():
                    previous['end'] = end.isoformat()
                    previous['peak'] = max(previous['peak'], value)
                    previous['measure'] = f"{metric}: {previous['peak']:g} {unit} (peak)"
                else:
                    warning = dict(id=f'{policy.policy_id}:{metric}:{start.isoformat()}',
                                   title=title, severity=severity, start=start.isoformat(), end=end.isoformat(),
                                   measure=f'{metric}: {value:g} {unit} (peak)', peak=value,
                                   policy=f'{policy.name} v{policy.version}', site_id=forecast.site_id,
                                   work_locations=policy.applies_to_work_locations,
                                   source=forecast.source, updated_at=forecast.issued_at.isoformat())
                    warnings.append(warning)
                    groups[key] = warning
    classified = []
    normalized = _normalize_activities(activities)
    for activity in normalized:
        applicable = policy_applies(activity,policy)
        covered = False
        if forecast:
            start, end = datetime.fromisoformat(activity['start']), datetime.fromisoformat(activity['end'])
            cursor = start
            metrics = [t.metric.value for t in policy.heat_thresholds] if policy else []
            for hour in forecast.hourly:
                if hour.valid_at <= cursor < hour.valid_at + timedelta(hours=1):
                    if hour.missing_fields() or any(getattr(hour, metric) is None for metric in metrics):
                        break
                    cursor = min(end, hour.valid_at + timedelta(hours=1))
                    if cursor == end:
                        break
            covered = (forecast.valid_from <= start < end <= forecast.valid_until and cursor == end
                       and activity.get('site_id') == forecast.site_id)
        item = {**activity, **classify_activity(activity, warnings, weather_fresh=fresh and covered, policy_applicable=applicable)}
        from workforce_agent.policy_windows import check_rest_intervals, policy_source
        rules,blocks,rest_review=[],[],False
        if fresh and covered and applicable and activity['kind']=='outdoor':
            rules,blocks,rest_review=check_rest_intervals(activity,forecast,policy,normalized)
        item['policy_validation_status']='needs-review' if item['status']=='needs-review' else 'blocked' if item['status']=='affected' else 'valid'
        if blocks:
            item['policy_validation_status']='needs-review' if rest_review or item['status']=='needs-review' else 'blocked'
            item['status']='needs-review'
            item['reason']+='; '+'; '.join(b['reason'] for b in blocks)
        item['policy_blocks']=blocks
        item['policy_context']=dict(status='needs-review' if item['status']=='needs-review' else 'configured' if policy else 'unknown',
            name=policy.name if policy else None,version=policy.version if policy else None,
            source=policy_source(policy),reason=item['reason'],illustrative=policy.illustrative if policy else False,
            applicable_work_rest_rules=rules)
        classified.append(item)
    for warning in warnings:
        warning['affected_activity_count'] = sum(warning['id'] in a['warning_ids'] for a in classified)
    return dict(warnings=warnings, activities=classified,
                affected_activities=[a for a in classified if a['warning_ids']],
                needs_review_activities=[a for a in classified if a['status']=='needs-review'],
                affected_activity_count=sum(bool(a['warning_ids']) for a in classified),
                weather=dict(status='current' if fresh else 'needs-review',
                             source=forecast.source if forecast else 'Unavailable',
                             updated_at=forecast.issued_at.isoformat() if forecast else None))


def demo_inputs(day: date):
    def at(time):
        return f'{day.isoformat()}T{time}:00+05:30'
    policy = SafetyPolicy.model_validate(dict(policy_id='demo-heat', name='Demo heat policy — requires site confirmation', version='1',
        source='Deterministic demo configuration; requires site confirmation', illustrative=True,
        applies_to_exposure_types=['outdoor_heat'], heat_thresholds=[dict(metric='apparent_temperature_c', caution_c=35, high_c=40, prohibitive_c=45)],
        work_rest_rules=[], lightning_prohibits_work=True, prohibited_weather_codes=[95, 96, 99], missing_weather_action='require_review'))
    forecast = WeatherForecast.model_validate(dict(site_id='VAD-PLANT-01', issued_at=at('05:00'), source='Deterministic demo forecast',
        valid_from=at('06:00'), valid_until=at('18:00'), hourly=[dict(valid_at=at(f'{h:02}:00'), temperature_c=30,
        apparent_temperature_c=41 if 12 <= h < 16 else 32, relative_humidity_pct=50,
        precipitation_mm=0, weather_code=0, wind_speed_ms=2) for h in range(6,18)],
        quality=dict(is_complete=True, is_stale=False, covers_requested_window=True, missing_variables=[], incomplete_hour_count=0, notes=[])))
    return forecast, policy


def demo_calendar(day: date, *, include_suggestions=True):
    def at(time):
        return f'{day.isoformat()}T{time}:00+05:30'
    forecast, policy = demo_inputs(day)
    employees = [{'id': str(i), 'name': name, 'role': role} for i, (name, role) in enumerate([
        ('Aarav Patel', 'Electrical technician'), ('Meera Shah', 'Site inspector'),
        ('Rohan Desai', 'Maintenance'), ('Nisha Rao', 'Operations')])]
    rows = [('0', 'Equipment inspection', '08:00', '10:00', 'outdoor', 'North yard'),
            ('0', 'Panel maintenance', '11:30', '13:30', 'outdoor', 'Substation'),
            ('1', 'Site inspection', '12:30', '15:00', 'outdoor', 'East perimeter'),
            ('1', 'Documentation', '09:00', '11:00', 'indoor', 'Site office'),
            ('2', 'Workshop repairs', '12:00', '16:00', 'indoor', 'Workshop'),
            ('2', 'Pump inspection', '15:30', '17:00', 'outdoor', 'Pump station'),
            ('3', 'Asset survey', '10:00', '12:00', 'unknown', None),
            ('3', 'Shift handover', '16:00', '17:00', 'indoor', 'Site office')]
    activities = []
    for i, (employee, title, start, end, kind, location) in enumerate(rows):
        item = dict(id=f'event-{i}', employee_id=employee, title=title, start=at(start), end=at(end), kind=kind, location=location, site_id='VAD-PLANT-01', notes='Supervisor note: follow the site briefing.')
        activities.append(item)
    analysis = analyze_calendar(activities, forecast, policy, now=datetime.fromisoformat(at('06:00')))
    activities, warnings = analysis['activities'], analysis['warnings']
    suggestions = validated_suggestions(activities, forecast, policy,
        datetime.fromisoformat(at('06:00')), datetime.fromisoformat(at('12:00'))) if include_suggestions else []
    return dict(date=day.isoformat(), site={'id': 'VAD-PLANT-01', 'name': 'Vadodara · Main plant', 'timezone': 'Asia/Kolkata'},
                window={'start': at('06:00'), 'end': at('18:00')}, employees=employees, activities=activities, warnings=warnings, suggestions=suggestions,
                weather={'status': 'fixture', 'source': 'Deterministic demo forecast', 'updated_at': at('05:00')},
                integrations={'agent': 'Simulated · no Gemini connection', 'mcp': 'Not connected', 'calendar': 'Demo · writes disabled'})


def validated_suggestions(activities, forecast, policy, lower, upper):
    """Greedy proposals on a 15-minute grid, reserved together and never applied.

    This bounded demo planner handles employee and location conflicts. Live
    equipment, travel, source versions and site-specific rules need an adapter.
    """
    from copy import deepcopy
    reservations = deepcopy(activities)
    suggestions = []
    for activity in activities:
        if not activity['warning_ids']:
            continue
        duration = datetime.fromisoformat(activity['end']) - datetime.fromisoformat(activity['start'])
        candidate, chosen = lower, None
        while candidate + duration <= upper:
            end = candidate + duration
            replacement = {**activity, 'start':candidate.isoformat(), 'end':end.isoformat()}
            validation = analyze_calendar([replacement]+[a for a in reservations if a['id']!=activity['id']], forecast, policy, now=forecast.issued_at)
            conflict = any(a['id'] != activity['id'] and
                           (a['employee_id'] == activity['employee_id'] or a['location'] == activity['location']) and
                           candidate < datetime.fromisoformat(a['end']) and end > datetime.fromisoformat(a['start'])
                           for a in reservations)
            if not conflict and validation['activities'][0]['status'] == 'unflagged' and activity['status'] != 'needs-review':
                chosen = replacement
                break
            candidate += timedelta(minutes=15)
        if chosen:
            reservations = [chosen if a['id'] == activity['id'] else a for a in reservations]
        suggestions.append(dict(id=f"proposal-{activity['id']}", activity_id=activity['id'],
            start=chosen['start'] if chosen else None, end=chosen['end'] if chosen else None,
            validation='demo-validated' if chosen else 'needs-review' if activity['status'] == 'needs-review' else 'no-feasible-slot',
            rationale='Validated against demo forecast/policy, duration, employee/location conflicts and requested window; approval required.' if chosen else (f'Required duration {duration.total_seconds()/60:g} minutes exceeds the requested {(upper-lower).total_seconds()/60:g}-minute window; no feasible slot.' if duration > upper-lower else 'Every candidate conflicts with a climate warning or employee/location availability under the demo policy; no feasible slot.'),
            warning_ids=activity['warning_ids'], warning_matches=activity.get('warning_matches',[]),
            infeasibility_reasons=[] if chosen else ['unknown-inputs'] if activity['status']=='needs-review' else ['duration-exceeds-window'] if duration>upper-lower else ['climate-or-availability-conflict'],
            validation_checks={'policy_and_availability': bool(chosen)},
            policy=f'{policy.policy_id} v{policy.version}', approval='pending'))
    return suggestions
