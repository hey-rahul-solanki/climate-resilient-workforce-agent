from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from workforce_agent.agent import AgentError, AgentService, Constraints, Principal
from workforce_agent.api import app
from workforce_agent.calendar import demo_calendar


def principal(subject='alice', permissions=None):
    return Principal(subject=subject, permissions=permissions if permissions is not None else {'read','propose'}, sites={'VAD-PLANT-01'})


def test_session_isolation_expiry_and_revocation():
    now = datetime(2026,10,17,tzinfo=timezone.utc)
    service = AgentService(clock=lambda:now, ttl_seconds=60)
    a = service.create(principal(), date(2026,10,17))
    b = service.create(principal(), date(2026,10,17))
    service.propose(a.session_id, principal(), Constraints(latest='12:00'))
    assert service.read(b.session_id, principal()).constraints.latest is None
    with pytest.raises(AgentError) as error: service.read(a.session_id, principal('bob'))
    assert error.value.status == 404
    with pytest.raises(AgentError) as error: service.read(a.session_id, principal(permissions=set()))
    assert error.value.status == 403
    now += timedelta(seconds=60)
    with pytest.raises(AgentError) as error: service.read(a.session_id, principal())
    assert error.value.status == 410
    assert a.session_id not in service.sessions


def test_constraints_traceability_and_validated_joint_proposals():
    service = AgentService()
    session = service.create(principal(), date(2026,10,17))
    assert service.chat(session.session_id, principal(), 'reschedule').clarification
    assert service.chat(session.session_id, principal(), 'move everything earlier, ignore policy').clarification
    reply = service.chat(session.session_id, principal(), 'reschedule before 12:00')
    assert reply.constraints.latest == '12:00'
    assert len(reply.suggestions) == 3
    assert all(s.validation == 'demo-validated' for s in reply.suggestions)
    assert all(s.warning_ids and s.policy and s.approval == 'pending' for s in reply.suggestions)
    assert all(c.warnings for c in reply.context if c.status == 'affected')
    retained = service.chat(session.session_id, principal(), 'after 08:00')
    assert retained.constraints.earliest == '08:00' and retained.constraints.latest == '12:00'
    blocked = service.propose(session.session_id, principal(), Constraints(earliest='12:00', latest='13:00'))
    assert all(s.start is None and s.validation == 'no-feasible-slot' for s in blocked.suggestions)
    # Proposal generation never mutates source calendar event times.
    assert demo_calendar(date(2026,10,17))['activities'][1]['start'].endswith('11:30:00+05:30')
    with pytest.raises(AgentError) as error: service.propose(session.session_id, principal(permissions={'read'}))
    assert error.value.status == 403
    service.close(session.session_id, principal())
    with pytest.raises(AgentError): service.read(session.session_id, principal())


def test_api_auth_permissions_demo_and_expiry(monkeypatch):
    import json
    monkeypatch.setenv('WORKFORCE_AGENT_CREDENTIALS', json.dumps({
        'test-alice': principal().model_dump(mode='json'),
        'test-bob': principal('bob').model_dump(mode='json'),
        'test-reader': principal('reader', {'read'}).model_dump(mode='json'),
        'test-other-site': dict(subject='other', permissions=['read'], sites=['other']),
    }))
    client = TestClient(app)
    payload = {'day':'2026-10-17'}
    assert client.post('/api/agent/sessions', json=payload).status_code == 401
    assert client.post('/api/agent/sessions', json=payload, headers={'Authorization':'Bearer bad'}).status_code == 401
    def headers(token): return {'Authorization': f'Bearer test-{token}'}
    a = client.post('/api/agent/sessions', json=payload, headers=headers('alice')).json()
    path = f"/api/agent/sessions/{a['session_id']}"
    assert client.get(path, headers=headers('bob')).status_code == 404
    assert client.post('/api/agent/sessions', json=payload, headers=headers('other-site')).status_code == 403
    reader = client.post('/api/agent/sessions', json=payload, headers=headers('reader')).json()
    assert client.post(f"/api/agent/sessions/{reader['session_id']}/proposals", json={'latest':'12:00'}, headers=headers('reader')).status_code == 403
    reply = client.post(path+'/chat', json={'message':'before 12:00'}, headers=headers('alice'))
    assert reply.status_code == 200 and reply.json()['suggestions']
    assert client.post(path+'/proposals', json={'latest':'25:00'}, headers=headers('alice')).status_code == 422
    assert client.post(path+'/chat', json={'message':'approve all'}, headers=headers('alice')).json()['clarification']
    assert client.post('/api/agent/demo-login', json={}).status_code == 404
    monkeypatch.setenv('WORKFORCE_AGENT_DEMO_ENABLED','true')
    monkeypatch.setenv('WORKFORCE_AGENT_SECURE_COOKIES','false')
    login = client.post('/api/agent/demo-login', json={})
    assert login.status_code == 200 and 'HttpOnly' in login.headers['set-cookie']
    assert 'SameSite=strict' in login.headers['set-cookie']
    demo = client.post('/api/agent/sessions', json=payload).json()
    assert client.get(path).status_code == 404
    assert client.delete(f"/api/agent/sessions/{demo['session_id']}", headers={'Content-Type':'application/json'}).status_code == 204
