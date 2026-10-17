"""Repeat the isolated fixture journey against Docker; no provider credentials."""
import argparse
import httpx


def run(base_url, day):
    with httpx.Client(base_url=base_url,timeout=20) as client:
        def call(method,path,body=None):
            response=client.request(method,'/api/agent'+path,json=body,headers={'Content-Type':'application/json'})
            response.raise_for_status()
            return response.json() if response.status_code != 204 else None
        call('POST','/demo-login',{})
        opened=call('POST','/sessions',{'day':day})
        sid=opened['session_id']; path=f'/sessions/{sid}'
        try:
            activities=opened['calendar']['activities']
            assert sum(a['status']=='affected' for a in activities)==3
            assert all(not a['warning_ids'] for a in activities if a['kind']=='indoor')
            print('1–2: Four employee rows; three affected outdoor activities; indoor work unflagged.')
            call('POST',path+'/chat',{'message':'who is affected'})
            proposed=call('POST',path+'/chat',{'message':'reschedule before 12:00'})
            print('3: Chat returned traceable evidence and validated proposals.')
            proposal=proposed['suggestions'][0]; pid=proposal['id']
            review=call('GET',path+f'/proposals/{pid}/review')
            assert all(review['checks'].values())
            approved=call('POST',path+f'/proposals/{pid}/decision',{'decision':'approve'})
            assert approved['audit'][-1]['result']=='applied'
            assert next(a for a in approved['calendar']['activities'] if a['id']==proposal['activity_id'])['start']==proposal['start']
            print('4: Explicit approval applied to isolated demo calendar; audit recorded.')
            call('POST',path+'/monitoring',{'enabled':True})
            first=call('POST',path+'/warning-pass',{})
            second=call('POST',path+'/warning-pass',{})
            assert len(first['monitoring']['last_run']['events'])==2
            assert all(e['result']=='unchanged' for e in second['monitoring']['last_run']['events'])
            print('5: Two remaining affected outdoor events annotated; repeated pass made no changes.')
            blocked=call('POST',path+'/proposals',{'earliest':'12:00','latest':'13:00'})
            assert all(s['start'] is None for s in blocked['suggestions'])
            pump=next(s for s in blocked['suggestions'] if s['activity_id']=='event-5')
            print('6: Infeasible pump inspection:',pump['rationale'])
            print('PASS — fixture-only calendar; no external provider calls or calendar changes.')
        finally:
            call('DELETE',path)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://localhost:5173')
    parser.add_argument('--date',default='2026-10-17')
    args=parser.parse_args()
    run(args.base_url,args.date)
