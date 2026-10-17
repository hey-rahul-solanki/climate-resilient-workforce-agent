import type { Calendar } from '../types/calendar';
import { forecastPresentation, hasOutdoorWarning } from '../utils/climatePresentation.js';

export function ClimateWarningBanner({calendar, onSelectActivity, compact=false}: {calendar: Calendar; onSelectActivity: (id:string) => void;compact?:boolean}) {
  const affected = calendar.activities.filter(hasOutdoorWarning);
  const forecast = forecastPresentation(calendar.weather);
  const dateTime = (value: string) => new Intl.DateTimeFormat('en-IN',{timeZone:calendar.site.timezone,dateStyle:'medium',timeStyle:'short'}).format(new Date(value));
  const range = (start:string,end:string) => `${dateTime(start)} – ${dateTime(end)}`;
  if (compact) return <section className="compact-climate-banner" aria-label="Climate warning summary"><span className="warning-symbol" aria-hidden="true">⚠</span><div className="compact-warning-content">
    {calendar.warnings.length ? calendar.warnings.map(w=><div className="compact-warning-row" key={w.id}><strong>{w.severity} · {w.title}</strong><span>{range(w.start,w.end)}</span><span>{w.measure}</span><span>• {affected.filter(a=>a.warning_ids.includes(w.id)).length} outdoor activities overlap</span></div>) : <strong>{forecast.needsReview ? forecast.label : 'No warning intervals reported'}</strong>}
    <small>{forecast.label} · Source: {calendar.weather.source || 'Unavailable'} · Updated: {calendar.weather.updated_at ? dateTime(calendar.weather.updated_at) : 'Unavailable'} · {calendar.activities.filter(a=>a.status==='needs-review'||a.kind==='unknown').length} need review</small>
    <details><summary>Warning evidence & affected activities</summary>{calendar.warnings.map(w=><div key={w.id}><p>{w.policy}</p>{affected.filter(a=>a.warning_ids.includes(w.id)).map(a=><button key={a.id} onClick={()=>onSelectActivity(a.id)}>{a.title} · {calendar.employees.find(e=>e.id===a.employee_id)?.name}</button>)}</div>)}</details>
    </div>{(calendar.mode==='fixture'||calendar.weather.status==='fixture') && <span className="forecast-badge">DEMO FORECAST</span>}</section>;
  return <section className={`climate-banner ${forecast.needsReview ? 'forecast-review' : ''}`} aria-labelledby="climate-summary-title"><span className="warning-symbol" aria-hidden="true">△</span><div>
    <h2 id="climate-summary-title">{calendar.warnings.length ? 'Climate warnings' : forecast.needsReview ? 'Climate conditions need review' : 'No warning intervals reported'}</h2>
    <p aria-live="polite">{affected.length} outdoor activities affected · {calendar.activities.filter(a => a.status === 'needs-review' || a.kind === 'unknown').length} need review</p>
    <p className="forecast-state"><strong>{forecast.label}</strong></p>
    <small>Source: {calendar.weather.source || 'Unavailable'} · Updated: {calendar.weather.updated_at ? dateTime(calendar.weather.updated_at) : 'Unavailable'} · {calendar.site.timezone}</small>
    {calendar.warnings.map(warning => {
      const matches = affected.filter(a => a.warning_ids.includes(warning.id));
      return <div className="warning-summary" key={warning.id}><p><strong>{warning.severity} · {warning.title}</strong> · {range(warning.start,warning.end)} · {warning.measure}</p><p>{warning.policy} · {matches.length} affected activities</p>
        <details><summary>Show all matching activities</summary><ul>{matches.map(a => <li key={a.id}><button onClick={() => onSelectActivity(a.id)}>{a.title} · {calendar.employees.find(e => e.id === a.employee_id)?.name} · {range(a.start,a.end)}{a.status === 'needs-review' ? ' · Needs review' : ''}</button></li>)}</ul></details>
      </div>;
    })}
    {forecast.needsReview && <p>Warning matches may be incomplete. Review forecast and site policy before planning outdoor work.</p>}
  </div></section>;
}
