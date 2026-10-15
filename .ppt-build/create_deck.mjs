import fs from 'node:fs/promises';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const OUT = '/Users/rahulsolanki/Documents/climate-resilient-workforce-agent/.ppt-build';
const ppt = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const C = {
  bg: '#F5F7F4', ink: '#15231F', muted: '#586861', green: '#176B55', lime: '#D9E8B7',
  white: '#FFFFFF', line: '#D8E1DC', amber: '#D7912B', pale: '#EAF0EB', dark: '#17342C',
  red: '#B65A4D', blue: '#49799A',
};

function shape(slide, x, y, w, h, fill, radius = 0, stroke = 'none') {
  return slide.shapes.add({
    geometry: radius ? 'roundRect' : 'rect',
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: 'solid', fill: stroke, width: stroke === 'none' ? 0 : 1 },
    ...(radius ? { borderRadius: radius } : {}),
  });
}
function txt(slide, text, x, y, w, h, size = 22, color = C.ink, bold = false, align = 'left') {
  const s = slide.shapes.add({
    geometry: 'textbox', position: { left: x, top: y, width: w, height: h },
    fill: 'none', line: { style: 'solid', fill: 'none', width: 0 },
  });
  s.text = text;
  s.text.style = { typeface: 'Arial', fontSize: size, color, bold, alignment: align, verticalAlignment: 'middle', autoFit: 'shrinkText', insets: 0 };
  return s;
}
function base(title, eyebrow, n) {
  const s = ppt.slides.add(); s.background.fill = C.bg;
  txt(s, eyebrow.toUpperCase(), 68, 38, 740, 22, 14, C.green, true);
  txt(s, title, 68, 70, 1125, 62, 46, C.ink, true);
  shape(s, 68, 655, 1144, 1, C.line);
  txt(s, 'CLIMATE-RESILIENT WORKFORCE PLANNING', 68, 665, 700, 18, 12, C.muted, true);
  txt(s, String(n).padStart(2, '0'), 1165, 660, 46, 24, 14, C.muted, true, 'right');
  return s;
}
function note(slide, text) { slide.speakerNotes.text = text; }
function bullet(slide, text, x, y, w, color = C.ink, dot = C.green, size = 22) {
  shape(slide, x, y + 10, 10, 10, dot, 5);
  txt(slide, text, x + 24, y, w - 24, 54, size, color);
}

// 1 — concise opening
{
  const s = ppt.slides.add(); s.background.fill = C.dark;
  shape(s, 824, 0, 456, 720, '#21483C');
  shape(s, 886, 104, 290, 4, C.lime);
  txt(s, 'PRODUCT FLOW • SCHEDULES', 78, 68, 680, 24, 15, C.lime, true);
  txt(s, 'The baseline\nschedule in action', 78, 138, 750, 180, 58, C.white, true);
  txt(s, 'Where the original plan is captured, how a supervisor uses it, and what an employee sees.', 82, 348, 655, 88, 25, '#E4EEE7');
  // Editable visual: one workday on a shared timeline
  txt(s, 'PLANNING RUN', 883, 144, 270, 20, 14, C.lime, true);
  txt(s, 'Vadodara Plant  •  13 Oct', 883, 178, 300, 32, 21, C.white, true);
  shape(s, 883, 246, 302, 2, '#80A393');
  for (const [x, label] of [[883, '06:00'], [1030, '10:00'], [1150, '14:00']]) txt(s, label, x, 255, 70, 20, 13, '#C9D8D0');
  shape(s, 901, 304, 221, 46, '#D9E8B7', 8);
  txt(s, 'WO-104  •  gasket repair', 914, 310, 210, 32, 16, C.dark, true);
  shape(s, 923, 369, 182, 46, '#9ABBA9', 8);
  txt(s, 'WO-105  •  inspection', 936, 375, 200, 32, 16, C.dark, true);
  txt(s, 'Snapshot saved before any climate-aware changes', 883, 474, 314, 58, 18, C.white, false);
  note(s, 'This deck proposes where baseline capture belongs in the product. The backend now has a planning-run request, immutable SQLite baseline snapshot, and a shared versioned evaluator. The current React app does not yet have role-specific schedule pages; the screens that follow are product concepts.');
}

// 2 — lifecycle
{
  const s = base('A planning run starts with the source schedule', 'Workflow', 2);
  const xs = [82, 365, 648, 931];
  const titles = ['1  Select inputs', '2  Capture baseline', '3  Evaluate', '4  Plan for climate'];
  const desc = [
    'Work orders, workers,\nequipment and original\nassignments',
    'Save the schedule and\ninput dataset under a\nunique run ID',
    'Apply shared metric\ndefinitions and store the\nmetric version',
    'Future schedule proposal\nuses the same dataset and\nevaluator',
  ];
  xs.forEach((x, i) => {
    shape(s, x, 200, 230, 236, C.white, 12, C.line);
    shape(s, x, 200, 230, 7, i === 1 ? C.amber : C.green);
    txt(s, titles[i], x + 20, 230, 192, 52, 22, C.ink, true);
    txt(s, desc[i], x + 20, 298, 192, 104, 18, C.muted);
    if (i < 3) {
      shape(s, x + 240, 310, 30, 2, C.green);
      txt(s, '›', x + 245, 285, 24, 46, 34, C.green, true, 'center');
    }
  });
  shape(s, 82, 478, 1080, 108, '#E6EDE7', 10);
  txt(s, 'One frozen reference', 106, 496, 265, 34, 21, C.green, true);
  txt(s, 'Assignments • time windows • worker IDs • equipment IDs • original input dataset • baseline metrics', 106, 537, 1000, 28, 18, C.ink);
  note(s, 'Steps 1–3 are represented by the current backend contract and service. Step 4 indicates the future use of the same dataset and evaluator; generating alternative schedules and before/after comparisons are outside this ticket.');
}

// 3 — manager page mockup
{
  const s = base('Supervisor view: capture, inspect, then continue planning', 'Manager / supervisor', 3);
  // UI screen as editable native slide objects
  shape(s, 68, 158, 1144, 455, C.white, 12, C.line);
  shape(s, 68, 158, 205, 455, '#F0F4F1', 12);
  txt(s, 'OPERATIONS', 90, 180, 155, 20, 13, C.muted, true);
  for (const [i, t] of ['Overview', 'Sites & Locations', 'Weather', 'Safety & Scheduling'].entries()) {
    if (i === 3) shape(s, 82, 346, 174, 38, '#DCE9E1', 7);
    txt(s, t, 94, 216 + i * 44, 160, 32, 16, i === 3 ? C.green : C.muted, i === 3);
  }
  txt(s, 'Safety & Scheduling', 300, 180, 500, 42, 29, C.ink, true);
  txt(s, 'Site  Vadodara Plant     Date  13 Oct 2026     Run  RUN-2048', 300, 228, 820, 27, 17, C.muted);
  shape(s, 300, 274, 876, 71, '#EEF4EF', 8);
  txt(s, 'SOURCE SCHEDULE SAVED', 320, 285, 240, 20, 13, C.green, true);
  txt(s, '8 tasks  ·  12 workers  ·  4 equipment items', 320, 309, 510, 27, 18, C.ink, true);
  shape(s, 953, 290, 194, 40, C.green, 6);
  txt(s, 'View baseline', 953, 293, 194, 32, 16, C.white, true, 'center');
  // Editable schedule table
  const cols = [320, 574, 730, 874, 1015];
  ['TASK', 'TIME WINDOW', 'WORKERS', 'EQUIPMENT', 'STATUS'].forEach((t, i) => txt(s, t, cols[i], 369, i === 0 ? 240 : 138, 24, 12, C.muted, true));
  shape(s, 316, 400, 836, 1, C.line);
  const rows = [
    ['WO-104  Gasket repair', '06:00–09:00', 'A. Patel, R. Shah', 'Crane 01', 'Scheduled'],
    ['WO-105  Site inspection', '09:30–10:15', 'M. Desai', '—', 'Scheduled'],
    ['WO-106  Pump service', '10:30–13:00', 'N. Joshi, A. Rao', 'Pump kit 02', 'Scheduled'],
  ];
  rows.forEach((row, r) => {
    const y = 410 + r * 54;
    row.forEach((v, i) => txt(s, v, cols[i], y, i === 0 ? 240 : 138, 36, 14, i === 0 ? C.ink : C.muted, i === 0));
    shape(s, 316, y + 48, 836, 1, '#E9EEEA');
  });
  txt(s, 'Placement', 82, 575, 120, 22, 14, C.green, true);
  txt(s, 'Add a Baseline section to the existing Safety & Scheduling workflow; make it available from the run detail.', 220, 568, 930, 34, 18, C.ink);
  note(s, 'Proposed supervisor page, not a screenshot of an implemented screen. The current frontend has the Safety & Scheduling tab but no schedule table or role-based access. The values shown are illustrative examples, not product data.');
}

// 4 — employee schedule
{
  const s = base('Employee schedule: work and safety guidance', 'Employee schedule', 4);
  txt(s, 'Today • Tuesday, 13 October', 78, 163, 760, 40, 28, C.ink, true);
  txt(s, 'Vadodara Plant', 78, 204, 500, 28, 18, C.muted);
  // timeline
  shape(s, 110, 278, 3, 280, C.line);
  const items = [
    { y: 272, time: '06:00–09:00', title: 'Replace heat-exchanger gasket', meta: 'Unit 2 • With R. Shah • Crane 01', fill: '#E4EFE6', accent: C.green },
    { y: 382, time: '09:00–09:20', title: 'Cooling break', meta: 'Shaded rest area • Hydrate', fill: '#FFF1D9', accent: C.amber },
    { y: 472, time: '09:30–10:15', title: 'Site housekeeping inspection', meta: 'North process area • Solo task', fill: '#EAF0F5', accent: C.blue },
  ];
  items.forEach((it) => {
    shape(s, 97, it.y + 20, 28, 28, it.accent, 14);
    shape(s, 160, it.y, 710, 84, it.fill, 10);
    txt(s, it.time, 180, it.y + 10, 142, 27, 15, it.accent, true);
    txt(s, it.title, 328, it.y + 8, 510, 30, 20, C.ink, true);
    txt(s, it.meta, 328, it.y + 42, 510, 26, 15, C.muted);
  });
  shape(s, 914, 250, 278, 306, C.dark, 12);
  txt(s, 'SAFETY DETAILS', 942, 276, 220, 24, 14, C.lime, true);
  txt(s, 'Heat guidance', 942, 319, 220, 28, 19, C.white, true);
  txt(s, 'Cooling break scheduled\nafter the first task.', 942, 357, 220, 56, 17, '#DDE9E1');
  shape(s, 942, 437, 218, 1, '#456458');
  txt(s, 'Schedule updated', 942, 458, 220, 25, 16, C.lime, true);
  txt(s, 'Show when the plan changes and who to contact.', 942, 491, 220, 48, 15, '#DDE9E1');
  txt(s, 'The baseline stays in the manager’s planning record; employees receive the active assignment and safety instructions.', 80, 595, 1105, 34, 18, C.muted);
  note(s, 'Proposed employee schedule concept. Employee-facing baseline access is not required for baseline capture. The employee sees current assigned work, scheduled breaks, equipment/location details and any published schedule changes. Times and names are illustrative.');
}

// 5 — role placement
{
  const s = base('Where the baseline fits across roles', 'Product placement', 5);
  // Two role lanes and shared backend record, explicitly an editable architecture diagram
  txt(s, 'SUPERVISOR', 85, 177, 300, 26, 14, C.green, true);
  txt(s, 'EMPLOYEE', 85, 398, 300, 26, 14, C.blue, true);
  shape(s, 80, 216, 380, 132, C.white, 10, C.line);
  txt(s, 'Start planning run', 108, 234, 325, 32, 23, C.ink, true);
  txt(s, 'Review original assignments and baseline metrics', 108, 278, 300, 52, 18, C.muted);
  shape(s, 80, 440, 380, 132, C.white, 10, C.line);
  txt(s, 'My schedule', 108, 457, 325, 32, 23, C.ink, true);
  txt(s, 'See published tasks, time windows, breaks and safety notes', 108, 501, 300, 56, 18, C.muted);
  // connective lines and central record
  shape(s, 460, 280, 103, 2, C.green); txt(s, '›', 520, 258, 30, 44, 34, C.green, true, 'center');
  shape(s, 460, 504, 103, 2, C.blue); txt(s, '›', 520, 482, 30, 44, 34, C.blue, true, 'center');
  shape(s, 580, 234, 600, 295, '#E8EEE9', 14);
  txt(s, 'PLANNING RUN RECORD', 613, 261, 500, 22, 14, C.green, true);
  txt(s, 'Original input dataset', 613, 302, 490, 33, 22, C.ink, true);
  txt(s, 'Work orders  •  workers  •  equipment', 613, 338, 490, 28, 17, C.muted);
  shape(s, 613, 383, 534, 1, '#CDD9D1');
  txt(s, 'Immutable baseline snapshot', 613, 401, 490, 33, 22, C.ink, true);
  txt(s, 'Assignments  •  windows  •  allocations  •  metrics v1', 613, 440, 510, 30, 16, C.muted);
  txt(s, 'The same dataset and evaluator can be reused when evaluating a future proposal.', 613, 480, 510, 40, 16, C.green, true);
  note(s, 'The supervisor owns planning and baseline review. The employee page consumes the active schedule. Both sit over the same planning run record. The current implementation persists baseline data in SQLite and exposes create/retrieve API endpoints; the role pages are proposed UI placement.');
}

// 6 — scope and status
{
  const s = base('What this ticket establishes', 'Delivery boundary', 6);
  const x1 = 84, x2 = 668;
  txt(s, 'IN THE BASELINE CAPTURE', x1, 180, 470, 26, 14, C.green, true);
  bullet(s, 'Original task assignments and time windows', x1, 226, 500);
  bullet(s, 'Worker and equipment allocations', x1, 292, 500);
  bullet(s, 'Input dataset stored with the run', x1, 358, 500);
  bullet(s, 'Versioned metrics and immutable snapshot', x1, 424, 500);
  shape(s, 620, 185, 1, 390, C.line);
  txt(s, 'NEXT PRODUCT WORK', x2, 180, 470, 26, 14, C.amber, true);
  bullet(s, 'Manager and employee schedule screens', x2, 226, 500, C.ink, C.amber);
  bullet(s, 'Schedule generation and publishing', x2, 292, 500, C.ink, C.amber);
  bullet(s, 'Before/after comparisons or recommendations', x2, 358, 500, C.ink, C.amber);
  bullet(s, 'Role-based access and employee notifications', x2, 424, 500, C.ink, C.amber);
  shape(s, 84, 528, 1090, 62, C.dark, 9);
  txt(s, 'Current app: shared operations shell + Safety & Scheduling page', 106, 541, 1040, 35, 19, C.white, true);
  note(s, 'Current implementation: Pydantic schemas for planning dataset and baseline snapshot; shared evaluator with a metric definition version; SQLite write-once persistence; POST and GET baseline endpoints. Proposed: schedule screens and employee/supervisor role experience. No alternative schedule generation, before/after improvement calculation, or manager recommendations are included in this ticket.');
}

for (const [index, slide] of ppt.slides.items.entries()) {
  const blob = await ppt.export({ slide, format: 'png', scale: 1 });
  await fs.writeFile(`${OUT}/slide-${String(index + 1).padStart(2, '0')}.png`, new Uint8Array(await blob.arrayBuffer()));
}
const deck = await PresentationFile.exportPptx(ppt);
await deck.save(`${OUT}/baseline-schedule-action-draft.pptx`);
console.log(`created ${ppt.slides.items.length} slides`);
