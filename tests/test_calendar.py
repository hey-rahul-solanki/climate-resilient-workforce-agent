from datetime import date

import pytest

from workforce_agent.calendar import classify_activity, demo_calendar


@pytest.mark.parametrize('start,end,kind,expected', [
    ('11:30', '12:30', 'outdoor', 'affected'),
    ('15:30', '16:30', 'outdoor', 'affected'),
    ('11:00', '12:00', 'outdoor', 'unflagged'),
    ('16:00', '17:00', 'outdoor', 'unflagged'),
    ('12:00', '16:00', 'indoor', 'unflagged'),
    ('12:00', '16:00', 'unknown', 'needs-review'),
])
def test_interval_boundaries(start, end, kind, expected):
    at = lambda value: f'2026-10-17T{value}:00+05:30'
    activity = dict(start=at(start), end=at(end), kind=kind, location='Yard')
    warnings = [dict(id='heat', start=at('12:00'), end=at('16:00'))]
    assert classify_activity(activity, warnings)['status'] == expected
    assert classify_activity(activity, warnings, weather_fresh=False)['status'] == 'needs-review'
    activity['location'] = None
    assert classify_activity(activity, warnings)['status'] == 'needs-review'


def test_demo_and_snapshot_match():
    import json
    from pathlib import Path
    snapshot = demo_calendar(date(2026, 10, 17))
    assert snapshot == json.loads(Path('frontend/src/data/calendarDemo.json').read_text())
    assert len([a for a in snapshot['activities'] if a['status'] == 'affected']) == 3
    for suggestion in snapshot['suggestions']:
        if not suggestion['start']:
            assert suggestion['validation'] == 'no-feasible-slot'
            continue
        activity = next(a for a in snapshot['activities'] if a['id'] == suggestion['activity_id'])
        replacement = {**activity, 'start': suggestion['start'], 'end': suggestion['end']}
        assert classify_activity(replacement, snapshot['warnings'])['status'] == 'unflagged'
        assert not any(a['employee_id'] == activity['employee_id'] and a['id'] != activity['id']
                       and a['start'] < replacement['end'] and a['end'] > replacement['start']
                       for a in snapshot['activities'])


def inputs():
    from workforce_agent.schemas import WeatherForecast, SafetyPolicy
    at = lambda h: f'2026-10-17T{h:02}:00:00+05:30'
    forecast = WeatherForecast.model_validate(dict(site_id='site', issued_at=at(9), source='test',
        valid_from=at(10), valid_until=at(18), hourly=[dict(valid_at=at(h), temperature_c=40 if h in (12,13,16) else 20,
        apparent_temperature_c=25, relative_humidity_pct=50, precipitation_mm=0, weather_code=0, wind_speed_ms=2) for h in range(10,18)],
        quality=dict(is_complete=True, is_stale=False, covers_requested_window=True, missing_variables=[], incomplete_hour_count=0, notes=[])))
    policy = SafetyPolicy.model_validate(dict(policy_id='policy', name='Test policy', version='2', applies_to_exposure_types=['outdoor_heat'],
        heat_thresholds=[dict(metric='temperature_c', caution_c=30, high_c=35, prohibitive_c=45)], work_rest_rules=[],
        lightning_prohibits_work=True, prohibited_weather_codes=[95], missing_weather_action='require_review'))
    return forecast, policy


def test_derived_multiple_warnings_and_site_scope():
    from workforce_agent.calendar import analyze_calendar
    from datetime import datetime
    forecast, policy = inputs()
    activity = dict(id='a', site_id='site', location='Yard', kind='outdoor', start='2026-10-17T11:30:00+05:30', end='2026-10-17T16:30:00+05:30')
    result = analyze_calendar([activity, {**activity, 'id':'indoor', 'kind':'indoor'}, {**activity, 'id':'other', 'site_id':'other'}], forecast, policy, now=datetime.fromisoformat('2026-10-17T10:00:00+05:30'))
    assert len(result['warnings']) == 2
    assert result['warnings'][0]['end'] == '2026-10-17T14:00:00+05:30'
    assert len(result['activities'][0]['warning_ids']) == 2
    assert result['affected_activity_count'] == 1
    assert all(w['affected_activity_count'] == 1 for w in result['warnings'])
    assert result['activities'][1]['status'] == 'unflagged'
    assert result['activities'][2]['status'] == 'needs-review'
    assert result['activities'][2]['warning_ids'] == []
    # Changing policy inputs changes warnings; there are no fixed heat windows.
    policy.heat_thresholds[0].caution_c = 41
    policy.heat_thresholds[0].high_c = 43
    assert analyze_calendar([activity], forecast, policy, now=forecast.issued_at)['warnings'] == []


@pytest.mark.parametrize('case', ['missing', 'stale', 'aged', 'incomplete', 'gap', 'missing_metric', 'policy'])
def test_unknown_inputs_require_review(case):
    from workforce_agent.calendar import analyze_calendar
    forecast, policy = inputs()
    now = forecast.issued_at
    if case == 'missing': forecast = None
    elif case == 'stale': forecast.quality.is_stale = True
    elif case == 'aged':
        from datetime import timedelta
        now += timedelta(hours=4)
    elif case == 'incomplete': forecast.quality.is_complete = False
    elif case == 'gap': forecast.hourly.pop(2)
    elif case == 'missing_metric': forecast.hourly[2].temperature_c = None
    elif case == 'policy': policy = None
    activity = dict(id='a', site_id='site', location='Yard', kind='outdoor', start='2026-10-17T11:30:00+05:30', end='2026-10-17T14:30:00+05:30')
    result = analyze_calendar([activity], forecast, policy, now=now)
    assert result['activities'][0]['status'] == 'needs-review'


def test_overlap_across_timezones_and_enclosing_warning():
    activity = dict(kind='outdoor', location='Yard', start='2026-10-17T06:00:00+00:00', end='2026-10-17T11:00:00+00:00')
    warnings = [dict(id='heat', title='Heat', start='2026-10-17T12:00:00+05:30', end='2026-10-17T16:00:00+05:30')]
    assert classify_activity(activity, warnings)['warning_ids'] == ['heat']


def test_stale_preserves_known_matches_without_clearance():
    from workforce_agent.calendar import analyze_calendar
    forecast, policy = inputs()
    forecast.quality.is_stale = True
    activity = dict(id='a', site_id='site', location='Yard', kind='outdoor', start='2026-10-17T12:00:00+05:30', end='2026-10-17T13:00:00+05:30')
    result = analyze_calendar([activity], forecast, policy, now=forecast.issued_at)
    assert result['activities'][0]['status'] == 'needs-review'
    assert result['activities'][0]['warning_ids']
    assert result['weather']['status'] == 'needs-review'


@pytest.mark.parametrize('kind,location,expected', [
    ('indoor','Workshop','unflagged'), ('outdoor','Yard','affected'),
    ('unknown','Yard','needs-review'), (None,'Yard','needs-review'),
    ('outdoor',None,'needs-review'), ('outdoor','  ','needs-review'),
    ('outdoor','unknown','needs-review'), ('indoor','TBD','needs-review'),
])
def test_activity_location_and_classification_contract(kind,location,expected):
    from workforce_agent.calendar import analyze_calendar
    forecast,policy=inputs()
    activity=dict(id='a',site_id='site',kind=kind,location=location,start='2026-10-17T12:00:00+05:30',end='2026-10-17T13:00:00+05:30')
    result=analyze_calendar([activity],forecast,policy,now=forecast.issued_at)['activities'][0]
    assert result['status']==expected
    if expected=='needs-review': assert 'needs review' in result['reason']
    if kind=='indoor': assert not result['warning_ids']


@pytest.mark.parametrize('scope,value,applies',[
    ('applies_to_site_ids',['site'],True),('applies_to_site_ids',['other'],False),
    ('applies_to_work_locations',['Yard'],True),('applies_to_work_locations',['Workshop'],False),
    ('applies_to_exposure_types',['outdoor_heat'],True),('applies_to_exposure_types',['indoor_controlled'],False),
])
def test_configured_policy_scope(scope,value,applies):
    from workforce_agent.calendar import analyze_calendar
    forecast,policy=inputs()
    setattr(policy,scope,value)
    activity=dict(id='a',site_id='site',kind='outdoor',location='Yard',start='2026-10-17T12:00:00+05:30',end='2026-10-17T13:00:00+05:30')
    result=analyze_calendar([activity],forecast,policy,now=forecast.issued_at)['activities'][0]
    assert result['status']==('affected' if applies else 'needs-review')
    assert bool(result['warning_ids'])==applies
    if not applies: assert 'No applicable configured policy' in result['reason']


@pytest.mark.parametrize('temperature,severity',[(29.99,None),(30,'Caution'),(35,'High'),(45,'Critical')])
def test_policy_heat_threshold_boundaries(temperature,severity):
    from workforce_agent.calendar import analyze_calendar
    forecast,policy=inputs()
    for hour in forecast.hourly: hour.temperature_c=temperature
    activity=dict(id='a',site_id='site',kind='outdoor',location='Yard',start='2026-10-17T12:00:00+05:30',end='2026-10-17T13:00:00+05:30')
    result=analyze_calendar([activity],forecast,policy,now=forecast.issued_at)
    assert result['activities'][0]['status']==('affected' if severity else 'unflagged')
    assert [w['severity'] for w in result['warnings']]==([severity] if severity else [])


def test_explicit_exposure_must_match_policy():
    from workforce_agent.calendar import analyze_calendar
    forecast,policy=inputs()
    activity=dict(id='a',site_id='site',kind='outdoor',exposure_type='outdoor_storm',location='Yard',start='2026-10-17T12:00:00+05:30',end='2026-10-17T13:00:00+05:30')
    result=analyze_calendar([activity],forecast,policy,now=forecast.issued_at)['activities'][0]
    assert result['status']=='needs-review' and result['warning_ids']==[]


def test_activity_model_rejects_naive_or_reversed_intervals():
    from workforce_agent.schemas.calendar import CalendarActivity
    from pydantic import ValidationError
    for start,end in [('2026-10-17T12:00:00','2026-10-17T13:00:00'),('2026-10-17T13:00:00Z','2026-10-17T12:00:00Z')]:
        with pytest.raises(ValidationError): CalendarActivity(id='a',start=start,end=end)
