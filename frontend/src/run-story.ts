import type { SimulationRun, ViewMode } from './data.ts';

export type StoryStage = 'intent' | 'sensitivity' | 'candidate' | 'validate' | 'evaluate';
export type StoryState = StoryStage | 'result' | 'refused';
/** Presentation boundary: future backend events must carry the displayed run's identity/source. */
export interface RunStoryEvent {
  runId: string;
  source: SimulationRun['source'];
  stage: StoryState;
  detail?: string;
}
export function assertStoryEvent(run: SimulationRun, event: RunStoryEvent): void {
  if (event.runId !== run.runId || event.source !== run.source) throw new Error('Presentation event does not match the displayed run.');
}
export const storyStages: readonly { id: StoryStage; title: string; detail: string; mode: ViewMode; duration: number }[] = [
  { id: 'intent', title: 'Keep the cabin. Find room to improve.', detail: 'Cabin locked in cyan. Only the allowed body surfaces can move.', mode: 'airflow', duration: 2100 },
  { id: 'sensitivity', title: 'Focus on the rear surfaces.', detail: 'The warm areas show where this preview places the strongest opportunity.', mode: 'sensitivity', duration: 2400 },
  { id: 'candidate', title: 'Make a small, targeted change.', detail: 'Amber shows the rear taper. Cyan keeps the original shape in view.', mode: 'displacement', duration: 2700 },
  { id: 'validate', title: 'Check the shape. Keep the promises.', detail: 'Same mesh connections. Fixed cabin. Movement inside the selected limit.', mode: 'mesh', duration: 2100 },
  { id: 'evaluate', title: 'Compare drag after the change.', detail: 'Showing the fresh-evaluation step with illustrative pressure and force values.', mode: 'pressure', duration: 2500 },
];
export function sourceLabel(source: SimulationRun['source']): string {
  return source === 'illustrative' ? 'DEMO WALKTHROUGH · NO SOLVER RUNNING' : source === 'recorded' ? 'RECORDED SURROGATE RUN' : 'LIVE SURROGATE RUN';
}
export function resultSummary(run: SimulationRun) {
  const baseline = run.forces.baselineN[0], candidate = run.forces.candidateN[0];
  return { baseline, candidate, deltaPercent: baseline === 0 ? null : (candidate - baseline) / Math.abs(baseline) * 100,
    maximumMm: Math.max(...run.candidate.displacementM) * 1000,
    label: run.source === 'illustrative' ? 'ILLUSTRATIVE DRAG COMPARISON' : 'SURROGATE DRAG COMPARISON' };
}
