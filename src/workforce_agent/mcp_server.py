"""Local stdio MCP adapter over the shared agent service.

Credentials are process environment, never tool arguments. MCP tools invoke
the service layer directly and do not depend on FastAPI or its HTTP API.
"""
import json
import os
import re
import secrets
from datetime import date
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from workforce_agent.agent import (
    AgentError,
    AnnotationReply,
    Constraints,
    Principal,
    Reply,
    Suggestion,
)
from workforce_agent.agent_runtime import service
from workforce_agent.config import get_settings
from workforce_agent.schemas import SafetyPolicy, WeatherForecast
from workforce_agent.schemas.calendar import DayCalendarResponse, DayContextSubmission, WarningMatch

mcp = FastMCP('Climate Workforce — validated planning')
SessionId = Annotated[str, Field(pattern=r'^[A-Za-z0-9_-]{43}$')]
ActivityId = Annotated[str, Field(min_length=1, max_length=100)]


class MCPServiceError(ValueError):
    """Sanitized actionable tool errors; never expose credentials."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(f'{code}: {message}')


def identity() -> Principal:
    token = os.environ.get('WORKFORCE_AGENT_TOKEN')
    if not token:
        raise MCPServiceError('authentication-required', 'WORKFORCE_AGENT_TOKEN is required; no anonymous MCP access')
    for configured, claims in get_settings().agent_credentials.items():
        if secrets.compare_digest(token, configured):
            return Principal.model_validate(claims)
    raise MCPServiceError('unauthenticated', 'Configured MCP credential was not recognized')


def invoke(action, *args, **kwargs):
    try:
        return action(*args, **kwargs)
    except AgentError as error:
        code = {401: 'unauthenticated', 403: 'forbidden', 404: 'not-found',
                409: 'conflict', 410: 'session-expired', 422: 'invalid-input'}.get(error.status, 'service-error')
        raise MCPServiceError(code, error.message) from error
    except ValueError as error:
        raise MCPServiceError('invalid-input', str(error)) from error


def checked_session_id(value):
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}', value or ''):
        raise MCPServiceError('invalid-input', 'Invalid session ID')
    return value


@mcp.tool()
def create_supervisor_session(day: date, site_id: str = 'VAD-PLANT-01') -> Reply:
    """Create an isolated, expiring session for the configured credential."""
    return invoke(service.create, identity(), day, site_id)


@mcp.tool()
def climate_agent(message: Annotated[str, Field(min_length=1, max_length=2000)],
                  day: date | None = None, site_id: str = 'VAD-PLANT-01',
                  session_id: SessionId | None = None) -> Reply:
    """Start or continue a conversation using server-authorized schedule context."""
    principal = identity()
    if session_id is None:
        if day is None:
            raise MCPServiceError('invalid-input', 'Provide day when starting a new session')
        session_id = invoke(service.create, principal, day, site_id).session_id
    return invoke(service.chat, checked_session_id(session_id), principal, message)


@mcp.tool()
def analyze_consumer_schedule(context: DayContextSubmission, policy: SafetyPolicy) -> DayCalendarResponse:
    """Analyze a submitted schedule against backend-owned weather; never writes the source calendar."""
    return invoke(service.analyze_consumer_schedule, identity(), context, policy)


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
    """Canonical agent reply, proposal and annotation schemas."""
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
        'service-error; missing or stale context must be treated as needs-review.'
    )


@mcp.tool()
def list_affected_activities(session_id: SessionId) -> Reply:
    """Read affected activities with traceable warning intervals and policy context."""
    return invoke(service.read, checked_session_id(session_id), identity())


@mcp.tool()
def get_climate_suggestions(session_id: SessionId) -> Reply:
    """Read existing structured suggestions; requires read/site/ownership permission."""
    return invoke(service.read, checked_session_id(session_id), identity())


@mcp.tool()
def create_rescheduling_proposal(session_id: SessionId, constraints: Constraints) -> Reply:
    """Prepare proposals only; times remain unchanged until the supervisor approval flow."""
    return invoke(service.request_proposals, checked_session_id(session_id), identity(), constraints)


@mcp.tool()
def supervisor_chat(session_id: SessionId, message: Annotated[str, Field(min_length=1, max_length=2000)]) -> Reply:
    """Continue a session; interpretation uses the configured reasoning provider when enabled."""
    return invoke(service.chat, checked_session_id(session_id), identity(), message)


@mcp.tool()
def configure_warning_notes(session_id: SessionId, enabled: bool) -> Reply:
    """Enable or disable separate informational notes; requires annotate permission."""
    return invoke(service.configure_monitoring, checked_session_id(session_id), identity(), enabled)


@mcp.tool()
def annotate_warning_notes(session_id: SessionId) -> Reply:
    """Run the configured informational note pass; never changes event times."""
    return invoke(service.warning_pass, checked_session_id(session_id), identity())


@mcp.tool()
def propose_reschedule(session_id: SessionId, constraints: Constraints,
                       activity_id: Annotated[str | None, Field(min_length=1, max_length=100)] = None) -> Reply:
    """Prepare validated proposals only; never applies times."""
    targets = [activity_id] if activity_id else None
    return invoke(service.request_proposals, checked_session_id(session_id), identity(), constraints, target_ids=targets)


@mcp.tool()
def review_proposal(session_id: SessionId, proposal_id: Annotated[str, Field(min_length=1, max_length=200)]) -> dict:
    """Refresh current source, climate, availability and duration checks for a proposal."""
    return invoke(service.review, checked_session_id(session_id), identity(), proposal_id)


@mcp.tool()
def decide_proposal(session_id: SessionId, proposal_id: Annotated[str, Field(min_length=1, max_length=200)],
                    decision: Literal['approve', 'reject', 'revise'],
                    reason: Annotated[str, Field(max_length=2000)] = '') -> Reply:
    """Record an explicit supervisor decision; approval revalidates before demo calendar changes."""
    return invoke(service.decide, checked_session_id(session_id), identity(), proposal_id, decision, reason)


@mcp.tool()
def annotate_affected_activity(session_id: SessionId, activity_id: ActivityId) -> AnnotationReply:
    """Annotate one affected outdoor event only when explicitly enabled and authorized."""
    return invoke(service.annotate_activity, checked_session_id(session_id), identity(), activity_id)


def run():
    mcp.run(transport='stdio')


if __name__ == '__main__':
    run()
