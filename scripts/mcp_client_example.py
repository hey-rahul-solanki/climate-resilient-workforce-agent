"""Minimal local stdio client; configure the MCP credential and token first."""
import asyncio
import os
import sys
from datetime import date

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from workforce_agent.calendar import demo_inputs
from workforce_agent.day_schedule import get_day_schedule


async def main():
    token=os.environ.get('WORKFORCE_AGENT_TOKEN')
    if not token:
        raise RuntimeError('Provision a read/propose/site credential in WORKFORCE_AGENT_TOKEN first')
    params=StdioServerParameters(command=sys.executable,args=['-m','workforce_agent.mcp_server'],env={
        'WORKFORCE_AGENT_TOKEN':token,
        'WORKFORCE_AGENT_CREDENTIALS':os.environ.get('WORKFORCE_AGENT_CREDENTIALS',''),
    })
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as client:
            await client.initialize()
            catalog=await client.list_tools()
            resources=await client.list_resources()
            print('Discovered tools:',', '.join(tool.name for tool in catalog.tools))
            print('Discovered schema resources:',', '.join(str(item.uri) for item in resources.resources))
            async def call(name,args):
                reply=await client.call_tool(name,args)
                if reply.isError: raise RuntimeError(str(reply.content))
                return reply.structuredContent
            day=date.today()
            consumer_calendar=get_day_schedule('VAD-PLANT-01',day).model_dump(mode='json')
            activity_fields={'id','employee_id','title','start','end','site_id','location','kind',
                             'exposure_type','scheduled_rest','mandatory_rest_intervals','version','source_event_id'}
            consumer_context={key:consumer_calendar[key] for key in ('date','site','window','employees')}
            consumer_context['activities']=[{key:value for key,value in activity.items() if key in activity_fields}
                                            for activity in consumer_calendar['activities']]
            _,policy=demo_inputs(day)
            result=await call('analyze_consumer_schedule',{
                'context':consumer_context,
                'policy':policy.model_dump(mode='json'),
            })
            print('Submitted site and timezone:',result['site']['id'],result['site']['timezone'])
            print('Weather freshness/source:',result['weather']['status'],result['weather']['source'])
            print('Activities:',len(result['activities']))
            print('Warning matches:',sum(len(item['warning_matches']) for item in result['activities']))


if __name__=='__main__': asyncio.run(main())
