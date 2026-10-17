export type ActivityKind = 'indoor' | 'outdoor' | 'unknown';
export type ActivityStatus = 'affected' | 'needs-review' | 'unflagged';
export interface PolicyContext {
  status: 'configured' | 'unknown' | 'needs-review';
  name: string | null;
  version?: string | null;
  source: string | null;
  reason: string | null;
  illustrative: boolean;
  applicable_work_rest_rules?: {work_minutes:number;rest_minutes:number;cooling_required:boolean;reason?:string}[];
}
export interface CalendarActivity {
  id: string;
  employee_id: string;
  title: string;
  start: string;
  end: string;
  site_id?: string | null;
  location: string | null;
  kind: ActivityKind;
  status: ActivityStatus;
  reason: string;
  warning_ids: string[];
  policy_context?: PolicyContext | null;
  notes?: string;
  version?: number;
}
export interface CalendarWarning {
  id: string;
  title: string;
  severity: string;
  start: string;
  end: string;
  measure: string;
  policy: string;
}
export interface CalendarSuggestion {
  id: string;
  activity_id: string;
  start: string | null;
  end: string | null;
  validation: string;
  rationale: string;
  warning_ids?: string[];
  policy?: string;
  approval?: string;
}
export interface Calendar {
  mode?: 'fixture';
  date: string;
  site: {id: string; name: string; timezone: string};
  window: {start: string; end: string};
  employees: {id: string; name: string; role: string; team?:string|null}[];
  activities: CalendarActivity[];
  warnings: CalendarWarning[];
  suggestions: CalendarSuggestion[];
  weather: {status: string; source: string; updated_at: string | null};
  integrations: {agent: string; mcp: string; calendar: string};
}

/** Validate the fixture and schedule response at the UI boundary, never infer risk. */
export function parseCalendar(value: unknown): Calendar {
  const record = (v: unknown): Record<string, unknown> => {
    if (typeof v !== 'object' || v === null || Array.isArray(v)) throw new Error('Invalid calendar object.');
    return v as Record<string, unknown>;
  };
  const strings = (v: Record<string,unknown>, keys: string[]) => {
    if (keys.some(key => typeof v[key] !== 'string')) throw new Error('Invalid calendar text field.');
  };
  const array = (v: unknown): unknown[] => {if (!Array.isArray(v)) throw new Error('Invalid calendar list.'); return v;};
  const interval = (v: Record<string,unknown>) => {
    strings(v,['start','end']);
    if (![v.start,v.end].every(t => /(?:Z|[+-]\d{2}:\d{2})$/.test(t as string) && Number.isFinite(Date.parse(t as string))) || Date.parse(v.end as string) <= Date.parse(v.start as string)) throw new Error('Invalid calendar time interval.');
  };
  const data = record(value);
  strings(data,['date']);
  const site = record(data.site); strings(site,['id','name','timezone']);
  new Intl.DateTimeFormat('en', {timeZone: site.timezone as string});
  interval(record(data.window));
  array(data.employees).forEach(v => strings(record(v),['id','name','role']));
  array(data.activities).forEach(v => {
    const a = record(v); strings(a,['id','employee_id','title','kind','status','reason']); interval(a);
    if (a.policy_context != null) {
      const p = record(a.policy_context);
      if (!['configured','unknown','needs-review'].includes(p.status as string) || typeof p.illustrative !== 'boolean' || ['name','source','reason'].some(key => p[key] !== null && typeof p[key] !== 'string') || (p.version != null && typeof p.version !== 'string')) throw new Error('Invalid policy explanation.');
      if (p.applicable_work_rest_rules !== undefined) array(p.applicable_work_rest_rules).forEach(value => {
        const rule=record(value);
        if (![rule.work_minutes,rule.rest_minutes].every(n=>typeof n==='number' && Number.isInteger(n) && n>=0) || typeof rule.cooling_required!=='boolean' || (rule.reason!==undefined && typeof rule.reason!=='string')) throw new Error('Invalid work/rest requirement.');
      });
    }
    if (!['indoor','outdoor','unknown'].includes(a.kind as string) || !['affected','needs-review','unflagged'].includes(a.status as string) || (a.location !== null && typeof a.location !== 'string') || !array(a.warning_ids).every(id => typeof id === 'string')) throw new Error('Invalid calendar activity.');
  });
  array(data.warnings).forEach(v => {const w = record(v); strings(w,['id','title','severity','measure','policy']); interval(w);});
  array(data.suggestions).forEach(v => {const s = record(v); strings(s,['id','activity_id','validation','rationale']); if (s.start !== null || s.end !== null) interval(s);});
  const weather = record(data.weather); strings(weather,['status','source']);
  if (weather.updated_at !== null && (typeof weather.updated_at !== 'string' || !Number.isFinite(Date.parse(weather.updated_at)))) throw new Error('Invalid forecast timestamp.');
  strings(record(data.integrations),['agent','mcp','calendar']);
  return value as Calendar;
}
