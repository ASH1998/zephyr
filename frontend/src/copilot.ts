import { createRunAssistant } from './run-assistant.ts';
import { api } from './live-data.ts';

export interface IntentRequest { geometryId: string; budgetMm: number; brief: string; mode: 'analysis'|'iteration' }
export interface IntentPlan {
  schemaVersion: 'zephyr.intent.v1'; intentId: string; request: IntentRequest;
  graph: { status:'ready'|'clarify'|'refuse'; message:string; effectiveBudgetMm:number; evidenceQuotes:string[]; handle:string; cabinDisplacementMm:number; topology:string };
  provenance: { model:string; seconds:number; usage?:{total_tokens?:number} };
}
export function sameRequest(a:IntentRequest,b:IntentRequest) {
  return a.geometryId===b.geometryId && a.mode===b.mode && a.budgetMm===b.budgetMm && a.brief.trim()===b.brief.trim();
}
export function validatePlan(value:IntentPlan,request:IntentRequest):IntentPlan {
  if(value?.schemaVersion!=='zephyr.intent.v1' || !/^intent-[a-f0-9]{32}$/.test(value.intentId) || !value.request || !sameRequest(value.request,request))throw new Error('Interpretation does not match this brief. Please retry.');
  const g=value.graph;
  if(!g || !['ready','clarify','refuse'].includes(g.status) || !g.message || !Number.isFinite(g.effectiveBudgetMm) || g.effectiveBudgetMm<=0 || g.effectiveBudgetMm>request.budgetMm || g.effectiveBudgetMm>4 || g.cabinDisplacementMm!==0 || g.topology!=='fixed' || (g.status==='ready' && g.handle!=='rear-width-quintic-v1') || !Array.isArray(g.evidenceQuotes) || !g.evidenceQuotes.length || g.evidenceQuotes.some(q=>typeof q!=='string'||!q.trim()||!request.brief.includes(q)) || !value.provenance?.model)throw new Error('Invalid interpretation constraints. No run started.');
  return value;
}
export interface Explanation {runId:string;source:'llm-ranked-evidence';provenance:{model:string};facts:{id:string;text:string;evidenceId:string}[];evidenceUrl:string;decision:string}
export function validateExplanation(value:Explanation,runId:string) {
  if(value?.runId!==runId || value.source!=='llm-ranked-evidence' || value.evidenceUrl!==`/api/runs/${runId}/evidence` || !Array.isArray(value.facts) || !value.facts.length || value.facts.some(f=>typeof f.text!=='string'||!f.evidenceId.startsWith(runId+':')) || !value.facts.some(f=>f.id==='decision') || !value.facts.some(f=>f.id==='cfd'))throw new Error('Explanation evidence does not match this run.');
  return value;
}
export function createCopilot(getRequest:()=>IntentRequest,lock:(busy:boolean)=>void) {
  const brief=document.querySelector<HTMLTextAreaElement>('#brief')!;
  const panel=document.createElement('section');panel.className='copilot-panel';panel.setAttribute('aria-label','Language model copilot');
  panel.innerHTML='<div class="copilot-heading"><span>BRIEF COPILOT</span><span class="copilot-state">Connecting</span></div><p class="copilot-model"></p><button type="button" class="boundary copilot-interpret">Interpret brief ↗</button><p class="copilot-message" aria-live="polite">Checking the configured language model…</p><details hidden><summary>Compiled constraints</summary><p class="copilot-constraints"></p><p class="copilot-quotes"></p><small class="copilot-meta"></small></details>';
  brief.after(panel);
  const $=<T extends HTMLElement>(s:string)=>panel.querySelector<T>(s)!;
  const preview=$<HTMLButtonElement>('.copilot-interpret');preview.disabled=true;
  const assistant=createRunAssistant();
  let enabled=false,plan:IntentPlan|undefined;
  let healthReady=false, controlsBusy=false;
  const ready=api<{copilot:{enabled:boolean;model?:string;competitionModel?:boolean}}>('/api/health').then(h=>{
    enabled=!!h.copilot?.enabled;assistant.setEnabled(enabled);healthReady=true;preview.disabled=!enabled||controlsBusy;
    $('.copilot-state').textContent=enabled?'Connected':'Disabled';
    $('.copilot-model').textContent=enabled?`${h.copilot.model} · ${h.copilot.competitionModel?'Nemotron':'development model'}`:'Local preset mode';
    $('.copilot-message').textContent=enabled?'Interpret your brief, then run a bounded local evaluation. Model calls use your configured API.':'Start the API with --enable-llm to use the configured model.';
    if(enabled){document.querySelector('#decision-copy')!.textContent='Your brief is interpreted before the local GPU run. The controller enforces the cabin lock and movement limit.';document.querySelector('.dialog-note')!.textContent='Brief interpretation and questions use the configured cloud model. GPU inference runs locally. Model provenance and full-resolution evidence stay in .local.';}
  }).catch(()=>{$('.copilot-state').textContent='Offline';$('.copilot-message').textContent='Local API unavailable. Start it with --enable-llm and reload.';});
  function renderPlan(value:IntentPlan) {
      $('.copilot-state').textContent=value.graph.status==='ready'?'Ready':value.graph.status==='clarify'?'Clarify':'Refused';
      $('.copilot-message').textContent=value.graph.message;
      $('details').hidden=false;
      $('.copilot-constraints').textContent=`${value.graph.effectiveBudgetMm.toFixed(2)} mm maximum · cabin fixed at 0 mm · fixed topology · bounded rear taper`;
      $('.copilot-quotes').textContent=value.graph.evidenceQuotes.map(q=>`“${q}”`).join(' · ');
      $('.copilot-meta').textContent=`${value.provenance.model} · ${value.provenance.seconds.toFixed(1)} s${value.provenance.usage?.total_tokens?` · ${value.provenance.usage.total_tokens} tokens`:''}`;
  }
  async function prepare(request:IntentRequest) {
    await ready;
    if(!healthReady)throw new Error('Local API unavailable. Reload after starting it.');
    if(!enabled)return undefined;
    if(plan && sameRequest(plan.request,request))return plan;
    $('.copilot-state').textContent='Interpreting';$('.copilot-message').textContent='Compiling your brief into the supported constraints…';
    try {
      plan=validatePlan(await api<IntentPlan>('/api/intent',request),request);
      renderPlan(plan);
      return plan;
    }catch(error){$('.copilot-state').textContent='Unavailable';$('.copilot-message').textContent=error instanceof Error?error.message:String(error);throw error;}
  }
  preview.onclick=async()=>{lock(true);try{await prepare(getRequest());}catch{/* Displayed above. */}finally{lock(false);}};
  function invalidate(){plan=undefined;if(enabled){$('.copilot-state').textContent='Brief changed';$('.copilot-message').textContent='Interpretation will refresh before the next run.';$('details').hidden=true;}}
  document.querySelector('#vehicle')!.addEventListener('change',invalidate);brief.addEventListener('input',invalidate);document.querySelector('#budget')!.addEventListener('input',invalidate);
  return {prepare,showResult:assistant.show,restore:(value:IntentPlan)=>{
    plan=validatePlan(value,value.request);renderPlan(plan);brief.value=plan.request.brief;
    const budget=document.querySelector<HTMLInputElement>('#budget')!;budget.value=String(plan.request.budgetMm);
    document.querySelector('#budget-value')!.textContent=`${plan.request.budgetMm.toFixed(1)} mm`;
  },setBusy:(busy:boolean)=>{controlsBusy=busy;preview.disabled=busy||!enabled;},reset:assistant.reset};
}
