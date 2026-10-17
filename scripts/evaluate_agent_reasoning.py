"""Offline replay of model-output evaluation fixtures; no live provider calls."""
import argparse
import json
from datetime import date
from pathlib import Path

from workforce_agent.agent import AgentService, Principal
from workforce_agent.reasoning import ReasoningService, ProviderResult


class RecordedProvider:
    name='recorded-evaluation-fixture'
    model='fixture-output-v1'
    def __init__(self,output): self.output=output
    def generate(self,message,context):
        return ProviderResult(self.output if isinstance(self.output,str) else json.dumps(self.output),model_version='fixture-output-v1')


def evaluate():
    cases=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/agent_evals/cases.json').read_text())
    results=[]
    user=Principal(subject='offline-evaluation',permissions={'read','propose'},sites={'VAD-PLANT-01'})
    for case in cases:
        service=AgentService(reasoning=ReasoningService(RecordedProvider(case['output'])))
        session=service.create(user,date(2026,10,17))
        before=service.approvals.events(session.session_id)
        reply=service.chat(session.session_id,user,case['request'])
        passed=reply.request_status==case['expected'] and service.approvals.events(session.session_id)==before
        results.append(dict(id=case['id'],category=case['category'],expected=case['expected'],observed=reply.request_status,
                            passed=passed,measurement=reply.model.model_dump()))
    return dict(mode='offline-recorded-outputs; not live model quality/latency',passed=sum(r['passed'] for r in results),total=len(results),cases=results)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=evaluate()
    if args.output:
        args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(f"Offline reasoning evaluations: {result['passed']}/{result['total']} passed; zero live provider calls")
    raise SystemExit(0 if result['passed']==result['total'] else 1)
