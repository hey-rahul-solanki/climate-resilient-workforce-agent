"""Complete deterministic experience without provider credentials."""
from datetime import date
from threading import Event

import pytest
from fastapi.testclient import TestClient

from workforce_agent.agent import AgentService, AgentError, Constraints, Principal
from workforce_agent.annotations import annotate_notes, START


def supervisor(permissions=None):
    return Principal(subject='demo-supervisor',permissions=permissions or {'read','propose','approve','annotate'},sites={'VAD-PLANT-01'})


def test_complete_demo_and_idempotent_notes():
    service=AgentService()
    who=supervisor()
    opened=service.create(who,date(2026,10,17)); sid=opened.session_id
    activities=opened.calendar['activities']
    assert len(opened.calendar['employees'])==4
    assert sum(a['status']=='affected' for a in activities)==3
    assert all(not a['warning_ids'] for a in activities if a['kind']=='indoor')
    assert service.chat(sid,who,'who is affected').context
    proposals=service.chat(sid,who,'reschedule before 12:00').suggestions
    pid=proposals[0].id
    review=service.review(sid,who,pid)
    assert all(review['checks'].values())
    approved=service.decide(sid,who,pid,'approve')
    assert approved.audit[-1]['result']=='applied'
    moved=next(a for a in approved.calendar['activities'] if a['id']==proposals[0].activity_id)
    assert moved['start']==proposals[0].start
    before={a['id']:a for a in service.approvals.events(sid)}
    assert service.warning_pass(sid,who).monitoring['last_run']['result']=='disabled'
    assert service.approvals.events(sid)==list(before.values())
    service.configure_monitoring(sid,who,True)
    first=service.warning_pass(sid,who)
    assert len(first.monitoring['last_run']['events'])==2
    second=service.warning_pass(sid,who)
    assert all(e['result']=='unchanged' for e in second.monitoring['last_run']['events'])
    after=service.approvals.events(sid)
    for a in after:
        old=before[a['id']]
        assert (a['start'],a['end'])==(old['start'],old['end'])
        if a['id'] in {e['activity_id'] for e in first.monitoring['last_run']['events']}:
            assert a['notes'].startswith(old['notes'])
            assert a['notes'].count(START)==1
        else:
            assert a==old  # Indoor, unknown, moved-outside-warning events unchanged.
    infeasible=service.propose(sid,who,Constraints(earliest='12:00',latest='13:00'))
    assert infeasible.suggestions and all(s.start is None for s in infeasible.suggestions)
    assert all('duration' in s.rationale or 'conflicts' in s.rationale for s in infeasible.suggestions)
    pump=next(s for s in infeasible.suggestions if s.activity_id=='event-5')
    assert '90 minutes' in pump.rationale and '60-minute' in pump.rationale
    assert service.decide(sid,who,pump.id,'approve').audit[-1]['result']=='blocked'
    assert service.approvals.events(sid)==after
    service.configure_monitoring(sid,who,False)
    service.background_pass()
    assert service.approvals.events(sid)==after


def test_note_updates_preserve_unowned_text_and_report_failure(monkeypatch):
    service=AgentService(); who=supervisor(); sid=service.create(who,date(2026,10,17)).session_id
    service.configure_monitoring(sid,who,True)
    warnings=service.read(sid,who).calendar['warnings']
    first=annotate_notes('Original\n',warnings)
    assert annotate_notes(first,warnings)==first
    changed=[{**warnings[0],'measure':'Updated measure'}]
    updated=annotate_notes(first+'\nUser suffix',changed)
    assert updated.startswith('Original\n') and updated.endswith('\nUser suffix')
    assert 'Updated measure' in updated
    with pytest.raises(ValueError): annotate_notes('Original '+START,warnings)
    before=service.approvals.events(sid)
    monkeypatch.setattr(service.approvals,'annotate',lambda *args: (_ for _ in ()).throw(RuntimeError('Failed')))
    reply=service.warning_pass(sid,who)
    assert reply.monitoring['last_run']['result']=='partial-failure'
    assert all(e['result']=='failed' for e in reply.monitoring['last_run']['events'])
    assert service.approvals.events(sid)==before
    with pytest.raises(AgentError): service.configure_monitoring(sid,supervisor({'read'}),True)


def test_background_task_runs_without_page_requests(monkeypatch):
    from workforce_agent import agent_api
    from workforce_agent.api import app
    service=AgentService(); who=supervisor(); sid=service.create(who,date(2026,10,17)).session_id
    service.configure_monitoring(sid,who,True)
    signal=Event(); original=service.background_pass
    def observed():
        original(); signal.set()
    monkeypatch.setattr(service,'background_pass',observed)
    monkeypatch.setattr(agent_api,'service',service)
    monkeypatch.setenv('WORKFORCE_BACKGROUND_CHECK_SECONDS','1')
    with TestClient(app):
        assert signal.wait(5), 'Scheduled background worker did not execute'
        assert service.sessions[sid]['monitoring']['last_run']['result']=='completed'
        assert any(START in a['notes'] for a in service.approvals.events(sid))
