"""Versioned HTTP adapter over the shared agent service."""
from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Response, Request, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from calendar_backend import agent_api
from workforce_agent.agent import AffectedActivity, Constraints, Principal, Reply
from workforce_agent.schemas.common import TimeWindow
from workforce_agent.schemas.calendar import WarningMatch

router=APIRouter(prefix='/api/v1/climate',tags=['Climate planning v1'])


class ServiceSessionRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    site_id: str = Field(min_length=1)
    date: date


class SuggestedAction(BaseModel):
    proposal_id: str
    activity_id: str
    current_activity: dict | None = None
    suggested_action: Literal['reschedule','request-review']
    current_window: TimeWindow | None
    proposed_window: TimeWindow | None
    candidate_window: TimeWindow | None = None
    requested_constraints: Constraints = Field(default_factory=Constraints)
    rationale: str
    warning_ids: list[str]
    warning_references: list[WarningMatch]
    policy_references: list[str]
    validation_status: Literal['demo-validated','risk-reduced','no-feasible-slot','needs-review']
    validation_checks: dict[str,bool]
    infeasibility_reasons: list[str]
    requires_supervisor_approval: bool = True
    approval_state: str


class PlanningResponse(BaseModel):
    api_version: Literal['1.0'] = '1.0'
    mode: Literal['fixture'] = 'fixture'
    session_id: str
    expires_at: datetime
    site_id: str
    timezone: str
    date: date
    affected_activities: list[AffectedActivity]
    actions: list[SuggestedAction]
    message: str
    clarification_required: bool


def service_identity(request: Request) -> Principal:
    """Custom services must supply their own credential, never a browser demo cookie."""
    if not request.headers.get('authorization','').startswith('Bearer '):
        raise HTTPException(401,'Authenticated service bearer identity required')
    return agent_api.identity(request)


def project(reply: Reply) -> PlanningResponse:
    calendar=reply.calendar
    actions=[]
    for suggestion in reply.suggestions:
        current=suggestion.current
        actions.append(SuggestedAction(proposal_id=suggestion.id,activity_id=suggestion.activity_id,
            suggested_action='reschedule' if suggestion.start and suggestion.end else 'request-review',
            current_window=TimeWindow(start=current['start'],end=current['end']) if current else None,
            proposed_window=TimeWindow(start=suggestion.start,end=suggestion.end) if suggestion.start and suggestion.end else None,
        candidate_window=suggestion.candidate_window,
        current_activity=current,
        requested_constraints=suggestion.requested_constraints,
            rationale=suggestion.rationale,warning_ids=suggestion.warning_ids,
            warning_references=suggestion.warning_matches,policy_references=[suggestion.policy],
            validation_status=suggestion.validation,validation_checks=suggestion.validation_checks,
            infeasibility_reasons=suggestion.infeasibility_reasons,approval_state=suggestion.approval))
    return PlanningResponse(session_id=reply.session_id,expires_at=reply.expires_at,
        site_id=calendar['site']['id'],timezone=calendar['site']['timezone'],date=calendar['date'],
        affected_activities=reply.context,actions=actions,message=reply.message,clarification_required=reply.clarification)


@router.post('/sessions',response_model=PlanningResponse,status_code=201)
def create_session(body: ServiceSessionRequest,response: Response,principal: Principal=Depends(service_identity)):
    response.headers['Cache-Control']='no-store'
    return project(agent_api.invoke(agent_api.service.create,principal,body.date,body.site_id))


@router.get('/sessions/{session_id}/affected-activities',response_model=PlanningResponse)
def affected_activities(session_id: str,response: Response,principal: Principal=Depends(service_identity)):
    response.headers['Cache-Control']='no-store'
    return project(agent_api.invoke(agent_api.service.read,session_id,principal))


@router.get('/sessions/{session_id}/suggestions',response_model=PlanningResponse)
def existing_suggestions(session_id: str,response: Response,principal: Principal=Depends(service_identity)):
    response.headers['Cache-Control']='no-store'
    return project(agent_api.invoke(agent_api.service.read,session_id,principal))


@router.post('/sessions/{session_id}/suggestions',response_model=PlanningResponse)
def create_suggestions(session_id: str,body: Constraints,response: Response,principal: Principal=Depends(service_identity)):
    response.headers['Cache-Control']='no-store'
    # No adapter-specific policy, slot search, inference, or event-time writer.
    return project(agent_api.invoke(agent_api.service.propose,session_id,principal,body))


@router.delete('/sessions/{session_id}',status_code=204)
def close_session(session_id: str,principal: Principal=Depends(service_identity)):
    agent_api.invoke(agent_api.service.close,session_id,principal)
