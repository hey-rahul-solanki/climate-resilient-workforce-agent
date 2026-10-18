import { useCallback, useEffect, useRef, useState } from 'react';
import type { Calendar } from '../types/calendar';
import { AgentSuggestions } from './AgentSuggestions';
import type { AgentSuggestion } from './AgentSuggestions';
import { FlaggedActivities } from './FlaggedActivities';
import { ProposalReview } from './ProposalReview';
import type { ProposalReviewData } from './ProposalReview';

type Suggestion = AgentSuggestion;
type Warning = { id: string; title: string; start: string; end: string; policy: string; measure: string };
type Context = { activity_id: string; title: string; current_start: string; current_end: string; status: string; reason: string; warnings: Warning[] };
type Reply = { session_id: string; agent_id: string; mode: string; model?: {provider:string;requested_model:string|null;returned_model_version:string|null;status:string}; expires_at: string; message: string; clarification: boolean; constraints: { earliest: string | null; latest: string | null }; suggestions: Suggestion[]; context: Context[]; calendar: Calendar; monitoring: {enabled: boolean; last_run: {timestamp: string; result: string; events: {activity_id:string;result:string;message?:string}[]} | null}; audit: {proposal_id: string; decision: string; actor: string; timestamp: string; result: string; message: string}[] };
type Props = { onPreviewProposal?:(suggestion:Suggestion|null)=>void; demoPolicies?: boolean; day: string; mode: string; siteId: string; timezone: string; suggestions: Suggestion[]; activities: Calendar['activities']; employees: Calendar['employees']; warnings: Calendar['warnings']; selectedActivity: string | null; onSelectActivity: (id:string) => void; affectedCount: number; onCalendar: (calendar: Calendar) => void };
export function ClimateAgentPanel(props: Props) {
  const [session, setSession] = useState<Reply | null>(null);
  const [suggestions, setSuggestions] = useState(props.suggestions);
  const [messages, setMessages] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [earliest, setEarliest] = useState('06:00');
  const [latest, setLatest] = useState('12:00');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  type Review = ProposalReviewData;
  const [review, setReview] = useState<Review | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [retryAction, setRetryAction] = useState<(() => Promise<void>) | null>(null);
  const [decisionReason, setDecisionReason] = useState('');
  const [chatState, setChatState] = useState('');
  const mounted = useRef(false);
  const contextVersion = useRef(0);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const onPreviewProposal = props.onPreviewProposal;
  const clearContext = useCallback(() => {
    contextVersion.current += 1;
    onPreviewProposal?.(null);
    setSession(null); setMessages([]); setSuggestions(props.suggestions);
    setReview(null); setConfirmed(false); setDecisionReason(''); setInput('');
    setEarliest('06:00'); setLatest('12:00'); setChatState(''); setRetryAction(null);
  }, [props.suggestions, onPreviewProposal]);
  useEffect(() => {
    if (!session) return;
    const timer = window.setTimeout(() => {
      clearContext();
      setError('Session expired. Start a new isolated session.');
    }, Math.max(0, Date.parse(session.expires_at) - Date.now()));
    return () => window.clearTimeout(timer);
  }, [session, clearContext]);
  const onCalendar = props.onCalendar;
  useEffect(() => {
    if (!session?.monitoring.enabled || busy) return;
    let active = true;
    const timer = window.setInterval(() => {
      void fetch(`/api/agent/sessions/${session.session_id}`, {credentials:'include', signal:AbortSignal.timeout(10000)})
        .then(async response => { if (!response.ok) { if (active && [401,404,410].includes(response.status)) clearContext(); throw new Error('Unable to refresh background-pass status.'); } return await response.json() as Reply; })
        .then(reply => { if (active) { setSession(reply); onCalendar(reply.calendar); } })
        .catch(e => {if (active) setError(e instanceof Error ? e.message : 'Status refresh failed.');});
    }, 10000);
    return () => { active = false; window.clearInterval(timer); };
  }, [session?.session_id, session?.monitoring.enabled, onCalendar, busy, clearContext]);
  const time = (value: string) => new Intl.DateTimeFormat('en-IN', {timeZone: props.timezone, hour: 'numeric', minute: '2-digit'}).format(new Date(value));
  const range = (start: string, end: string) => `${time(start)} – ${time(end)}`;
  async function request<T = Reply>(path: string, body?: unknown, method = 'POST'): Promise<T | null> {
    const version = contextVersion.current;
    const response = await fetch(`/api/agent${path}`, {method, credentials: 'include', headers: {'Content-Type':'application/json'}, body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(15000)});
    if (!mounted.current || version !== contextVersion.current) throw new Error('Calendar context changed; response discarded.');
    if (!response.ok) {
      const failure = await response.json().catch(() => ({})) as {detail?: string};
      if (response.status === 401 || response.status === 404 || response.status === 410) clearContext();
      throw new Error(failure.detail ?? `Agent API returned ${response.status}`);
    }
    const result = response.status === 204 ? null : await response.json() as T;
    if (!mounted.current || version !== contextVersion.current) throw new Error('Session context changed; response discarded.');
    return result;
  }
  function accept(reply: Reply) {
    if (!mounted.current) return;
    props.onCalendar(reply.calendar);
    setSession(reply); setMessages(previous => [...previous, `${reply.clarification ? 'Clarification' : 'Agent'}: ${reply.message}`].slice(-20));
    setSuggestions(reply.suggestions); setReview(null);
    setChatState(reply.clarification ? 'Clarification needed — please provide more detail.' : 'Backend response received. Proposals remain subject to approval; update results appear in decision history.');
    if (reply.constraints.earliest) setEarliest(reply.constraints.earliest);
    if (reply.constraints.latest) setLatest(reply.constraints.latest);
  }
  async function perform(action: () => Promise<void>) {
    setRetryAction(() => action);
    setBusy(true); setError('');
    try { await action(); } catch (e) { if (mounted.current) { setError(e instanceof Error ? e.message : 'Agent unavailable.'); setReview(previous => previous ? {...previous,server_reviewed:false} : null); setConfirmed(false); } } finally { if (mounted.current) setBusy(false); }
  }
  return <aside className="agent-panel"><div className="agent-heading"><div><h2>Climate agent</h2><small>{session?.mode.includes('/vertex') ? `Fixture data · Vertex reasoning ${session.model?.status ?? 'not called'}` : 'Deterministic demo · Gemini not connected'}</small></div></div>
    <details className="integration-status"><summary>Integration & session status</summary>API: {session ? 'Session active' : 'Not connected'} · MCP: no connection verified<br />Runtime: {session?.mode ?? 'Fixture display — no active runtime session'}<br />Calendar: isolated demo · approval-gated updates<br />{session?.model && <>Model: {session.model.requested_model ?? 'not configured'} · returned version: {session.model.returned_model_version ?? 'not verified'}<br /></>}{session && <>Agent: {session.agent_id}<br />Session expires: {time(session.expires_at)} (site time)</>}</details>
    <div className="agent-warning-summary"><span aria-hidden="true">⚠</span><div><h3>{props.affectedCount} outdoor activities flagged</h3><p className="agent-intro">{session ? 'Session proposals require supervisor approval.' : 'Existing fixture suggestions. Start a backend session to request new proposals.'}</p><p>Backend warning matches · indoor activities are not weather-flagged.</p></div></div><h3 className="top-suggestions-title">Top suggestions</h3>
    <AgentSuggestions compact demoPolicies={props.demoPolicies ?? props.mode==='demo'} suggestions={suggestions} activities={props.activities} employees={props.employees} warnings={props.warnings} timezone={props.timezone} selectedActivity={props.selectedActivity} loading={busy} error={error} onRetry={() => {if(retryAction) void perform(retryAction);}} onSelect={s => {
      props.onSelectActivity(s.activity_id); onPreviewProposal?.((s.approval ?? 'pending')==='pending' && s.start && s.end ? s : null); setConfirmed(false); setDecisionReason('');
      const activity=props.activities.find(a=>a.id===s.activity_id);
      setReview({proposal:s,current:activity ? {...activity,location:activity.location ?? 'Unknown location',version:activity.version ?? 1} : null,employees:props.employees.filter(e=>e.id===activity?.employee_id),checks:{},conflicts:[],climate_rationale:s.rationale,annotation:'Read-only proposal preview. Start a session for fresh backend review before approval.',server_reviewed:false});
      if(session) void perform(async()=>{const result=await request<Review>(`/sessions/${session.session_id}/proposals/${s.id}/review`,undefined,'GET'); if(result) setReview({...result,server_reviewed:true});});
    }}>{s => review?.proposal.id === s.id && <ProposalReview review={review} timezone={props.timezone} busy={busy} sessionAvailable={!!session} confirmed={confirmed} reason={decisionReason} onConfirm={setConfirmed} onReason={setDecisionReason} onDecision={decision => void perform(async () => {
      if (!session) return;
      const reply = await request(`/sessions/${session.session_id}/proposals/${s.id}/decision`, {decision,reason:decisionReason});
      if (reply) accept(reply);
      if (decision === 'revise') setInput('reschedule');
    })} />}</AgentSuggestions>
    <FlaggedActivities demo={props.demoPolicies ?? (props.mode==='demo' || !!session?.mode.includes('demo'))} calendar={{activities:props.activities,employees:props.employees,warnings:props.warnings,site:{id:props.siteId,name:props.siteId,timezone:props.timezone}}} selectedActivity={props.selectedActivity} onSelect={props.onSelectActivity} />
    <details className="cooling-periods" open><summary>Cooling periods</summary><div><p>{props.demoPolicies ? 'Illustrative site policy · verify against site requirements.' : 'Configured policy requirements supplied by backend.'}</p>{props.activities.some(a=>a.policy_context?.applicable_work_rest_rules?.length) ? props.activities.filter(a=>a.policy_context?.applicable_work_rest_rules?.length).map(a=><p key={a.id}><strong>{a.title}</strong>{a.policy_context!.applicable_work_rest_rules!.map((r,i)=><span key={i}> · {r.work_minutes} min work / {r.rest_minutes} min rest · cooling {r.cooling_required ? 'required' : 'not required by supplied rule'}</span>)}</p>) : <p>No applicable work/rest interval supplied in the current policy. Review site requirements.</p>}</div></details>
    <section className="agent-chat"><h3>Ask the climate agent</h3><div className="chat-prompts"><button disabled={!session || busy} onClick={()=>setInput('who is affected')}>Who is affected?</button><button disabled={!session || busy} onClick={()=>setInput('reschedule before 12:00')}>Suggest safer times</button></div><details className="chat-capabilities"><summary>Chat capabilities</summary><p>{session?.mode.includes('/vertex') ? 'Vertex reasoning interprets your request; deterministic validation and approval remain mandatory.' : 'Demo grammar: “who is affected”, “reschedule before 12:00”, “after 08:00”, or “reschedule”. Try “move outdoor inspections before noon” or “keep this crew together”; unsupported demo requests trigger clarification.'}</p></details>
      {!session ? <button disabled={busy || props.mode !== 'demo'} onClick={() => void perform(async () => { await request('/demo-login'); const reply = await request('/sessions', {day: props.day, site_id:props.siteId}); if (reply) accept(reply); })}>{busy ? 'Connecting…' : 'Start isolated demo session'}</button> : <button disabled={busy} onClick={() => void perform(async () => { await request(`/sessions/${session.session_id}`, undefined, 'DELETE'); clearContext(); })}>End session & clear context</button>}
      {props.mode !== 'demo' && <p>Live agent and authenticated sign-in are not configured.</p>}
      <p id="chat-help">Enter sends a message. A proposal does not change the calendar; review and explicit approval are required.</p>
      <p role="status">{busy ? 'Waiting for backend confirmation…' : chatState}</p>
      <div role="log" aria-label="Current session conversation" aria-live="polite" aria-relevant="additions" tabIndex={0} className="chat-log">{messages.map((message,i) => <p className="chat-message" key={i}>{message}</p>)}</div>
      {session && <details><summary>Affected activities & evidence</summary>{session.context.map(a => <div key={a.activity_id} className="chat-message"><strong>{a.title} · {a.status}</strong><p>{range(a.current_start,a.current_end)} · {a.reason}</p>{a.warnings.map(w => <p key={w.id}>{w.title} · {range(w.start,w.end)} · {w.measure}<br />{w.policy}<br />Reference: {w.id}</p>)}</div>)}</details>}
      <form onSubmit={e => { e.preventDefault(); if (!session || busy || !input.trim()) return; const text = input; setInput(''); setMessages(m => [...m, `You: ${text}`].slice(-20)); void perform(async () => { const reply = await request(`/sessions/${session.session_id}/chat`, {message:text}); if (reply) accept(reply); }); }}><label className="sr-only" htmlFor="agent-message">Message climate agent</label><input id="agent-message" aria-describedby="chat-help" autoComplete="off" maxLength={2000} disabled={!session || busy} value={input} onChange={e => setInput(e.target.value)} placeholder="Move outdoor inspections before noon" /><button disabled={!session || busy || !input.trim()}>Send</button></form>
      <details className="advanced-agent-controls"><summary>Scheduling constraints & demo controls</summary><form className="constraint-form" onSubmit={e => { e.preventDefault(); if (!session) return; void perform(async () => {const reply = await request(`/sessions/${session.session_id}/proposals`, {earliest:earliest || null, latest:latest || null}); if (reply) accept(reply); }); }}><p>Proposal window · {props.timezone}</p><label>Earliest start<input type="time" value={earliest} onChange={e => setEarliest(e.target.value)} /></label><label>Latest finish<input type="time" value={latest} onChange={e => setLatest(e.target.value)} /></label><button disabled={!session || busy}>Prepare validated proposals</button></form>

      {session && <section className="background-demo"><h3>Background warning notes</h3><p>Independent of rescheduling approval. Writes informational notes only to affected outdoor events in this demo session.</p><button disabled={busy} onClick={() => void perform(async () => {const reply = await request(`/sessions/${session.session_id}/monitoring`, {enabled:!session.monitoring.enabled}); if(reply) accept(reply);})}>{session.monitoring.enabled ? 'Disable automatic notes' : 'Enable automatic notes'}</button><button disabled={busy || !session.monitoring.enabled} onClick={() => void perform(async () => {const reply = await request(`/sessions/${session.session_id}/warning-pass`, {}); if(reply) accept(reply);})}>Run warning pass now</button><p>Automatic pass: {session.monitoring.enabled ? 'Enabled on backend; UI need not remain open' : 'Disabled'}</p>{session.monitoring.last_run && <div role="status"><p>Last pass: {session.monitoring.last_run.result} · {session.monitoring.last_run.timestamp}</p>{session.monitoring.last_run.events.map(event => <p key={event.activity_id}>{props.activities.find(a => a.id===event.activity_id)?.title ?? event.activity_id}: {event.result} {event.message}</p>)}</div>}</section>}
      <section className="infeasible-demo"><h3>Infeasible example</h3><p>Try a 12:00–13:00 window: high heat overlaps it, and the pump inspection needs 90 minutes.</p><button disabled={busy || !session} onClick={() => void perform(async () => {if (!session) return; const reply=await request(`/sessions/${session.session_id}/proposals`,{earliest:'12:00',latest:'13:00'}); if(reply) accept(reply);})}>Show infeasible proposals</button></section>
      {session && <details><summary>Decision history ({session.audit.length})</summary>{session.audit.map((record,i) => <p className="chat-message" key={i}>{record.decision} · {record.result}<br />{record.actor} · {record.timestamp}<br />{record.message}</p>)}</details>}
    </details></section><p className="approval-note">Only explicit approval can update this demo calendar. External calendar integration is not connected. Note annotation is an independently configured demo action.</p></aside>;
}
