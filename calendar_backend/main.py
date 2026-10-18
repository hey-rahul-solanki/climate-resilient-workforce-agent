"""Calendar-facing HTTP gateway; agent operations are executed through MCP."""
from __future__ import annotations

import asyncio
import json
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    gateway = MCPGateway()
    await gateway.start()
    app.state.mcp_gateway = gateway
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
    return {'name': body.name, 'result': await gateway.call(body.name, body.arguments)}


def run():
    import uvicorn
    uvicorn.run('calendar_backend.main:app', host='0.0.0.0', port=8010)


if __name__ == '__main__':
    run()
