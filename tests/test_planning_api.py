import json

import pytest
from fastapi.testclient import TestClient

from workforce_agent import agent_api
from workforce_agent.agent import AgentService
from workforce_agent.api import app
from workforce_agent.planning_api import PlanningResponse


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(agent_api,'service',AgentService())
    monkeypatch.setenv('WORKFORCE_AGENT_DEMO_ENABLED','true')
    monkeypatch.setenv('WORKFORCE_AGENT_CREDENTIALS',json.dumps({
        'service':dict(subject='scheduler-service',permissions=['read','propose'],sites=['VAD-PLANT-01']),
        'reader':dict(subject='reader-service',permissions=['read'],sites=['VAD-PLANT-01']),
        'other':dict(subject='other-service',permissions=['read','propose'],sites=['OTHER']),
    }))
    return TestClient(app)


def headers(token='service'): return {'Authorization':f'Bearer {token}'}


def create(client,token='service'):
    response=client.post('/api/v1/climate/sessions',json={'site_id':'VAD-PLANT-01','date':'2026-10-17'},headers=headers(token))
    assert response.status_code==201
    return PlanningResponse.model_validate(response.json())


def test_versioned_contract_and_shared_core_no_time_writes(client):
    opened=create(client)
    sid=opened.session_id
    before=agent_api.service.approvals.events(sid)
    path=f'/api/v1/climate/sessions/{sid}'
    response=client.post(path+'/suggestions',json={'latest':'12:00'},headers=headers())
    assert response.status_code==200 and response.headers['cache-control']=='no-store'
    result=PlanningResponse.model_validate(response.json())
    assert result.api_version=='1.0' and result.mode=='fixture'
    assert len(result.actions)==3 and result.affected_activities
    core=agent_api.service.read(sid,agent_api.Principal(subject='scheduler-service',permissions={'read','propose'},sites={'VAD-PLANT-01'}))
    ids={a.proposal_id for a in result.actions}
    current=[s for s in core.suggestions if s.id in ids]
    assert [a.proposal_id for a in result.actions]==[s.id for s in current]
    for action,suggestion in zip(result.actions,current):
        assert action.activity_id==suggestion.activity_id
        assert action.proposed_window.start.isoformat()==suggestion.start
        assert action.warning_ids and action.warning_references and action.policy_references
        assert action.requires_supervisor_approval and action.approval_state=='pending'
        assert action.validation_status=='demo-validated' and action.suggested_action=='reschedule'
    assert agent_api.service.approvals.events(sid)==before
    assert client.get(path+'/affected-activities',headers=headers()).status_code==200
    assert client.get(path+'/suggestions',headers=headers()).status_code==200
    assert agent_api.service.approvals.events(sid)==before
    schema=client.get('/openapi.json').json()
    assert schema['paths']['/api/v1/climate/sessions/{session_id}/suggestions']['post']['responses']['200']['content']['application/json']['schema']['$ref'].endswith('/PlanningResponse')


def test_authorization_and_malformed_requests(client):
    assert client.post('/api/v1/climate/sessions',json={'site_id':'VAD-PLANT-01','date':'2026-10-17'}).status_code==401
    assert client.post('/api/agent/demo-login',json={}).status_code==200
    assert client.post('/api/v1/climate/sessions',json={'site_id':'VAD-PLANT-01','date':'2026-10-17'}).status_code==401
    assert client.post('/api/v1/climate/sessions',json={'site_id':'VAD-PLANT-01','date':'2026-10-17'},headers=headers('other')).status_code==403
    opened=create(client)
    path=f'/api/v1/climate/sessions/{opened.session_id}'
    assert client.get(path+'/suggestions',headers=headers('other')).status_code==404
    assert client.post(path+'/suggestions',json={'latest':'12:00'},headers=headers('reader')).status_code==404
    read=create(client,'reader')
    assert client.get(f'/api/v1/climate/sessions/{read.session_id}/suggestions',headers=headers('reader')).status_code==200
    assert client.post(f'/api/v1/climate/sessions/{read.session_id}/suggestions',json={'latest':'12:00'},headers=headers('reader')).status_code==403
    assert client.post(path+'/suggestions',json={'latest':'25:00'},headers=headers()).status_code==422
    assert client.post(path+'/suggestions',json={'latest':'12:00','approve':True},headers=headers()).status_code==422


def test_infeasible_and_missing_forecast_are_explicit(client,monkeypatch):
    opened=create(client)
    path=f'/api/v1/climate/sessions/{opened.session_id}/suggestions'
    result=client.post(path,json={'earliest':'12:00','latest':'13:00'},headers=headers()).json()
    assert all(a['proposed_window'] is None and a['validation_status']=='no-feasible-slot' and a['infeasibility_reasons'] for a in result['actions'])
    monkeypatch.setattr(agent_api.service,'_inputs',lambda _: (None,None))
    unknown=client.post(path,json={'latest':'12:00'},headers=headers()).json()
    assert unknown['clarification_required'] and unknown['actions']==[]
