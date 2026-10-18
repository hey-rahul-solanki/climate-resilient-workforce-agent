import test, {after} from 'node:test';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import assert from 'node:assert/strict';
import {mkdtempSync, writeFileSync, readFileSync, rmSync, symlinkSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';

// Compile the real TypeScript helpers; works with the Docker Node 20 baseline.
const output = mkdtempSync(join(tmpdir(),'workforce-calendar-test-'));
after(() => rmSync(output,{recursive:true,force:true}));
execFileSync(process.execPath,[resolve('node_modules/typescript/bin/tsc'),'src/utils/timeline.ts','src/types/calendar.ts','src/utils/climatePresentation.ts','src/components/ClimateWarningBanner.tsx','src/components/AgentSuggestions.tsx','src/components/FlaggedActivities.tsx','src/components/ClimateAgentPanel.tsx','src/components/ProposalTimelinePreview.tsx','--jsx','react-jsx','--moduleResolution','bundler','--ignoreConfig','--outDir',output,'--target','ES2023','--module','esnext','--skipLibCheck'],{stdio:'pipe'});
writeFileSync(join(output,'package.json'),'{"type":"module"}');
symlinkSync(resolve('node_modules'),join(output,'node_modules'),'dir');
const {timelineGeometry,layoutEmployeeEvents,timelineTicks} = await import(pathToFileURL(join(output,'utils/timeline.js')));
const {parseCalendar} = await import(pathToFileURL(join(output,'types/calendar.js')));
const window = {start:'2026-10-17T06:00:00+05:30',end:'2026-10-17T18:00:00+05:30'};
const at = hour => `2026-10-17T${hour}:00+05:30`;
const item = (id,start,end) => ({id,start:at(start),end:at(end)});

const {hasOutdoorWarning,activityWarningPresentation,forecastPresentation}=await import(pathToFileURL(join(output,'utils/climatePresentation.js')));
const {ClimateWarningBanner}=await import(pathToFileURL(join(output,'components/ClimateWarningBanner.js')));
const renderBanner=calendar=>renderToStaticMarkup(createElement(ClimateWarningBanner,{calendar,onSelectActivity:()=>{}}));


const {AgentSuggestions}=await import(pathToFileURL(join(output,'components/AgentSuggestions.js')));
const {FlaggedActivities}=await import(pathToFileURL(join(output,'components/FlaggedActivities.js')));

// Exercise the real panel markup without creating an authenticated session.
const panelPath=join(output,'components/ClimateAgentPanel.js');
writeFileSync(panelPath,readFileSync(panelPath,'utf8').replaceAll("'./AgentSuggestions'", "'./AgentSuggestions.js'").replaceAll("'./FlaggedActivities'", "'./FlaggedActivities.js'").replaceAll("'./ProposalReview'", "'./ProposalReview.js'"));
const {ClimateAgentPanel}=await import(pathToFileURL(panelPath));

const {ProposalReview}=await import(pathToFileURL(join(output,'components/ProposalReview.js')));

const {PolicyExplanation}=await import(pathToFileURL(join(output,'components/PolicyExplanation.js')));

const {ProposalTimelinePreview}=await import(pathToFileURL(join(output,'components/ProposalTimelinePreview.js')));

test('duration geometry is proportional and uses absolute timestamps across timezone offsets',()=>{
  const geometry=timelineGeometry(at('08:00'),at('12:00'),window);
  assert.ok(Math.abs(parseFloat(geometry.left)-100/6)<1e-10);
  assert.ok(Math.abs(parseFloat(geometry.width)-100/3)<1e-10);
  assert.deepEqual(timelineGeometry('2026-10-17T02:30:00Z','2026-10-17T06:30:00Z',window),geometry);
});
test('warning and activity boundaries share the exact geometry function',()=>{
  const warning=timelineGeometry(at('12:00'),at('16:00'),window);
  assert.equal(warning.left,'50%');
  assert.ok(Math.abs(parseFloat(warning.width)-100/3)<1e-10);
});
test('short events retain their duration; out-of-window geometry is clipped',()=>{
  assert.ok(Math.abs(parseFloat(timelineGeometry(at('08:00'),at('08:15'),window).width)-100/48)<1e-10);
  assert.equal(timelineGeometry(at('05:00'),at('07:00'),window).left,'0%');
  assert.ok(Math.abs(parseFloat(timelineGeometry(at('05:00'),at('07:00'),window).width)-100/12)<1e-10);
  assert.equal(timelineGeometry(at('19:00'),at('20:00'),window).width,'0%');
});
test('overlapping and nested events receive distinct lanes; touching intervals reuse lanes',()=>{
  const input=[item('b','09:00','10:00'),item('a','08:00','12:00'),item('c','09:00','11:00'),item('d','12:00','13:00')];
  const result=layoutEmployeeEvents(input,window);
  assert.equal(result.laneCount,3);
  const lanes=Object.fromEntries(result.items.map(i=>[i.event.id,i.lane]));
  assert.equal(lanes.a,lanes.d);
  assert.equal(new Set([lanes.a,lanes.b,lanes.c]).size,3);
  assert.equal(input[0].id,'b'); // Layout does not mutate service-owned data.
});
test('simultaneous events remain accessible and lane allocation is deterministic',()=>{
  const input=[item('b','08:00','09:00'),item('a','08:00','09:00')];
  assert.deepEqual(layoutEmployeeEvents(input,window),layoutEmployeeEvents([...input].reverse(),window));
  assert.equal(layoutEmployeeEvents(input,window).laneCount,2);
});
test('empty employees retain a row; events outside the visible window are omitted',()=>{
  assert.deepEqual(layoutEmployeeEvents([],window),{items:[],laneCount:1});
  const result=layoutEmployeeEvents([item('before','05:00','06:00'),item('after','18:00','19:00'),item('partial','05:30','06:30')],window);
  assert.deepEqual(result.items.map(i=>i.event.id),['partial']);
});
test('ticks derive from the window, including a non-hour end',()=>{
  const ticks=timelineTicks({start:at('06:00'),end:at('08:30')});
  assert.equal(ticks.length,4);
  assert.deepEqual(ticks.map(t=>t.position),[0,40,80,100]);
});
const fixture=JSON.parse(readFileSync('src/data/calendarDemo.json','utf8'));
test('bundled fixture satisfies the explicit calendar contract',()=>{
  assert.equal(parseCalendar(fixture),fixture);
  assert.equal(parseCalendar({...fixture,employees:[],activities:[],warnings:[],suggestions:[]}).activities.length,0);
});
test('invalid responses fail at the boundary so the page can render its error state',()=>{
  assert.throws(()=>parseCalendar({}),/Invalid/);
  assert.throws(()=>parseCalendar({...fixture,site:{...fixture.site,timezone:'invalid/timezone'}}));
  assert.throws(()=>parseCalendar({...fixture,activities:[{...fixture.activities[0],kind:'safe'}]}),/Invalid calendar activity/);
  assert.throws(()=>parseCalendar({...fixture,activities:[{...fixture.activities[0],start:'2026-10-17T08:00:00'}]}),/Invalid calendar time/);
});


test('all backend-flagged outdoor activities are counted independently of suggestions',()=>{
  const activities=fixture.activities.map(a=>a.id==='event-0'?{...a,status:'affected',warning_ids:[]}:a);
  assert.equal(activities.filter(hasOutdoorWarning).length,4);
  assert.equal(activityWarningPresentation(activities[0]).icon,'⚠');
  const html=renderBanner({...fixture,activities,suggestions:[]});
  assert.match(html,/4 outdoor activities affected/);
});
test('warning matches remain visible when backend additionally requires review',()=>{
  const activity={...fixture.activities.find(a=>a.status==='affected'),status:'needs-review'};
  assert.equal(activityWarningPresentation(activity).label,'Climate warning · Needs review');
  assert.equal(activityWarningPresentation(activity).tone,'needs-review');
});
test('indoor activities do not acquire weather-only warning styling from active warnings',()=>{
  const indoor={...fixture.activities.find(a=>a.kind==='indoor'),status:'affected',warning_ids:fixture.warnings.map(w=>w.id)};
  assert.equal(hasOutdoorWarning(indoor),false);
  assert.equal(activityWarningPresentation(indoor).tone,'unflagged');
  assert.equal(activityWarningPresentation(indoor).label,'No weather flag');
});
test('banner renders typed severity, full site-local intervals, measure, source and update timestamp',()=>{
  const html=renderBanner(fixture);
  assert.ok(html.includes(fixture.warnings[0].severity));
  assert.ok(html.includes(fixture.warnings[0].measure.replaceAll('&','&amp;')));
  assert.ok(html.includes(fixture.weather.source));
  assert.match(html,/Updated:/);
  assert.match(html,/Asia\/Kolkata/);
  assert.match(html,/12:00/);
  assert.match(html,/4:00/);
  assert.match(html,/3 outdoor activities affected/);
});
test('multiple warning counts are distinct per warning; total counts each activity once',()=>{
  const first=fixture.warnings[0];
  const warnings=[first,{...first,id:'second-warning',severity:'Critical',title:'Second warning'}];
  const activities=fixture.activities.map(a=>a.id==='event-1'?{...a,warning_ids:[first.id,'second-warning']}:a);
  const html=renderBanner({...fixture,warnings,activities});
  assert.match(html,/3 outdoor activities affected/);
  assert.match(html,/Critical/);
  assert.match(html,/1 affected activities/);
});
for (const status of ['stale','incomplete','unavailable','missing','unknown','needs-review','unrecognized','safe']) {
  test(`forecast ${status} explicitly needs review even without warning intervals`,()=>{
    const weather={...fixture.weather,status};
    const presentation=forecastPresentation(weather);
    assert.equal(presentation.needsReview,true);
    assert.doesNotMatch(presentation.label,/safe/i);
    const html=renderBanner({...fixture,warnings:[],weather});
    assert.match(html,/needs review|requires review/);
    assert.match(html,/Climate conditions need review/);
    assert.doesNotMatch(html,/No warning intervals reported/);
  });
}
test('missing forecast update timestamp is explicit instead of current or safe',()=>{
  const html=renderBanner({...fixture,weather:{...fixture.weather,status:'current',updated_at:null}});
  assert.match(html,/Forecast update time unavailable/);
  assert.match(html,/Updated: Unavailable/);
});


function suggestionProps(overrides={}) {
  return {suggestions:fixture.suggestions,activities:fixture.activities,employees:fixture.employees,warnings:fixture.warnings,timezone:fixture.site.timezone,selectedActivity:null,loading:false,error:'',onRetry:()=>{},onSelect:()=>{},...overrides};
}
function findButtons(node,result=[]) {
  if(Array.isArray(node)) node.forEach(child=>findButtons(child,result));
  else if(node && typeof node==='object' && node.props) {
    if(node.type==='button') result.push(node);
    findButtons(node.props.children,result);
  }
  return result;
}
test('suggestions render employee, current/proposed times, source warning, rationale and validation',()=>{
  const html=renderToStaticMarkup(createElement(AgentSuggestions,suggestionProps()));
  assert.match(html,/Panel maintenance/);
  assert.match(html,/Aarav Patel/);
  assert.match(html,/Current at proposal:/);
  assert.match(html,/Proposed:/);
  assert.match(html,/demo-validated/);
  assert.match(html,/Heat warning/);
  assert.match(html,/Reference:/);
  assert.match(html,/not safety clearance/);
  assert.ok(html.includes(fixture.suggestions[0].rationale));
});
test('selection calls calendar/review callback with structured suggestion and reflects highlight',()=>{
  let selected;
  const first=fixture.suggestions[0];
  const props=suggestionProps({selectedActivity:first.activity_id,onSelect:s=>{selected=s;}});
  const buttons=findButtons(AgentSuggestions(props));
  buttons.find(b=>b.props.children==='Select event & review').props.onClick();
  assert.equal(selected.id,first.id);
  const html=renderToStaticMarkup(createElement(AgentSuggestions,props));
  assert.match(html,/selected-suggestion/);
  assert.match(html,/aria-current="true"/);
});
test('empty response presents explicit empty state without stale suggestions',()=>{
  const html=renderToStaticMarkup(createElement(AgentSuggestions,suggestionProps({suggestions:[]})));
  assert.match(html,/No suggested schedule updates/);
  assert.doesNotMatch(html,/Panel maintenance/);
});
test('loading and error states remain explicit with disabled selection and retry',()=>{
  const loading=AgentSuggestions(suggestionProps({loading:true}));
  assert.ok(findButtons(loading).every(b=>b.props.disabled));
  assert.match(renderToStaticMarkup(loading),/Loading or validating/);
  let retried=false;
  const error=AgentSuggestions(suggestionProps({suggestions:[],error:'Agent API unavailable',onRetry:()=>{retried=true;}}));
  findButtons(error).find(b=>b.props.children==='Retry agent request').props.onClick();
  assert.equal(retried,true);
  assert.match(renderToStaticMarkup(error),/role="alert"/);
});
test('infeasible and needs-review suggestions never display invented proposed times',()=>{
  const original=fixture.suggestions[0];
  const html=renderToStaticMarkup(createElement(AgentSuggestions,suggestionProps({suggestions:[{...original,start:null,end:null,validation:'no-feasible-slot',rationale:'No slot satisfies the requested window.'}]})));
  assert.match(html,/No feasible alternative/);
  assert.doesNotMatch(html,/Proposed:/);
  const unknown=renderToStaticMarkup(createElement(AgentSuggestions,suggestionProps({suggestions:[{...original,start:null,end:null,validation:'needs-review'}]})));
  assert.match(unknown,/No proposed time — needs review/);
});
test('View more exposes every flagged activity and unknown needs-review, without relying on suggestions',()=>{
  let selected;
  const props={calendar:fixture,selectedActivity:'event-5',onSelect:id=>{selected=id;}};
  const tree=FlaggedActivities(props);
  const buttons=findButtons(tree);
  assert.equal(buttons.length,4);
  assert.ok(buttons.some(b=>b.props['aria-pressed']));
  buttons.at(-1).props.onClick();
  assert.equal(selected,'event-6');
  const html=renderToStaticMarkup(tree);
  assert.match(html,/View more · all flagged activities \(4\)/);
  for(const title of ['Panel maintenance','Site inspection','Pump inspection','Asset survey']) assert.ok(html.includes(title));
  assert.doesNotMatch(html,/Workshop repairs/);
});

test('chat starts isolated, accessible and explicitly approval gated',()=>{
  const calendar=JSON.parse(readFileSync(resolve('src/data/calendarDemo.json'),'utf8'));
  const markup=renderToStaticMarkup(createElement(ClimateAgentPanel,{day:calendar.date,mode:'demo',siteId:calendar.site.id,timezone:calendar.site.timezone,suggestions:calendar.suggestions,activities:calendar.activities,employees:calendar.employees,warnings:calendar.warnings,selectedActivity:null,onSelectActivity:()=>{},affectedCount:3,onCalendar:()=>{}}));
  assert.match(markup,/Start isolated demo session/);
  assert.match(markup,/Deterministic demo/);
  assert.match(markup,/role="log" aria-label="Current session conversation"/);
  assert.match(markup,/aria-describedby="chat-help"/);
  assert.match(markup,/A proposal does not change the calendar/);
  assert.match(markup,/keep this crew together/);
  assert.match(markup,/id="agent-message"[^>]*disabled/);
  assert.doesNotMatch(markup,/Bearer |localStorage|service-token/);
});

function reviewProps(overrides={}) {
  const activity=fixture.activities[0];
  const proposal={...fixture.suggestions[0],approval:'pending',current:{start:activity.start,end:activity.end},warning_matches:[{warning_id:'heat-1',overlap:{start:at('12:00'),end:at('13:00')},severity:'high',rationale:'Outdoor heat overlap',policy:'Demo heat policy'}]};
  return {review:{proposal,current:{...activity,version:1,notes:'Informational warning note only'},employees:[{name:'Supervisor crew'}],checks:{source_version:true,weather_policy:true,availability:true},conflicts:[],climate_rationale:'Move outside warning',annotation:'Notes are independent',server_reviewed:true},timezone:fixture.site.timezone,busy:false,sessionAvailable:true,confirmed:true,reason:'',onConfirm:()=>{},onReason:()=>{},onDecision:()=>{},...overrides};
}
test('review displays backend evidence and separates notes from reschedule status',()=>{
  const html=renderToStaticMarkup(createElement(ProposalReview,reviewProps()));
  for(const text of ['Current calendar time','Original time at proposal','Proposed:','Supervisor crew','Location:','Overlap:','Outdoor heat overlap','Weather and policy','Employee and location/resource availability','separate from rescheduling','Informational warning note only','proposal only; no calendar time change confirmed']) assert.ok(html.includes(text),text);
});
test('approve requires confirmation and successful fresh checks; reject/revise remain available for stale proposal',()=>{
  const props=reviewProps();
  const buttons=findButtons(ProposalReview({...props,confirmed:false}));
  assert.equal(buttons[0].props.disabled,true);
  assert.equal(buttons[1].props.disabled,false);
  const stale={...props.review,checks:{...props.review.checks,source_version:false}};
  const node=ProposalReview({...props,review:stale});
  assert.match(renderToStaticMarkup(node),/Stale proposal/);
  assert.equal(findButtons(node)[0].props.disabled,true);
  assert.equal(findButtons(node)[2].props.disabled,false);
});
test('review actions pass explicit decisions and never apply optimistically',()=>{
  const decisions=[];
  const node=ProposalReview(reviewProps({onDecision:d=>decisions.push(d)}));
  findButtons(node).forEach(button=>button.props.onClick());
  assert.deepEqual(decisions,['approve','reject','revise']);
  assert.doesNotMatch(renderToStaticMarkup(node),/Backend update result: applied/);
});
test('pending/rejected/failed proposals never report applied and terminal actions stay disabled',()=>{
  for(const status of ['rejected','blocked','integration-failed','superseded']) {
    const props=reviewProps();
    props.review.proposal={...props.review.proposal,approval:status,outcome:{result:status,message:'No calendar times changed.'}};
    const node=ProposalReview(props);
    assert.ok(findButtons(node).every(button=>button.props.disabled));
    assert.doesNotMatch(renderToStaticMarkup(node),/Backend update result: applied/);
  }
  const props=reviewProps();
  props.review.proposal={...props.review.proposal,approval:'applied',outcome:{result:'applied',message:'Backend confirmed demo update.'}};
  assert.match(renderToStaticMarkup(createElement(ProposalReview,props)),/Backend update result: applied/);
});
test('failed or missing backend review cannot authorize decisions',()=>{
  const props=reviewProps();
  props.review={...props.review,server_reviewed:false};
  assert.ok(findButtons(ProposalReview(props)).every(button=>button.props.disabled));
  props.review={...props.review,server_reviewed:true,checks:{}};
  assert.equal(findButtons(ProposalReview(props))[0].props.disabled,true);
});

const policyContext={status:'configured',name:'Configured test policy',version:'test-v2',source:'Site supervisor approved policy document',reason:'Backend says this rule applies to this outdoor activity',illustrative:false,applicable_work_rest_rules:[{work_minutes:37,rest_minutes:13,cooling_required:true,reason:'Cooling area required by supplied rule'}]};
function policyMarkup(activity,demo=false){return renderToStaticMarkup(createElement(PolicyExplanation,{activity,warnings:fixture.warnings,demo}));}
test('policy explanation renders backend source, reason and applicable work/rest/cooling verbatim',()=>{
  const html=policyMarkup({...fixture.activities[0],policy_context:policyContext});
  for(const text of [policyContext.name,policyContext.source,policyContext.reason,'37 minutes','13 minutes','Cooling: required',policyContext.applicable_work_rest_rules[0].reason]) assert.ok(html.includes(text),text);
  assert.doesNotMatch(html,/Illustrative demo policy/);
});
test('illustrative policies are explicit and missing rest data never becomes a fabricated rule',()=>{
  const html=policyMarkup({...fixture.activities[0],policy_context:null},true);
  assert.match(html,/Illustrative demo policy/);
  assert.match(html,/not official guidance/);
  assert.match(html,/No applicable work\/rest requirement supplied/);
  assert.match(html,/Source: Not supplied — needs review/);
  assert.doesNotMatch(html,/Work: \d+ minutes/);
});
test('unknown classification, location, policy and source remain needs-review',()=>{
  const base={...fixture.activities[0],status:'unflagged',policy_context:policyContext};
  for(const activity of [{...base,kind:'unknown'},{...base,location:null},{...base,location:'  '},{...base,policy_context:{...policyContext,status:'unknown'}},{...base,policy_context:{...policyContext,source:null}}]) assert.match(policyMarkup(activity),/Needs review/);
  assert.equal(activityWarningPresentation({...base,location:null}).tone,'needs-review');
  assert.equal(activityWarningPresentation({...base,policy_context:{...policyContext,status:'unknown'}}).tone,'needs-review');
});
test('policy contract rejects invalid requirements and preserves typed backend context',()=>{
  const calendar=structuredClone(fixture);
  calendar.activities[0].policy_context=structuredClone(policyContext);
  assert.equal(parseCalendar(calendar).activities[0].policy_context.applicable_work_rest_rules[0].rest_minutes,13);
  for(const invalid of [-1,1.5,'13',null]) {
    calendar.activities[0].policy_context.applicable_work_rest_rules[0].rest_minutes=invalid;
    assert.throws(()=>parseCalendar(calendar),/Invalid work\/rest/);
  }
});

test('reference-style compact banner keeps computed counts and forecast provenance',()=>{
  const html=renderToStaticMarkup(createElement(ClimateWarningBanner,{calendar:fixture,compact:true,onSelectActivity:()=>{}}));
  assert.match(html,/compact-climate-banner/);
  assert.match(html,/DEMO FORECAST/);
  assert.match(html,/3 outdoor activities overlap/);
  assert.ok(html.includes(fixture.weather.source));
  assert.match(html,/Warning evidence &amp; affected activities/);
});
test('compact suggestion cards retain review and expandable additional proposals',()=>{
  const html=renderToStaticMarkup(createElement(AgentSuggestions,suggestionProps({compact:true})));
  assert.match(html,/compact-suggestion/);
  assert.match(html,/>Review<\/button>/);
  assert.match(html,/More proposals/);
  assert.match(html,/Policy, validation &amp; warning evidence/);
  for(const s of fixture.suggestions) assert.ok(html.includes(s.rationale));
});

test('proposed replacement uses the same timestamp geometry without mutating the event',()=>{
  const props={start:at('08:00'),end:at('12:00'),window,timezone:'Asia/Kolkata',top:100};
  const before=structuredClone(props);
  const node=ProposalTimelinePreview(props);
  assert.deepEqual(node.props.style,{...timelineGeometry(props.start,props.end,window),top:'100px'});
  assert.deepEqual(props,before);
  const html=renderToStaticMarkup(node);
  assert.match(html,/not applied/);
  assert.match(html,/supervisor approval required/);
});
test('proposed preview labels remain site-local across timestamp offsets',()=>{
  const local=ProposalTimelinePreview({start:at('08:00'),end:at('12:00'),window,timezone:'Asia/Kolkata',top:100});
  const utc=ProposalTimelinePreview({start:'2026-10-17T02:30:00Z',end:'2026-10-17T06:30:00Z',window,timezone:'Asia/Kolkata',top:100});
  assert.deepEqual(local.props.style,utc.props.style);
  assert.equal(local.props['aria-label'],utc.props['aria-label']);
});
