"""Authenticated, scoped adapters over the shared agent service."""
from datetime import date, datetime, timedelta, timezone
from typing import Literal
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, ConfigDict

from workforce_agent.agent import AgentError, Constraints, Principal, Reply, AnnotationReply
from workforce_agent.agent_runtime import service
from workforce_agent.config import get_settings
from workforce_agent.schemas import SafetyPolicy
from workforce_agent.schemas.calendar import DayCalendarResponse, DayContextSubmission

router = APIRouter(prefix='/api/agent', tags=['Climate agent'])


demo_identities: dict[str, tuple[Principal, datetime]] = {}


def identity(request: Request) -> Principal:
    settings = get_settings()
    header = request.headers.get('authorization', '')
    if header:
        token = header.removeprefix('Bearer ')
        for configured, principal in settings.agent_credentials.items():
            if header.startswith('Bearer ') and secrets.compare_digest(token, configured):
                return Principal.model_validate(principal)
        raise HTTPException(401, 'Invalid credentials')
    cookie = request.cookies.get('workforce_demo_identity', '')
    record = demo_identities.get(cookie)
    if settings.agent_demo_enabled and record and record[1] > datetime.now(timezone.utc):
        return record[0]
    raise HTTPException(401, 'Authentication required; demo login must be explicitly enabled')


def invoke(action, *args, **kwargs):
    try:
        return action(*args, **kwargs)
    except AgentError as error:
        raise HTTPException(error.status, error.message) from error


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    day: date
    site_id: str = 'VAD-PLANT-01'


class ConsumerScheduleAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    context: DayContextSubmission
    policy: SafetyPolicy


@router.post('/analysis/consumer-schedule', response_model=DayCalendarResponse)
def analyze_consumer_schedule(body: ConsumerScheduleAnalysisRequest, principal: Principal = Depends(identity)):
    """Analyze caller-supplied schedule and policy using backend-owned weather."""
    return invoke(service.analyze_consumer_schedule, principal, body.context, body.policy)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message: str = Field(min_length=1, max_length=2000)


@router.post('/demo-login')
def demo_login(response: Response):
    if not get_settings().agent_demo_enabled:
        raise HTTPException(404, 'Demo identity disabled')
    now = datetime.now(timezone.utc)
    for token, (_, expiry) in list(demo_identities.items()):
        if expiry <= now:
            del demo_identities[token]
    if len(demo_identities) >= 1000:
        raise HTTPException(503, 'Demo identity capacity reached')
    token = secrets.token_urlsafe(32)
    demo_identities[token] = (Principal(subject=f'demo:{secrets.token_urlsafe(16)}', permissions={'read', 'propose', 'approve', 'annotate'}, sites={'VAD-PLANT-01'}), now + timedelta(minutes=30))
    response.set_cookie('workforce_demo_identity', token, httponly=True, samesite='strict',
                        secure=get_settings().agent_secure_cookies, max_age=1800, path='/api')
    response.headers['Cache-Control'] = 'no-store'
    return {'identity': 'Isolated demo supervisor', 'agent': 'Deterministic demo; no Vertex AI', 'expires_in_seconds':1800}


@router.post('/sessions', response_model=Reply)
def create_session(body: SessionRequest, principal: Principal = Depends(identity)):
    return invoke(service.create, principal, body.day, body.site_id)


@router.get('/sessions/{sid}', response_model=Reply)
def read_session(sid: str, principal: Principal = Depends(identity)):
    return invoke(service.read, sid, principal)


@router.post('/sessions/{sid}/chat', response_model=Reply)
def chat(sid: str, body: ChatRequest, principal: Principal = Depends(identity)):
    return invoke(service.chat, sid, principal, body.message)


class ProposalRequest(Constraints):
    activity_id: str | None = None


@router.post('/sessions/{sid}/proposals', response_model=Reply)
def propose(sid: str, body: ProposalRequest, principal: Principal = Depends(identity)):
    constraints = Constraints(earliest=body.earliest, latest=body.latest)
    target_ids = [body.activity_id] if body.activity_id else None
    return invoke(service.request_proposals, sid, principal, constraints, target_ids=target_ids)


@router.delete('/sessions/{sid}', status_code=204)
def close_session(sid: str, principal: Principal = Depends(identity)):
    invoke(service.close, sid, principal)


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    decision: Literal['approve', 'reject', 'revise']
    reason: str = Field(default='', max_length=2000)


@router.get('/sessions/{sid}/proposals/{pid}/review')
def review_proposal(sid: str, pid: str, principal: Principal = Depends(identity)):
    return invoke(service.review,sid,principal,pid)


@router.post('/sessions/{sid}/proposals/{pid}/decision', response_model=Reply)
def decide_proposal(sid: str, pid: str, body: DecisionRequest, principal: Principal = Depends(identity)):
    return invoke(service.decide,sid,principal,pid,body.decision,body.reason)


class MonitoringRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    enabled: bool


@router.post('/sessions/{sid}/monitoring', response_model=Reply)
def configure_monitoring(sid: str, body: MonitoringRequest, principal: Principal = Depends(identity)):
    return invoke(service.configure_monitoring,sid,principal,body.enabled)


@router.post('/sessions/{sid}/warning-pass', response_model=Reply)
def run_warning_pass(sid: str, principal: Principal = Depends(identity)):
    return invoke(service.warning_pass,sid,principal)


from contextlib import asynccontextmanager
import asyncio


@asynccontextmanager
async def agent_lifespan(app):
    async def monitor():
        while True:
            await asyncio.sleep(get_settings().background_check_seconds)
            await asyncio.to_thread(service.background_pass)
    task = asyncio.create_task(monitor())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


class AnnotationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    activity_id: str = Field(min_length=1,max_length=100)


@router.post('/sessions/{sid}/annotations', response_model=AnnotationReply)
def annotate_activity(sid: str, body: AnnotationRequest, principal: Principal = Depends(identity)):
    return invoke(service.annotate_activity,sid,principal,body.activity_id)
