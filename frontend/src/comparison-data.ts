import type { Job, LiveRun } from './live-data';
import { maximumMovementMm } from './live-data.ts';

export function canCompare(run: LiveRun | undefined, state: Job['state']) {
  return state === 'complete' && run?.status === 'comparison' && !!run.candidate &&
    run.car?.id !== 'x57' && run.car?.id !== 'global-hawk' &&
    !['x57', 'global-hawk'].includes(run.geometryId ?? run.intent?.request.geometryId ?? '') && run.validation.freshEvaluation === 'passed';
}

export function comparisonVerdict(run: LiveRun) {
  if (!run.candidate || run.forces.candidateDragN === null) return 'Original only. No changed shape was evaluated.';
  const difference = run.forces.candidateDragN - run.forces.baselineDragN;
  const percent = run.forces.baselineDragN === 0 ? null : Math.abs(difference / run.forces.baselineDragN * 100);
  const movement = maximumMovementMm(run);
  const result = difference === 0 ? 'Estimated resistance is unchanged.' :
    `Estimated resistance ${difference < 0 ? 'decreased' : 'increased'} by ${Math.abs(difference).toFixed(2)} N${percent === null ? '' : ` (${percent.toFixed(3)}%)`}.`;
  return `${run.syntheticDent?'Synthetic hood dent. ':''}${result} Actual maximum movement: ${movement.toFixed(2)} mm. Cabin unchanged. ${run.trust.decision === 'accept' ? 'Accepted for further evaluation only. Engineering validation pending.' : 'Engineering acceptance: refused.'} ${run.trust.reason.split(' Research gates:')[0]} Surrogate estimate; independent CFD: ${run.validation.independentCfd}.`;
}

/** A single absolute clock lets both renderers sample precisely the same frame time. */
export function playbackClock() {
  let elapsed = 0, previous: number | undefined;
  return { tick(now: number, paused: boolean) {
    if (previous !== undefined && !paused) elapsed += Math.max(0, Math.min((now - previous) / 1000, .04));
    previous = now;
    return elapsed;
  }};
}
