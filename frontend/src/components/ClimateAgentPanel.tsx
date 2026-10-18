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
type Props = { onDismissActivity:()=>void; onPreviewProposal?:(suggestion:Suggestion|null)=>void; demoPolicies?: boolean; day: string; mode: string; siteId: string; timezone: string; suggestions: Suggestion[]; activities: Calendar['activities']; employees: Calendar['employees']; warnings: Calendar['warnings']; selectedActivity: string | null; onSelectActivity: (id:string) => void; affectedCount: number; onCalendar: (calendar: Calendar) => void };
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
  const [proposalNotice, setProposalNotice] = useState('');
  const [mcpToolCount, setMcpToolCount] = useState(0);
  const activityDialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    setReview(null); setConfirmed(false); setDecisionReason(''); setProposalNotice('');
    if (props.selectedActivity) activityDialog.current?.showModal();
    else activityDialog.current?.close();
  }, [props.selectedActivity]);
  const selected = props.activities.find(a => a.id === props.selectedActivity);
  const mounted = useRef(false);
  const contextVersion = useRef(0);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const onPreviewProposal = props.onPreviewProposal;
  const clearContext = useCallback(() => {
    contextVersion.current += 1;
    onPreviewProposal?.(null);
    setSession(null); setMessages([]); setSuggestions(props.suggestions);
    setReview(null); setConfirmed(false); setDecisionReason(''); setInput(''); setMcpToolCount(0);
    setEarliest('06:00'); setLatest('12:00'); setChatState(''); setRetryAction(null);
  }, [props.suggestions, onPreviewProposal]);
  useEffect(() => {
    if (!session) return;
    const timer = window.setTimeout(() => {
      clearContext();
      setError('Session expired. Reconnecting automatically.');
    }, Math.max(0, Date.parse(session.expires_at) - Date.now()));
    return () => window.clearTimeout(timer);
  }, [session, clearContext]);
  const onCalendar = props.onCalendar;
  useEffect(() => {
    if (!session?.monitoring.enabled || busy) return;
    let active = true;
    const timer = window.setInterval(() => {
      void requestTool<Reply>('get_climate_suggestions', {session_id:session.session_id}, 10000)
        .then(reply => { if (active) { setSession(reply); onCalendar(reply.calendar); } })
        .catch(e => {if (active) setError(e instanceof Error ? e.message : 'Status refresh failed.');});
    }, 10000);
    return () => { active = false; window.clearInterval(timer); };
  }, [session?.session_id, session?.monitoring.enabled, onCalendar, busy, clearContext]);
  const sessionAvailable = !!session;
  const [connectionAttempt, setConnectionAttempt] = useState(0);
  useEffect(() => {
    if (props.mode !== 'demo' || sessionAvailable) return;
    const controller = new AbortController();
    let active = true;
    setBusy(true); setError(''); setChatState('Connecting to the climate agent…');
    async function connect() {
      const options = {method:'POST', credentials:'include' as const, headers:{'Content-Type':'application/json'}, signal:controller.signal};
      const login = await fetch('/agent/login', options);
      if (!login.ok) throw new Error('Unable to connect to the demo agent.');
      const discovery = await fetch('/agent', {credentials:'include', signal:controller.signal});
      if (!discovery.ok) throw new Error('Unable to discover climate agent tools.');
      const catalog = await discovery.json() as {tools:Record<string,unknown>};
      if (!catalog.tools?.create_supervisor_session) throw new Error('MCP server does not expose session creation.');
      setMcpToolCount(Object.keys(catalog.tools).length);
      const reply = await requestTool<Reply>('create_supervisor_session', {day:props.day, site_id:props.siteId});
      if (!active) return;
      onCalendar(reply.calendar); setSession(reply); setSuggestions(reply.suggestions);
      setMessages([`Agent: ${reply.message}`]); setChatState('Climate agent ready.');
    }
    void connect().catch(e => {
      if (active) { setError(e instanceof Error ? e.message : 'Agent unavailable.'); setChatState('Connection failed. Please retry.'); }
    }).finally(() => { if (active) setBusy(false); });
    return () => { active = false; controller.abort(); };
  }, [props.mode, props.day, props.siteId, sessionAvailable, connectionAttempt, onCalendar]);
  const time = (value: string) => new Intl.DateTimeFormat('en-IN', {timeZone: props.timezone, hour: 'numeric', minute: '2-digit'}).format(new Date(value));
  const range = (start: string, end: string) => `${time(start)} – ${time(end)}`;
  async function requestTool<T = Reply>(name: string, args: Record<string,unknown>, timeout = 45000): Promise<T> {
    const version = contextVersion.current;
    const response = await fetch('/agent', {method:'POST', credentials:'include', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name,arguments:args}), signal:AbortSignal.timeout(timeout)});
    if (!mounted.current || version !== contextVersion.current) throw new Error('Calendar context changed; response discarded.');
    if (!response.ok) {
      const failure = await response.json().catch(() => ({})) as {detail?: string};
      if (response.status === 401 || response.status === 404) clearContext();
      throw new Error(failure.detail ?? `MCP gateway returned ${response.status}`);
    }
    const payload = await response.json() as {result:T};
    if (!mounted.current || version !== contextVersion.current) throw new Error('Session context changed; response discarded.');
    return payload.result;
  }
  function accept(reply: Reply) {
    if (!mounted.current) return;
    props.onCalendar(reply.calendar);
    setSession(reply); setMessages(previous => [...previous, `${reply.clarification ? 'Clarification' : 'Agent'}: ${reply.message}`].slice(-20));
    setSuggestions(reply.suggestions); setReview(null);
    const selectedProposal = reply.suggestions.find(s => s.activity_id === props.selectedActivity
      && (s.start && s.end || s.candidate_window));
    onPreviewProposal?.(selectedProposal ?? null);
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
    <details className="integration-status"><summary>Integration & session status</summary>Calendar backend: {session ? 'Session active' : 'Not connected'} · MCP tools: {mcpToolCount ? `${mcpToolCount} discovered` : 'Not discovered'}<br />Runtime: {session?.mode ?? 'Fixture display — no active runtime session'}<br />Calendar: isolated demo · approval-gated updates<br />{session?.model && <>Model: {session.model.requested_model ?? 'not configured'} · returned version: {session.model.returned_model_version ?? 'not verified'}<br /></>}{session && <>Agent: {session.agent_id}<br />Session expires: {time(session.expires_at)} (site time)</>}</details>
    <section className="agent-chat"><h3>Ask the climate agent</h3><div className="chat-prompts"><button disabled={!session || busy} onClick={()=>setInput('who is affected')}>Who is affected?</button><button disabled={!session || busy} onClick={()=>setInput('reschedule before 12:00')}>Suggest safer times</button></div><details className="chat-capabilities"><summary>Chat capabilities</summary><p>{session?.mode.includes('/vertex') ? 'Vertex reasoning interprets your request; deterministic validation and approval remain mandatory.' : 'Demo grammar: “who is affected”, “reschedule before 12:00”, “after 08:00”, or “reschedule”. Try “move outdoor inspections before noon” or “keep this crew together”; unsupported demo requests trigger clarification.'}</p></details>
      {!session && error && <div role="alert"><p>{error}</p><button disabled={busy} onClick={() => setConnectionAttempt(n => n + 1)}>Retry connection</button></div>}
      {props.mode !== 'demo' && <p>Live agent and authenticated sign-in are not configured.</p>}
      <p id="chat-help">Enter sends a message. A proposal does not change the calendar; review and explicit approval are required.</p>
      <p role="status">{busy ? 'Waiting for backend confirmation…' : chatState}</p>
      <div role="log" aria-label="Current session conversation" aria-live="polite" aria-relevant="additions" tabIndex={0} className="chat-log">{messages.map((message,i) => <p className="chat-message" key={i}>{message}</p>)}</div>
      {session && <details><summary>Affected activities & evidence</summary>{session.context.map(a => <div key={a.activity_id} className="chat-message"><strong>{a.title} · {a.status}</strong><p>{range(a.current_start,a.current_end)} · {a.reason}</p>{a.warnings.map(w => <p key={w.id}>{w.title} · {range(w.start,w.end)} · {w.measure}<br />{w.policy}<br />Reference: {w.id}</p>)}</div>)}</details>}
      <form onSubmit={e => { e.preventDefault(); if (!session || busy || !input.trim()) return; const text = input; setInput(''); setMessages(m => [...m, `You: ${text}`].slice(-20)); void perform(async () => { const reply = await requestTool<Reply>('supervisor_chat', {session_id:session.session_id, message:text}, 100000); accept(reply); }); }}><label className="sr-only" htmlFor="agent-message">Message climate agent</label><input id="agent-message" aria-describedby="chat-help" autoComplete="off" maxLength={2000} disabled={!session || busy} value={input} onChange={e => setInput(e.target.value)} placeholder="Move outdoor inspections before noon" /><button disabled={!session || busy || !input.trim()}>Send</button></form>
      <details className="advanced-agent-controls"><summary>Scheduling constraints & demo controls</summary><form className="constraint-form" onSubmit={e => { e.preventDefault(); if (!session) return; void perform(async () => {const reply = await requestTool<Reply>('propose_reschedule', {session_id:session.session_id, constraints:{earliest:earliest || null, latest:latest || null}}); accept(reply); }); }}><p>Proposal window · {props.timezone}</p><label>Earliest start<input type="time" value={earliest} onChange={e => setEarliest(e.target.value)} /></label><label>Latest finish<input type="time" value={latest} onChange={e => setLatest(e.target.value)} /></label><button disabled={!session || busy}>Prepare validated proposals</button></form>

      {session && <section className="background-demo"><h3>Background warning notes</h3><p>Independent of rescheduling approval. Writes informational notes only to affected outdoor events in this demo session.</p><button disabled={busy} onClick={() => void perform(async () => {const reply = await requestTool<Reply>('configure_warning_notes', {session_id:session.session_id, enabled:!session.monitoring.enabled}); accept(reply);})}>{session.monitoring.enabled ? 'Disable automatic notes' : 'Enable automatic notes'}</button><button disabled={busy || !session.monitoring.enabled} onClick={() => void perform(async () => {const reply = await requestTool<Reply>('annotate_warning_notes', {session_id:session.session_id}); accept(reply);})}>Run warning pass now</button><p>Automatic pass: {session.monitoring.enabled ? 'Enabled on backend; UI need not remain open' : 'Disabled'}</p>{session.monitoring.last_run && <div role="status"><p>Last pass: {session.monitoring.last_run.result} · {session.monitoring.last_run.timestamp}</p>{session.monitoring.last_run.events.map(event => <p key={event.activity_id}>{props.activities.find(a => a.id===event.activity_id)?.title ?? event.activity_id}: {event.result} {event.message}</p>)}</div>}</section>}
      <section className="infeasible-demo"><h3>Infeasible example</h3><p>Try a 12:00–13:00 window: high heat overlaps it, and the pump inspection needs 90 minutes.</p><button disabled={busy || !session} onClick={() => void perform(async () => {if (!session) return; const reply=await requestTool<Reply>('propose_reschedule',{session_id:session.session_id,constraints:{earliest:'12:00',latest:'13:00'}}); accept(reply);})}>Show infeasible proposals</button></section>
      {session && <details><summary>Decision history ({session.audit.length})</summary>{session.audit.map((record,i) => <p className="chat-message" key={i}>{record.decision} · {record.result}<br />{record.actor} · {record.timestamp}<br />{record.message}</p>)}</details>}
    </details></section>
    <div className="agent-warning-summary"><span aria-hidden="true">⚠</span><div><h3>{props.affectedCount} outdoor activities flagged</h3><p className="agent-intro">{session ? 'Session proposals require supervisor approval.' : 'The climate agent connects automatically to prepare proposals.'}</p><p>Backend warning matches · indoor activities are not weather-flagged.</p></div></div>
    <dialog ref={activityDialog} className="activity-modal" aria-labelledby="activity-modal-title" onCancel={props.onDismissActivity} onClose={props.onDismissActivity}>
      <header className="activity-modal-header"><h2 id="activity-modal-title">Supervisor review</h2><button aria-label="Close activity review" onClick={props.onDismissActivity}>Close</button></header>
      {selected && <section><h3>{selected.title}</h3><p>{range(selected.start, selected.end)} · {props.timezone}</p><p>{props.employees.find(e => e.id === selected.employee_id)?.name} · {selected.kind} · {selected.location ?? 'Unknown location'}</p><p>{selected.reason}</p><details><summary>Event notes</summary><pre className="event-notes">{selected.notes || 'No event notes'}</pre></details><p>Warning references: {selected.warning_ids.join(', ') || 'None'}</p></section>}
      <h3>Schedule proposals & actions</h3>
      {!session && <p role="status">{busy ? 'Connecting to the climate agent…' : 'Agent connection required. Retry from the chat panel.'}</p>}
      {session && <button disabled={busy} onClick={() => {
        setProposalNotice('Sending request to the climate agent…');
        const activityTitle = selected?.title ?? 'affected activities';
        const employeeName = props.employees.find(employee => employee.id === selected?.employee_id)?.name;
        const details = selected
          ? ` (ID ${selected.id}; ${selected.kind}; currently ${range(selected.start, selected.end)}; ${employeeName ?? 'employee unavailable'}; ${selected.location ?? 'location unavailable'})`
          : '';
        const windowStart = earliest || '06:00';
        const windowEnd = latest || '18:00';
        setMessages(previous => [...previous, `You: Prepare validated proposals for ${activityTitle}${details} on ${props.day} at ${props.siteId}, within ${windowStart}–${windowEnd} ${props.timezone} time.`].slice(-20));
        void perform(async () => {
          try {
            const reply = await requestTool<Reply>('propose_reschedule', {session_id:session.session_id, constraints:{earliest:earliest || null, latest:latest || null}, activity_id:props.selectedActivity});
            accept(reply);
            setProposalNotice('Message sent to the agent. You can close this window and check the Climate agent panel for the response.');
          } catch (failure) {
            setProposalNotice('The request could not be confirmed. Please retry.');
            throw failure;
          }
        });
      }}>{busy ? 'Sending…' : 'Prepare validated proposals'}</button>}
      {proposalNotice && <div className="proposal-notification" role="status" aria-live="polite"><p>{proposalNotice}</p>{!busy && <button onClick={props.onDismissActivity}>Close and check Climate agent</button>}</div>}

    <AgentSuggestions compact demoPolicies={props.demoPolicies ?? props.mode==='demo'} suggestions={suggestions.filter(s => s.activity_id === props.selectedActivity)} activities={props.activities} employees={props.employees} warnings={props.warnings} timezone={props.timezone} selectedActivity={props.selectedActivity} loading={busy} error={error} onRetry={() => {if(retryAction) void perform(retryAction);}} onSelect={s => {
      props.onSelectActivity(s.activity_id); onPreviewProposal?.((s.approval ?? 'pending')==='pending' && (s.start && s.end || s.candidate_window) ? s : null); setConfirmed(false); setDecisionReason('');
      const activity=props.activities.find(a=>a.id===s.activity_id);
      setReview({proposal:s,current:activity ? {...activity,location:activity.location ?? 'Unknown location',version:activity.version ?? 1} : null,employees:props.employees.filter(e=>e.id===activity?.employee_id),checks:{},conflicts:[],climate_rationale:s.rationale,annotation:'Read-only proposal preview. Fresh backend review is required before approval.',server_reviewed:false});
      if(session) void perform(async()=>{const result=await requestTool<Review>('review_proposal',{session_id:session.session_id,proposal_id:s.id}); setReview({...result,server_reviewed:true});});
    }}>{s => review?.proposal.id === s.id && <ProposalReview review={review} timezone={props.timezone} busy={busy} sessionAvailable={!!session} confirmed={confirmed} reason={decisionReason} onConfirm={setConfirmed} onReason={setDecisionReason} onDecision={decision => void perform(async () => {
      if (!session) return;
      const reply = await requestTool<Reply>('decide_proposal',{session_id:session.session_id,proposal_id:s.id,decision,reason:decisionReason});
      accept(reply);
      if (decision === 'revise') setInput('reschedule');
    })} />}</AgentSuggestions>
    </dialog>
    <FlaggedActivities demo={props.demoPolicies ?? (props.mode==='demo' || !!session?.mode.includes('demo'))} calendar={{activities:props.activities,employees:props.employees,warnings:props.warnings,site:{id:props.siteId,name:props.siteId,timezone:props.timezone}}} selectedActivity={props.selectedActivity} onSelect={props.onSelectActivity} />
    <details className="cooling-periods" open><summary>Cooling periods</summary><div><p>{props.demoPolicies ? 'Illustrative site policy · verify against site requirements.' : 'Configured policy requirements supplied by backend.'}</p>{props.activities.some(a=>a.policy_context?.applicable_work_rest_rules?.length) ? props.activities.filter(a=>a.policy_context?.applicable_work_rest_rules?.length).map(a=><p key={a.id}><strong>{a.title}</strong>{a.policy_context!.applicable_work_rest_rules!.map((r,i)=><span key={i}> · {r.work_minutes} min work / {r.rest_minutes} min rest · cooling {r.cooling_required ? 'required' : 'not required by supplied rule'}</span>)}</p>) : <p>No applicable work/rest interval supplied in the current policy. Review site requirements.</p>}</div></details>
<p className="approval-note">Only explicit approval can update this demo calendar. External calendar integration is not connected. Note annotation is an independently configured demo action.</p></aside>;
}
