import type { CalendarActivity, CalendarWarning } from '../types/calendar';

/** Display backend-supplied applicability only. Never select work/rest bands here. */
export function PolicyExplanation({activity,warnings,demo=false}:{activity:CalendarActivity;warnings:CalendarWarning[];demo?:boolean}) {
  const policy=activity.policy_context;
  const references=[...new Set(warnings.filter(w=>activity.warning_ids.includes(w.id)).map(w=>w.policy).filter(Boolean))];
  const unknownActivity=activity.kind==='unknown' || !activity.location?.trim();
  const unknownPolicy=!policy || policy.status!=='configured' || !policy.name?.trim() || !policy.source?.trim();
  return <section className="policy-explanation" aria-label={`Policy explanation for ${activity.title}`}>
    <h5>Policy explanation</h5>
    {(demo || policy?.illustrative) && <p><strong>Illustrative demo policy · requires site confirmation; not official guidance.</strong></p>}
    {(unknownActivity || unknownPolicy || activity.status==='needs-review') && <p className="policy-review"><span aria-hidden="true">⚠ </span><strong>Needs review</strong>{unknownActivity ? ' · activity type or work location is unknown.' : unknownPolicy ? ' · policy applicability or source is unavailable.' : ' · backend requires review.'}</p>}
    <p>Work location: {activity.location?.trim() || 'Unknown location'} · Type: {activity.kind}</p>
    <p>Reason: {policy?.reason || activity.reason || 'Policy reason unavailable — needs review.'}</p>
    <p>Policy: {policy?.name || references.join('; ') || 'Unknown policy — needs review'}{policy?.version ? ` · version ${policy.version}` : ''}</p>
    <p>Source: {policy?.source || 'Not supplied — needs review'}</p>
    <h5>Applicable work / rest requirements</h5>
    {policy?.applicable_work_rest_rules?.length ? <ul>{policy.applicable_work_rest_rules.map((rule,i)=><li key={i}>Work: {rule.work_minutes} minutes · Rest: {rule.rest_minutes} minutes · Cooling: {rule.cooling_required ? 'required' : 'not required by this supplied rule'}{rule.reason ? ` · ${rule.reason}` : ''}</li>)}</ul> : <p>No applicable work/rest requirement supplied. This does not mean breaks or cooling are unnecessary.</p>}
    <p>Requirements above are backend-supplied context, not confirmation that a schedule satisfies them.</p>
  </section>;
}
