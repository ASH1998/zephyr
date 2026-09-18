import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemoRun, demoAtBudget } from '../src/data.ts';
import { assertStoryEvent, resultSummary, sourceLabel } from '../src/run-story.ts';
import { previewWake } from '../src/flow-preview.ts';

test('presentation cannot attach a stage to a different run or provenance source', () => {
  const run = createDemoRun();
  assert.doesNotThrow(() => assertStoryEvent(run, { runId: run.runId, source: run.source, stage: 'evaluate' }));
  assert.throws(() => assertStoryEvent(run, { runId: 'another-run', source: run.source, stage: 'result' }));
  assert.throws(() => assertStoryEvent(run, { runId: run.runId, source: 'live', stage: 'result' }));
  assert.match(sourceLabel('illustrative'), /NO SOLVER RUNNING/);
  assert.match(sourceLabel('recorded'), /RECORDED/);
  assert.match(sourceLabel('live'), /LIVE/);
});

test('result numbers use the supplied forces and actual displacement, independent of display magnification', () => {
  const run = demoAtBudget(1);
  run.forces.baselineN[0] = 500; run.forces.candidateN[0] = 475;
  const result = resultSummary(run);
  assert.equal(result.deltaPercent, -5); assert.equal(result.candidate, 475);
  assert.ok(Math.abs(result.maximumMm - 1) < 1e-6);
  run.forces.baselineN[0] = 0; assert.equal(resultSummary(run).deltaPercent, null);
  run.source = 'recorded'; assert.match(resultSummary(run).label, /SURROGATE/);
});

test('authored wake transition leaves the car/inlet unchanged and narrows only the downstream candidate', () => {
  for (const morph of [0, .5, 1]) assert.deepEqual(previewWake(1, .5, 1.2, .2, morph), [1, .5, 1.2]);
  let baselineOscillation = 0, candidateOscillation = 0;
  for (let x = 2.2; x <= 6; x += .05) {
    const baseline = previewWake(x, .5, 1.2, .2, 0), candidate = previewWake(x, .5, 1.2, .2, 1);
    assert.ok([...baseline, ...candidate].every(Number.isFinite));
    baselineOscillation += Math.abs(baseline[1] - .5); candidateOscillation += Math.abs(candidate[1] - .5);
    assert.ok(candidate[2] <= 1.2 && candidate[2] > .9);
  }
  assert.ok(baselineOscillation > 1); assert.equal(candidateOscillation, 0);
});
