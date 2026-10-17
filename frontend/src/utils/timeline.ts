export interface TimedItem {id: string; start: string; end: string}

/** Display geometry only. Policy and warning matches remain backend-owned. */
export function timelineGeometry(start: string, end: string, window: {start: string; end: string}) {
  const from = Date.parse(window.start), duration = Date.parse(window.end) - from;
  const left = Math.max(0, Math.min(100, (Date.parse(start) - from) / duration * 100));
  const right = Math.max(0, Math.min(100, (Date.parse(end) - from) / duration * 100));
  return {left: `${left}%`, width: `${Math.max(0,right-left)}%`};
}

/** Allocate the lowest available lane. Touching intervals can share one lane. */
export function layoutEmployeeEvents<T extends TimedItem>(events: T[], window: {start: string; end: string}) {
  const ends: number[] = [];
  const visible = events.filter(event => Date.parse(event.start) < Date.parse(window.end) && Date.parse(event.end) > Date.parse(window.start))
    .sort((a,b) => Date.parse(a.start)-Date.parse(b.start) || Date.parse(a.end)-Date.parse(b.end) || a.id.localeCompare(b.id));
  const items = visible.map(event => {
    let lane = ends.findIndex(end => end <= Date.parse(event.start));
    if (lane < 0) lane = ends.length;
    ends[lane] = Date.parse(event.end);
    return {event, lane};
  });
  return {items, laneCount: Math.max(1,ends.length)};
}

export function timelineTicks(window: {start: string; end: string}) {
  const start=Date.parse(window.start), end=Date.parse(window.end);
  const ticks=[];
  for (let at=start; at<end; at+=3600000) ticks.push({at:new Date(at).toISOString(), position:(at-start)/(end-start)*100});
  ticks.push({at:new Date(end).toISOString(),position:100});
  return ticks;
}
