/** Versioned renderer boundary. No model or solver runs in the browser. */
export type Vec3 = [number, number, number];
export type Decision = 'accept' | 'shrink' | 'refuse';
export type ViewMode = 'airflow' | 'pressure' | 'sensitivity' | 'displacement' | 'mesh';
export interface Surface {
  displayColor?: number[];
  positions: number[]; // XYZ triples, metres
  triangles: number[];
  pressurePa: number[]; // vertex-associated values
  wallShearPa: number[]; // XYZ triples
  sensitivity: number[]; // d(-drag N)/d(position m), XYZ triples
  normalSensitivity: number[]; // N/m
  protectedMask: number[]; // 1 = immovable
  displacementM: number[];
}
export interface SimulationRun {
  schemaVersion: 'zephyr.surface.v1';
  runId: string;
  source: 'illustrative' | 'recorded' | 'live';
  createdAt: string;
  coordinates: { units: 'm'; up: '+Y'; streamwise: '+X'; handedness: 'right'; fieldAssociation: 'vertex' };
  provenance: { artifactVersion: string; modelVersion: string; meshHash: string; evidenceUrls: string[]; solver: string | null };
  conditions: { streamVelocityMps: Vec3; densityKgM3: number };
  baseline: Surface;
  candidate: Surface;
  forces: { baselineN: Vec3; candidateN: Vec3; predictedDragN: number };
  constraints: { maxDisplacementM: number; protectedRegion: string };
  trust: { decision: Decision; predictionErrorPercent: number; thresholdPercent: number; calibrated: boolean };
  validation: { geometry: 'illustrative' | 'passed' | 'failed'; freshEvaluation: 'illustrative' | 'passed' | 'failed'; independentCfd: 'not-run' | 'passed' | 'disagreed'; evidenceIds: string[] };
}
export interface SimulationAdapter { load(signal?: AbortSignal): Promise<SimulationRun> }
export function fieldRange(values: number[]): [number, number] { return values.reduce<[number, number]>(([lo, hi], v) => [Math.min(lo, v), Math.max(hi, v)], [Infinity, -Infinity]); }

export function validateRun(input: unknown): SimulationRun {
  const r = input as SimulationRun;
  const fail = (message: string): never => { throw new Error(`Simulation data rejected: ${message}`); };
  if (!r || r.schemaVersion !== 'zephyr.surface.v1') fail('unsupported schema version. Expected zephyr.surface.v1.');
  if (!['illustrative', 'recorded', 'live'].includes(r.source)) fail('missing or invalid provenance source.');
  if (!r.runId || !Number.isFinite(Date.parse(r.createdAt))) fail('run identity or timestamp missing.');
  if (r.coordinates?.units !== 'm' || r.coordinates?.up !== '+Y' || r.coordinates?.streamwise !== '+X' || r.coordinates?.handedness !== 'right' || r.coordinates?.fieldAssociation !== 'vertex') fail('coordinate/field convention mismatch. Convert payload explicitly.');
  if (!r.provenance?.artifactVersion || !r.provenance.modelVersion || !r.provenance.meshHash || !Array.isArray(r.provenance.evidenceUrls)) fail('incomplete artifact provenance.');
  const finite = (v: unknown, n?: number): v is number[] => Array.isArray(v) && (n === undefined || v.length === n) && v.every(Number.isFinite);
  if (!finite(r.conditions?.streamVelocityMps, 3) || !(r.conditions.densityKgM3 > 0)) fail('invalid flow conditions.');
  if (!(r.constraints?.maxDisplacementM > 0) || !r.constraints.protectedRegion) fail('invalid constraints.');
  for (const [name, s] of [['baseline', r.baseline], ['candidate', r.candidate]] as const) {
    if (!s || !finite(s.positions) || s.positions.length < 9 || s.positions.length % 3 || s.positions.length > 600000) fail(`${name}: invalid vertices or exceeds 200,000-vertex browser payload limit.`);
    const n = s.positions.length / 3;
    if (!finite(s.triangles) || !s.triangles.length || s.triangles.length % 3 || s.triangles.some(i => !Number.isInteger(i) || i < 0 || i >= n)) fail(`${name}: invalid connectivity.`);
    for (const f of ['pressurePa', 'normalSensitivity', 'protectedMask', 'displacementM'] as const) if (!finite(s[f], n)) fail(`${name}: ${f} length/values invalid.`);
    for (const f of ['wallShearPa', 'sensitivity'] as const) if (!finite(s[f], n * 3)) fail(`${name}: ${f} length/values invalid.`);
    if (s.protectedMask.some(v => v !== 0 && v !== 1) || s.displacementM.some(v => v < 0)) fail(`${name}: invalid mask/displacement.`);
  }
  if (r.baseline.positions.length !== r.candidate.positions.length || r.baseline.triangles.length !== r.candidate.triangles.length || r.baseline.triangles.some((v, i) => v !== r.candidate.triangles[i])) fail('candidate topology changed.');
  for (let i = 0; i < r.baseline.protectedMask.length; i++) {
    if (r.baseline.protectedMask[i] !== r.candidate.protectedMask[i]) fail('protected mask changed.');
    const d = Math.hypot(...[0, 1, 2].map(k => r.candidate.positions[i * 3 + k] - r.baseline.positions[i * 3 + k]));
    if (r.baseline.protectedMask[i] && d > 1e-8) fail('protected cabin moved.');
    if (d > r.constraints.maxDisplacementM + 1e-8 || Math.abs(d - r.candidate.displacementM[i]) > 1e-7) fail('candidate displacement violates payload/budget.');
  }
  if (!finite(r.forces?.baselineN, 3) || !finite(r.forces.candidateN, 3) || !Number.isFinite(r.forces.predictedDragN)) fail('invalid force result.');
  if (!r.trust || !['accept', 'shrink', 'refuse'].includes(r.trust.decision) || !Number.isFinite(r.trust.predictionErrorPercent) || r.trust.predictionErrorPercent < 0 || !(r.trust.thresholdPercent > 0) || !Number.isFinite(r.trust.thresholdPercent) || typeof r.trust.calibrated !== 'boolean') fail('invalid trust result.');
  if (!r.validation || !['illustrative', 'passed', 'failed'].includes(r.validation.geometry) || !['illustrative', 'passed', 'failed'].includes(r.validation.freshEvaluation) || !['not-run', 'passed', 'disagreed'].includes(r.validation.independentCfd) || !Array.isArray(r.validation.evidenceIds)) fail('invalid validation state.');
  if (r.source !== 'illustrative' && (!r.provenance.evidenceUrls.length || !r.validation.evidenceIds.length || r.validation.geometry === 'illustrative' || r.validation.freshEvaluation === 'illustrative')) fail('real runs require evidence and non-demo validation.');
  return r;
}

const profile = [[-2.35, .72, .72], [-2.05, .83, .91], [-1.25, .91, .94], [-.58, 1.48, .89], [.45, 1.5, .89], [1.17, 1.0, .93], [1.9, .91, .87], [2.3, .79, .75]];
function section(x: number) {
  const k = Math.max(0, profile.findIndex(p => p[0] >= x) - 1);
  const a = profile[k], b = profile[Math.min(k + 1, profile.length - 1)];
  const t = Math.max(0, Math.min(1, (x - a[0]) / (b[0] - a[0])));
  const smooth = t * t * (3 - 2 * t);
  return [a[1] + (b[1] - a[1]) * smooth, a[2] + (b[2] - a[2]) * smooth];
}
export function createDemoRun(): SimulationRun {
  const s: Surface = { positions: [], triangles: [], pressurePa: [], wallShearPa: [], sensitivity: [], normalSensitivity: [], protectedMask: [], displacementM: [] };
  const slices = 100, ring = 64;
  for (let i = 0; i <= slices; i++) {
    const x = -2.35 + i / slices * 4.65;
    const [top, width] = section(x);
    for (let j = 0; j < ring; j++) {
      const t = j / ring * Math.PI * 2, sn = Math.sin(t), cs = Math.cos(t);
      const y = .39 + (top - .39) * (Math.sign(sn) * Math.abs(sn) ** .48 + 1) / 2;
      const z = width * Math.sign(cs) * Math.abs(cs) ** .45 * (1 - Math.max(0, y - .93) * .34);
      const locked = x > -1.12 && x < 1.18 && y > .88;
      const sens = Math.exp(-Math.pow((x - 1.55) / .62, 2)) * Math.max(0, y - .45) / .55;
      s.positions.push(x, y, z);
      s.pressurePa.push(480 * Math.exp(-Math.pow((x + 2.3) / .36, 2)) - 310 * Math.exp(-Math.pow((x + .45) / .83, 2)) * Math.max(0, y - .6) - 110 * Math.exp(-Math.pow((x - 1.7) / .65, 2)));
      s.wallShearPa.push(2 + Math.abs(z), .1 * sn, .15 * cs);
      s.sensitivity.push(sens * 32, -sens * 105, -z * sens * 40);
      s.normalSensitivity.push(sens * 100); s.protectedMask.push(locked ? 1 : 0); s.displacementM.push(0);
      if (i < slices) { const a = i * ring + j, b = i * ring + (j + 1) % ring, c = a + ring, d = b + ring; s.triangles.push(a, c, b, b, c, d); }
    }
  }
  // End caps retain the same vertex/index layout in both states.
  for (let j = 1; j < ring - 1; j++) { s.triangles.push(0, j, j + 1); const o = slices * ring; s.triangles.push(o, o + j + 1, o + j); }
  const candidate = structuredClone(s);
  for (let i = 0; i < s.positions.length / 3; i++) {
    const x = s.positions[i * 3], y = s.positions[i * 3 + 1], z = s.positions[i * 3 + 2];
    const weight = s.protectedMask[i] ? 0 : Math.exp(-Math.pow((x - 1.8) / .52, 2)) * Math.max(0, Math.min(1, (y - .42) / .4));
    const dy = -.0032 * weight, dz = -.0018 * z * weight;
    candidate.positions[i * 3 + 1] += dy; candidate.positions[i * 3 + 2] += dz;
    candidate.displacementM[i] = Math.hypot(dy, dz); candidate.pressurePa[i] += 35 * weight;
  }
  return validateRun({ schemaVersion: 'zephyr.surface.v1', runId: 'DEMO-Z01-001', source: 'illustrative', createdAt: '2026-09-17T12:00:00Z',
    coordinates: { units: 'm', up: '+Y', streamwise: '+X', handedness: 'right', fieldAssociation: 'vertex' },
    provenance: { artifactVersion: 'procedural-sedan-v1', modelVersion: 'analytic-demo-v1 (no model executed)', meshHash: 'procedural-101x64-v1', evidenceUrls: [], solver: null },
    conditions: { streamVelocityMps: [32, 0, 0], densityKgM3: 1.225 }, baseline: s, candidate,
    forces: { baselineN: [412, 0, 28], candidateN: [398, 0, 27], predictedDragN: 397.5 },
    constraints: { maxDisplacementM: .004, protectedRegion: 'cabin' },
    trust: { decision: 'accept', predictionErrorPercent: 3.6, thresholdPercent: 10, calibrated: false },
    validation: { geometry: 'illustrative', freshEvaluation: 'illustrative', independentCfd: 'not-run', evidenceIds: [] } });
}
export class DemoAdapter implements SimulationAdapter { async load() { return createDemoRun(); } }
/** Deterministic fixture scaling, not an aerodynamic calculation. */
export function demoAtBudget(budgetMm: number, seed?: SimulationRun): SimulationRun {
  if (!Number.isFinite(budgetMm) || budgetMm <= 0 || budgetMm > 4) throw new Error('Demo budget must be within (0, 4] mm.');
  const run = seed ? structuredClone(seed) : createDemoRun();
  const scale = budgetMm / (Math.max(...run.candidate.displacementM) * 1000);
  run.candidate.positions = run.candidate.positions.map((v, i) => run.baseline.positions[i] + (v - run.baseline.positions[i]) * scale);
  run.candidate.displacementM = run.candidate.displacementM.map(v => v * scale);
  run.candidate.pressurePa = run.candidate.pressurePa.map((v, i) => run.baseline.pressurePa[i] + (v - run.baseline.pressurePa[i]) * scale);
  const delta = 14 * budgetMm / 3.6;
  run.forces.candidateN[0] = run.forces.baselineN[0] - delta;
  run.forces.predictedDragN = run.forces.candidateN[0] - .5 * budgetMm / 3.6;
  return validateRun(run);
}
/** Explicit opt-in only. Errors never fall back to DemoAdapter. Poll load() with AbortSignal for updates. */
export class HttpRunAdapter implements SimulationAdapter {
  private url: string;
  constructor(url: string) { this.url = url; }
  async load(signal?: AbortSignal) {
    const response = await fetch(this.url, { signal, headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error(`Run request failed: HTTP ${response.status}`);
    return validateRun(await response.json());
  }
}
export function decideRequest(brief: string, displacementMm: number): { decision: Decision; message: string } {
  if (!Number.isFinite(displacementMm) || displacementMm <= 0) return { decision: 'refuse', message: 'Invalid displacement budget. A positive finite bound is required.' };
  if (/\b(lower|shrink|reshape|change|move|remove|unlock)\b.{0,30}\b(cabin|roof|windscreen)\b/i.test(brief)) return { decision: 'refuse', message: 'Cabin conflict. The protected envelope cannot move. Revise the brief to use an allowed region.' };
  if (displacementMm > 4) return { decision: 'refuse', message: `${displacementMm} mm exceeds the 4 mm hard limit. Candidate refused; accepted geometry is preserved.` };
  if (displacementMm > 3.6) return { decision: 'shrink', message: 'Demo trust error exceeds 10%. Step shrunk to 3.6 mm before a new illustrative evaluation.' };
  if (!/reduce\s+drag/i.test(brief)) return { decision: 'refuse', message: 'Intent unresolved. This offline preview understands “Reduce drag” only. A real constraint compiler is not connected.' };
  return { decision: 'accept', message: 'Illustrative candidate accepted. Cabin unchanged; bounded rear taper. Independent CFD remains pending.' };
}

