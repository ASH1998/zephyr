import test from 'node:test';
import assert from 'node:assert/strict';
import { validateLiveRun, nextEvents, trustPresentation, maximumMovementMm } from '../src/live-data.ts';
import type { LiveRun, Job } from '../src/live-data.ts';
function fixture(): LiveRun {
  const surface={positions:[0,0,0,1,0,0,0,1,0],triangles:[0,1,2],pressurePa:[10,20,30],wallShearPa:Array(9).fill(0),sensitivity:Array(9).fill(0),normalSensitivity:[-1,0,1],protectedMask:[1,0,1],displacementM:[0,0,0]};
  return {schemaVersion:'zephyr.surface.v2',runId:'test-real-contract',source:'live',createdAt:'2026-09-18T00:00:00Z',status:'analysis',coordinates:{units:'m',up:'+Y',streamwise:'+X',handedness:'right',fieldAssociation:'vertex',rotation:[[1,0,0],[0,0,1],[0,-1,0]],upstreamOriginM:[0,0,0],transform:'test'},provenance:{modelVersion:'test fixture, not inference',checkpointSha256:'a'.repeat(64),meshHash:'b'.repeat(64),upstreamCommit:'c'.repeat(40),evidenceUrls:['/api/test'],forceConvention:'D=Fx',fieldTransfer:'area weighted',sensitivityConvention:'d(-Fx)/dX',reduction:{}},conditions:{streamVelocityMps:[38.889,0,0],densityKgM3:1.205},baseline:surface,candidate:null,forces:{baselineN:[600,0,0],baselineDragN:600,candidateN:null,candidateDragN:null,predictedDragN:null},constraints:{maxDisplacementM:.004,protectedRegion:'cabin'},trust:{decision:'refuse',calibrated:false,predictionErrorPercent:null,reason:'Analysis only'},validation:{geometry:'not-run',freshEvaluation:'not-run',independentCfd:'not-run',evidenceIds:['test:baseline'],checks:{}},timings:{}};
}
function comparison(){const r=fixture();r.candidate=structuredClone(r.baseline);r.candidate.positions[3]+=.002;r.candidate.displacementM[1]=.002;r.status='comparison';r.forces.candidateN=[601,0,0];r.forces.candidateDragN=601;r.forces.predictedDragN=599;r.validation.freshEvaluation='passed';return r;}
test('analysis is valid with no invented candidate or candidate force',()=>{assert.equal(validateLiveRun(fixture()).candidate,null);const r=fixture();r.forces.candidateDragN=599;assert.throws(()=>validateLiveRun(r),/invent/);});
test('short sedan comparison stays inspectable without claiming skipped calibration passed',()=>{
  const r=comparison();r.geometryId='drivaer-1';r.executionProfile='sedan-demo-v1';r.validation.geometry='passed';
  r.calibration={status:'not-run'};Object.assign(r.trust,{policyVersion:'sedan-demo-v1',engineeringValidated:false});
  assert.equal(trustPresentation(validateLiveRun(r)).state,'Comparison complete');
  assert.equal(trustPresentation(r).headline,'This change did not help.');
  r.trust.decision='accept';assert.throws(()=>validateLiveRun(r),/demo comparison/);r.trust.decision='refuse';
  r.calibration.status='passed';assert.throws(()=>validateLiveRun(r),/demo comparison/);r.calibration.status='not-run';
  r.geometryId='x57';assert.throws(()=>validateLiveRun(r),/demo comparison/);r.geometryId='drivaer-1';
  r.validation.geometry='failed';assert.equal(trustPresentation(validateLiveRun(r)).state,'Not accepted');
});
test('fresh worsening comparison remains visible with refusal',()=>{const r=comparison();assert.equal(validateLiveRun(r).forces.candidateDragN,601);r.trust.decision='accept';assert.throws(()=>validateLiveRun(r),/unearned/);});
test('local acceptance needs fresh improvement, scoped calibration and completed geometry checks',()=>{
  const r=comparison();r.geometryId='drivaer-1';r.forces.candidateN![0]=599;r.forces.candidateDragN=599;r.validation.geometry='passed';r.validation.checks=Object.fromEntries(['topology','finite','protected','bounds','normals','triangleArea','watertight','symmetricHandle','transition','selfIntersection'].map(k=>[k,{status:'passed'}]));
  r.calibration={status:'passed'};Object.assign(r.trust,{decision:'accept',calibrated:true,calibrationScope:'local-surrogate-handle-only',engineeringValidated:false,predictionErrorN:.01,predictionErrorPercent:1});
  assert.equal(validateLiveRun(r).trust.decision,'accept');assert.equal(trustPresentation(r).state,'Local check passed');assert.match(trustPresentation(r).detail,/0.010 N.*predicted change/);
  assert.match(trustPresentation(r).headline,/further evaluation/);assert.doesNotMatch(trustPresentation(r).candidateLabel,/not accepted/);
  for(const mutate of [(x:LiveRun)=>{x.calibration!.status='failed';},(x:LiveRun)=>{x.trust.engineeringValidated=true;},(x:LiveRun)=>{x.validation.checks.selfIntersection.status='not-run';},(x:LiveRun)=>{x.car={id:'hatchback',label:'test',experimental:true};}]){const c=structuredClone(r);mutate(c);assert.throws(()=>validateLiveRun(c),/unearned/);}
});
test('unresolved small prediction never displays an invented relative error',()=>{
  const r=comparison();Object.assign(r.trust,{predictionErrorN:.01,predictionErrorPercent:null});
  assert.match(trustPresentation(r).detail,/0.010 N.*unresolved/);assert.doesNotMatch(trustPresentation(r).detail,/NaN|Infinity/);
});
test('real contract rejects wrong run, provenance, nonfinite fields and wrong coordinates',()=>{
  assert.throws(()=>validateLiveRun(fixture(),'other'),/identity/);
  for(const mutate of [(r:LiveRun)=>{r.provenance.checkpointSha256='missing';},(r:LiveRun)=>{r.baseline.pressurePa[0]=NaN;},(r:LiveRun)=>{r.coordinates.rotation[2][1]=1;},(r:LiveRun)=>{r.forces.baselineDragN=-600;}]){const r=fixture();mutate(r);assert.throws(()=>validateLiveRun(r));}
});
test('candidate must preserve protected vertices topology and displacement evidence',()=>{
  for(const mutate of [(r:LiveRun)=>{r.candidate!.positions[0]+=.001;},(r:LiveRun)=>{r.candidate!.triangles[0]=1;},(r:LiveRun)=>{r.candidate!.displacementM[1]=.004;},(r:LiveRun)=>{r.validation.freshEvaluation='not-run';}]){const r=comparison();mutate(r);assert.throws(()=>validateLiveRun(r));}
});

test('larger research replays require complete sedan evidence and never grant acceptance',()=>{
  const r=comparison();r.source='recorded';r.geometryId='drivaer-1';r.constraints.maxDisplacementM=.060;
  r.candidate!.positions[3]=1.03;r.candidate!.displacementM[1]=.03;r.forces.predictedDragN=null;
  r.trust.engineeringValidated=false;
  r.research={policyVersion:'sedan-forward-study-v1',planSha256:'a'.repeat(64),candidateRecordSha256:'b'.repeat(64),searchComplete:true,confirmationCount:3,numericalResearchPassed:false,trainingDistributionVerified:false};
  r.validation.checks=Object.fromEntries(['topology','finite','protected','bounds','normals','triangleArea','edgeLength','aspectGrowth','watertight','legalEnvelope','checkpointBounds','selfIntersection'].map(k=>[k,{status:'passed'}]));
  assert.equal(validateLiveRun(r).candidate!.displacementM[1],.03);
  const paused=structuredClone(r);Object.assign(paused.research!,{provisional:true,searchComplete:false,confirmationCount:0,selectionSha256:'c'.repeat(64),phaseCounts:{lhs:100,tpe:90,random:0,confirm:0}});
  assert.equal(validateLiveRun(paused).research!.searchComplete,false);
  for(const mutate of [(x:LiveRun)=>{x.research!.numericalResearchPassed=true;},(x:LiveRun)=>{delete x.research!.selectionSha256;},(x:LiveRun)=>{x.research!.phaseCounts!.tpe=-1;},(x:LiveRun)=>{x.research!.searchComplete=true;}]){const bad=structuredClone(paused);mutate(bad);assert.throws(()=>validateLiveRun(bad));}
  for(const mutate of [(x:LiveRun)=>{x.source='live';},(x:LiveRun)=>{x.geometryId='x57';},(x:LiveRun)=>{x.research!.confirmationCount=2;},(x:LiveRun)=>{x.trust.decision='accept';},(x:LiveRun)=>{x.validation.checks.selfIntersection.status='not-run';},(x:LiveRun)=>{delete x.research;}]){
    const bad=structuredClone(r);mutate(bad);assert.throws(()=>validateLiveRun(bad));
  }
});
test('polling event identities and ordering are guarded and duplicates ignored',()=>{
  const j={runId:'a',source:'live',state:'running',stage:'baseline',detail:'',sequence:2,baselineReady:false,resultReady:false,events:[{runId:'a',source:'live',sequence:1,stage:'baseline',detail:'',completed:1,total:92},{runId:'a',source:'live',sequence:2,stage:'baseline',detail:'',completed:2,total:92}]} as Job;
  assert.equal(nextEvents(j,'a',1).length,1);assert.equal(nextEvents(j,'a',2).length,0);assert.throws(()=>nextEvents(j,'b',0));j.events[1].runId='b';assert.throws(()=>nextEvents(j,'a',0));j.events[1].runId='a';j.events[1].sequence=1;assert.throws(()=>nextEvents(j,'a',0));
});

test('maximum movement uses full resolution evidence when display reduction omits the deepest vertex',()=>{
  const r=comparison();r.constraints.maxDisplacementM=.012;
  r.validation.checks.bounds={status:'passed',maximumM:.011302};
  assert.equal(maximumMovementMm(r),11.302);
  r.validation.checks.bounds.maximumM=NaN;assert.equal(maximumMovementMm(r),2);
  r.validation.checks.bounds.maximumM=.02;assert.equal(maximumMovementMm(r),2);
});

test('synthetic dent is recorded, geometry-screened and cannot imply structural acceptance',()=>{
  const r=comparison();r.source='recorded';r.geometryId='drivaer-1';r.constraints.maxDisplacementM=.012;
  r.forces.predictedDragN=null;r.trust.engineeringValidated=false;
  r.syntheticDent={schemaVersion:'zephyr.synthetic-dent.v1',scenarioSha256:'c'.repeat(64),preset:{name:'synthetic-hood-dent-v1',depthMm:12,scope:'Synthetic geometry only'},trainingDistributionVerified:false,structuralAssessment:false,roadworthinessAssessment:false};
  r.validation.checks=Object.fromEntries(['topology','finite','protected','bounds','normals','triangleArea','edgeLength','aspectGrowth','watertight','legalEnvelope','checkpointBounds','selfIntersection'].map(k=>[k,{status:'passed'}]));
  assert.equal(validateLiveRun(r).syntheticDent!.preset.depthMm,12);
  assert.match(trustPresentation(r).headline,/Synthetic dent/);
  for(const mutate of [(x:LiveRun)=>{x.source='live';},(x:LiveRun)=>{x.geometryId='x57';},(x:LiveRun)=>{x.syntheticDent!.scenarioSha256='';},(x:LiveRun)=>{x.trust.decision='accept';},(x:LiveRun)=>{x.validation.checks.selfIntersection.status='not-run';},(x:LiveRun)=>{x.constraints.maxDisplacementM=.013;},(x:LiveRun)=>{delete x.syntheticDent;}]){const bad=structuredClone(r);mutate(bad);assert.throws(()=>validateLiveRun(bad));}
});
