import { PolicyExplanation } from './PolicyExplanation.js';
import type { ReactNode } from 'react';
import type { Calendar, CalendarSuggestion } from '../types/calendar';

export type AgentSuggestion = CalendarSuggestion & {
  current?: {start:string;end:string};
  source_version?: number;
  warning_matches?: {warning_id:string;overlap:{start:string;end:string};severity:string;rationale:string;policy?:string|null}[];
  outcome?: {result:string;message:string};
};

type Props = {
  suggestions: AgentSuggestion[];
  activities: Calendar['activities']; employees: Calendar['employees']; warnings: Calendar['warnings'];
  timezone: string; selectedActivity: string | null;
  demoPolicies?: boolean;
  compact?: boolean;
  loading: boolean; error: string; onRetry: () => void;
  onSelect: (suggestion: AgentSuggestion) => void;
  children?: (suggestion: AgentSuggestion) => ReactNode;
};

/** Structured display only: validation labels are evidence, never safety clearance. */
export function AgentSuggestions(props: Props) {
  const time=(at:string)=>new Intl.DateTimeFormat('en-IN',{timeZone:props.timezone,hour:'numeric',minute:'2-digit'}).format(new Date(at));
  const range=(start:string,end:string)=>`${time(start)} – ${time(end)}`;
  return <section aria-label="Suggested schedule updates" aria-busy={props.loading}>
    {props.loading && <p role="status">Loading or validating agent suggestions…</p>}
    {props.error && <div role="alert" className="agent-error"><p>{props.error}</p><button onClick={props.onRetry} disabled={props.loading}>Retry agent request</button></div>}
    {!props.loading && !props.error && !props.suggestions.length && <p className="agent-empty">No suggested schedule updates. View all flagged activities below or ask the agent for a proposal.</p>}
    <div className="suggestions">{props.suggestions.map((s,index)=>{
      const activity=props.activities.find(a=>a.id===s.activity_id);
      const warnings=props.warnings.filter(w=>s.warning_ids?.includes(w.id));
      const card=<article className={`suggestion ${props.compact ? 'compact-suggestion' : ''} ${index>=2 ? 'additional-suggestion' : ''} ${props.selectedActivity===s.activity_id?'selected-suggestion':''}`} key={s.id} aria-current={props.selectedActivity===s.activity_id ? 'true' : undefined}>
        <span className="validation">{s.validation} · {s.approval ?? 'pending'}</span>
        {(s.approval ?? 'pending')==='pending' && <p>Proposal only · awaiting supervisor decision</p>}
        {s.approval==='rejected' && <p>Rejected · no calendar time change</p>}
        {s.approval==='superseded' && <p>Superseded · request a current proposal</p>}
        <h4>{activity?.title ?? s.activity_id}</h4><small>{props.employees.find(e=>e.id===activity?.employee_id)?.name ?? 'Employee unavailable'}</small>
        <p>Current at proposal: {s.current ? range(s.current.start,s.current.end) : activity ? range(activity.start,activity.end) : 'Unavailable'}</p>
        <p className="new-time">{s.start && s.end ? `Proposed: ${range(s.start,s.end)}` : s.candidate_window ? `Requested candidate (not validated): ${range(s.candidate_window.start,s.candidate_window.end)}` : s.validation==='no-feasible-slot' ? 'No feasible alternative' : 'No proposed time — needs review'}</p>
        {s.infeasibility_reasons?.length ? <p>Failed checks: {s.infeasibility_reasons.map(reason=>reason.replaceAll('_',' ')).join(', ')}</p> : null}
        <p>{s.rationale}</p>
        <details className="suggestion-evidence"><summary>Policy, validation & warning evidence</summary>
        {s.policy && <p>Policy: {s.policy}</p>}
        {activity && <PolicyExplanation activity={activity} warnings={props.warnings} demo={props.demoPolicies} />}
        {warnings.map(w=><p className="suggestion-warning" key={w.id}><strong>{w.severity} · {w.title}</strong><br />{range(w.start,w.end)} · {w.measure}<br />{w.policy}<br />Reference: {w.id}</p>)}
        {s.warning_ids?.filter(id=>!warnings.some(w=>w.id===id)).map(id=><p key={id}>Warning reference: {id} · source details unavailable; review required.</p>)}
        </details>
        {s.outcome && <p role="status"><strong>{s.outcome.result}</strong>: {s.outcome.message}</p>}
        <button disabled={props.loading} onClick={()=>props.onSelect(s)}>{props.compact ? 'Review' : 'Select event & review'}</button>
        {props.children?.(s)}
      </article>;
      return props.compact && index>=2 ? <details className="more-proposals" key={s.id}><summary>More proposals · {activity?.title ?? s.activity_id}</summary>{card}</details> : card;
    })}</div>
    <p className="approval-note">Generated explanations and validation labels are not safety clearance. Applying a change requires explicit approval and fresh backend validation.</p>
  </section>;
}
