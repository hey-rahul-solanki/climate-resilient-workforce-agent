from datetime import date
from copy import deepcopy
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from workforce_agent.api import app
from workforce_agent.day_schedule import get_day_schedule
from workforce_agent.schemas.calendar import DayCalendarResponse


def test_typed_day_contract_and_stable_activity_ids(monkeypatch):
    import workforce_agent.calendar as calendar
    monkeypatch.setattr(calendar,'validated_suggestions',lambda *a,**kw: (_ for _ in ()).throw(AssertionError('Read endpoint must not plan')))
    first=get_day_schedule('VAD-PLANT-01',date(2026,10,17))
    second=get_day_schedule('VAD-PLANT-01',date(2026,10,17))
    assert isinstance(first,DayCalendarResponse) and first==second
    assert first.mode=='fixture' and first.site.timezone=='Asia/Kolkata'
    assert all(e.role and e.team for e in first.employees)
    assert {a.kind for a in first.activities}=={'indoor','outdoor','unknown'}
    assert all(a.id and a.source_event_id and a.version==1 for a in first.activities)
    tomorrow=get_day_schedule('VAD-PLANT-01',date(2026,10,18))
    assert {a.source_event_id for a in first.activities}.isdisjoint(a.source_event_id for a in tomorrow.activities)
    assert not first.suggestions


@pytest.mark.parametrize('kind', ['indoor','outdoor','unknown'])
def test_activity_classification_roundtrip(kind):
    payload=get_day_schedule('VAD-PLANT-01',date(2026,10,17)).model_dump(mode='json')
    parsed=DayCalendarResponse.model_validate(payload)
    activity=next(a for a in parsed.activities if a.kind==kind)
    if kind=='indoor': assert not activity.warning_ids
    elif kind=='unknown': assert activity.status=='needs-review' and activity.location is None
    else: assert activity.location and activity.site_id==parsed.site.id


@pytest.mark.parametrize('mutation', ['naive','zero','reversed','timezone','outside-day','employee','duplicate'])
def test_invalid_intervals_timezone_and_references_rejected(mutation):
    payload=get_day_schedule('VAD-PLANT-01',date(2026,10,17)).model_dump(mode='json')
    activity=payload['activities'][0]
    if mutation=='naive': activity['start']='2026-10-17T08:00:00'
    elif mutation=='zero': activity['end']=activity['start']
    elif mutation=='reversed': activity['end']='2026-10-17T07:00:00+05:30'
    elif mutation=='timezone': payload['site']['timezone']='unknown/invalid'
    elif mutation=='outside-day': activity.update(start='2026-10-16T08:00:00+05:30',end='2026-10-16T09:00:00+05:30')
    elif mutation=='employee': activity['employee_id']='not-present'
    elif mutation=='duplicate': payload['activities'].append(deepcopy(activity))
    with pytest.raises(ValidationError): DayCalendarResponse.model_validate(payload)


def test_utc_instants_and_cross_midnight_activity_are_included():
    payload=get_day_schedule('VAD-PLANT-01',date(2026,10,17)).model_dump(mode='json')
    payload['activities'][0].update(start='2026-10-16T18:00:00Z',end='2026-10-16T20:00:00Z')
    response=DayCalendarResponse.model_validate(payload)
    # 23:30 on previous local day through 01:30 on selected day intersects it.
    assert response.activities[0].start.utcoffset().total_seconds()==0
    assert response.activities[0].end.date()==date(2026,10,16)


@pytest.mark.parametrize('day,hours',[('2026-03-08',23),('2026-11-01',25)])
def test_site_local_day_can_span_dst_transition(day,hours):
    from datetime import datetime,timedelta,timezone
    from zoneinfo import ZoneInfo
    payload=get_day_schedule('VAD-PLANT-01',date.fromisoformat(day)).model_dump(mode='json')
    zone=ZoneInfo('America/New_York')
    start=datetime.combine(date.fromisoformat(day),datetime.min.time(),tzinfo=zone)
    end=datetime.combine(date.fromisoformat(day)+timedelta(days=1),datetime.min.time(),tzinfo=zone)
    payload.update(site={**payload['site'],'timezone':'America/New_York'},window={'start':start.isoformat(),'end':end.isoformat()},activities=[],warnings=[])
    response=DayCalendarResponse.model_validate(payload)
    assert (response.window.end.astimezone(timezone.utc)-response.window.start.astimezone(timezone.utc)).total_seconds()==hours*3600


def test_day_http_auth_query_errors_and_openapi(monkeypatch):
    credentials={
        'read-token':dict(subject='reader',permissions=['read'],sites=['VAD-PLANT-01','NO-SOURCE']),
        'wrong-site':dict(subject='other',permissions=['read'],sites=['other']),
        'no-read':dict(subject='restricted',permissions=['propose'],sites=['VAD-PLANT-01']),
    }
    monkeypatch.setenv('WORKFORCE_AGENT_CREDENTIALS',json.dumps(credentials))
    client=TestClient(app)
    path='/api/calendar/day?site_id=VAD-PLANT-01&date=2026-10-17'
    assert client.get(path).status_code==401
    for token in ['wrong-site','no-read']:
        assert client.get(path,headers={'Authorization':f'Bearer {token}'}).status_code==403
    headers={'Authorization':'Bearer read-token'}
    result=client.get(path,headers=headers)
    assert result.status_code==200 and result.headers['cache-control']=='no-store'
    assert result.json()['date']=='2026-10-17' and result.json()['mode']=='fixture'
    assert client.get(path.replace('2026-10-17','invalid'),headers=headers).status_code==422
    assert client.get('/api/calendar/day?site_id=NO-SOURCE&date=2026-10-17',headers=headers).status_code==404
    assert client.get('/api/calendar/day?site_id=VAD-PLANT-01',headers=headers).status_code==422
    schema=client.get('/openapi.json').json()
    assert schema['paths']['/api/calendar/day']['get']['responses']['200']['content']['application/json']['schema']['$ref'].endswith('/DayCalendarResponse')
