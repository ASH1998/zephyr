import {api} from './live-data';
import type {IntentRequest,IntentPlan} from './copilot';
import {bodyRegions} from './body-regions';

interface Trial {runId:string;label:string;state:string;movementMm?:number;seconds?:number;forces?:{baselineDragN:number;candidateDragN:number|null};trust?:{decision:string;reason:string}}
interface Study {studyId:string;createdAt?:string;state:string;intent?:IntentPlan;runs:Trial[];plannedHandles:string[];currentRunId:string|null;conclusion?:string;error?:string;recommendedRunId?:string|null}
export function createExploration(request:()=>IntentRequest,prepare:(r:IntentRequest)=>Promise<IntentPlan|undefined>,lock:(busy:boolean)=>void,observeRun:(id:string,context:string)=>void=()=>{}){
  const root=document.createElement('section');root.className='exploration-panel';root.setAttribute('aria-label','Design exploration and history');
  root.innerHTML='<h3>Explore the body</h3><p>Shape the nose, hood, sides or rear deck. The cabin and lower wheel/ground envelope stay fixed. Every region gets fresh DoMINO probes and a separate candidate.</p><label>Design region <select class="region-select"><option value="compare-body-regions">Compare all 5 body regions</option></select></label><p>Uses the displacement slider above (up to 4 mm). A five-region sedan search can take 25 minutes or longer.</p><button class="region-run" type="button">Run selected region search</button><p class="region-note">Explicit presets use your region selection and slider; they do not interpret the free-text brief. Use the copilot below for additional brief constraints.</p><button class="explore-start" type="button">Interpret exploration brief with copilot</button><p class="explore-plan" role="status"></p><button class="explore-confirm" type="button" hidden>Run this exploration</button><button class="explore-cancel" type="button" hidden>Cancel exploration</button><div class="explore-results"></div><details><summary>Previous runs</summary><button class="history-refresh" type="button">Refresh history</button><div class="run-history"></div></details>';
  document.querySelector('#iterate')!.before(root);
  const start=root.querySelector<HTMLButtonElement>('.explore-start')!,confirm=root.querySelector<HTMLButtonElement>('.explore-confirm')!,cancel=root.querySelector<HTMLButtonElement>('.explore-cancel')!,status=root.querySelector('.explore-plan')!,results=root.querySelector('.explore-results')!;
  let studyId:string|null=null,plan:IntentPlan|undefined,externalBusy=false;
  const region=root.querySelector<HTMLSelectElement>('.region-select')!,preset=root.querySelector<HTMLButtonElement>('.region-run')!;
  for(const [id,label] of bodyRegions){const option=document.createElement('option');option.value=id;option.textContent=label;region.append(option);}
  preset.onclick=async()=>{if(externalBusy||studyId)return;setBusy(true);try{const r=request();const study=await api<Study>('/api/preset-runs',{geometryId:r.geometryId,budgetMm:r.budgetMm,handle:region.value});studyId=study.studyId;sessionStorage.setItem('zephyr-study',studyId);confirm.hidden=true;void poll();}catch(e){status.textContent=e instanceof Error?e.message:String(e);setBusy(false);}};
  function setBusy(busy:boolean){lock(busy);start.disabled=busy;confirm.disabled=busy;cancel.hidden=!studyId||!busy;}
  function render(study:Study){
    if(study.intent?.graph.handle)region.value=study.intent.graph.handle;
    const current=study.runs.findIndex(r=>r.runId===study.currentRunId);
    const regionContext=study.state==='running'&&current>=0?`Region ${current+1} of ${study.plannedHandles.length} · ${study.runs[current].label}`:'';
    const liveRun=study.currentRunId??study.runs.at(-1)?.runId;if(liveRun)observeRun(liveRun,regionContext);
    results.replaceChildren();
    const table=document.createElement('table');table.className='exploration-table';
    const header=document.createElement('tr');for(const title of ['Region','Drag change','Movement','Local check','Result']){const th=document.createElement('th');th.textContent=title;header.append(th);}table.append(header);
    for(const r of study.runs){const tr=document.createElement('tr');const f=r.forces;const delta=f&&f.candidateDragN!==null?f.candidateDragN-f.baselineDragN:null;
      for(const value of [r.label,delta===null?'—':`${delta>0?'+':''}${delta.toFixed(4)} N (${(100*delta/f!.baselineDragN).toFixed(4)}%)`,r.movementMm===undefined?'—':`${r.movementMm.toFixed(3)} mm`,r.trust?.decision==='accept'?'Passed; CFD pending':r.trust?'Refused':r.state]){const td=document.createElement('td');td.textContent=value;tr.append(td);}
      const td=document.createElement('td');if(r.state==='complete'){const a=document.createElement('a');a.href=`/?replay=${r.runId}`;a.target='_blank';a.rel='noopener';a.textContent='Inspect ↗';td.append(a);}tr.append(td);table.append(tr);
      if(r.trust){const row=document.createElement('tr'),cell=document.createElement('td');cell.colSpan=5;cell.textContent=r.trust.reason;row.append(cell);table.append(row);}
    }
    const completed=study.runs.filter(r=>r.state==='complete');
    const durations=completed.map(r=>r.seconds).filter((s):s is number=>typeof s==='number'&&Number.isFinite(s)&&s>0);
    const started=Date.parse(study.createdAt??'');
    const elapsed=Number.isFinite(started)?` ${Math.floor(Math.max(0,Date.now()-started)/60000)} min elapsed overall.`:'';
    const estimate=durations.length?` Estimated total: about ${Math.ceil(durations.reduce((a,b)=>a+b,0)/durations.length*study.plannedHandles.length/60)} min, based on completed regions; later regions may take longer.`:'';
    results.append(table);status.textContent=study.conclusion??study.error??`${regionContext||'Preparing next region'}. ${completed.length} of ${study.plannedHandles.length} regions complete.${elapsed}${estimate} Calculation phases repeat for each region; the batch percentage resets for each GPU pass.`;
  }
  async function poll(){if(!studyId)return;try{const study=await api<Study>(`/api/studies/${studyId}`);render(study);if(study.state==='running'){setBusy(true);window.setTimeout(()=>void poll(),1500);}else{studyId=null;sessionStorage.removeItem('zephyr-study');setBusy(false);void history();}}catch(e){status.textContent=`${e instanceof Error?e.message:String(e)}. Exploration identity retained; reconnecting…`;window.setTimeout(()=>void poll(),3000);}}
  start.onclick=async()=>{if(externalBusy||studyId)return;setBusy(true);confirm.hidden=true;try{plan=await prepare({...request(),mode:'exploration'});if(!plan)throw new Error('Enable the copilot to plan an exploration');status.textContent=plan.graph.message;confirm.hidden=plan.graph.status!=='ready';confirm.textContent=plan.graph.handle==='compare-body-regions'?'Run 5 body regions':plan.graph.handle==='compare-rear-tapers'?'Run 3 bounded profiles':'Run selected region';}catch(e){status.textContent=e instanceof Error?e.message:String(e);}finally{setBusy(false);}};
  confirm.onclick=async()=>{if(!plan||studyId||externalBusy)return;setBusy(true);try{const current={...request(),mode:'exploration' as const};if(JSON.stringify(current)!==JSON.stringify(plan.request)){// Server also checks exact binding; compare fields independent of ordering.
      if(current.brief.trim()!==plan.request.brief||current.geometryId!==plan.request.geometryId||current.budgetMm!==plan.request.budgetMm)throw new Error('Brief or limits changed. Interpret exploration again.');}
      const study=await api<Study>('/api/studies',{...current,intentId:plan.intentId});studyId=study.studyId;sessionStorage.setItem('zephyr-study',studyId);confirm.hidden=true;void poll();
    }catch(e){status.textContent=e instanceof Error?e.message:String(e);setBusy(false);}};
  cancel.onclick=async()=>{if(studyId){await api(`/api/studies/${studyId}/cancel`,{});status.textContent='Cancelling current calculation and remaining profiles…';}};
  async function history(){const target=root.querySelector('.run-history')!;try{const data=await api<{runs:{runId:string;geometryId:string;handle:string|null;decision:string;forces:{baselineDragN:number;candidateDragN:number|null}}[]}>('/api/runs');target.replaceChildren();for(const r of data.runs){const p=document.createElement('p'),a=document.createElement('a');a.href=`/?replay=${r.runId}`;a.textContent=`${r.geometryId} · ${r.handle??'baseline'} · ${r.forces.candidateDragN===null?'baseline only':r.decision==='accept'?'local check passed':'refused'} · ${r.runId.slice(-8)}`;p.append(a);target.append(p);}}catch{target.textContent='History unavailable; check the local API.';}}
  root.querySelector<HTMLButtonElement>('.history-refresh')!.onclick=()=>void history();void history();
  const saved=sessionStorage.getItem('zephyr-study');if(saved&&/^study-[a-f0-9]{32}$/.test(saved)){studyId=saved;queueMicrotask(()=>{setBusy(true);void poll();});}
  return {setBusy(value:boolean){externalBusy=value;start.disabled=value||!!studyId;confirm.disabled=value||!!studyId;preset.disabled=region.disabled=value||!!studyId;root.hidden=request().geometryId==='x57'||request().geometryId==='global-hawk';},isRunning:()=>!!studyId};
}
