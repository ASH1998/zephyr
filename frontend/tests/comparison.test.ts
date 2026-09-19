import test from 'node:test';
import assert from 'node:assert/strict';
import { canCompare, comparisonVerdict, playbackClock } from '../src/comparison-data.ts';
import type { LiveRun, Job } from '../src/live-data';
import { progressStage, stageProgress } from '../src/run-progress.ts';

const result = () => ({status:'comparison',geometryId:'hatchback',candidate:{displacementM:[0,.0036]},forces:{baselineDragN:475,candidateDragN:473.5},validation:{freshEvaluation:'passed',independentCfd:'not-run'},trust:{decision:'refuse',reason:'Calibration and intersection checks are pending.'}} as LiveRun);
test('only a completed car result with a freshly evaluated candidate can open a pair', () => {
  for (const state of ['running','failed','cancelled','cancelling'] as Job['state'][]) assert.equal(canCompare(result(),state),false);
  assert.equal(canCompare(undefined,'complete'),false);
  assert.equal(canCompare(result(),'complete'),true);
  const r=result();r.candidate=null;assert.equal(canCompare(r,'complete'),false);
  for (const geometryId of ['x57','global-hawk']) assert.equal(canCompare({...result(),geometryId},'complete'),false);
  assert.equal(canCompare({...result(),validation:{...result().validation,freshEvaluation:'not-run'}},'complete'),false);
});
test('verdict reports direction, absolute N and percent separately from acceptance', () => {
  const r=result();assert.match(comparisonVerdict(r),/decreased by 1.50 N \(0.316%\)/);
  assert.match(comparisonVerdict(r),/3.60 mm.*acceptance: refused/);
  r.forces.candidateDragN=476;assert.match(comparisonVerdict(r),/increased by 1.00 N/);
  r.forces.candidateDragN=475;assert.match(comparisonVerdict(r),/unchanged/);
  r.forces.baselineDragN=0;assert.doesNotMatch(comparisonVerdict(r),/Infinity|NaN/);
  r.candidate=null;assert.equal(comparisonVerdict(r),'Original only. No changed shape was evaluated.');
});
test('paired renderers sample the same clock, pause without catching up and clamp inactive gaps', () => {
  const c=playbackClock();assert.equal(c.tick(100,false),0);
  assert.equal(c.tick(116,false),.016);assert.equal(c.tick(116,false),.016);
  assert.equal(c.tick(132,true),.016);assert.equal(c.tick(5000,true),.016);
  assert.equal(c.tick(5016,false),.032);assert.equal(c.tick(10000,false),.07200000000000001);
});
test('worker completion does not announce a result before API publication', () => {
  assert.equal(progressStage({state:'running',stage:'complete'}),'publishing');
  assert.match(stageProgress('publishing').detail,/Waiting for the complete result/);
  assert.equal(progressStage({state:'complete',stage:'complete'}),'complete');
  assert.equal(stageProgress('smoothing',undefined,undefined,'evaluate: smoothing').step,4);
});
test('accepted surrogate step remains explicitly separate from engineering validation',()=>{
  const r=result();r.trust.decision='accept';r.trust.reason='Local checks passed.';
  assert.match(comparisonVerdict(r),/Accepted for further evaluation only.*Engineering validation pending/);
  assert.doesNotMatch(comparisonVerdict(r),/Engineering acceptance: accept/);
  for(const phase of ['calibration','repeat','probe-plus-h','probe-minus-h','probe-plus-half','probe-minus-half'])assert.equal(stageProgress(phase).step,3);
});
