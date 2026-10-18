"""Minimal local stdio client; configure WORKFORCE_AGENT_TOKEN and API URL first."""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    token=os.environ.get('WORKFORCE_AGENT_TOKEN')
    if not token:
        raise RuntimeError('Provision a read/propose/site credential in WORKFORCE_AGENT_TOKEN first')
    params=StdioServerParameters(command=sys.executable,args=['-m','workforce_agent.mcp_server'],env={
        'WORKFORCE_AGENT_TOKEN':token,
        'WORKFORCE_AGENT_API_URL':os.environ.get('WORKFORCE_AGENT_API_URL','http://127.0.0.1:8000'),
    })
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as client:
            await client.initialize()
            async def call(name,args):
                reply=await client.call_tool(name,args)
                if reply.isError: raise RuntimeError(str(reply.content))
                return reply.structuredContent or json.loads(reply.content[0].text)
            created=await call('create_supervisor_session',{'day':'2026-10-17','site_id':'VAD-PLANT-01'})
            sid=created['session_id']
            affected=await call('list_affected_activities',{'session_id':sid})
            print('Affected/review activities:',len(affected['context']))
            result=await call('propose_reschedule',{'session_id':sid,'constraints':{'latest':'12:00'}})
            print('Pending proposals:',len(result['suggestions']))
            print('No event times changed. This example session expires in 30 minutes.')


if __name__=='__main__': asyncio.run(main())
