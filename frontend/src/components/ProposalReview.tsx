import type { AgentSuggestion } from './AgentSuggestions';

export type ProposalReviewData = {
  proposal: AgentSuggestion;
  current: {start:string;end:string;location:string|null;kind:string;version:number;title?:string;notes?:string} | null;
  employees: {name:string}[];
  checks: Record<string,boolean>;
  conflicts: {title:string}[];
  climate_rationale: string;
  annotation: string;
  server_reviewed?: boolean;
};
type Decision = 'approve'|'reject'|'revise';
type Props = {review:ProposalReviewData;timezone:string;busy:boolean;sessionAvailable:boolean;confirmed:boolean;reason:string;onConfirm:(value:boolean)=>void;onReason:(value:string)=>void;onDecision:(decision:Decision)=>void};
const checkLabels:Record<string,string>={source_version:'Source event version',weather_policy:'Weather and policy',availability:'Employee and location/resource availability',duration:'Activity duration',session_window:'Site day window'};

export function ProposalReview(props:Props) {
  const {review:r}=props;
  const s=r.proposal;
  const time=(value:string)=>new Intl.DateTimeFormat('en-IN',{timeZone:props.timezone,month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}).format(new Date(value));
  const range=(start:string,end:string)=>`${time(start)} – ${time(end)}`;
  const stale=r.server_reviewed && r.checks.source_version===false;
  const pending=(s.approval ?? 'pending')==='pending';
  const checksPassed=Object.keys(r.checks).length>0 && Object.values(r.checks).every(Boolean);
  const requiresRiskReason=s.validation==='risk-reduced';
  const canDecide=props.sessionAvailable && r.server_reviewed && pending && !props.busy;
  const failedChecks=Object.entries(r.checks).filter(([,passed])=>!passed).map(([name])=>checkLabels[name] ?? name.replaceAll('_',' '));
  const approvalBlockMessage=!props.sessionAvailable ? 'Approval is unavailable because the agent session is not active.'
    : !r.server_reviewed ? 'Approval is unavailable until the backend completes a fresh review.'
    : !pending ? 'This proposal already has a decision.'
    : !s.start || !s.end ? 'This requested time did not pass validation, so it cannot be approved. Choose another time window; the calendar has not changed.'
    : !checksPassed ? `Approval is blocked because these checks failed: ${failedChecks.join(', ')}.`
    : requiresRiskReason && !props.reason.trim() ? 'Residual climate-warning overlap remains. Enter a decision reason to approve this reduced-risk proposal.'
    : '';
  return <section className="proposal-review" aria-label="Supervisor proposal review" aria-busy={props.busy}>
    <h4>Supervisor review · {r.current?.title ?? s.activity_id}</h4>
    <p>Reschedule status: {s.approval ?? 'pending'}{pending ? ' — proposal only; no calendar time change confirmed.' : ''}</p>
    {s.outcome && <p role="status">Backend update result: {s.outcome.result} · {s.outcome.message}</p>}
    {stale && <p role="alert">Stale proposal: the source event changed. Approval is disabled; request a revision.</p>}
    {!r.server_reviewed && <p role="status">Preview only. Fresh backend review is required before any decision.</p>}
    <p>Current calendar time: {r.current ? range(r.current.start,r.current.end) : 'Source event unavailable'}</p>
    {s.current && <p>Original time at proposal: {range(s.current.start,s.current.end)}</p>}
    <p>Proposed: {s.start && s.end ? range(s.start,s.end) : s.candidate_window ? `${range(s.candidate_window.start,s.candidate_window.end)} — failed validation` : 'No proposed time — review required'} · {props.timezone}</p>
    <p>Employees: {r.employees.map(e=>e.name).join(', ') || 'Unavailable'}<br />Location: {r.current?.location ?? 'Unknown location'} · {r.current?.kind ?? 'unknown'}</p>
    <p>{r.climate_rationale}</p><p>Validation: {s.validation} · Policy: {s.policy ?? 'Reference unavailable'}</p>
    <h5>Original warning overlap evidence</h5>
    {s.warning_matches?.length ? s.warning_matches.map(w=><p key={w.warning_id}>{w.severity} · {w.warning_id}<br />Overlap: {range(w.overlap.start,w.overlap.end)}<br />{w.rationale}<br />{w.policy}</p>) : <p>Exact overlap evidence unavailable in this preview. Warning references: {s.warning_ids?.join(', ') || 'Unavailable'}. Refresh backend review.</p>}
    <h5>Backend policy and resource checks</h5>
    <p>Source version: {r.current?.version ?? 'unknown'}</p>
    {r.server_reviewed ? <ul>{Object.entries(r.checks).map(([name,passed])=><li key={name}>{passed ? '✓' : '⚠'} {checkLabels[name] ?? name.replaceAll('_',' ')}: {passed ? 'passed' : 'failed'}</li>)}</ul> : <p>Checks have not been refreshed.</p>}
    <p>Conflicts: {!r.server_reviewed ? 'Not checked' : r.conflicts.length ? r.conflicts.map(c=>c.title).join(', ') : 'None detected'}</p>
    <section aria-label="Separate event-note disclaimer status"><h5>Event notes / disclaimers · separate from rescheduling</h5><p>{r.annotation}</p>{r.current?.notes ? <details><summary>Show current calendar notes</summary><pre className="event-notes">{r.current.notes}</pre></details> : <p>No event-note content returned. No annotation success is implied.</p>}</section>
    {approvalBlockMessage && <p role="status" className="approval-blocked">{approvalBlockMessage}</p>}
    <label><input type="checkbox" checked={props.confirmed} disabled={!canDecide || !checksPassed || !s.start || !s.end} onChange={e=>props.onConfirm(e.target.checked)} />{requiresRiskReason ? 'I acknowledge residual climate-warning overlap and approve these exact times.' : 'I approve these exact times in the isolated demo calendar.'}</label>
    <label>Decision / revision reason<input value={props.reason} maxLength={2000} disabled={!canDecide} onChange={e=>props.onReason(e.target.value)} /></label>
    {(['approve','reject','revise'] as const).map(decision=><button key={decision} disabled={!canDecide || (decision==='approve' && (!props.confirmed || !checksPassed || !s.start || !s.end || (requiresRiskReason && !props.reason.trim())))} onClick={()=>props.onDecision(decision)}>{decision==='approve' ? 'Approve & apply demo change' : decision==='reject' ? 'Reject' : 'Request revision'}</button>)}
    <p>Approval triggers fresh backend revalidation. Only an applied backend result confirms a calendar time change.</p>
  </section>;
}
