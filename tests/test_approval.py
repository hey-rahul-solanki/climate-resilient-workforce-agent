from datetime import date

import pytest

from workforce_agent.agent import AgentService, AgentError, Principal
from workforce_agent.approval import ApprovalStore


def supervisor(subject='alice', permissions=None):
    return Principal(subject=subject,permissions=permissions or {'read','propose','approve'},sites={'VAD-PLANT-01'})


def setup_service(store=None):
    service = AgentService(approval_store=store)
    who = supervisor()
    reply = service.create(who,date(2026,10,17))
    return service,who,reply.session_id,reply.suggestions[0].id


def test_explicit_approval_atomic_update_audit_and_idempotency(tmp_path):
    path = tmp_path/'approvals.sqlite3'
    service,who,sid,pid = setup_service(ApprovalStore(path))
    before = service.approvals.events(sid)
    review = service.review(sid,who,pid)
    assert all(review['checks'].values()) and not review['conflicts']
    assert review['current']['location'] and review['current']['kind'] == 'outdoor'
    assert review['employees'] and review['warnings']
    assert service.approvals.events(sid) == before  # review/pending never writes
    result = service.decide(sid,who,pid,'approve')
    changed = next(a for a in result.calendar['activities'] if a['id']==review['proposal']['activity_id'])
    assert changed['start'] == review['proposal']['start'] and changed['version'] == 2
    assert result.audit[-1]['actor'] == 'alice' and result.audit[-1]['timestamp']
    assert result.audit[-1]['result'] == 'applied'
    assert result.audit[-1]['integration'] == 'isolated-demo-calendar'
    assert service.decide(sid,who,pid,'approve').audit == result.audit
    with pytest.raises(AgentError): service.decide(sid,who,pid,'reject')
    assert ApprovalStore(path).audit(sid)[-1]['result'] == 'applied'
    # No unrelated event fields, notes, or other activities changed.
    after = service.approvals.events(sid)
    for original in before:
        updated = next(a for a in after if a['id']==original['id'])
        if original['id'] == changed['id']:
            assert {k:v for k,v in original.items() if k not in ('start','end','version')} == {k:v for k,v in updated.items() if k not in ('start','end','version')}
        else:
            assert updated == original


@pytest.mark.parametrize('decision', ['reject','revise'])
def test_reject_revision_terminal_and_no_write(decision):
    service,who,sid,pid = setup_service()
    before = service.approvals.events(sid)
    reply = service.decide(sid,who,pid,decision,'Please keep the team together')
    assert reply.audit[-1]['decision'] == decision
    assert service.approvals.events(sid) == before
    with pytest.raises(AgentError) as error: service.decide(sid,who,pid,'approve')
    assert error.value.status == 409


@pytest.mark.parametrize('failure', ['version','weather','policy','missing-weather','deleted-event','availability','write'])
def test_revalidation_and_integration_failure_are_reported(failure, monkeypatch):
    service,who,sid,pid = setup_service()
    proposal = service.approvals.get(sid,pid)
    if failure == 'version':
        service.approvals.db.execute('UPDATE demo_events SET version=version+1 WHERE session=? AND id=?',(sid,proposal['activity_id']))
        service.approvals.db.commit()
    elif failure == 'missing-weather':
        monkeypatch.setattr(service,'_inputs',lambda _: (None,None))
    elif failure == 'deleted-event':
        service.approvals.db.execute('DELETE FROM demo_events WHERE session=? AND id=?',(sid,proposal['activity_id']))
        service.approvals.db.commit()
    elif failure in ('weather','policy'):
        from workforce_agent.calendar import demo_inputs
        forecast,policy = demo_inputs(date(2026,10,17))
        if failure == 'weather': forecast.quality.is_stale = True
        else: policy.version = 'changed'
        monkeypatch.setattr(service,'_inputs',lambda _: (forecast,policy))
    elif failure == 'availability':
        import json
        conflict = {**proposal['current'], 'id':'new-conflict', 'start':proposal['start'],'end':proposal['end']}
        service.approvals.db.execute('INSERT INTO demo_events VALUES (?,?,?,?)',(sid,conflict['id'],1,json.dumps(conflict)))
        service.approvals.db.commit()
    else:
        original = service.approvals.apply_event
        def failed_write(*args):
            original(*args)
            raise RuntimeError('Simulated failure after write')
        monkeypatch.setattr(service.approvals,'apply_event',failed_write)
    before = service.approvals.events(sid)
    reply = service.decide(sid,who,pid,'approve')
    assert reply.audit[-1]['result'] == ('integration-failed' if failure == 'write' else 'blocked')
    assert service.approvals.events(sid) == before
    assert service.decide(sid,who,pid,'approve').audit == reply.audit


def test_ownership_permissions_and_superseded_proposals():
    service,who,sid,pid = setup_service()
    with pytest.raises(AgentError) as error: service.decide(sid,supervisor('bob'),pid,'approve')
    assert error.value.status == 404
    with pytest.raises(AgentError) as error: service.decide(sid,supervisor(permissions={'read','propose'}),pid,'approve')
    assert error.value.status == 403
    from workforce_agent.agent import Constraints
    service.propose(sid,who,Constraints(latest='12:00'))
    with pytest.raises(AgentError) as error: service.decide(sid,who,pid,'approve')
    assert error.value.status == 409


def test_http_decision_and_client_cannot_supply_times(monkeypatch):
    from fastapi.testclient import TestClient
    from workforce_agent.api import app
    monkeypatch.setenv('WORKFORCE_AGENT_DEMO_ENABLED','true')
    monkeypatch.setenv('WORKFORCE_AGENT_SECURE_COOKIES','false')
    client=TestClient(app)
    client.post('/api/agent/demo-login',json={}).raise_for_status()
    session=client.post('/api/agent/sessions',json={'day':'2026-10-17'}).json()
    sid,pid=session['session_id'],session['suggestions'][0]['id']
    path=f'/api/agent/sessions/{sid}/proposals/{pid}'
    assert client.get(path+'/review').status_code == 200
    assert client.post(path+'/decision',json={'decision':'approve','start':'tampered'}).status_code == 422
    reply=client.post(path+'/decision',json={'decision':'approve'})
    assert reply.status_code == 200 and reply.json()['audit'][-1]['result']=='applied'
    applied=next(s for s in reply.json()['suggestions'] if s['id']==pid)
    assert applied['decision_state']=='approved' and applied['calendar_update_state']=='applied'


def test_decision_and_calendar_result_are_separate_durable_states(tmp_path):
    path=tmp_path/'state.sqlite3'
    service,who,sid,pid=setup_service(ApprovalStore(path))
    initial=service.approvals.get(sid,pid)
    assert initial['decision_state']=='pending' and initial['calendar_update_state']=='not-requested'
    service.decide(sid,who,pid,'approve')
    reopened=ApprovalStore(path)
    proposal=reopened.get(sid,pid)
    assert proposal['decision_state']=='approved' and proposal['calendar_update_state']=='applied'
    records=[a for a in reopened.audit(sid) if a['proposal_id']==pid]
    assert [a['result'] for a in records]==['approved','applied']
    assert all(a['actor']=='alice' and a['timestamp'] and a['decision']=='approve' for a in records)


@pytest.mark.parametrize('checks',[{}, {'source_version':True}, {'source_version':True,'weather_policy':True,'availability':True,'duration':True,'session_window':1}])
def test_storage_fails_closed_on_missing_or_non_boolean_checks(checks):
    service,who,sid,pid=setup_service()
    before=service.approvals.events(sid)
    result=service.approvals.decide(sid,service.approvals.get(sid,pid),'approve',who.subject,'2026-10-17T00:00:00Z',checks)
    assert result['result']=='blocked' and result['decision_state']=='approved'
    assert result['calendar_update_state']=='failed'
    assert service.approvals.events(sid)==before


def test_storage_reloads_proposal_and_cannot_reapprove_rejected_snapshot():
    service,who,sid,pid=setup_service()
    original=service.approvals.get(sid,pid)
    checks=service.review(sid,who,pid)['checks']
    service.decide(sid,who,pid,'reject')
    before=service.approvals.events(sid)
    with pytest.raises(ValueError,match='already decided'):
        service.approvals.decide(sid,original,'approve',who.subject,'2026-10-17T00:00:00Z',checks)
    assert service.approvals.events(sid)==before
    assert service.approvals.get(sid,pid)['calendar_update_state']=='not-requested'


def test_storage_ignores_caller_supplied_times_and_duplicate_decisions():
    service,who,sid,pid=setup_service()
    stored=service.approvals.get(sid,pid)
    checks=service.review(sid,who,pid)['checks']
    tampered={**stored,'start':'2099-01-01T00:00:00Z'}
    result=service.approvals.decide(sid,tampered,'approve',who.subject,'2026-10-17T00:00:00Z',checks)
    event=next(a for a in service.approvals.events(sid) if a['id']==stored['activity_id'])
    assert event['start']==stored['start'] and event['version']==2
    audit=service.approvals.audit(sid)
    assert service.approvals.decide(sid,stored,'approve',who.subject,'2026-10-17T01:00:00Z',checks)==result
    assert service.approvals.audit(sid)==audit


def test_concurrent_duplicate_service_approvals_apply_once():
    from concurrent.futures import ThreadPoolExecutor
    service,who,sid,pid=setup_service()
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies=list(pool.map(lambda _:service.decide(sid,who,pid,'approve'),range(2)))
    assert all(r.audit[-1]['result']=='applied' for r in replies)
    proposal=service.approvals.get(sid,pid)
    event=next(a for a in service.approvals.events(sid) if a['id']==proposal['activity_id'])
    assert event['version']==2
    assert len([a for a in service.approvals.audit(sid) if a['proposal_id']==pid and a['result']=='applied'])==1


def test_legacy_applied_proposals_preserve_truthful_states():
    from workforce_agent.agent import Suggestion
    service,who,sid,pid=setup_service()
    service.decide(sid,who,pid,'approve')
    old=service.approvals.get(sid,pid)
    old.pop('decision_state'); old.pop('calendar_update_state')
    parsed=Suggestion.model_validate(old)
    assert parsed.decision_state=='approved' and parsed.calendar_update_state=='applied'


def test_resource_revalidation_runs_inside_final_write_transaction(monkeypatch):
    import json
    service,who,sid,pid=setup_service()
    proposal=service.approvals.get(sid,pid)
    original=service.approvals.decide
    def conflict_arrives(*args,**kwargs):
        conflict={**proposal['current'],'id':'late-conflict','start':proposal['start'],'end':proposal['end']}
        with service.approvals.db:
            service.approvals.db.execute('INSERT INTO demo_events VALUES (?,?,?,?)',(sid,conflict['id'],1,json.dumps(conflict)))
        return original(*args,**kwargs)
    monkeypatch.setattr(service.approvals,'decide',conflict_arrives)
    result=service.decide(sid,who,pid,'approve')
    assert result.audit[-1]['result']=='blocked'
    assert result.audit[-1]['checks']['availability'] is False
    event=next(a for a in service.approvals.events(sid) if a['id']==proposal['activity_id'])
    assert event['start']==proposal['current']['start'] and event['version']==1
