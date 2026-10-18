"""Calendar-facing HTTP gateway; agent operations are executed through MCP."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import sys
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Support both `calendar_backend.main:app` from the project root and
# `main:app` when the working directory is this package's folder.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / 'src'
for import_root in (PROJECT_ROOT, SOURCE_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, ConfigDict, Field

from workforce_agent.agent_runtime import service
from workforce_agent.config import get_settings
from calendar_backend.auth import browser_identity, demo_identities
from calendar_backend.http_api import router as http_api_router

logger = logging.getLogger(__name__)


class ToolRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=100)
    arguments: dict[str, Any] = Field(default_factory=dict)


class MCPGateway:
    """Own one persistent MCP client connection for process-local sessions."""

    def __init__(self):
        self.stack: AsyncExitStack | None = None
        self.session: ClientSession | None = None
        self.tools: dict[str, dict[str, Any]] = {}
        self.lock = asyncio.Lock()
        self.startup_error: str | None = None

    async def start(self):
        project_root = PROJECT_ROOT
        source_root = SOURCE_ROOT
        child_env = {
            key: value for key, value in os.environ.items()
            if key.startswith('WORKFORCE_') or key in {
                'PATH', 'HOME', 'PYTHONPATH', 'VIRTUAL_ENV',
                'GOOGLE_APPLICATION_CREDENTIALS', 'GOOGLE_CLOUD_PROJECT',
                'GOOGLE_CLOUD_LOCATION', 'GOOGLE_GENAI_USE_VERTEXAI',
            }
        }
        # The MCP subprocess must use this checkout's tools and schemas. A
        # regular (non-editable) install can otherwise leave it importing an
        # older wheel that does not expose tools expected by the frontend.
        existing_pythonpath = child_env.get('PYTHONPATH', '')
        child_env['PYTHONPATH'] = str(source_root) + (
            os.pathsep + existing_pythonpath if existing_pythonpath else ''
        )
        token = child_env.get('WORKFORCE_AGENT_TOKEN')
        settings = get_settings()
        if not token and settings.agent_demo_enabled:
            token = secrets.token_urlsafe(32)
            child_env['WORKFORCE_AGENT_TOKEN'] = token
            child_env['WORKFORCE_AGENT_CREDENTIALS'] = json.dumps({token: {
                'subject': 'calendar-backend-demo',
                'permissions': ['read', 'propose', 'approve', 'annotate'],
                'sites': ['VAD-PLANT-01'],
            }})
        elif not token or token not in settings.agent_credentials:
            raise RuntimeError('Configure WORKFORCE_AGENT_TOKEN and its matching WORKFORCE_AGENT_CREDENTIALS principal')
        server = StdioServerParameters(
            command=sys.executable,
            args=['-m', 'workforce_agent.mcp_server'],
            env=child_env,
            cwd=str(project_root),
        )
        self.stack = AsyncExitStack()
        try:
            read, write = await self.stack.enter_async_context(stdio_client(server))
            self.session = await self.stack.enter_async_context(ClientSession(read, write))
            await self.session.initialize()
            discovered = await self.session.list_tools()
            self.tools = {tool.name: {
                'name': tool.name,
                'description': tool.description,
                'inputSchema': tool.inputSchema,
            } for tool in discovered.tools}
        except Exception:
            await self.stack.aclose()
            self.stack = None
            self.session = None
            raise

    async def close(self):
        if self.stack:
            await self.stack.aclose()
        self.stack = None
        self.session = None

    async def list_tools(self):
        if not self.session:
            raise HTTPException(503, 'MCP connection is not ready')
        return list(self.tools.values())

    async def call(self, name: str, arguments: dict[str, Any]):
        if not self.session:
            raise HTTPException(503, 'MCP connection is not ready')
        if name not in self.tools:
            raise HTTPException(404, 'Requested MCP tool was not discovered')
        async with self.lock:
            try:
                result = await asyncio.wait_for(
                    self.session.call_tool(name, arguments), timeout=75)
            except asyncio.TimeoutError as error:
                raise HTTPException(504, 'MCP tool call timed out; read current session state before retrying') from error
            except Exception as error:
                raise HTTPException(502, 'MCP tool call failed') from error
        if result.isError:
            detail = 'MCP tool returned an error'
            if result.content:
                detail = next((item.text for item in result.content if getattr(item, 'text', None)), detail)
            raise HTTPException(422, detail)
        structured = getattr(result, 'structuredContent', None)
        if structured is not None:
            return structured
        text_items = [item.text for item in result.content if getattr(item, 'text', None)]
        if len(text_items) == 1:
            try:
                return json.loads(text_items[0])
            except json.JSONDecodeError:
                return {'text': text_items[0]}
        return {'content': text_items}


class GatewayMCPTool:
    """ADK tool adapter that preserves an MCP tool's discovered JSON schema."""

    def __new__(cls, name, definition, gateway):
        from google.adk.tools import BaseTool
        from google.adk.tools._gemini_schema_util import _to_gemini_schema
        from google.genai import types

        class _Tool(BaseTool):
            def __init__(self):
                super().__init__(name=name, description=definition.get('description') or name)

            def _get_declaration(self):
                return types.FunctionDeclaration(
                    name=self.name,
                    description=self.description,
                    parameters=_to_gemini_schema(definition.get('inputSchema', {})),
                )

            async def run_async(self, *, args, tool_context):
                return await gateway.call(name, args)

        return _Tool()


class ClimateADKAgent:
    """Gemini ADK supervisor agent whose callable tools invoke the MCP server."""

    TOOL_NAMES = {'list_affected_activities', 'get_climate_suggestions', 'propose_reschedule'}

    def __init__(self, gateway: MCPGateway):
        from google.adk.agents import Agent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types

        settings = get_settings()
        if settings.reasoning_provider != 'vertex' or not settings.vertex_project or not settings.vertex_model:
            raise RuntimeError('Configure Vertex Gemini reasoning before enabling supervisor chat')
        # Configure ADK's Gen AI client in the FastAPI process itself. These
        # standard variables are not implied by WORKFORCE_VERTEX_* settings.
        os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'true'
        os.environ['GOOGLE_CLOUD_PROJECT'] = settings.vertex_project
        os.environ['GOOGLE_CLOUD_LOCATION'] = settings.vertex_location
        self.gateway = gateway
        self.sessions = InMemorySessionService()
        self.lock = asyncio.Lock()
        tools = []
        for name in sorted(self.TOOL_NAMES):
            schema = gateway.tools.get(name)
            if not schema:
                raise RuntimeError(f'Required MCP scheduling tool is unavailable: {name}')
            tools.append(GatewayMCPTool(name, schema, gateway))

        instruction = '''You are the climate scheduling agent for a supervisor. Interpret the
supervisor's natural-language request, inspect the current schedule through MCP when needed,
then call the appropriate MCP scheduling tool with structured fields. Use only the discovered
MCP tools; the backend owns authorization, schedule state, timezone, duration, policy checks,
and proposal validation. For a requested time range, use site-local 24-hour HH:MM constraints.
When the supervisor names an activity, identify its exact activity_id from MCP schedule data
and pass it to propose_reschedule. To revise a pending proposal, interpret the new requested
range as the new allowed window and prepare a replacement proposal for that same activity.
Do not invent event IDs, times, constraints, or reasons. Never claim a schedule changed:
proposals require explicit approval. After the MCP tool returns, explain the result and any
validation issues plainly, using the tool response as the sole source of scheduling facts.
If the activity or time request is ambiguous, ask a concise clarifying question and do not
create a proposal.'''
        agent = Agent(name='climate_supervisor_agent', model=settings.vertex_model,
                      description='Interprets supervisor requests and calls climate scheduling MCP tools.',
                      instruction=instruction, tools=tools,
                      generate_content_config=types.GenerateContentConfig(temperature=0,
                          max_output_tokens=settings.model_max_output_tokens,
                          http_options=types.HttpOptions(timeout=int(settings.model_timeout_seconds * 1000),
                              retry_options=types.HttpRetryOptions(attempts=1))))
        self.runner = Runner(agent=agent, app_name='climate_supervisor_agent',
                             session_service=self.sessions)

    async def chat(self, message: str, session_id: str):
        from google.genai import types
        from time import perf_counter

        async with self.lock:
            started = perf_counter()
            current = await self.sessions.get_session(app_name='climate_supervisor_agent',
                user_id='supervisor', session_id=session_id)
            if current is None:
                await self.sessions.create_session(app_name='climate_supervisor_agent',
                    user_id='supervisor', session_id=session_id)
            content = types.Content(role='user', parts=[types.Part(text=json.dumps({
                'session_id': session_id, 'supervisor_request': message,
            }, separators=(',', ':')))])
            events = []
            async for event in self.runner.run_async(user_id='supervisor', session_id=session_id,
                                                     new_message=content):
                events.append(event)
            final = next((event for event in reversed(events)
                          if event.is_final_response() and event.content), None)
            response_text = ''.join(part.text or '' for part in final.content.parts) if final else ''
            # MCP tool results are emitted in function-response events. Return
            # the complete typed Reply to the UI, not a model-authored summary.
            structured = []
            for event in events:
                for part in (event.content.parts if event.content else []):
                    result = getattr(getattr(part, 'function_response', None), 'response', None)
                    if isinstance(result, dict):
                        if isinstance(result.get('result'), dict):
                            result = result['result']
                        structured.append(result)
            reply = next((item for item in reversed(structured)
                          if {'session_id', 'suggestions', 'calendar'}.issubset(item)), None)
            if reply is None:
                reply = await self.gateway.call('get_climate_suggestions', {'session_id': session_id})
                reply['clarification'] = True
            # Preserve the authoritative structured response and use the model
            # text only for its supervisor-facing explanation.
            if response_text:
                reply['message'] = response_text
            measurement = reply.get('model') or {}
            usage = getattr(final, 'usage_metadata', None) if final else None
            measurement.update({
                'provider': 'vertex-adk-gemini',
                'requested_model': get_settings().vertex_model,
                'returned_model_version': (getattr(final, 'model_version', None) or get_settings().vertex_model) if final else None,
                'latency_ms': round((perf_counter() - started) * 1000, 3),
                'prompt_tokens': getattr(usage, 'prompt_token_count', None),
                'output_tokens': getattr(usage, 'candidates_token_count', None),
                'thought_tokens': getattr(usage, 'thoughts_token_count', None),
                'status': 'ready' if final else 'needs-review',
            })
            reply['model'] = measurement
            reply['mode'] = 'fixture-data/vertex-reasoning'
            reply['agent_id'] = 'climate-workforce/adk-mcp-v1'
            return reply

    async def close(self):
        await self.runner.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    gateway = MCPGateway()
    await gateway.start()
    app.state.mcp_gateway = gateway
    settings = get_settings()
    try:
        app.state.climate_agent = ClimateADKAgent(gateway) if settings.reasoning_provider == 'vertex' else None
    except Exception:
        await gateway.close()
        raise
    async def monitor():
        while True:
            await asyncio.sleep(get_settings().background_check_seconds)
            await asyncio.to_thread(service.background_pass)
    monitor_task = asyncio.create_task(monitor())
    try:
        yield
    finally:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        if app.state.climate_agent:
            await app.state.climate_agent.close()
        await gateway.close()


app = FastAPI(
    title='Calendar Backend',
    version='0.1.0',
    description='Calendar HTTP API and frontend gateway for Climate Workforce MCP tools.',
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(http_api_router)


@app.get('/health', tags=['Health'])
def health(request: Request):
    gateway = getattr(request.app.state, 'mcp_gateway', None)
    return {'status': 'ok' if gateway and gateway.session else 'unavailable',
            'mcp_tools': len(gateway.tools) if gateway else 0}


@app.post('/agent/login')
def demo_login(response: Response):
    settings = get_settings()
    if not settings.agent_demo_enabled:
        raise HTTPException(404, 'Demo login is disabled')
    now = datetime.now(timezone.utc)
    for token, (_, expiry) in list(demo_identities.items()):
        if expiry <= now:
            del demo_identities[token]
    if len(demo_identities) >= 1000:
        raise HTTPException(503, 'Demo identity capacity reached')
    token = secrets.token_urlsafe(32)
    from workforce_agent.agent import Principal
    demo_identities[token] = (Principal(
        subject=f'demo:{secrets.token_urlsafe(16)}',
        permissions={'read', 'propose', 'approve', 'annotate'},
        sites={'VAD-PLANT-01'},
    ), now + timedelta(minutes=30))
    response.set_cookie('calendar_demo_identity', token, httponly=True, samesite='strict',
                        secure=settings.agent_secure_cookies, max_age=1800, path='/')
    response.headers['Cache-Control'] = 'no-store'
    return {'identity': 'Isolated demo supervisor', 'expires_in_seconds': 1800}


@app.get('/agent')
def discover_tools(request: Request):
    browser_identity(request)
    gateway: MCPGateway = request.app.state.mcp_gateway
    if not gateway.session:
        raise HTTPException(503, 'MCP server is not connected')
    return {'server': 'climate-workforce', 'tools': gateway.tools}


@app.post('/agent')
async def invoke_tool(body: ToolRequest, request: Request):
    browser_identity(request)
    gateway: MCPGateway = request.app.state.mcp_gateway
    if body.name == 'supervisor_chat':
        agent: ClimateADKAgent | None = request.app.state.climate_agent
        if agent is None:
            raise HTTPException(503, 'The ADK Gemini supervisor agent is not configured')
        session_id = body.arguments.get('session_id')
        message = body.arguments.get('message')
        if not isinstance(session_id, str) or not isinstance(message, str) or not message.strip():
            raise HTTPException(422, 'supervisor_chat requires session_id and message')
        try:
            result = await asyncio.wait_for(agent.chat(message, session_id), timeout=90)
        except asyncio.TimeoutError as error:
            raise HTTPException(504, 'Climate agent request timed out; check session state before retrying') from error
        except Exception as error:
            logger.warning('Climate ADK MCP orchestration failed (%s)', type(error).__name__)
            raise HTTPException(502, 'Climate ADK agent could not complete the MCP scheduling request') from error
        return {'name': body.name, 'result': result}
    return {'name': body.name, 'result': await gateway.call(body.name, body.arguments)}


def run():
    import uvicorn
    uvicorn.run('calendar_backend.main:app', host='0.0.0.0', port=8010)


if __name__ == '__main__':
    run()
