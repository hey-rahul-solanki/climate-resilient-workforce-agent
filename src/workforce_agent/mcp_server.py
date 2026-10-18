"""Local stdio MCP adapter. Credentials are process env, never tool arguments.

Tools proxy the authenticated API, so all clients share policy/session logic.
This server exposes no rescheduling write or approval tool. Note annotation is
a separately authorized informational write.
"""
import os
import re
import json
from datetime import date
from typing import Annotated
from pydantic import Field, ValidationError

import httpx
from mcp.server.fastmcp import FastMCP
from workforce_agent.agent import Constraints, Reply, Suggestion, AnnotationReply
from workforce_agent.schemas import SafetyPolicy, WeatherForecast
from workforce_agent.schemas.calendar import DayCalendarResponse, DayContextSubmission, WarningMatch

mcp = FastMCP('Climate Workforce — validated planning')
SessionId = Annotated[str, Field(pattern=r'^[A-Za-z0-9_-]{43}$')]
ActivityId = Annotated[str, Field(min_length=1,max_length=100)]


class MCPServiceError(ValueError):
    """Sanitized actionable errors; SDK emits a tool error, never credentials."""
    def __init__(self, code, message):
        self.code=code
        super().__init__(f'{code}: {message}')


def request(method: str, path: str, body=None, response_model=Reply):
    if '/sessions/' in path and not re.fullmatch(r'/sessions/[A-Za-z0-9_-]{43}(?:/(?:chat|proposals|monitoring|warning-pass|annotations))?', path):
        raise MCPServiceError('invalid-input','Invalid session ID')
    token = os.environ.get('WORKFORCE_AGENT_TOKEN')
    if not token:
        raise MCPServiceError('authentication-required','WORKFORCE_AGENT_TOKEN is required; no anonymous MCP access')
    base = os.environ.get('WORKFORCE_AGENT_API_URL', 'http://127.0.0.1:8000')
    try:
        parsed = httpx.URL(base)
    except (ValueError,httpx.InvalidURL):
        raise MCPServiceError('invalid-config','Invalid backend URL') from None
    if not parsed.host or parsed.username or parsed.password or parsed.query or parsed.fragment or (parsed.scheme != 'https' and not (parsed.scheme=='http' and parsed.host in ('localhost','127.0.0.1','::1'))):
        raise MCPServiceError('invalid-config','Use HTTPS for remote services or loopback HTTP; credentials must not appear in URLs')
    try:
        with httpx.Client(base_url=base, headers={'Authorization': f'Bearer {token}'}, timeout=20,follow_redirects=False) as client:
            response = client.request(method, f'/api/agent{path}', json=body)
            if not response.is_success:
                codes={401:('unauthenticated','Check the configured credential'),403:('forbidden','Missing site/action permission'),404:('not-found','Session/activity not found or not owned by this identity'),409:('conflict','Annotation disabled or proposal state changed; review configuration'),410:('session-expired','Create a new supervisor session'),422:('invalid-input','Check date, constraints and required fields')}
                code,message=codes.get(response.status_code,('backend-unavailable','Backend rejected the request; retry or inspect service health'))
                raise MCPServiceError(code,message)
            try:
                return response_model.model_validate(response.json())
            except (ValidationError,ValueError):
                raise MCPServiceError('invalid-response','Backend returned an invalid structured response; no success asserted') from None
    except httpx.TimeoutException:
        raise MCPServiceError('backend-timeout','Backend timed out; read current session state before retrying') from None
    except httpx.HTTPError:
        raise MCPServiceError('backend-unavailable','Cannot reach backend; check the configured URL and service health') from None



@mcp.tool()
def create_supervisor_session(day: date, site_id: str = 'VAD-PLANT-01') -> Reply:
    """Create an isolated, expiring session authorized for the configured credential."""
    return request('POST', '/sessions', {'day':day.isoformat(), 'site_id':site_id})


@mcp.tool()
def analyze_consumer_schedule(context: DayContextSubmission, policy: SafetyPolicy) -> DayCalendarResponse:
    """Analyze a consumer-owned schedule and site policy against backend weather.

    Requires read permission for context.site.id. Provide raw source activities and the
    applicable site safety policy, without derived status/warning fields. Weather is
    fetched by the backend. Unavailable, stale, or incomplete evidence yields needs-review.
    This tool never writes the source calendar.
    """
    return request('POST', '/analysis/consumer-schedule', {
        'context': context.model_dump(mode='json'),
        'policy': policy.model_dump(mode='json'),
    }, DayCalendarResponse)


@mcp.resource('climate://schemas/day-calendar-response')
def day_calendar_schema() -> str:
    """Canonical selected-day calendar response JSON Schema."""
    return json.dumps(DayCalendarResponse.model_json_schema(), sort_keys=True)


@mcp.resource('climate://schemas/climate-evidence')
def climate_evidence_schema() -> str:
    """Canonical warning, weather and safety policy JSON Schemas."""
    return json.dumps({
        'WarningMatch': WarningMatch.model_json_schema(),
        'WeatherForecast': WeatherForecast.model_json_schema(),
        'SafetyPolicy': SafetyPolicy.model_json_schema(),
    }, sort_keys=True)


@mcp.resource('climate://schemas/planning-responses')
def planning_response_schemas() -> str:
    """Canonical agent reply, proposal and annotation response JSON Schemas."""
    return json.dumps({
        'Reply': Reply.model_json_schema(),
        'Suggestion': Suggestion.model_json_schema(),
        'AnnotationReply': AnnotationReply.model_json_schema(),
    }, sort_keys=True)


@mcp.resource('climate://schemas/usage')
def climate_usage() -> str:
    """Interpretation, permissions, time and interval semantics for MCP results."""
    return (
        'Canonical models are DayCalendarResponse, CalendarActivity, WeatherForecast, '
        'SafetyPolicy, WarningMatch, and structured Reply/Suggestion responses. '
        'Timestamps are ISO-8601 with timezone offsets; intervals are half-open [start, end). '
        'Calendar dates and HH:MM constraints use the site IANA timezone. '
        'Statuses affected, needs-review, and unflagged are operational classifications, '
        'not safety clearance. Weather status/source/updated_at and forecast quality describe '
        'freshness and provenance. WarningMatch contains the exact overlap, severity, rationale, '
        'and optional policy reference. Every day-context or session tool requires an authenticated '
        'credential with read permission and access to the requested site. Errors use stable '
        'codes such as authentication-required, forbidden, not-found, invalid-input, and '
        'backend-unavailable; missing or stale context must be treated as needs-review.'
    )


@mcp.tool()
def list_affected_activities(session_id: SessionId) -> Reply:
    """Read affected activities with traceable warning intervals and policy context."""
    return request('GET', f'/sessions/{session_id}')


@mcp.tool()
def get_climate_suggestions(session_id: SessionId) -> Reply:
    """Read existing structured suggestions; requires read/site/ownership permission."""
    return request('GET', f'/sessions/{session_id}')


@mcp.tool()
def create_rescheduling_proposal(session_id: SessionId, constraints: Constraints) -> Reply:
    """Prepare proposals, never change event times. Requires propose permission."""
    return request('POST', f'/sessions/{session_id}/proposals', constraints.model_dump())


@mcp.tool()
def supervisor_chat(session_id: SessionId, message: Annotated[str, Field(min_length=1,max_length=2000)]) -> Reply:
    """Converse using the deterministic grammar; unsupported intent asks clarification."""
    return request('POST', f'/sessions/{session_id}/chat', {'message':message})



@mcp.tool()
def configure_warning_notes(session_id: SessionId, enabled: bool) -> Reply:
    """Explicitly enable/disable informational demo notes; requires annotate permission."""
    return request('POST', f'/sessions/{session_id}/monitoring', {'enabled':enabled})


@mcp.tool()
def annotate_warning_notes(session_id: SessionId) -> Reply:
    """Run the idempotent configured note pass; never change event times."""
    return request('POST', f'/sessions/{session_id}/warning-pass', {})



@mcp.tool()
def propose_reschedule(session_id: SessionId, constraints: Constraints) -> Reply:
    """Prepare validated proposals only; requires propose/site/ownership authorization. Never applies times."""
    return request('POST', f'/sessions/{session_id}/proposals', constraints.model_dump())


@mcp.tool()
def annotate_affected_activity(session_id: SessionId, activity_id: ActivityId) -> AnnotationReply:
    """Annotate one affected outdoor event only when explicitly enabled and authorized. Never changes times."""
    return AnnotationReply.model_validate(request('POST', f'/sessions/{session_id}/annotations', {'activity_id':activity_id}).model_dump(mode='json'))


def run():
    mcp.run(transport='stdio')


if __name__ == '__main__':
    run()
