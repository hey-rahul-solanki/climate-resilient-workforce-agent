import path from 'node:path';
import { pathToFileURL } from 'node:url';

const workspaceDir = '/Users/rahulsolanki/Documents/climate-resilient-workforce-agent';
const skillDir = '/Users/rahulsolanki/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';
const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir, 'container_tools/artifact_tool_utils.mjs')).href);
const result = await finalizePresentation({
  explicitTotalSlideCount: 6,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  workspaceDir,
  candidatePath: path.join(workspaceDir, '.ppt-build/baseline-schedule-cycle-final-draft.pptx'),
  finalPath: path.join(workspaceDir, '.ppt-output/Baseline-Schedule-Cycle-Experience-Final.pptx'),
  pythonExecutable: '/Users/rahulsolanki/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',
  integrityValidatorPath: path.join(skillDir, 'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath: path.join(skillDir, 'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs: ['--expected-slide-size-emu', '12192000,6858000'],
  fontPolicy: { basis: 'design', families: ['Arial'] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(workspaceDir, '.ppt-build/Baseline-Schedule-Cycle-Experience-Final.validation.json'),
});
console.log(JSON.stringify(result, null, 2));
