import { timelineGeometry } from '../utils/timeline.js';

/** Display only: does not update the calendar event or imply approval. */
export function ProposalTimelinePreview({start,end,window,timezone,top}:{start:string;end:string;window:{start:string;end:string};timezone:string;top:number}) {
  const time=(at:string)=>new Intl.DateTimeFormat('en-IN',{timeZone:timezone,hour:'numeric',minute:'2-digit'}).format(new Date(at));
  const label=`Proposed ${time(start)} – ${time(end)} · not applied · supervisor approval required`;
  return <div className="proposed-activity" role="img" aria-label={label} title={label} style={{...timelineGeometry(start,end,window),top:`${top}px`}}><span>Proposed · not applied</span><strong>{time(start)} – {time(end)}</strong></div>;
}
