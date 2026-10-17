from datetime import datetime

import pytest

from workforce_agent.calendar import match_warning_intervals, analyze_calendar
from workforce_agent.schemas.calendar import WarningMatch


def at(value): return f'2026-10-17T{value}:00+05:30'


def activity(start='11:30',end='13:30',kind='outdoor',location='North yard'):
    return dict(id='event',site_id='site',kind=kind,location=location,start=at(start),end=at(end))


def warning(id='heat',start='12:00',end='16:00',severity='High'):
    return dict(id=id,site_id='site',start=at(start),end=at(end),severity=severity,title='Heat warning',policy='Illustrative policy v1')


@pytest.mark.parametrize('start,end,expected',[
    ('11:30','13:30',('12:00','13:30')),
    ('15:30','17:00',('15:30','16:00')),
    ('11:00','17:00',('12:00','16:00')),
    ('12:00','16:00',('12:00','16:00')),
    ('11:00','12:00',None),('16:00','17:00',None),
])
def test_partial_enclosing_and_exact_boundaries(start,end,expected):
    result=match_warning_intervals([activity(start,end)],[warning()])
    assert len(result['activities'])==1
    assert result['affected_activity_count']==(1 if expected else 0)
    matches=result['activities'][0]['warning_matches']
    if expected:
        assert matches[0]['overlap']==dict(start=at(expected[0]),end=at(expected[1]))
        evidence=WarningMatch.model_validate(matches[0])
        assert evidence.warning_id=='heat' and evidence.severity=='High'
        assert evidence.policy=='Illustrative policy v1' and 'Outdoor activity' in evidence.rationale
    else:
        assert matches==[]


def test_multiple_warnings_duplicate_inputs_and_all_references():
    a=activity('11:00','17:00')
    first=warning(); second=warning('wind','15:00','18:00','Critical')
    result=match_warning_intervals([a,a],[first,second,first])
    assert len(result['affected_activities'])==result['affected_activity_count']==1
    event=result['affected_activities'][0]
    assert event['warning_ids']==['heat','wind']
    assert len(event['warning_matches'])==2
    assert event['warning_matches'][1]['overlap']==dict(start=at('15:00'),end=at('17:00'))
    assert event['warning_matches'][1]['severity']=='Critical'


@pytest.mark.parametrize('kind,location,status,matched',[
    ('indoor','Workshop','unflagged',False),('outdoor','Yard','affected',True),
    ('unknown','Yard','needs-review',False),('unrecognized','Yard','needs-review',False),
    ('outdoor',None,'needs-review',True),('outdoor','unknown','needs-review',True),
])
def test_classification_and_unknown_location(kind,location,status,matched):
    result=match_warning_intervals([activity(kind=kind,location=location)],[warning()])
    event=result['activities'][0]
    assert event['status']==status and bool(event['warning_matches'])==matched
    assert bool(result['needs_review_activities'])==(status=='needs-review')


def test_stale_matches_preserve_evidence_without_clearance():
    result=match_warning_intervals([activity()],[warning()],weather_fresh=False)
    event=result['affected_activities'][0]
    assert event['status']=='needs-review'
    assert event['warning_matches'][0]['warning_id']=='heat'
    assert 'requires review' in event['warning_matches'][0]['rationale']
    assert result['needs_review_activities']==result['affected_activities']


def test_offsets_compare_instants_and_reject_invalid_warning_intervals():
    w={**warning(),'start':'2026-10-17T06:30:00Z','end':'2026-10-17T10:30:00Z'}
    match=match_warning_intervals([activity()],[w])['affected_activities'][0]['warning_matches'][0]
    assert datetime.fromisoformat(match['overlap']['start'])==datetime.fromisoformat(at('12:00'))
    assert datetime.fromisoformat(match['overlap']['end'])==datetime.fromisoformat(at('13:30'))
    with pytest.raises(ValueError): match_warning_intervals([activity()],[{**w,'end':w['start']}])
    with pytest.raises(ValueError): match_warning_intervals([activity()],[{**w,'start':'2026-10-17T12:00:00'}])


def test_conflicting_duplicate_ids_are_rejected_not_silently_overwritten():
    with pytest.raises(ValueError): match_warning_intervals([activity(),activity(end='14:00')],[warning()])
    with pytest.raises(ValueError): match_warning_intervals([activity()],[warning(),warning(severity='Critical')])


def test_normalized_forecast_service_exposes_same_evidence_and_deduplicates():
    from tests.test_calendar import inputs
    forecast,policy=inputs()
    a=activity('11:30','17:00')
    result=analyze_calendar([a,a],forecast,policy,now=forecast.issued_at)
    assert result['affected_activity_count']==1 and len(result['affected_activities'])==1
    matches=result['affected_activities'][0]['warning_matches']
    assert len(matches)==2
    assert all(m['severity']=='High' and m['policy']=='Test policy v2' for m in matches)
    forecast.quality.is_stale=True
    stale=analyze_calendar([a],forecast,policy,now=forecast.issued_at)
    assert stale['affected_activities'][0]['status']=='needs-review'
    assert len(stale['affected_activities'][0]['warning_matches'])==2


def test_typed_day_api_publishes_match_evidence():
    from datetime import date
    from workforce_agent.day_schedule import get_day_schedule
    day=get_day_schedule('VAD-PLANT-01',date(2026,10,17))
    flagged=[a for a in day.activities if a.warning_matches]
    assert len(flagged)==3
    assert flagged[0].warning_matches[0].overlap.start.isoformat()==at('12:00')
