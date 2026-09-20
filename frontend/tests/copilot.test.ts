import test from 'node:test';
import assert from 'node:assert/strict';
import {sameRequest,validatePlan,validateExplanation} from '../src/copilot.ts';
import {bodyRegions,comparisonTools} from '../src/body-regions.ts';
const request={geometryId:'drivaer-1',budgetMm:3.6,brief:'Reduce drag.',mode:'iteration' as const};
const plan={schemaVersion:'zephyr.intent.v1' as const,intentId:'intent-'+'a'.repeat(32),request,graph:{status:'ready' as const,message:'Ready',effectiveBudgetMm:2,evidenceQuotes:['Reduce drag.'],handle:'rear-width-quintic-v1',cabinDisplacementMm:0,topology:'fixed'},provenance:{model:'test-model',seconds:1}};
test('every body region is supported but comparisons require exploration',()=>{
  for(const [handle] of bodyRegions)assert.doesNotThrow(()=>validatePlan({...plan,graph:{...plan.graph,handle}},request));
  for(const handle of comparisonTools){
    assert.throws(()=>validatePlan({...plan,graph:{...plan.graph,handle}},request));
    const exploration={...request,mode:'exploration' as const};
    assert.doesNotThrow(()=>validatePlan({...plan,request:exploration,graph:{...plan.graph,handle}},exploration));
  }
});
test('plan binds all run inputs and fixed constraints',()=>{
  assert.equal(validatePlan(plan,request),plan);
  for(const patch of [{brief:'Move cabin'},{budgetMm:4},{mode:'analysis' as const},{geometryId:'other'}]){assert.equal(sameRequest(request,{...request,...patch}),false);assert.throws(()=>validatePlan(plan,{...request,...patch}));}
  for(const patch of [{effectiveBudgetMm:4},{cabinDisplacementMm:1},{handle:'raw-vertices'},{evidenceQuotes:['invented']}])assert.throws(()=>validatePlan({...plan,graph:{...plan.graph,...patch}},request));
});
test('explanation must match the displayed run and retain decision and CFD',()=>{
  const runId='local-'+'a'.repeat(32),e={runId,source:'llm-ranked-evidence' as const,provenance:{model:'test-model'},facts:['decision','cfd'].map(id=>({id,text:id,evidenceId:runId+':'+id})),evidenceUrl:`/api/runs/${runId}/evidence`,decision:'refuse'};
  assert.equal(validateExplanation(e,runId),e);
  assert.throws(()=>validateExplanation(e,'local-'+'b'.repeat(32)));
  assert.throws(()=>validateExplanation({...e,facts:e.facts.slice(1)},runId));
});
