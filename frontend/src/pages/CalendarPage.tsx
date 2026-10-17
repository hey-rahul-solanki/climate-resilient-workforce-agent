import { useCallback, useEffect, useRef, useState } from 'react';
import fixture from '../data/calendarDemo.json';
import { getApiBaseUrl } from '../services/api';
import './calendar.css';
import { parseCalendar } from '../types/calendar';
import type { Calendar } from '../types/calendar';
import { layoutEmployeeEvents, timelineGeometry, timelineTicks } from '../utils/timeline';
import { hasOutdoorWarning, activityWarningPresentation, forecastPresentation } from '../utils/climatePresentation';
import { ClimateWarningBanner } from '../components/ClimateWarningBanner';
import { ProposalTimelinePreview } from '../components/ProposalTimelinePreview';
import type { AgentSuggestion } from '../components/AgentSuggestions';
import { ClimateAgentPanel } from '../components/ClimateAgentPanel';

const calendarFixture: Calendar = parseCalendar(fixture);
const initialDay = calendarFixture.date;
function demo(day: string): Calendar {
  // Shift the backend-produced snapshot's dates only; never classify safety here.
  return parseCalendar(JSON.parse(JSON.stringify(calendarFixture).replaceAll(initialDay, day)));
}
export function CalendarPage() {
  const [day, setDay] = useState(initialDay);
  const [mode, setMode] = useState('demo');
  const [data, setData] = useState<Calendar | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const [preview,setPreview] = useState<AgentSuggestion | null>(null);
  const acceptCalendar=useCallback((calendar:Calendar)=>{setData(calendar);setPreview(null);},[]);
  const activityElements = useRef(new Map<string, HTMLButtonElement>());
  function selectActivity(id: string) {
    setReview(id); setPreview(null);
    const element = activityElements.current.get(id);
    element?.scrollIntoView({behavior:'smooth',block:'nearest',inline:'center'});
    element?.focus({preventScroll:true});
  }
  const [review, setReview] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    async function load() {
      setLoading(true); setError(''); setData(null); setReview(null); setPreview(null);
      try {
        if (mode === 'demo') { setData(demo(day)); return; }
        const response = await fetch(`${getApiBaseUrl()}/api/calendar/day?site_id=VAD-PLANT-01&date=${day}`, {
          credentials: 'include', headers: { Accept: 'application/json' }, signal: controller.signal,
        });
        if (!response.ok) throw new Error(`Calendar service returned ${response.status}. An authenticated calendar backend is required.`);
        const result = parseCalendar(await response.json());
        if (result.date !== day || !Array.isArray(result.activities) || !result.window || !result.integrations) throw new Error('Invalid calendar response.');
        if (!controller.signal.aborted) setData(result);
      } catch (e) { if (!active) return; if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Unable to load calendar.'); else setError('Calendar request timed out. Retry the service.'); }
      finally { if (active) setLoading(false); }
    }
    void load();
    return () => { active = false; clearTimeout(timer); controller.abort(); };
  }, [day, mode, retry]);
  const time = (value: string) => new Intl.DateTimeFormat('en-IN', { timeZone: data?.site.timezone ?? 'Asia/Kolkata', hour: 'numeric', minute: '2-digit' }).format(new Date(value));
  const range = (start: string, end: string) => `${time(start)} – ${time(end)}`;
  const geometry = (start: string, end: string) => timelineGeometry(start, end, data!.window);
  function navigate(offset: number) {
    const next = new Date(`${day}T12:00:00Z`); next.setUTCDate(next.getUTCDate() + offset); setDay(next.toISOString().slice(0, 10));
  }
  const affected = data?.activities.filter(hasOutdoorWarning) ?? [];
  return <main className="calendar-app"><div className="calendar-layout"><section className="schedule-panel">
    <header className="day-header"><div><h1>Day view · {data?.site.name ?? calendarFixture.site.name}</h1><div className="day-navigation"><p>{new Intl.DateTimeFormat('en-IN',{dateStyle:'full',timeZone:'UTC'}).format(new Date(`${day}T12:00:00Z`))}</p><button aria-label="Previous day" onClick={() => navigate(-1)}>‹</button><button onClick={() => setDay(new Intl.DateTimeFormat('en-CA',{timeZone:data?.site.timezone ?? calendarFixture.site.timezone}).format(new Date()))}>Today</button><button aria-label="Next day" onClick={() => navigate(1)}>›</button><label className="date-picker-label"><span className="sr-only">Selected date</span><input aria-label="Selected date" type="date" value={day} onChange={e => {if(e.target.value) setDay(e.target.value);}} /></label></div></div><div className="site-meta"><span>♧ {data?.employees.length ?? '—'} employees</span><label><span className="sr-only">Selected site</span><select aria-label="Selected site"><option>{data?.site.name ?? calendarFixture.site.name}</option></select></label></div></header>
    {loading && <div className="cal-state" role="status">Loading employee schedules and climate context…</div>}
    {error && <div className="cal-state" role="alert"><h2>Calendar unavailable</h2><p>{error}</p><button onClick={() => setRetry(retry+1)}>Retry</button><button onClick={() => setMode('demo')}>Use demo fixtures</button></div>}
    {data && !loading && <><ClimateWarningBanner compact calendar={data} onSelectActivity={selectActivity} />
        {!data.activities.length && <p className="cal-state">No activities scheduled for this day.</p>}
        <p className="scroll-hint">Scroll horizontally to explore the day. Select any activity for full details.</p><div className="timeline-scroll" tabIndex={0} role="region" aria-label="Employee day calendar, horizontally scrollable"><div className="timeline"><div className="timeline-head"><div>EMPLOYEE</div><div className="hour-axis">{timelineTicks(data.window).map(tick => <span key={tick.at} style={{left: `${tick.position}%`}}>{time(tick.at)}</span>)}</div></div>
          {data.employees.map(employee => { const layout = layoutEmployeeEvents(data.activities.filter(a => a.employee_id === employee.id),data.window); const proposed=preview?.start && preview.end && (preview.approval ?? 'pending')==='pending' && data.activities.some(a=>a.id===preview.activity_id && a.employee_id===employee.id) ? preview : null; return <div className="employee-row" key={employee.id} style={{minHeight: `${(layout.laneCount + (proposed ? 1 : 0)) * 88 + 12}px`}}><div className="employee-label"><span className="avatar">{employee.name.split(' ').map(n => n[0]).join('')}</span><div><strong>{employee.name}</strong><small>{employee.role}{employee.team ? ` · ${employee.team}` : ''}</small></div></div><div className="employee-track" style={{backgroundSize: `${3600000 / (Date.parse(data.window.end)-Date.parse(data.window.start)) * 100}% 100%`}}>{data.warnings.map(w => <div className="warning-band" key={w.id} style={geometry(w.start, w.end)} title={`${w.title}: ${range(w.start, w.end)}`} />)}{layout.items.map(({event: a,lane}) => { const state = activityWarningPresentation(a); return <button key={a.id} ref={element => {if(element) activityElements.current.set(a.id,element); else activityElements.current.delete(a.id);}} aria-pressed={review === a.id} className={`activity ${a.kind} ${state.tone} ${review === a.id ? 'selected-activity' : ''}`} aria-label={`${a.title} · ${range(a.start,a.end)} · ${a.kind} · ${state.label} · ${a.reason}`} style={{...geometry(a.start, a.end), top: `${10 + lane * 88}px`}} title={`${a.title} · ${range(a.start, a.end)} · ${a.location ?? 'Unknown location'} · ${a.reason}`} onClick={() => selectActivity(a.id)}><span className="activity-symbol" aria-hidden="true">{a.kind==='outdoor' ? '☀' : a.kind==='indoor' ? '⌂' : '?'}</span><strong>{a.title} · {a.kind}</strong><span className="activity-time">{range(a.start, a.end)}</span><span className="activity-location">{a.location ?? 'Unknown location'}</span>{state.icon && <b className="activity-flag">{state.icon} {state.label}</b>}</button>; })}{proposed?.start && proposed.end && <ProposalTimelinePreview start={proposed.start} end={proposed.end} window={data.window} timezone={data.site.timezone} top={10+layout.laneCount*88} />}</div></div>; })}
        </div></div>{preview?.start && preview.end && <p className="proposal-preview-notice" role="status">Proposed preview: {range(preview.start,preview.end)} · {data.site.timezone} · Not applied. The current event remains unchanged until backend-confirmed approval.<button onClick={()=>setPreview(null)}>Hide preview</button></p>}<div className="cal-legend"><span>▧ Climate warning window</span><span>☀ Outdoor</span><span>▣ Indoor</span><span>? Unknown / needs review</span><span>▱ Proposed preview · not applied</span></div>
        {review && <div className="event-detail"><button className="close-detail" onClick={() => setReview(null)}>Close</button>{data.activities.filter(a => a.id === review).map(a => <div key={a.id}><h3>{a.title}</h3><p>{range(a.start, a.end)} · {a.kind} · {a.location ?? 'Unknown location'} · Site: {a.site_id ?? 'Unknown site'}</p><p>{a.reason}</p><details><summary>Event notes</summary><pre className="event-notes">{a.notes || 'No event notes'}</pre></details><small>Warning references: {a.warning_ids.join(', ') || 'None'} · Forecast: {forecastPresentation(data.weather).label}</small></div>)}</div>}
          </>}
    <details className="workspace-settings"><summary>Workspace settings · {mode==='demo' ? 'Demo fixtures' : 'Authenticated backend'} · {data?.site.timezone ?? calendarFixture.site.timezone}</summary><label>Data source<select value={mode} onChange={e=>setMode(e.target.value)}><option value="demo">Deterministic demo</option><option value="live">Authenticated backend</option></select></label><p>Demo workspace · simulated forecast and calendar. Illustrative policies require site confirmation. Only explicit approval can apply an isolated demo change.</p></details>
    </section>{data && !loading && <ClimateAgentPanel demoPolicies={mode==='demo' || data.mode==='fixture' || data.weather.status==='fixture'} key={`${mode}:${data.site.id}:${day}`} day={day} mode={mode} siteId={data.site.id} timezone={data.site.timezone} suggestions={data.suggestions} activities={data.activities} employees={data.employees} affectedCount={affected.length} onCalendar={acceptCalendar} onPreviewProposal={setPreview} warnings={data.warnings} selectedActivity={review} onSelectActivity={selectActivity} />}</div></main>;
}
