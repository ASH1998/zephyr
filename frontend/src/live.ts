import { previewSurface } from './geometry-preview';
import { createCopilot } from './copilot';
import { FlowScene } from './scene';
import { fieldRange } from './data';
import type { ViewMode } from './data';
import { api, nextEvents, validateLiveRun } from './live-data';
import type { Job, JobEvent, LiveRun } from './live-data';

export async function startLive() {
  const $ = <T extends HTMLElement>(s: string) => document.querySelector<T>(s)!;
  let scene: FlowScene | undefined, run: LiveRun | undefined, jobId: string | undefined;
  let active=false, sequence=0, baselineLoaded=false, resultLoaded=false, explainNewRun=false, explanationRequested=false, restoredIntent=false;
  let view: ViewMode='airflow';
  let flowPaused=matchMedia('(prefers-reduced-motion: reduce)').matches;
  const button=$<HTMLButtonElement>('#iterate'), budget=$<HTMLInputElement>('#budget'), compare=$<HTMLInputElement>('#compare'), magnify=$<HTMLInputElement>('#magnify');
  magnify.checked=false;$('#app').classList.add('live-workspace');
  const text=(selector:string,value:string)=>{$(selector).textContent=value;};
  const status=(title:string,detail:string)=>{text('#decision-title',title);text('#decision-copy',detail);};
  text('footer > span:first-child','DRIVAERML / SAMPLE 1');text('#run-id','NO RUN YET');$('.metrics').setAttribute('aria-label','Surrogate evaluation metrics');text('#run-source','LOCAL GPU');text('.demo-tag','DoMINO');
  $('#vehicle').replaceChildren(new Option('DrivAerML · official sample 1','drivaer-1'));$<HTMLSelectElement>('#vehicle').disabled=true;
  text('.metric-main .eyebrow b','SURROGATE');text('.metric-main p','No inference yet · actual fields appear after the GPU run');
  for(const s of ['.baseline-value','#candidate-force','#delta','#displacement'])text(s,'—');
  text('#scale-caption','No candidate yet');text('#trust-state','Not evaluated');text('#trust-detail','Trust radius uncalibrated');text('.proof-value','Not run');text('.metrics .metric:last-child p','Local surrogate · independent CFD not run');
  status('Ready for real local inference','Run the official sample on your GPU. The local preset locks the cabin and tests one bounded rear taper. Language model connection is being checked.');
  for(const s of ['.flow-label','.wake-key','.rear-callout','.cabin-label','#motion','.asset-credit','.comparison'])$(s).hidden=true;
  $('[data-mode="airflow"]').removeAttribute('disabled');
  text('.flow-label','→ ILLUSTRATIVE AIRFLOW');
  for(const key of ['pressure','sensitivity','displacement'])$(`[data-mode="${key}"]`).setAttribute('disabled','');
  text('#legend','Illustrative airflow · animated paths, not a computed velocity field');text('#evidence-dialog h2','Every result has a source.');
  text('#evidence-dialog > p','The local GPU runs NVIDIA’s open DoMINO checkpoint on the installed DrivAerML sample. Pressure and sensitivity are surrogate outputs, not CFD ground truth. Airflow is an illustrative animation around the geometry; its paths and animation speed are not computed fluid velocities.');
  text('.dialog-note','No cloud resources or paid calls. Full-resolution VTK and logs stay in .local/runs. Display geometry is reduced; forces use the full mesh.');
  text('#export','Download run JSON');$<HTMLButtonElement>('#export').disabled=true;text('#refuse','Test 12 mm boundary');
  const analyze=document.createElement('button');analyze.className='boundary';analyze.textContent='Run baseline analysis only';button.after(analyze);
  const cancel=document.createElement('button');cancel.className='boundary';cancel.textContent='Cancel GPU job';cancel.hidden=true;analyze.after(cancel);
  const demo=document.createElement('a');demo.className='quiet';demo.href='?demo=1';demo.textContent='Open illustrative design walkthrough ↗';cancel.after(demo);
  const progress=document.createElement('progress');progress.className='live-progress';progress.max=1;progress.hidden=true;$('#story-narration').append(progress);
  const brief=$<HTMLTextAreaElement>('#brief');
  const getRequest=(mode:'analysis'|'iteration'='iteration',budgetMm=+budget.value)=>({geometryId:'drivaer-1',budgetMm,brief:brief.value,mode});
  function lockControls(busy:boolean){button.disabled=analyze.disabled=budget.disabled=brief.disabled=busy;copilot.setBusy(busy);}
  const copilot=createCopilot(()=>getRequest(),busy=>{active=busy;lockControls(busy);});
  function mode(value:ViewMode) {
    view=value;scene?.setMode(value);scene?.setStory(value==='displacement' && run?.candidate ? 'result' : undefined);$('.rear-callout').hidden=!(value==='displacement' && run?.candidate);if(value==='sensitivity' && run)blend(0);
    document.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach(b=>{const on=b.dataset.mode===value;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});
    text('#show-candidate',value==='airflow'?'02 Candidate geometry':'02 Candidate + change map');
    $('.flow-label').hidden=value!=='airflow';$('#motion').hidden=value!=='airflow';
    if(value==='airflow'){text('#legend','Illustrative airflow · same paths for both shapes · animation speed is not air velocity');return;}
    if(!run){text('#legend','DrivAerML geometry preview · run inference for measured surface fields');return;}
    const range=fieldRange(value==='sensitivity'?run.baseline.normalSensitivity:run.baseline.pressurePa), candidateRange=run.candidate?fieldRange(run.candidate.pressurePa):range;const lo=value==='pressure'?Math.min(range[0],candidateRange[0]):range[0],hi=value==='pressure'?Math.max(range[1],candidateRange[1]):range[1];
    const mm=run.candidate?fieldRange(run.candidate.displacementM)[1]*1000:0;
    const label=value==='pressure'?`Pressure · ${lo.toFixed(0)} to ${hi.toFixed(0)} Pa`:value==='sensitivity'?`Baseline normal sensitivity · ${lo.toFixed(2)} to ${hi.toFixed(2)} N/m · signed asinh color scale`:value==='displacement'?`Actual displacement · 0–${mm.toFixed(2)} mm`:`${(run.baseline.positions.length/3).toLocaleString()} display vertices · reduced mesh`;
    $('#legend').replaceChildren();const scale=document.createElement('span');scale.className=`color-scale ${value}`;$('#legend').append(scale,label+' · live surrogate');
  }
  document.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach(b=>b.onclick=()=>mode(b.dataset.mode as ViewMode));
  function blend(v:number){$('.rear-callout').hidden=!(view==='displacement' && run?.candidate && v>0);compare.value=String(v);scene?.setBlend(v/100);text('#compare-status',v===0?'Baseline geometry':v===100?'Evaluated candidate · not accepted':`${v}% geometry blend`);$('#show-baseline').setAttribute('aria-pressed',String(v===0));$('#show-candidate').setAttribute('aria-pressed',String(v===100));}
  compare.oninput=()=>blend(+compare.value);$('#show-baseline').onclick=()=>blend(0);$('#show-candidate').onclick=()=>{if(view!=='airflow')mode('displacement');blend(100);};
  magnify.onchange=()=>{scene?.setMagnified(magnify.checked);text('#result-scale',magnify.checked?'Shape ×24 · field in actual mm':'True-scale shape · field in actual mm');};
  function updateMotion(){scene?.setPaused(flowPaused);text('#motion',flowPaused?'▷ Resume flow':'Ⅱ Pause flow');$('#motion').setAttribute('aria-pressed',String(flowPaused));}
  $('#motion').onclick=()=>{flowPaused=!flowPaused;updateMotion();};updateMotion();
  $('#camera').onclick=()=>scene?.resetCamera();budget.oninput=()=>text('#budget-value',`${(+budget.value).toFixed(1)} mm`);
  function install(payload:LiveRun) {
    if(payload.intent && !restoredIntent){copilot.restore(payload.intent);restoredIntent=true;}
    run=payload;scene?.dispose();scene=new FlowScene($('#scene'),run);updateMotion();for(const key of ['pressure','sensitivity','displacement'])$(`[data-mode="${key}"]`).removeAttribute('disabled');scene.setMagnified(magnify.checked);mode(view);blend(0);
    $('.cabin-label').hidden=false;$('.viewport').classList.add('story-active');$('#run-story').hidden=false;
    text('.baseline-value',`${run.forces.baselineDragN.toFixed(2)} N`);text('#candidate-force',run.forces.candidateDragN===null?'—':`${run.forces.candidateDragN.toFixed(2)} N`);
    const delta=run.forces.candidateDragN===null?null:(run.forces.candidateDragN-run.forces.baselineDragN)/run.forces.baselineDragN*100;
    text('#delta',delta===null?'Baseline only':`${delta>0?'+':''}${delta.toFixed(3)}%`);$('#delta').classList.toggle('worse',delta!==null&&delta>=0);
    text('.metric-main p',run.candidate?'Fresh baseline vs candidate · surrogate, not CFD':'Actual baseline · candidate has not been evaluated');
    const mm=run.candidate?fieldRange(run.candidate.displacementM)[1]*1000:0;
    text('#displacement',run.candidate?`${mm.toFixed(2)} mm`:'No candidate');text('#scale-caption',run.candidate?`Actual maximum: ${mm.toFixed(2)} mm · cabin 0.00 mm`:'Analysis only');text('#run-id',run.runId);
    text('#trust-state',run.candidate?'Refused':'Analysis only');text('#trust-detail',run.trust.predictionErrorPercent===null?'Trust radius uncalibrated':`Prediction error ${run.trust.predictionErrorPercent.toFixed(1)}% · uncalibrated`);
    text('.proof-value','CFD pending');text('.metrics .metric:last-child p',`Geometry: ${run.validation.geometry} · fresh evaluation: ${run.validation.freshEvaluation}`);
    for(const s of ['.comparison','.result-controls','#story-result'])$(s).hidden=!run.candidate;
    if(run.candidate){text('#result-label','FRESH SURROGATE COMPARISON · NOT ACCEPTED');text('#result-before',`${run.forces.baselineDragN.toFixed(2)} N`);text('#result-after',`${run.forces.candidateDragN!.toFixed(2)} N`);text('#result-delta',`${delta!>0?'+':''}${delta!.toFixed(3)}%`);$('#result-delta').classList.toggle('worse',delta!>=0);text('#result-scale',magnify.checked?'Shape ×24 · field in actual mm':'True-scale shape · field in actual mm');text('#rear-displacement',`${mm.toFixed(2)} mm actual movement`);if(view!=='airflow')mode('displacement');blend(100);}
    $('#provenance').replaceChildren();
    const rows:Record<string,string>={Run:run.runId,Source:run.source,Model:run.provenance.modelVersion,'Checkpoint SHA-256':run.provenance.checkpointSha256,'Mesh SHA-256':run.provenance.meshHash,'Upstream commit':run.provenance.upstreamCommit,Coordinates:'Metres · upstream (X,Y,Z) → (X,Z,−Y), translated to centre/ground',Forces:run.provenance.forceConvention,Fields:run.provenance.fieldTransfer,Sensitivity:run.provenance.sensitivityConvention,Reduction:JSON.stringify(run.provenance.reduction),Timings:JSON.stringify(run.timings),Decision:run.trust.reason,Checks:JSON.stringify(run.validation.checks)};
    if(run.intent){rows['Brief model']=run.intent.provenance.model;rows['Compiled brief']=run.intent.request.brief;rows['Intent ID']=run.intent.intentId;rows['Compiled ceiling']=`${run.intent.graph.effectiveBudgetMm} mm`;}
    for(const [key,value] of Object.entries(rows)){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=key;dd.textContent=value;$('#provenance').append(dt,dd);}
    for(const url of run.provenance.evidenceUrls){const a=document.createElement('a');a.href=url;a.textContent='Machine-readable evidence ↗';a.target='_blank';a.rel='noopener';$('#provenance').append(a);}
    $<HTMLButtonElement>('#export').disabled=false;
  }
  function event(e:JobEvent){
    $('.viewport').classList.add('story-active');$('#run-story').hidden=false;text('#story-source','LIVE LOCAL SURROGATE · NVIDIA DoMINO');
    const titles:Record<string,string>={loading:'Load the real model.',baseline:'Compute pressure and sensitivity.',smoothing:'Smooth the model gradient.',converting:'Prepare the surface fields.','baseline-ready':'The baseline is ready.',candidate:'Make one bounded rear taper.',validate:'Check the shape. Keep the cabin.',evaluate:'Evaluate the changed shape.',complete:'Evidence is ready.',failed:'The run stopped.',cancelled:'GPU job cancelled.',cancelling:'Stopping the GPU job.'};
    text('#story-title',titles[e.stage]||'Starting local worker.');text('#story-detail',e.detail);text('#story-count',e.completed===undefined?e.stage.toUpperCase():`${e.completed} / ${e.total} GPU batches`);
    progress.hidden=false;if(e.completed===undefined)progress.removeAttribute('value');else{progress.max=e.total!;progress.value=e.completed;}
    const index=e.stage==='complete'?5:['smoothing','converting','baseline-ready'].includes(e.stage)?1:['loading','baseline','candidate','validate','evaluate'].indexOf(e.stage);
    document.querySelectorAll<HTMLElement>('[data-step], [data-story-stage]').forEach((el,i)=>{const n=i%5,done=index>n&&(n<2||!!run?.candidate)&&(n!==3||run?.validation.geometry==='passed');el.classList.toggle('running',n===index);el.classList.toggle('current',n===index);el.classList.toggle('done',done);const mark=el.querySelector('b');if(mark)mark.textContent=n===3&&run?.validation.geometry==='incomplete'?'!':done?'✓':n===index?'○':'—';});
    if(view!=='airflow'&&run&&e.stage==='candidate')mode('sensitivity');if(view!=='airflow'&&run&&e.stage==='validate')mode('mesh');if(view!=='airflow'&&run&&e.stage==='evaluate')mode('pressure');
    if(['complete','failed','cancelled'].includes(e.stage))progress.hidden=true;
    if(e.stage==='complete' && run){mode(view==='airflow'?'airflow':run.candidate?'displacement':'pressure');if(run.candidate)blend(100);}
  }
  async function poll(){
    if(!jobId)return;
    try{
      const expected=jobId,job=await api<Job>(`/api/runs/${expected}`);if(expected!==jobId)return;const events=nextEvents(job,expected,sequence);
      if(job.baselineReady&&!baselineLoaded){const payload=validateLiveRun(await api(`/api/runs/${expected}/baseline`),expected);if(expected!==jobId)return;install(payload);baselineLoaded=true;}
      if(job.resultReady&&!resultLoaded){const payload=validateLiveRun(await api(`/api/runs/${expected}/result`),expected);if(expected!==jobId)return;install(payload);resultLoaded=true;}
      for(const e of events){event(e);sequence=e.sequence;}
      status(job.state==='complete'?'Local run complete · acceptance refused':job.state==='failed'?'GPU run failed':job.state==='cancelled'?'Run cancelled':'DoMINO is running locally',job.detail);
      if(['complete','failed','cancelled'].includes(job.state)){active=false;lockControls(false);cancel.hidden=true;text('#iterate','Run bounded iteration ↗');}
      else window.setTimeout(()=>void poll(),750);
      if(job.state==='complete' && resultLoaded && !explanationRequested){explanationRequested=true;void copilot.explain(expected,!explainNewRun);}
    }catch(error){if(error instanceof Error && error.message.startsWith('Live data rejected:')){active=false;lockControls(false);cancel.hidden=false;status('Result rejected',error.message);return;}status('Connection interrupted',`${error instanceof Error?error.message:String(error)}. Job identity retained; polling will retry. Cancel remains available.`);window.setTimeout(()=>void poll(),2500);}
  }
  async function start(runMode:'analysis'|'iteration',budgetMm=+budget.value){
    if(active)return;active=true;lockControls(true);
    try{
      const request=getRequest(runMode,budgetMm),plan=await copilot.prepare(request);
      if(plan && plan.graph.status!=='ready')throw new Error(plan.graph.message);
      const job=await api<Job>('/api/runs',{...request,...(plan?{intentId:plan.intentId}:{})});nextEvents(job,job.runId,0);
      copilot.reset();explainNewRun=true;explanationRequested=false;restoredIntent=false;
      active=true;jobId=job.runId;sequence=0;baselineLoaded=resultLoaded=false;budget.disabled=true;cancel.hidden=false;sessionStorage.setItem('zephyr-active-run',jobId);
      run=undefined;scene?.setBlend(0);for(const key of ['pressure','sensitivity','displacement'])$(`[data-mode="${key}"]`).setAttribute('disabled','');mode('airflow');for(const s of ['.baseline-value','#candidate-force','#delta','#displacement'])text(s,'—');text('#trust-state','Running');text('.proof-value','Running');text('.metric-main p','Waiting for fresh baseline fields');text('#trust-detail','Trust radius uncalibrated');
      for(const s of ['.comparison','.result-controls','#story-result','.cabin-label'])$(s).hidden=true;$<HTMLButtonElement>('#export').disabled=true;$('#provenance').replaceChildren();text('#iterate','Running on local GPU…');text('#run-id',jobId);status('DoMINO is starting','The browser requested a real local GPU run.');void poll();
    }catch(error){active=false;lockControls(false);status('Request refused / unavailable',error instanceof Error?error.message:String(error));}
  }
  mode('airflow');
  button.onclick=()=>void start('iteration');analyze.onclick=()=>void start('analysis');$('#refuse').onclick=()=>void start('iteration',12);
  cancel.onclick=async()=>{if(jobId)try{await api(`/api/runs/${jobId}/cancel`,{});status('Cancelling','Waiting for the GPU process to stop.');}catch(error){status('Cancel failed',String(error));}};
  $('#export').onclick=()=>{if(!run)return;const url=URL.createObjectURL(new Blob([JSON.stringify(run)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`${run.runId}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  window.addEventListener('pagehide',()=>scene?.dispose(),{once:true});
  void fetch('/models/drivaer-preview.json').then(r=>{if(!r.ok)throw new Error('Geometry preview unavailable');return r.json();}).then(value=>{
    if(run || scene)return;
    scene=new FlowScene($('#scene'),{baseline:previewSurface(value),candidate:null,source:'geometry-preview'});scene.setMagnified(false);updateMotion();mode(view);$('.cabin-label').hidden=false;
  }).catch(()=>{if(!run)text('#legend','Geometry preview unavailable · run local inference to load the car');});
  const saved=sessionStorage.getItem('zephyr-active-run');
  if(saved&&/^local-[a-f0-9]{32}$/.test(saved)){try{const job=await api<Job>(`/api/runs/${saved}`);nextEvents(job,saved,0);jobId=saved;active=!['complete','failed','cancelled'].includes(job.state);explainNewRun=active;lockControls(active);cancel.hidden=!active;void poll();}catch{sessionStorage.removeItem('zephyr-active-run');}}
}
