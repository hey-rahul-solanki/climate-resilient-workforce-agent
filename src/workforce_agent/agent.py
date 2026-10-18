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
from workforce_agent.day_schedule import analyze_submitted_day_context
from workforce_agent.schemas import SafetyPolicy, WeatherForecast
from workforce_agent.schemas.calendar import DayCalendarResponse, DayContextSubmission

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
    suggested_action: Literal['reschedule','request-review'] = 'request-review'
    start: str | None
    end: str | None
    candidate_window: TimeWindow | None = None
    validation: Literal['demo-validated', 'risk-reduced', 'no-feasible-slot', 'needs-review']
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
    requested_constraints: Constraints = Field(default_factory=Constraints)


    @model_validator(mode='before')
    @classmethod
    def legacy_decision_states(cls, value):
        if isinstance(value, dict):
            value = dict(value)
            value.setdefault('suggested_action', 'reschedule' if value.get('start') and value.get('end') else 'request-review')
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
    def __init__(self, *, clock=None, ttl_seconds=1800, approval_store=None, reasoning: ReasoningService | None = None, weather_client=None):
        self.reasoning = reasoning
        self.weather_client = weather_client
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.ttl_seconds = ttl_seconds
        self.approvals = approval_store or ApprovalStore()
        self.sessions = {}
        self.lock = RLock()

    def authorize(self, principal, site, permission):
        if site not in principal.sites or permission not in principal.permissions:
            raise AgentError(403, 'Not authorized for this site/action')

    def analyze_consumer_schedule(self, principal: Principal, context: DayContextSubmission,
                                  policy: SafetyPolicy) -> DayCalendarResponse:
        """Analyze consumer-owned schedule and policy against backend-owned weather."""
        self.authorize(principal, context.site.id, 'read')
        try:
            if self.weather_client is None:
                # Keep isolated service instances deterministic for tests and demos.
                forecast = demo_inputs(context.date)[0]
            else:
                from workforce_agent.locations import load_site
                from workforce_agent.weather.exceptions import WeatherError
                try:
                    site = load_site(context.site.id)
                    forecast = self.weather_client.get_forecast(site, context.window)
                except (KeyError, WeatherError):
                    forecast = None
            return analyze_submitted_day_context(context, forecast, policy, now=self.clock())
        except ValueError as error:
            raise AgentError(422, str(error)) from error

    def create(self, principal: Principal, day: date, site='VAD-PLANT-01') -> Reply:
        self.authorize(principal, site, 'read')
        if site != 'VAD-PLANT-01':
            raise AgentError(404, 'No fixture for this site')
        with self.lock:
            now = self.clock()
            expired = [k for k,v in self.sessions.items() if v['expires'] <= now]
            for key in expired:
                self.sessions.pop(key, None)
                self._delete_reasoning_session(key)
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
        model = session.get('model')
        if model is None and self.reasoning:
            model = ModelMeasurement(provider=self.reasoning.provider.name,
                                     requested_model=self.reasoning.provider.model,
                                     status='not-called')
        return Reply(session_id=sid, expires_at=session['expires'].isoformat(), message=message,
                     clarification=clarification, constraints=session['constraints'].model_copy(),
                     suggestions=suggestions if suggestions is not None else self.approvals.proposals(sid), context=context,
                     calendar=calendar, audit=self.approvals.audit(sid), monitoring=session['monitoring'],
                     model=model,request_status=session.get('request_status','not-evaluated'),
                     mode='fixture-data/vertex-reasoning' if self.reasoning else 'deterministic-demo',
                     agent_id='climate-workforce/validated-reasoning-v1' if self.reasoning else AGENT_ID)

    @staticmethod
    def _supervisor_message(suggestions, activities, timezone):
        zone = ZoneInfo(timezone)
        by_id = {activity['id']: activity for activity in activities}

        def clock(value):
            timestamp = value if isinstance(value, datetime) else datetime.fromisoformat(value)
            return timestamp.astimezone(zone).strftime('%-I:%M %p')

        lines = []
        for proposal in suggestions:
            activity = by_id.get(proposal.activity_id, {})
            title = activity.get('title', proposal.activity_id)
            current = proposal.current or activity
            old_slot = (f"currently scheduled {clock(current['start'])}–{clock(current['end'])}"
                        if current.get('start') and current.get('end') else 'with no current time available')
            if proposal.start and proposal.end:
                new_slot = f"move it to {clock(proposal.start)}–{clock(proposal.end)}"
                reason = proposal.model_explanation or proposal.rationale
                state = ('This proposal reduces climate-warning overlap but residual exposure remains; acknowledge it and provide a reason when approving. The calendar has not changed.'
                         if proposal.validation == 'risk-reduced' else
                         'This proposal passed deterministic validation and is waiting for your approval; the calendar has not changed.'
                         if proposal.validation == 'demo-validated' else
                         'This proposal needs review before it can be approved; the calendar has not changed.')
                lines.append(f"{title} is {old_slot}. I recommend {new_slot} because {reason} {state}")
            elif proposal.candidate_window:
                candidate = proposal.candidate_window
                labels = {'weather_policy':'climate policy', 'availability':'employee/location availability',
                          'requested_window':'requested time window', 'duration':'activity duration',
                          'activity_scope':'activity eligibility'}
                failed = ', '.join(labels.get(name, name.replace('_',' '))
                                   for name in proposal.infeasibility_reasons) or 'policy review'
                lines.append(f"I could not recommend moving {title} to {clock(candidate.start)}–{clock(candidate.end)} because it failed the {failed} check. {proposal.model_explanation or proposal.rationale} The schedule remains unchanged.")
            else:
                reason = proposal.rationale or 'No feasible time was found in the requested window.'
                lines.append(f"I could not find a feasible new time for {title}, {old_slot}. {reason}")
        return ' '.join(lines) if lines else 'I could not prepare a rescheduling proposal for the requested activity and time window.'

    def read(self, sid, principal):
        with self.lock:
            s = self._session(sid, principal)
            return self._reply(sid, s, 'Affected activities and warning/policy references are included in context.')

    def propose(self, sid, principal, constraints: Constraints | None = None, *, target_ids=None):
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
                           validated_suggestions(cal['activities'], forecast, policy, lower, upper,
                                                 target_ids=set(target_ids) if target_ids is not None else None)]
            for suggestion in suggestions:
                suggestion.requested_constraints = c.model_copy()
            saved = self.approvals.save(sid, [item.model_dump(mode='json') for item in suggestions], cal['activities'], principal.subject, self.clock().isoformat())
            suggestions = [Suggestion.model_validate(item) for item in saved]
            s['request_status']='validated'
            message = self._supervisor_message(suggestions, cal['activities'], cal['site']['timezone'])
            return self._reply(sid, s, message, suggestions=suggestions)

    def request_proposals(self, sid, principal, constraints: Constraints, *, target_ids=None):
        """Execute an already-structured MCP action through the authoritative planner."""
        return self.propose(sid, principal, constraints, target_ids=target_ids)

    def chat(self, sid, principal, message):
        # Keep common, unambiguous requests on the deterministic path even when
        # Gemini is configured. Natural-language interpretation is a fallback
        # for requests the small deterministic grammar cannot safely handle.
        if self.reasoning and not self._handles_deterministically(message):
            return self._reasoned_chat(sid,principal,message)
        with self.lock:
            s = self._session(sid, principal)
            s['model'] = None
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

    @staticmethod
    def _handles_deterministically(message):
        text = message.strip().lower()
        return bool(
            re.fullmatch(r'(who is affected\??|who is affected today\??|list affected activities|why\??|show warnings)', text)
            or re.fullmatch(r'(reschedule|propose|suggestions|show suggestions)', text)
            or re.fullmatch(r'(?:reschedule |move |propose )?(before|after) ((?:[01]\d|2[0-3]):[0-5]\d)', text)
        )

    def close(self, sid, principal):
        with self.lock:
            self._session(sid, principal)
            del self.sessions[sid]
            self._delete_reasoning_session(sid)

    def _delete_reasoning_session(self, sid):
        provider = getattr(self.reasoning, 'provider', None)
        delete = getattr(provider, 'delete_session', None)
        if delete:
            try:
                delete(sid)
            except Exception:
                # Backend expiry is authoritative; failed ADK cleanup is not
                # allowed to change authorization or session behavior.
                pass


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
                from workforce_agent.suggestion_service import warning_overlap_minutes
                current_overlap=warning_overlap_minutes(current)
                candidate_analysis=analyze_calendar([candidate]+[a for a in cal['activities'] if a['id']!=current['id']],forecast,policy,
                    now=forecast.issued_at if forecast else self.clock())['activities'][0]
                candidate_overlap=warning_overlap_minutes(candidate_analysis)
                hard_blocks=[b for b in candidate_analysis.get('policy_blocks',[]) if b.get('code')!='climate-warning']
                climate_ok=(policy_validation.status=='valid' or
                    (candidate_analysis['status']=='affected' and candidate_overlap<current_overlap and not hard_blocks))
                checks['weather_policy'] = climate_ok and proposal['policy'] == f'{policy.policy_id} v{policy.version}'
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
            if decision == 'approve' and proposal.get('validation') == 'risk-reduced' and not reason.strip():
                raise AgentError(422, 'A supervisor reason is required when residual climate-warning overlap remains')
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
                self._delete_reasoning_session(expired)
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
            forecast,policy=self._inputs(s)
            context=dict(agent_session_id=sid,date=cal['date'],site=cal['site'],timezone=cal['site']['timezone'],window=cal['window'],
                weather=cal.get('weather'),
                forecast=forecast.model_dump(mode='json') if forecast else None,
                policy=policy.model_dump(mode='json') if policy else None,
                constraints=s['constraints'].model_dump(),
                activities=[{key:a.get(key) for key in (
                    'id','title','employee_id','kind','location','start','end','status','warning_ids',
                    'reason','policy_context','policy_blocks')} for a in cal['activities']],
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
                if outcome.status=='clarification' and outcome.plan:
                    detail = (', '.join(outcome.plan.unsupported_constraints)
                              if outcome.plan.unsupported_constraints else outcome.plan.explanation)
                    message = f'Please clarify before I prepare a proposal: {detail}'
                elif outcome.status=='declined':
                    message = 'I cannot help with requests to bypass policy or approval, or disclose sensitive information.'
                else:
                    message = 'I could not interpret this request reliably. Please restate the activity and requested site-local time window. No new proposal was created.'
                return self._reply(sid,s,message,clarification=True,suggestions=[])
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
                    allowed={a['id'] for a in cal['activities']
                             if a['kind']=='outdoor' and a['warning_ids'] and a['status']!='needs-review'}
                    if not set(plan.activity_ids).issubset(allowed):
                        s['request_status']='needs-review'
                        return self._reply(sid,s,'The requested activity scope is not eligible for deterministic rescheduling; review the affected activity context.',clarification=True,suggestions=[])
                    result=self.propose(sid,principal,constraints,target_ids=plan.activity_ids)
                    s['request_status']='needs-review' if result.request_status=='needs-review' else 'validated' if not result.clarification else 'clarification'
                    return self._reply(sid,s,'Gemini interpreted the request; deterministic planner generated the proposals. '+result.message,
                                       clarification=result.clarification,suggestions=result.suggestions)
                reply=self.propose(sid,principal,constraints)
                s['request_status']='needs-review' if reply.request_status=='needs-review' else 'validated' if not reply.clarification else 'clarification'
                return self._reply(sid,s,'Gemini interpreted the request; deterministic planner generated the proposals. '+reply.message,
                                   clarification=reply.clarification,suggestions=reply.suggestions)
            results=validate_model_candidates(plan,cal,forecast,policy,constraints,evaluation_time=forecast.issued_at if forecast else self.clock())
            s['constraints']=constraints
            for result in results:
                result['requested_constraints'] = constraints.model_dump()
            saved=self.approvals.save(sid,results,cal['activities'],principal.subject,self.clock().isoformat())
            s['request_status']='validated' if all(r['validation'] in ('demo-validated','risk-reduced') for r in results) else 'needs-review'
            saved_suggestions = [Suggestion.model_validate(r) for r in saved]
            message = 'I used the AI’s scheduling suggestions and checked them against the schedule and policy. ' + self._supervisor_message(
                saved_suggestions, cal['activities'], cal['site']['timezone'])
            return self._reply(sid,s,message,suggestions=saved_suggestions)


    def annotate_activity(self, sid, principal, activity_id):
        with self.lock:
            s=self._session(sid,principal,'annotate')
            if not s['monitoring']['enabled']:
                raise AgentError(409,'Warning-note annotation is disabled; explicit configuration is required')
            if not any(a['id']==activity_id for a in self.approvals.events(sid)):
                raise AgentError(404,'Activity not found in this session')
            self._annotate(sid,s,activity_id)
            return AnnotationReply.model_validate(self._reply(sid,s,'Requested note pass completed. Inspect updated/unchanged/skipped/failed status; no event times changed.').model_dump(mode='json'))
