import { timelineGeometry } from '../utils/timeline.js';

/** Display only: does not update the calendar event or imply approval. */
export function ProposalTimelinePreview({start,end,window,timezone,top,validated=true}:{start:string;end:string;window:{start:string;end:string};timezone:string;top:number;validated?:boolean}) {
  const time=(at:string)=>new Intl.DateTimeFormat('en-IN',{timeZone:timezone,hour:'numeric',minute:'2-digit'}).format(new Date(at));
  const label=validated ? `Proposed ${time(start)} – ${time(end)} · not applied · supervisor approval required` : `Requested time ${time(start)} – ${time(end)} · failed validation · not applied`;
  return <div className={`proposed-activity ${validated ? '' : 'unvalidated'}`} role="img" aria-label={label} title={label} style={{...timelineGeometry(start,end,window),top:`${top}px`}}><span>{validated ? 'Proposed · not applied' : 'Requested · failed validation'}</span><strong>{time(start)} – {time(end)}</strong></div>;
}
