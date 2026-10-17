import { PolicyExplanation } from './PolicyExplanation.js';
import type { Calendar } from '../types/calendar';
import { hasOutdoorWarning, activityWarningPresentation } from '../utils/climatePresentation.js';

export function FlaggedActivities({calendar, selectedActivity, onSelect, demo=false}: {calendar: Pick<Calendar,'activities'|'employees'|'site'|'warnings'>;selectedActivity:string|null;onSelect:(id:string)=>void;demo?:boolean}) {
  const flagged=calendar.activities.filter(a=>hasOutdoorWarning(a)||a.status==='needs-review'||a.kind==='unknown'||!a.location?.trim()||a.policy_context?.status==='unknown'||a.policy_context?.status==='needs-review');
  const time=(at:string)=>new Intl.DateTimeFormat('en-IN',{timeZone:calendar.site.timezone,hour:'numeric',minute:'2-digit'}).format(new Date(at));
  return <details className="all-flagged"><summary>View more · all flagged activities ({flagged.length})</summary>
    {!flagged.length && <p>No flagged activities reported.</p>}
    <ul>{flagged.map(a=><li key={a.id}><button aria-pressed={selectedActivity===a.id} onClick={()=>onSelect(a.id)}><strong>{a.title}</strong><span>{calendar.employees.find(e=>e.id===a.employee_id)?.name} · {time(a.start)} – {time(a.end)}</span><span>{activityWarningPresentation(a).label} · {a.kind} · {a.location ?? 'Unknown location'}</span><small>{a.reason}</small></button><PolicyExplanation activity={a} warnings={calendar.warnings} demo={demo} /></li>)}</ul>
  </details>;
}
