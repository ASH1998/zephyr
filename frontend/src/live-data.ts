import { validateAirflow } from './airflow.ts';
import type { Airflow } from './airflow.ts';
import type { IntentPlan } from './copilot';
import type { Surface, Vec3 } from './data.ts';
export interface LiveRun {
  geometryId?:string;car?:{id:string;label:string;experimental:boolean};airflow?:{baseline:Airflow;candidate?:Airflow};airflowStatus?:string;airflowError?:string;
  intent?: IntentPlan;
  schemaVersion: 'zephyr.surface.v2'; runId: string; source: 'live' | 'recorded'; createdAt: string; status: 'analysis' | 'comparison';
  coordinates: { units: 'm'; up: '+Y'; streamwise: '+X'; handedness: 'right'; fieldAssociation: 'vertex'; rotation: number[][]; upstreamOriginM: Vec3; transform: string };
  provenance: { modelVersion: string; checkpointSha256: string; meshHash: string; upstreamCommit: string; evidenceUrls: string[]; forceConvention: string; fieldTransfer: string; sensitivityConvention: string; reduction: Record<string, unknown>; [key: string]: unknown };
  conditions: { streamVelocityMps: Vec3; densityKgM3: number };
  baseline: Surface; candidate: Surface | null;
  forces: { baselineN: Vec3; candidateN: Vec3 | null; baselineDragN: number; candidateDragN: number | null; predictedDragN: number | null };
  constraints: { maxDisplacementM: number; protectedRegion: string };
  trust: { decision: 'refuse' | 'shrink' | 'accept'; calibrated: boolean; predictionErrorPercent: number | null; reason: string; predictionErrorN?:number; predictionErrorBaselinePercent?:number|null; reductionRatio?:number|null; calibrationScope?:string; engineeringValidated?:boolean; policyVersion?:string };
  calibration?: {status:string; policyVersion?:string; slopeDisagreementPercent?:number; numericalFloorN?:number; samples?:unknown[]};
  validation: { geometry: string; freshEvaluation: string; independentCfd: string; evidenceIds: string[]; checks: Record<string, { status: string; detail?: string }> };
  timings: Record<string, number>;
}
export interface JobEvent { runId: string; source: 'live'; sequence: number; stage: string; detail: string; completed?: number; total?: number }
export interface Job { createdAt?:string; runId: string; source: 'live'; state: 'running' | 'cancelling' | 'cancelled' | 'failed' | 'complete'; stage: string; detail: string; sequence: number; events: JobEvent[]; baselineReady: boolean; resultReady: boolean }
const fail = (s: string): never => { throw new Error(`Live data rejected: ${s}`); };
const finite = (a: unknown, n?: number): a is number[] => Array.isArray(a) && (n === undefined || a.length === n) && a.every(Number.isFinite);
export function validateLiveRun(input: unknown, runId?: string): LiveRun {
  const r = input as LiveRun;
  if (!r || r.schemaVersion !== 'zephyr.surface.v2' || !['live', 'recorded'].includes(r.source) || !r.runId || (runId && r.runId !== runId) || !Number.isFinite(Date.parse(r.createdAt))) fail('identity/source');
  if (r.coordinates?.units !== 'm' || r.coordinates.up !== '+Y' || r.coordinates.streamwise !== '+X' || r.coordinates.handedness !== 'right' || r.coordinates.fieldAssociation !== 'vertex') fail('coordinate convention');
  if (JSON.stringify(r.coordinates.rotation) !== '[[1,0,0],[0,0,1],[0,-1,0]]' || !finite(r.coordinates.upstreamOriginM, 3)) fail('coordinate transform');
  for (const key of ['checkpointSha256', 'meshHash', 'upstreamCommit'] as const) if (!/^[a-f0-9]{40,64}$/.test(r.provenance?.[key] ?? '')) fail('hash provenance');
  if (!r.provenance.evidenceUrls?.length || !r.provenance.forceConvention || !r.provenance.fieldTransfer || !r.provenance.sensitivityConvention || !r.validation?.evidenceIds?.length) fail('field/force evidence');
  if (!finite(r.conditions?.streamVelocityMps, 3) || !Number.isFinite(r.conditions.densityKgM3) || r.conditions.densityKgM3 <= 0 || !Number.isFinite(r.constraints?.maxDisplacementM) || r.constraints.maxDisplacementM <= 0 || r.constraints.maxDisplacementM > .004) fail('conditions/bounds');
  for (const s of [r.baseline, ...(r.candidate ? [r.candidate] : [])]) {
    if (!s || !finite(s.positions) || s.positions.length < 9 || s.positions.length % 3 || s.positions.length > 600000) fail('vertices');
    const n = s.positions.length / 3;
    if (!finite(s.triangles) || !s.triangles.length || s.triangles.length % 3 || s.triangles.some(i => !Number.isInteger(i) || i < 0 || i >= n)) fail('triangles');
    for (const k of ['pressurePa', 'normalSensitivity', 'protectedMask', 'displacementM'] as const) if (!finite(s[k], n)) fail(k);
    for (const k of ['wallShearPa', 'sensitivity'] as const) if (!finite(s[k], n * 3)) fail(k);
    if(s.displayColor&&(!finite(s.displayColor,n*3)||s.displayColor.some(c=>c<0||c>1)))fail('car colors');
    if (s.protectedMask.some(v => v !== 0 && v !== 1) || s.displacementM.some(v => v < 0)) fail('mask/displacement');
  }
  if (r.baseline.displacementM.some(d => d !== 0)) fail('baseline displacement');
  if (!finite(r.forces?.baselineN, 3) || !Number.isFinite(r.forces.baselineDragN) || Math.abs(r.forces.baselineDragN - r.forces.baselineN[0]) > 1e-6) fail('force convention');
  if (r.candidate) {
    if (r.status !== 'comparison' || r.validation.freshEvaluation !== 'passed' || !finite(r.forces.candidateN, 3) || !Number.isFinite(r.forces.candidateDragN) || !Number.isFinite(r.forces.predictedDragN) || Math.abs(r.forces.candidateDragN! - r.forces.candidateN![0]) > 1e-6) fail('candidate evaluation');
    const b = r.baseline, c = r.candidate;
    if (b.positions.length !== c.positions.length || b.triangles.length !== c.triangles.length || b.triangles.some((v, i) => v !== c.triangles[i])) fail('topology');
    for (let i = 0; i < b.protectedMask.length; i++) {
      const d = Math.hypot(c.positions[i*3]-b.positions[i*3], c.positions[i*3+1]-b.positions[i*3+1], c.positions[i*3+2]-b.positions[i*3+2]);
      if (b.protectedMask[i] !== c.protectedMask[i] || (b.protectedMask[i] && d !== 0) || d > r.constraints.maxDisplacementM + 1e-10 || Math.abs(d-c.displacementM[i]) > 1e-9) fail('protected/bounded displacement');
    }
  } else if (r.status !== 'analysis' || r.forces.candidateN !== null || r.forces.candidateDragN !== null || r.forces.predictedDragN !== null || r.validation.freshEvaluation !== 'not-run') fail('analysis must not invent a candidate');
  if (!r.trust || !['refuse', 'shrink', 'accept'].includes(r.trust.decision) || typeof r.trust.calibrated !== 'boolean' || !r.trust.reason || (r.trust.predictionErrorPercent !== null && (!Number.isFinite(r.trust.predictionErrorPercent) || r.trust.predictionErrorPercent < 0))) fail('trust');
  if (r.trust.decision === 'accept' && (!r.candidate || !r.trust.calibrated || r.validation.geometry !== 'passed' ||
      r.calibration?.status !== 'passed' || r.trust.calibrationScope !== 'local-surrogate-handle-only' || r.trust.engineeringValidated !== false ||
      r.forces.candidateDragN! >= r.forces.baselineDragN || r.car?.experimental || r.geometryId !== 'drivaer-1' ||
      ['topology','finite','protected','bounds','normals','triangleArea','watertight','symmetricHandle','transition','selfIntersection'].some(key=>r.validation.checks[key]?.status!=='passed') || Object.values(r.validation.checks).some(c=>c.status!=='passed'))) fail('unearned acceptance');
  if(r.airflow){const id=r.geometryId??r.intent?.request.geometryId??'drivaer-1';validateAirflow(r.airflow.baseline,id,r.provenance.meshHash);if(r.airflow.candidate)validateAirflow(r.airflow.candidate,id,String(r.provenance.candidateMeshHash));}
  return r;
}
export function trustPresentation(run:LiveRun) {
  const t=run.trust;
  const state=!run.candidate?'Analysis only':t.decision==='accept'?'Local check passed':t.decision==='shrink'?'Smaller step needed':'Not accepted';
  const detail=t.predictionErrorN!==undefined?`Prediction difference ${t.predictionErrorN.toFixed(3)} N${t.predictionErrorPercent===null?' · relative change unresolved':` · ${t.predictionErrorPercent.toFixed(1)}% of predicted change`}. Local surrogate check only.`:
    t.predictionErrorPercent===null?'No validated local prediction':`Legacy change-relative error ${t.predictionErrorPercent.toFixed(1)}% · uncalibrated`;
  const headline=!run.candidate?'Original shape tested.':t.decision==='accept'?'Local check passed. Ready for further evaluation.':
    run.forces.candidateDragN!>=run.forces.baselineDragN?'This change did not help.':'Lower predicted resistance. Step not accepted.';
  const candidateLabel=t.decision==='accept'?'Evaluated candidate · local check passed':'Evaluated candidate · not accepted';
  return {state,detail,headline,candidateLabel};
}
export function nextEvents(job: Job, runId: string, sequence: number): JobEvent[] {
  if (job.runId !== runId || job.source !== 'live' || !Array.isArray(job.events)) fail('job identity');
  let last = 0;
  for (const event of job.events) {
    if (event.runId !== runId || event.source !== 'live' || !Number.isInteger(event.sequence) || event.sequence <= last) fail('event identity/order');
    if (event.completed !== undefined && (!Number.isInteger(event.completed) || !Number.isInteger(event.total) || event.completed < 0 || event.completed > event.total!)) fail('batch progress');
    last = event.sequence;
  }
  return job.events.filter(e => e.sequence > sequence);
}
export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, { ...(body === undefined ? {} : {method: 'POST', body: JSON.stringify(body), headers: {'Content-Type': 'application/json'}}), signal: AbortSignal.timeout(120000) });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || `Local API HTTP ${response.status}`);
  }
  return response.json();
}
