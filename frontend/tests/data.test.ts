import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemoRun, validateRun, demoAtBudget, decideRequest, HttpRunAdapter } from '../src/data.ts';

test('demo is deterministic, fixed topology, bounded and every protected coordinate is identical', () => {
  const a = createDemoRun(); assert.deepEqual(a, createDemoRun());
  assert.equal(a.source, 'illustrative'); assert.equal(a.provenance.solver, null);
  assert.deepEqual(a.baseline.triangles, a.candidate.triangles);
  assert.ok(Math.max(...a.candidate.displacementM) <= .004);
  let locked = 0;
  a.baseline.protectedMask.forEach((v, i) => { if (v) { locked++; assert.deepEqual(a.baseline.positions.slice(i * 3, i * 3 + 3), a.candidate.positions.slice(i * 3, i * 3 + 3)); } });
  assert.ok(locked > 500);
});
test('surface connectivity has two oppositely directed uses of every edge', () => {
  const s = createDemoRun().baseline, edges = new Map<string, number[]>();
  for (let i = 0; i < s.triangles.length; i += 3) {
    const t = s.triangles.slice(i, i + 3);
    for (let j = 0; j < 3; j++) { const a = t[j], b = t[(j + 1) % 3], key = `${Math.min(a, b)}:${Math.max(a, b)}`; edges.set(key, [...(edges.get(key) || []), a < b ? 1 : -1]); }
  }
  for (const directions of edges.values()) { assert.equal(directions.length, 2); assert.equal(directions[0] + directions[1], 0); }
});
test('smaller budgets alter coordinates and stay within the selected bound', () => {
  for (const budget of [1, 2, 3.6, 4]) {
    const run = demoAtBudget(budget);
    assert.ok(Math.abs(Math.max(...run.candidate.displacementM) * 1000 - budget) < 1e-7);
    assert.equal(validateRun(run), run);
  }
  assert.throws(() => demoAtBudget(12)); assert.throws(() => demoAtBudget(NaN));
});
test('adapter refuses schema, topology, field, mask and displacement corruption', () => {
  for (const mutate of [
    (r: any) => r.schemaVersion = 'v2',
    (r: any) => r.coordinates.units = 'mm',
    (r: any) => r.candidate.triangles[0] = 999999,
    (r: any) => r.candidate.pressurePa.pop(),
    (r: any) => r.candidate.wallShearPa[0] = NaN,
    (r: any) => r.candidate.positions[0] += .02,
    (r: any) => r.candidate.protectedMask[0] = 2,
    (r: any) => { const i = r.baseline.protectedMask.indexOf(1); r.candidate.positions[i * 3] += .001; },
    (r: any) => r.source = 'live',
  ]) { const run = createDemoRun(); mutate(run); assert.throws(() => validateRun(run), /Simulation data rejected/); }
});
test('accept/shrink/refuse enforce offline intent and hard constraints', () => {
  assert.equal(decideRequest('Reduce drag. Keep the cabin unchanged.', 3.6).decision, 'accept');
  assert.equal(decideRequest('Reduce drag.', 4).decision, 'shrink');
  assert.equal(decideRequest('Reduce drag.', 12).decision, 'refuse');
  assert.equal(decideRequest('Reduce drag. Lower the cabin.', 3).decision, 'refuse');
  assert.equal(decideRequest('Make a flying car.', 3).decision, 'refuse');
});
test('HTTP adapter propagates failure and never silently returns demo data', async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async () => new Response('Unavailable', { status: 503 });
    await assert.rejects(new HttpRunAdapter('/run').load(), /HTTP 503/);
    globalThis.fetch = async () => new Response(JSON.stringify({ schemaVersion: 'wrong' }), { status: 200 });
    await assert.rejects(new HttpRunAdapter('/run').load(), /unsupported schema/);
  } finally { globalThis.fetch = original; }
});
