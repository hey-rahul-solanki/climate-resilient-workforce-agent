"""Session-scoped deterministic agent with explicit approval for demo calendar updates."""
from __future__ import annotations

import re
import secrets
from datetime import date, datetime, timedelta, timezone
from threading import RLock
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, ConfigDict, model_validator

from workforce_agent.calendar import demo_calendar, demo_inputs, validated_suggestions, analyze_calendar
from workforce_agent.approval import ApprovalStore
from workforce_agent.reasoning import ReasoningService, ModelMeasurement
from workforce_agent.schemas.calendar import WarningMatch, DayWarning
from workforce_agent.schemas.common import TimeWindow
from workforce_agent.suggestion_service import validate_model_candidates

AGENT_ID = 'climate-workforce/deterministic-v1'


class Principal(BaseModel):
    subject: str
    permissions: set[str]
    sites: set[str]


class Constraints(BaseModel):
    model_config = ConfigDict(extra='forbid')
    earliest: str | None = Field(default=None, pattern=r'^(?:[01]\d|2[0-3]):[0-5]\d$')
    latest: str | None = Field(default=None, pattern=r'^(?:[01]\d|2[0-3]):[0-5]\d$')


class Suggestion(BaseModel):
    id: str
    activity_id: str
    start: str | None
    end: str | None
    validation: Literal['demo-validated', 'no-feasible-slot', 'needs-review']
    rationale: str
    warning_ids: list[str]
    policy: str
    approval: str = 'pending'
    decision_state: Literal['pending','approved','rejected','revision-requested'] = 'pending'
    calendar_update_state: Literal['not-requested','applied','failed'] = 'not-requested'
    current: dict | None = None
    source_version: int | None = None
    outcome: dict | None = None
    infeasibility_reasons: list[str] = Field(default_factory=list)
    validation_checks: dict[str,bool] = Field(default_factory=dict)
    model_explanation: str | None = None
    policy_blocks: list[dict] = Field(default_factory=list)
    policy_context: dict | None = None
    warning_matches: list[WarningMatch] = Field(default_factory=list)


    @model_validator(mode='before')
    @classmethod
    def legacy_decision_states(cls, value):
        if isinstance(value, dict):
            value = dict(value)
            status = value.get('approval', 'pending')
            decision = (value.get('outcome') or {}).get('decision')
            value.setdefault('decision_state', {'approve':'approved','reject':'rejected','revise':'revision-requested'}.get(decision,
                {'applied':'approved','blocked':'approved','integration-failed':'approved','rejected':'rejected','revision-requested':'revision-requested'}.get(status,'pending')))
            value.setdefault('calendar_update_state', 'applied' if status=='applied' else 'failed' if status in ('blocked','integration-failed') else 'not-requested')
        return value


class AffectedActivity(BaseModel):
    policy_context: dict | None = None
    policy_blocks: list[dict] = Field(default_factory=list)
    activity_id: str
    title: str
    employee_id: str
    current_start: datetime
    current_end: datetime
    status: Literal['affected','needs-review','unflagged']
    reason: str
    warnings: list[DayWarning]
    warning_matches: list[WarningMatch] = Field(default_factory=list)

    @model_validator(mode='after')
    def valid_interval(self):
        TimeWindow(start=self.current_start,end=self.current_end)
        return self


class Reply(BaseModel):
    session_id: str
    agent_id: str = AGENT_ID
    mode: str = 'deterministic-demo'
    expires_at: str
    message: str
    clarification: bool = False
    constraints: Constraints
    suggestions: list[Suggestion] = []
    context: list[AffectedActivity] = []
    model: ModelMeasurement | None = None
    request_status: Literal['not-evaluated','needs-review','validated','clarification'] = 'not-evaluated'
    calendar: dict | None = None
    audit: list[dict] = []
    monitoring: dict = {}


class AnnotationEventResult(BaseModel):
    activity_id: str
    result: Literal['updated','unchanged','skipped','failed']
    message: str | None = None


class AnnotationPass(BaseModel):
    timestamp: datetime
    result: Literal['disabled','completed','partial-failure','failed']
    events: list[AnnotationEventResult]


class AnnotationMonitoring(BaseModel):
    enabled: bool
    last_run: AnnotationPass | None = None


class AnnotationReply(Reply):
    monitoring: AnnotationMonitoring


class AgentError(Exception):
    def __init__(self, status: int, message: str):
        self.status, self.message = status, message


class AgentService:
    def __init__(self, *, clock=None, ttl_seconds=1800, approval_store=None, reasoning: ReasoningService | None = None):
        self.reasoning = reasoning
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.ttl_seconds = ttl_seconds
        self.approvals = approval_store or ApprovalStore()
        self.sessions = {}
        self.lock = RLock()

    def authorize(self, principal, site, permission):
        if site not in principal.sites or permission not in principal.permissions:
            raise AgentError(403, 'Not authorized for this site/action')

    def create(self, principal: Principal, day: date, site='VAD-PLANT-01') -> Reply:
        self.authorize(principal, site, 'read')
        if site != 'VAD-PLANT-01':
            raise AgentError(404, 'No fixture for this site')
        with self.lock:
            now = self.clock()
            self.sessions = {k:v for k,v in self.sessions.items() if v['expires'] > now}
            if len(self.sessions) >= 1000:
                raise AgentError(503, 'Session capacity reached')
            sid = secrets.token_urlsafe(32)
            session = dict(owner=principal.subject, site=site, day=day,
                           expires=now + timedelta(seconds=self.ttl_seconds), constraints=Constraints(), monitoring={'enabled':False, 'last_run':None})
            self.sessions[sid] = session
            self.approvals.seed(sid, demo_calendar(day)['activities'])
            if 'propose' in principal.permissions:
                self.approvals.save(sid, demo_calendar(day)['suggestions'], self.approvals.events(sid), principal.subject, now.isoformat())
            return self._reply(sid, session, 'Fixture-data agent ready. Ask who is affected, or request a reschedule before 12:00.')

    def _session(self, sid, principal, permission='read'):
        session = self.sessions.get(sid)
        if not session or session['owner'] != principal.subject:
            raise AgentError(404, 'Session not found')
        if session['expires'] <= self.clock():
            del self.sessions[sid]
            raise AgentError(410, 'Session expired; start a new session')
        self.authorize(principal, session['site'], permission)
        return session

    def _reply(self, sid, session, message, *, clarification=False, suggestions=None):
        calendar = self._calendar(sid, session)
        context = [dict(activity_id=a['id'], title=a['title'], employee_id=a['employee_id'],
                        policy_context=a.get('policy_context'),policy_blocks=a.get('policy_blocks',[]),
                        current_start=a['start'], current_end=a['end'], status=a['status'], reason=a['reason'], warning_matches=a.get('warning_matches',[]),
                        warnings=[w for w in calendar['warnings'] if w['id'] in a['warning_ids']])
                   for a in calendar['activities'] if a['warning_ids'] or a['status'] == 'needs-review']
        return Reply(session_id=sid, expires_at=session['expires'].isoformat(), message=message,
                     clarification=clarification, constraints=session['constraints'].model_copy(),
                     suggestions=suggestions if suggestions is not None else self.approvals.proposals(sid), context=context,
                     calendar=calendar, audit=self.approvals.audit(sid), monitoring=session['monitoring'],
                     model=session.get('model'),request_status=session.get('request_status','not-evaluated'),
                     mode='fixture-data/vertex-reasoning' if self.reasoning else 'deterministic-demo',
                     agent_id='climate-workforce/validated-reasoning-v1' if self.reasoning else AGENT_ID)

    def read(self, sid, principal):
        with self.lock:
            s = self._session(sid, principal)
            return self._reply(sid, s, 'Affected activities and warning/policy references are included in context.')

    def propose(self, sid, principal, constraints: Constraints | None = None):
        with self.lock:
            s = self._session(sid, principal, 'propose')
            if constraints is not None:
                s['constraints'] = constraints
            c = s['constraints']
            if not c.earliest and not c.latest:
                return self._reply(sid, s, 'What time window should I use? Specify before HH:MM and/or after HH:MM in site time.', clarification=True)
            cal = self._calendar(sid, s)
            tz = ZoneInfo(cal['site']['timezone'])
            def at(value):
                return datetime.fromisoformat(f"{s['day']}T{value}:00").replace(tzinfo=tz)
            lower = max(at(c.earliest or '06:00'), datetime.fromisoformat(cal['window']['start']))
            upper = min(at(c.latest or '18:00'), datetime.fromisoformat(cal['window']['end']))
            if lower >= upper:
                return self._reply(sid, s, 'The requested time window is empty. Please provide an end after the start.', clarification=True)
            forecast, policy = self._inputs(s)
            if forecast is None or policy is None:
                s['request_status']='needs-review'
                return self._reply(sid,s,'Forecast or policy is unavailable; no new feasible proposal can be created.',clarification=True,suggestions=[])
            suggestions = [Suggestion.model_validate(item) for item in
                           validated_suggestions(cal['activities'], forecast, policy, lower, upper)]
            saved = self.approvals.save(sid, [item.model_dump(mode='json') for item in suggestions], cal['activities'], principal.subject, self.clock().isoformat())
            suggestions = [Suggestion.model_validate(item) for item in saved]
            return self._reply(sid, s, 'Prepared proposals only. No calendar times changed.', suggestions=suggestions)

    def chat(self, sid, principal, message):
        if self.reasoning:
            return self._reasoned_chat(sid,principal,message)
        with self.lock:
            s = self._session(sid, principal)
            text = message.strip().lower()
            # Deliberately narrow grammar: unrecognized constraints never silently disappear.
            if re.fullmatch(r'(who is affected\??|who is affected today\??|list affected activities|why\??|show warnings)', text):
                return self._reply(sid, s, 'See affected activities below with their exact warning windows and configured policy references.')
            if re.fullmatch(r'(reschedule|propose|suggestions|show suggestions)', text):
                return self.propose(sid, principal)
            match = re.fullmatch(r'(?:reschedule |move |propose )?(before|after) ((?:[01]\d|2[0-3]):[0-5]\d)', text)
            if match:
                c = s['constraints'].model_copy(update={'latest' if match[1] == 'before' else 'earliest':match[2]})
                return self.propose(sid, principal, c)
            return self._reply(sid, s, 'Please clarify. I support “who is affected”, “reschedule before 12:00”, “after 08:00”, and “reschedule”. Use the time-window fields for combined constraints. Other constraints need a connected reasoning agent.', clarification=True)

    def close(self, sid, principal):
        with self.lock:
            self._session(sid, principal)
            del self.sessions[sid]


    def _calendar(self, sid, session):
        cal = demo_calendar(session['day'])
        forecast, policy = self._inputs(session)
        # Demo evaluation time is explicit, independent of the real approval timestamp.
        analysis = analyze_calendar(self.approvals.events(sid), forecast, policy, now=forecast.issued_at if forecast else self.clock())
        cal.update(activities=analysis['activities'], warnings=analysis['warnings'], weather={**analysis['weather'], 'status':'fixture' if analysis['weather']['status'] == 'current' else 'needs-review'})
        cal['integrations']['calendar'] = 'Isolated demo calendar · approval-gated writes'
        return cal

    def _inputs(self, session):
        return demo_inputs(session['day'])

    def review(self, sid, principal, pid):
        with self.lock:
            s = self._session(sid, principal)
            proposal = self.approvals.get(sid,pid)
            if not proposal:
                raise AgentError(404, 'Proposal not found')
            cal = self._calendar(sid,s)
            current = next((a for a in cal['activities'] if a['id'] == proposal['activity_id']),None)
            forecast, policy = self._inputs(s)
            checks = dict(source_version=bool(current and current['version'] == proposal['source_version']),
                          weather_policy=False, availability=False, duration=False, session_window=False)
            conflicts = []
            policy_validation = None
            if current and proposal['start'] and proposal['end']:
                start,end = datetime.fromisoformat(proposal['start']),datetime.fromisoformat(proposal['end'])
                candidate = {**current,'start':proposal['start'],'end':proposal['end']}
                from workforce_agent.policy_windows import evaluate_proposed_window
                policy_validation=evaluate_proposed_window(candidate,forecast,policy,activities=cal['activities'],
                    now=forecast.issued_at if forecast else self.clock())
                checks['weather_policy'] = policy_validation.status == 'valid' and proposal['policy'] == f'{policy.policy_id} v{policy.version}'
                checks['duration'] = end-start == datetime.fromisoformat(proposal['current']['end'])-datetime.fromisoformat(proposal['current']['start'])
                conflicts = [dict(activity_id=a['id'],title=a['title'],employee_id=a['employee_id']) for a in cal['activities']
                    if a['id'] != current['id'] and (a['employee_id'] == current['employee_id'] or a['location'] == current['location'])
                    and start < datetime.fromisoformat(a['end']) and end > datetime.fromisoformat(a['start'])]
                checks['availability'] = not conflicts
                checks['session_window'] = datetime.fromisoformat(cal['window']['start']) <= start < end <= datetime.fromisoformat(cal['window']['end'])
            return dict(proposal=proposal, current=current, employees=[e for e in cal['employees'] if current and e['id']==current['employee_id']],
                        checks=checks, conflicts=conflicts, policy_validation=policy_validation.model_dump() if policy_validation else None, climate_rationale=proposal['rationale'],
                        warnings=[w for w in demo_calendar(s['day'])['warnings'] if w['id'] in proposal['warning_ids']],
                        integration='isolated-demo-calendar', annotation='Separate informational action; not enabled or invoked by approval')

    def decide(self, sid, principal, pid, decision, reason=''):
        if decision not in ('approve','reject','revise'):
            raise AgentError(422,'Unknown supervisor decision')
        with self.lock:
            s = self._session(sid,principal,'approve')
            review = self.review(sid,principal,pid)
            proposal = review['proposal']
            if proposal.get('outcome'):
                if proposal['outcome']['decision'] != decision:
                    raise AgentError(409,'Proposal already decided; request a new proposal')
                return self._reply(sid,s,proposal['outcome']['message'])
            if proposal['approval'] != 'pending':
                raise AgentError(409,'Proposal superseded; review a new proposal')
            outcome = self.approvals.decide(sid,proposal,decision,principal.subject,self.clock().isoformat(),review['checks'],reason,
                revalidate=lambda: self.review(sid,principal,pid))
            return self._reply(sid,s,outcome['message'])


    def configure_monitoring(self, sid, principal, enabled):
        with self.lock:
            s = self._session(sid,principal,'annotate')
            s['monitoring']['enabled'] = enabled
            return self._reply(sid,s,'Background note annotation enabled.' if enabled else 'Background note annotation disabled.')

    def warning_pass(self, sid, principal):
        with self.lock:
            s = self._session(sid,principal,'annotate')
            self._annotate(sid,s)
            return self._reply(sid,s,'Warning-note pass completed. Inspect per-event results; event times were not changed.')

    def _annotate(self, sid, session, activity_id=None):
        from workforce_agent.annotations import annotate_notes
        results = []
        if not session['monitoring']['enabled']:
            session['monitoring']['last_run'] = dict(timestamp=self.clock().isoformat(), result='disabled', events=[])
            return
        cal = self._calendar(sid,session)
        for event in cal['activities']:
            if activity_id is not None and event['id'] != activity_id:
                continue
            if event['kind'] != 'outdoor' or event['status'] != 'affected':
                if activity_id is not None:
                    results.append(dict(activity_id=event['id'],result='skipped',message='Only affected outdoor activities with current inputs can be annotated.'))
                continue
            try:
                warnings = [w for w in cal['warnings'] if w['id'] in event['warning_ids']]
                notes = annotate_notes(event.get('notes',''),warnings)
                outcome = self.approvals.annotate(sid,event,notes)
                results.append(dict(activity_id=event['id'],result=outcome))
            except Exception:
                results.append(dict(activity_id=event['id'],result='failed',message='Note write failed; no success claimed.'))
        session['monitoring']['last_run'] = dict(timestamp=self.clock().isoformat(), result='partial-failure' if any(e['result']=='failed' for e in results) else 'completed', events=results)

    def background_pass(self):
        with self.lock:
            now=self.clock()
            for expired in [sid for sid,s in self.sessions.items() if s['expires']<=now]:
                del self.sessions[expired]
            for sid,session in self.sessions.items():
                if session['expires'] > self.clock() and session['monitoring']['enabled']:
                    try:
                        self._annotate(sid,session)
                    except Exception:
                        session['monitoring']['last_run'] = dict(timestamp=self.clock().isoformat(),result='failed',events=[])


    def _reasoned_chat(self, sid, principal, message):
        # Snapshot under lock, call provider outside it, then reauthorize/revalidate.
        with self.lock:
            s=self._session(sid,principal)
            cal=self._calendar(sid,s)
            context=dict(date=cal['date'],timezone=cal['site']['timezone'],window=cal['window'],
                constraints=s['constraints'].model_dump(),
                activities=[{key:a.get(key) for key in ('id','employee_id','kind','location','start','end','status','warning_ids')} for a in cal['activities']],
                warnings=cal['warnings'])
        outcome=self.reasoning.interpret(message,context)
        with self.lock:
            s=self._session(sid,principal)  # Expiry and permissions apply after inference too.
            s['model']=outcome.measurement
            if s['constraints'].model_dump()!=context['constraints']:
                s['request_status']='needs-review'
                return self._reply(sid,s,'Session constraints changed during inference; retry with current context.',clarification=True,suggestions=[])
            if outcome.status!='ready':
                s['request_status']='clarification' if outcome.status=='clarification' else 'needs-review'
                return self._reply(sid,s,'Request needs review or clarification. No new feasible proposal was created. '+outcome.code,clarification=True,suggestions=[])
            plan=outcome.plan
            if plan.action=='list_affected':
                s['request_status']='not-evaluated'
                return self._reply(sid,s,'Affected activities and deterministic warning/policy evidence are included in context.')
            self.authorize(principal,s['site'],'propose')
            merged=s['constraints'].model_dump()
            merged.update({key:value for key,value in plan.constraints.model_dump().items() if value is not None})
            constraints=Constraints.model_validate(merged)
            if not constraints.earliest and not constraints.latest:
                s['request_status']='clarification'
                return self._reply(sid,s,'Specify an earliest start and/or latest finish in site time before proposing changes.',clarification=True,suggestions=[])
            cal=self._calendar(sid,s)
            forecast,policy=self._inputs(s)
            if not plan.candidates:
                if plan.activity_ids:
                    s['request_status']='clarification'
                    return self._reply(sid,s,'Activity-specific requests need explicit candidate times; clarify the scope/window.',clarification=True,suggestions=[])
                reply=self.propose(sid,principal,constraints)
                s['request_status']='needs-review' if reply.request_status=='needs-review' else 'validated' if not reply.clarification else 'clarification'
                return self._reply(sid,s,reply.message,clarification=reply.clarification,suggestions=reply.suggestions)
            results=validate_model_candidates(plan,cal,forecast,policy,constraints,evaluation_time=forecast.issued_at if forecast else self.clock())
            s['constraints']=constraints
            saved=self.approvals.save(sid,results,cal['activities'],principal.subject,self.clock().isoformat())
            s['request_status']='validated' if all(r['validation']=='demo-validated' for r in results) else 'needs-review'
            return self._reply(sid,s,'Model candidates were checked by deterministic code. Review validation failures; no calendar times changed.',suggestions=[Suggestion.model_validate(r) for r in saved])


    def annotate_activity(self, sid, principal, activity_id):
        with self.lock:
            s=self._session(sid,principal,'annotate')
            if not s['monitoring']['enabled']:
                raise AgentError(409,'Warning-note annotation is disabled; explicit configuration is required')
            if not any(a['id']==activity_id for a in self.approvals.events(sid)):
                raise AgentError(404,'Activity not found in this session')
            self._annotate(sid,s,activity_id)
            return AnnotationReply.model_validate(self._reply(sid,s,'Requested note pass completed. Inspect updated/unchanged/skipped/failed status; no event times changed.').model_dump(mode='json'))
