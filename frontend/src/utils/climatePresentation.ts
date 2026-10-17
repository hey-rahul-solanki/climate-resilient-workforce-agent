import type { Calendar, CalendarActivity } from '../types/calendar';

/** Render backend decisions only: no browser interval/threshold or safety evaluation. */
export function hasOutdoorWarning(activity: CalendarActivity): boolean {
  return activity.kind === 'outdoor' && (activity.status === 'affected' || activity.warning_ids.length > 0);
}

export function activityWarningPresentation(activity: CalendarActivity) {
  const affected = hasOutdoorWarning(activity);
  const review = activity.status === 'needs-review' || activity.kind === 'unknown' || !activity.location?.trim() || activity.policy_context?.status === 'unknown' || activity.policy_context?.status === 'needs-review';
  return {
    affected,
    icon: affected ? '⚠' : review ? '?' : '',
    label: [affected ? 'Climate warning' : '', review ? 'Needs review' : ''].filter(Boolean).join(' · ') || 'No weather flag',
    // An inconsistent indoor status must not receive weather-only affected styling.
    tone: affected && !review ? 'affected' : review ? 'needs-review' : 'unflagged',
  };
}

export function forecastPresentation(weather: Calendar['weather']) {
  const labels: Record<string,string> = {
    stale:'Stale forecast — needs review', incomplete:'Incomplete forecast — needs review',
    unavailable:'Forecast unavailable — needs review', missing:'Forecast unavailable — needs review',
    unknown:'Forecast unknown — needs review', 'needs-review':'Forecast requires review — data may be missing, stale or incomplete',
  };
  if (labels[weather.status]) return {label:labels[weather.status], needsReview:true};
  if (!['current','fixture'].includes(weather.status)) return {label:'Forecast status unknown — needs review',needsReview:true};
  if (!weather.updated_at) return {label:'Forecast update time unavailable — needs review',needsReview:true};
  return {label:weather.status === 'fixture' ? 'Illustrative fixture forecast' : 'Current forecast',needsReview:false};
}
