import {createExploration} from './exploration';
import { createComparison } from './comparison';
import { canCompare } from './comparison-data';
import type { VisualSpec } from './detailed-vehicle';
import {loadDetailedVehicle,disposeVehicle} from './detailed-vehicle';
import {validateAirflow} from './airflow';
import type {Airflow} from './airflow';
import { createRunProgress, stageProgress, progressStage } from './run-progress';
import { previewSurface } from './geometry-preview';
import { createCopilot } from './copilot';
import { FlowScene } from './scene';
import { fieldRange } from './data';
import type { ViewMode } from './data';
import { api, nextEvents, validateLiveRun, trustPresentation, maximumMovementMm } from './live-data';
import type { Job, JobEvent, LiveRun } from './live-data';
import {activityCaption,computationActive} from './render-policy';

export async function startLive() {
  const $ = <T extends HTMLElement>(s: string) => document.querySelector<T>(s)!;
  let scene: FlowScene | undefined, run: LiveRun | undefined, jobId: string | undefined;
  let active=false, sequence=0, baselineLoaded=false, resultLoaded=false, explanationRequested=false, restoredIntent=false;
  type Car={category:'car'|'aircraft';id:string;label:string;description:string;experimental:boolean;preview:string;airflow:string};
  let cars:Car[]=[],selectedId='drivaer-1',previewEpoch=0,cachedFlow:Airflow|undefined;
  const vehicleSelect=$<HTMLSelectElement>('#vehicle');const carIntro=$('.intro').innerHTML;
  const carInfo=document.createElement('p');carInfo.className='car-description';vehicleSelect.parentElement!.after(carInfo);const aircraftNote=document.createElement('p');aircraftNote.className='aircraft-note';aircraftNote.textContent='Orange spirals start at the wing tips and turn in opposite directions. Rotate the aircraft to follow them behind the wings. Use Flow illustration to see air bend around the shape, or NVIDIA prediction to inspect the calculated paths. This is an experimental visual preview, not a flight-performance test.';carInfo.after(aircraftNote);
  const pair = createComparison();
  let visualSpec: VisualSpec | undefined;
  let recordedReplay = false;
  let view: ViewMode='airflow';
  let flowStyle:'illustration'|'prediction'='illustration';
  const flowChoice=document.createElement('div');flowChoice.className='flow-choice';flowChoice.setAttribute('role','group');flowChoice.setAttribute('aria-label','Airflow display');flowChoice.innerHTML='<button data-flow-style="illustration" aria-pressed="true">Flow illustration</button><button data-flow-style="prediction" aria-pressed="false">NVIDIA prediction</button>';$('.flow-label').before(flowChoice);
  flowChoice.querySelectorAll<HTMLButtonElement>('button').forEach(b=>b.onclick=()=>{flowStyle=b.dataset.flowStyle as typeof flowStyle;scene?.setFlowStyle(flowStyle);flowLegend();});
  let flowPaused=matchMedia('(prefers-reduced-motion: reduce)').matches;
  let computingStage:string|undefined;
  const viewerState=document.createElement('span');viewerState.className='viewer-state';$('#motion').after(viewerState);
  const button=$<HTMLButtonElement>('#iterate'), budget=$<HTMLInputElement>('#budget'), compare=$<HTMLInputElement>('#compare'), magnify=$<HTMLInputElement>('#magnify');
  magnify.checked=true;
  magnify.parentElement!.lastChild!.textContent=" Enlarge movement ×120 (display only)";$('#app').classList.add('live-workspace');
  const text=(selector:string,value:string)=>{$(selector).textContent=value;};
  const status=(title:string,detail:string)=>{text('#decision-title',title);text('#decision-copy',detail);};
  text('footer > span:first-child','DRIVAERML / SAMPLE 1');text('#run-id','NO RUN YET');$('.metrics').setAttribute('aria-label','Surrogate evaluation metrics');text('#run-source','LOCAL GPU');text('.demo-tag','DoMINO');
  $('#vehicle').replaceChildren(new Option('DrivAerML · official sample 1','drivaer-1'));$<HTMLSelectElement>('#vehicle').disabled=true;
  text('.metric-main .eyebrow b','SURROGATE');text('.metric-main p','No inference yet · actual fields appear after the GPU run');
  for(const s of ['.baseline-value','#candidate-force','#delta','#displacement'])text(s,'—');
  text('#scale-caption','No candidate yet');text('#trust-state','Not evaluated');text('#trust-detail','Trust radius uncalibrated');text('.proof-value','Not run');text('.metrics .metric:last-child p','Local surrogate · independent CFD not run');
  status('Ready for local inference','Choose a body region below or interpret a design brief. The cabin stays fixed while the selected region is evaluated.');
  for(const s of ['.flow-label','.wake-key','.rear-callout','.cabin-label','#motion','.asset-credit','.comparison'])$(s).hidden=true;
  $('[data-mode="airflow"]').removeAttribute('disabled');
  text('.flow-label','→ ILLUSTRATIVE AIRFLOW');
  for(const key of ['pressure','sensitivity','displacement'])$(`[data-mode="${key}"]`).setAttribute('disabled','');
  text('#legend','Illustrative airflow · animated paths, not a computed velocity field');text('#evidence-dialog h2','Every result has a source.');
  const credits=document.createElement('a');credits.href='/models/VEHICLE_CREDITS.md';credits.target='_blank';credits.rel='noopener';credits.textContent='Vehicle and aircraft sources & credits ↗';credits.className='quiet';$('#evidence-dialog').append(credits);
  text('#evidence-dialog > p','NVIDIA’s open DoMINO surface model predicts pressure and sensitivity; its separate volume checkpoint predicts velocity around each car. Choose NVIDIA prediction to view that field as moving trails in slow motion. The default Flow illustration is a separate, geometry-following explanation. Cyan trails travel around the body; amber trails illustrate the wake. Its colors are not calculated speeds or proof of improvement. The additional vehicle models are outside the sedan training distribution.');
  text('.dialog-note','No cloud resources or paid calls. Full-resolution VTK and logs stay in .local/runs. Display geometry is reduced; forces use the full mesh.');
  text('#export','Download run JSON');$<HTMLButtonElement>('#export').disabled=true;document.querySelector<HTMLElement>('#candidate-export')?.setAttribute('hidden','');text('#refuse','Test 12 mm boundary');
  const analyze=document.createElement('button');analyze.className='boundary';analyze.textContent='Run baseline analysis only';button.after(analyze);
  const cancel=document.createElement('button');cancel.className='boundary';cancel.textContent='Cancel GPU job';cancel.hidden=true;analyze.after(cancel);
  const demo=document.createElement('a');demo.className='quiet';demo.href='?demo=1';demo.textContent='Open illustrative design walkthrough ↗';cancel.after(demo);
  const technical=document.createElement('details');technical.className='technical-checks';
  const technicalTitle=document.createElement('summary');technicalTitle.textContent='Behind the scenes · calculation checks';technical.append(technicalTitle);$('.sequence-heading').before(technical);technical.append($('.sequence-heading'),$('.steps'));$('#refuse').before(technical);
  const runProgress=createRunProgress($('#story-narration'));
  const activity=document.createElement('p');activity.className='compute-activity';activity.hidden=true;activity.setAttribute('role','status');$('#story-narration').append(activity);
  // The run summary grows with progress and result text. Place tabs below it,
  // instead of letting fixed offsets cover the result at laptop widths.
  const placeRunTools=()=>{const story=$('#run-story'),tools=$('.view-tools'),host=$('#scene');if(!story.hidden){const top=story.offsetTop+story.offsetHeight+12;if(window.innerWidth<=1100){tools.style.top=`${top}px`;flowChoice.style.top=`${top+43}px`;host.style.top=`${top+(computingStage?44:84)}px`;}else{tools.style.top='';flowChoice.style.top='';host.style.top=`${Math.max(180,top)}px`;}}else{tools.style.top='';flowChoice.style.top='';host.style.top='';}};
  const storyLayout=new ResizeObserver(placeRunTools);storyLayout.observe($('#run-story'));storyLayout.observe($('.viewport'));window.addEventListener('pagehide',()=>storyLayout.disconnect(),{once:true});

  const brief=$<HTMLTextAreaElement>('#brief');
  const getRequest=(mode:'analysis'|'iteration'='iteration',budgetMm=+budget.value)=>({geometryId:selectedId,budgetMm,brief:cars.find(c=>c.id===selectedId)?.category==='aircraft'?'Reduce drag. Keep the cabin unchanged.':brief.value,mode});
  function lockControls(busy:boolean){const plane=cars.find(c=>c.id===selectedId)?.category==='aircraft';analyze.disabled=vehicleSelect.disabled=busy;button.disabled=budget.disabled=brief.disabled=busy||plane;copilot.setBusy(busy||plane);if(typeof exploration!=='undefined')exploration.setBusy(busy||plane);}
  const copilot=createCopilot(()=>getRequest(),busy=>{active=busy;lockControls(busy);});
  const exploration=createExploration(()=>getRequest(),copilot.prepare,busy=>{active=busy;lockControls(busy);},followStudyRun);
  function mode(value:ViewMode) {
    text('.rear-callout strong',(run?.handle?.label??'BODY REGION')+' CHANGED');
    const outline=$('.rear-callout small:last-child');outline.textContent='Cyan outline = original shape';
    view=value;magnify.disabled=value!=='displacement';scene?.setMode(value);scene?.setStory(value==='displacement' && run?.candidate ? 'result' : undefined);$('.rear-callout').hidden=!(value==='displacement' && run?.candidate);if(value==='sensitivity' && run)blend(0);
    document.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach(b=>{const on=b.dataset.mode===value;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});
    text('#show-candidate',value==='airflow'?'02 Candidate geometry':'02 Candidate + change map');
    flowChoice.hidden=value!=='airflow';$('.flow-label').hidden=value!=='airflow';$('#motion').hidden=value!=='airflow';
    if(value==='airflow'){flowLegend();return;}
    text('#result-scale',view==='displacement'&&magnify.checked?'Movement enlarged ×120 · actual mm shown':'True-scale shape · field in actual units');
    if(!run){text('#legend','DrivAerML geometry preview · run inference for measured surface fields');return;}
    const range=fieldRange(value==='sensitivity'?run.baseline.normalSensitivity:run.baseline.pressurePa), candidateRange=run.candidate?fieldRange(run.candidate.pressurePa):range;const lo=value==='pressure'?Math.min(range[0],candidateRange[0]):range[0],hi=value==='pressure'?Math.max(range[1],candidateRange[1]):range[1];
    const mm=maximumMovementMm(run);
    const label=value==='pressure'?`Pressure · ${lo.toFixed(0)} to ${hi.toFixed(0)} Pa`:value==='sensitivity'?`Baseline normal sensitivity · ${lo.toFixed(2)} to ${hi.toFixed(2)} N/m · signed asinh color scale`:value==='displacement'?`Actual displacement · 0–${mm.toFixed(2)} mm`:`${(run.baseline.positions.length/3).toLocaleString()} display vertices · reduced mesh`;
    $('#legend').replaceChildren();const scale=document.createElement('span');scale.className=`color-scale ${value}`;$('#legend').append(scale,label+' · live surrogate');
  }
  document.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach(b=>b.onclick=()=>{stopReplay();mode(b.dataset.mode as ViewMode);});
  function blend(v:number){$('.rear-callout').hidden=!(view==='displacement' && run?.candidate && v>0);compare.value=String(v);scene?.setBlend(v/100);text('#compare-status',v===0?'Baseline geometry':v===100&&run?trustPresentation(run).candidateLabel:`${v}% geometry blend`);$('#show-baseline').setAttribute('aria-pressed',String(v===0));$('#show-candidate').setAttribute('aria-pressed',String(v===100));if(view==='airflow')flowLegend();}
  let replayFrame=0;
  const replay=document.createElement('button');replay.id='replay-change';replay.textContent='▶ Show me the change';$('.result-controls').append(replay);
  const stopReplay=()=>{cancelAnimationFrame(replayFrame);replayFrame=0;replay.disabled=false;};
  replay.onclick=()=>{
    if(!run?.candidate)return;
    stopReplay();mode('displacement');magnify.checked=!(run.research||run.syntheticDent);magnify.onchange?.call(magnify,new Event('change'));
    if(matchMedia('(prefers-reduced-motion: reduce)').matches){blend(100);return;}
    replay.disabled=true;const started=performance.now();
    const animate=(now:number)=>{const t=Math.min(1,(now-started)/3500);blend(Math.round((.5-.5*Math.cos(t*Math.PI*3))*100));if(t<1)replayFrame=requestAnimationFrame(animate);else stopReplay();};
    replayFrame=requestAnimationFrame(animate);
  };
  window.addEventListener('pagehide',stopReplay,{once:true});
  compare.oninput=()=>{stopReplay();blend(+compare.value);};$('#show-baseline').onclick=()=>{stopReplay();blend(0);};$('#show-candidate').onclick=()=>{stopReplay();if(view!=='airflow')mode('displacement');blend(100);};
  magnify.onchange=()=>{scene?.setMagnified(magnify.checked,120);text('#result-scale',magnify.checked?'Movement enlarged ×120 · actual mm shown':'True-scale shape · field in actual mm');};
  function updateMotion(){scene?.setFlowStyle(flowStyle);scene?.setPaused(flowPaused);text('#motion',flowPaused?'▷ Resume viewer animation':'Ⅱ Pause viewer animation');$('#motion').setAttribute('aria-pressed',String(flowPaused));viewerState.textContent=computingStage?'Live GPU calculation':resultLoaded?(flowPaused?'Inference finished · viewer paused':'Inference finished · viewer animation only'):(flowPaused?'Viewer paused':'Viewer animation · not inference');}
  $('#motion').onclick=()=>{flowPaused=!flowPaused;updateMotion();};updateMotion();
  $('#camera').onclick=()=>scene?.resetCamera();budget.oninput=()=>text('#budget-value',`${(+budget.value).toFixed(1)} mm`);
  function flowLegend(){
    if(view==='airflow')text('#result-scale',cars.find(c=>c.id===selectedId)?.category==='aircraft'?'Scaled aircraft · 3.3 m wingspan':'Actual-size car · enlargement applies in Change view');
    const field=run?.airflow?(+compare.value>=50&&run.airflow.candidate?run.airflow.candidate:run.airflow.baseline):cachedFlow;
    flowChoice.querySelectorAll<HTMLButtonElement>('button').forEach(b=>{b.setAttribute('aria-pressed',String(b.dataset.flowStyle===flowStyle));b.disabled=b.dataset.flowStyle==='prediction'&&!field;});
    if(flowStyle==='illustration'){text('.flow-label',cars.find(c=>c.id===selectedId)?.category==='aircraft'?'ORANGE SPIRALS: WINGTIP VORTICES':'BLUE: AROUND THE BODY  ·  ORANGE: WAKE BEHIND');text('#legend',cars.find(c=>c.id===selectedId)?.category==='aircraft'?'Illustration · two air spirals turn in opposite directions behind the wings':run?.candidate?'Original-shape flow illustration':'Flow illustration · shape-following trails, not calculated air speeds');return;}
    if(field){const original=run?.candidate&&!run.airflow?.candidate;const label=cars.find(c=>c.id===selectedId)?.category==='aircraft'?'EXPERIMENTAL AIRCRAFT FLOW':run?.airflow?(original?'ORIGINAL-CAR AIRFLOW':'NVIDIA PREDICTED AIRFLOW'):'SAVED NVIDIA AIRFLOW';text('.flow-label','→ '+label);text('#legend',`${label.toLowerCase()} · blue = slower, orange = faster · 0–60+ m/s · slow motion`);}
    else{text('.flow-label','→ ILLUSTRATIVE AIRFLOW');text('#legend','Illustrative preview · model-driven airflow is not available for this shape yet');}
  }
  function describeCar(){const car=cars.find(c=>c.id===selectedId);const plane=car?.category==='aircraft';$('#app').classList.toggle('aircraft-workspace',plane);$('.intro').innerHTML=plane?'<p class="eyebrow">AIRCRAFT EXPLORER</p><h1>Follow the air.<br>Across the wings.<br><em>Around the tail.</em></h1><p class="subcopy">NASA aircraft models · experimental airflow.<br>Drag to rotate. Scroll to get closer.</p>':carIntro;analyze.textContent=plane?'Run experimental baseline analysis':'Run baseline analysis only';button.textContent=plane?'Shape editing is available for cars':'Run bounded iteration ↗';lockControls(active);carInfo.textContent=car?car.description+(car.experimental?' · detailed model · experimental airflow':''):'';text('footer > span:first-child',car?.label.toUpperCase()??selectedId.toUpperCase());}
  async function loadCar(id:string){
    const car=cars.find(c=>c.id===id);if(!car||active)return;
    if(run?.research||run?.syntheticDent)magnify.checked=true;
    text('.metrics .within','/ 4 mm');
    stopReplay();pair.clear();computingStage=undefined;activity.hidden=true;recordedReplay=false;history.replaceState(null,'',location.pathname);const epoch=++previewEpoch;selectedId=id;sessionStorage.setItem('zephyr-car',id);sessionStorage.removeItem('zephyr-active-run');jobId=undefined;run=undefined;cachedFlow=undefined;baselineLoaded=resultLoaded=explanationRequested=restoredIntent=false;copilot.reset();scene?.dispose();scene=undefined;
    $('.run-progress-card').hidden=true;$('.viewport').classList.remove('story-active');for(const name of ['#run-story','.comparison','.result-controls','#story-result','.rear-callout'])$(name).hidden=true;
    for(const name of ['.baseline-value','#candidate-force','#delta','#displacement'])text(name,'—');text('#trust-state','Not evaluated');text('.proof-value','Not run');text('.metrics .metric:last-child p','No surface or shape test for this selection yet');text('#trust-detail','Run a test to compare shapes');text('.metric-main p','Airflow preview loaded separately · no drag test yet');text('#run-id','NO RUN YET');$<HTMLButtonElement>('#export').disabled=true;document.querySelector<HTMLElement>('#candidate-export')?.setAttribute('hidden','');
    for(const key of ['pressure','sensitivity','displacement'])$(`[data-mode="${key}"]`).setAttribute('disabled','');describeCar();mode('airflow');status('Loading '+car.label,'Preparing this car and its NVIDIA airflow.');
    try{
      const response=await fetch(car.preview);if(!response.ok)throw new Error('Car geometry unavailable');const value=await response.json();if(epoch!==previewEpoch||run||jobId)return;
      const baseline=previewSurface(value,id);const asset=value.visual?await loadDetailedVehicle(value.visual,baseline):undefined;if(epoch!==previewEpoch||run||jobId){if(asset)disposeVehicle(asset);return;}scene=new FlowScene($('#scene'),{baseline,candidate:null,source:'geometry-preview'},asset);scene.setMagnified(false);updateMotion();$('.cabin-label').hidden=false;
      const flowResponse=await fetch(car.airflow);if(!flowResponse.ok)throw new Error('Saved model airflow unavailable');const flow=validateAirflow(await flowResponse.json(),id,value.meshHash??value.sourceMeshSha256);if(epoch!==previewEpoch||run||jobId)return;
      cachedFlow=flow;scene.setAirflow(flow);mode('airflow');status(car.label+' · airflow ready',car.category==='aircraft'?'Experimental flow around a scaled aircraft. This car-trained model does not establish aircraft performance.':'NVIDIA airflow calculated on a simplified version of this detailed car. Run a test to evaluate a new shape.');
    }catch(error){if(epoch===previewEpoch){status('Preview unavailable',error instanceof Error?error.message:String(error));mode('airflow');}}
  }
  async function install(payload:LiveRun) {
    if(run?.runId!==payload.runId && (payload.research || payload.syntheticDent || run?.research || run?.syntheticDent))magnify.checked=!(payload.research||payload.syntheticDent);
    ++previewEpoch;cachedFlow=undefined;selectedId=payload.geometryId??payload.intent?.request.geometryId??'drivaer-1';vehicleSelect.value=selectedId;describeCar();
    if(payload.intent && !restoredIntent){copilot.restore(payload.intent);restoredIntent=true;}
    run=payload;const epoch=previewEpoch;const car=cars.find(c=>c.id===selectedId);const preview=car?await fetch(car.preview).then(r=>r.json()):undefined;const asset=preview?.visual && preview.meshHash===payload.provenance.meshHash?await loadDetailedVehicle(preview.visual,payload.baseline):undefined;if(epoch!==previewEpoch){if(asset)disposeVehicle(asset);return;}visualSpec=asset?preview.visual:undefined;scene?.dispose();scene=new FlowScene($('#scene'),run,asset);updateMotion();for(const key of ['pressure','sensitivity','displacement'])$(`[data-mode="${key}"]`).removeAttribute('disabled');scene.setMagnified(magnify.checked,120);mode(view);blend(0);
    $('.cabin-label').hidden=false;$('.viewport').classList.add('story-active');$('#run-story').hidden=false;
    if(active&&!run.candidate)mode('pressure');scene.setComputation(computingStage);
    text('.baseline-value',`${run.forces.baselineDragN.toFixed(2)} N`);text('#candidate-force',run.forces.candidateDragN===null?'—':`${run.forces.candidateDragN.toFixed(2)} N`);
    const delta=run.forces.candidateDragN===null?null:(run.forces.candidateDragN-run.forces.baselineDragN)/run.forces.baselineDragN*100;
    text('#delta',delta===null?'Baseline only':`${delta>0?'+':''}${delta.toFixed(3)}%`);$('#delta').classList.toggle('worse',delta!==null&&delta>=0);
    text('.metric-main p',run.candidate?'Fresh baseline vs candidate · surrogate, not CFD':'Actual baseline · candidate has not been evaluated');
    const mm=maximumMovementMm(run);
    text('.metrics .within',`/ ${(run.constraints.maxDisplacementM*1000).toFixed(0)} mm`);
    text('#displacement',run.candidate?`${mm.toFixed(2)} mm`:'No candidate');text('#scale-caption',run.candidate?`Actual maximum: ${mm.toFixed(2)} mm · cabin 0.00 mm`:'Analysis only');text('#run-id',run.runId);
    const trust=trustPresentation(run);text('#trust-state',trust.state);text('#trust-detail',trust.detail);
    text('.proof-value',run.research&&run.validation.independentCfd==='compared'?'CFD compared':run.research&&run.validation.independentCfd==='inconclusive'?'CFD inconclusive':'CFD pending');text('.metrics .metric:last-child p',`Geometry: ${run.validation.geometry} · fresh evaluation: ${run.validation.freshEvaluation}`);
    for(const s of ['.comparison','.result-controls','#story-result'])$(s).hidden=!run.candidate;
    if(run.candidate){text('#result-label',run.executionProfile==='sedan-demo-v1'&&run.validation.geometry==='passed'?'FRESH SURROGATE COMPARISON':run.trust.decision==='accept'?'LOCAL SURROGATE CHECK PASSED · CFD PENDING':'FRESH SURROGATE COMPARISON · NOT ACCEPTED');text('#result-before',`${run.forces.baselineDragN.toFixed(2)} N`);text('#result-after',`${run.forces.candidateDragN!.toFixed(2)} N`);text('#result-delta',`${delta!>0?'+':''}${delta!.toFixed(3)}%`);$('#result-delta').classList.toggle('worse',delta!>=0);text('#result-scale',magnify.checked?'Movement enlarged ×120 · actual mm shown':'True-scale shape · field in actual mm');text('#rear-displacement',`${mm.toFixed(2)} mm actual movement`);if(view!=='airflow')mode('displacement');blend(100);}
    $('#provenance').replaceChildren();
    const rows:Record<string,string>={Run:run.runId,Source:run.source,Model:run.provenance.modelVersion,'Checkpoint SHA-256':run.provenance.checkpointSha256,'Mesh SHA-256':run.provenance.meshHash,'Upstream commit':run.provenance.upstreamCommit,Coordinates:'Metres · upstream (X,Y,Z) → (X,Z,−Y), translated to centre/ground',Forces:run.provenance.forceConvention,Fields:run.provenance.fieldTransfer,Sensitivity:run.provenance.sensitivityConvention,Reduction:JSON.stringify(run.provenance.reduction),Timings:JSON.stringify(run.timings),Decision:run.trust.reason,Checks:JSON.stringify(run.validation.checks)};
    if(run.intent){rows['Brief model']=run.intent.provenance.model;rows['Compiled brief']=run.intent.request.brief;rows['Intent ID']=run.intent.intentId;rows['Compiled ceiling']=`${run.intent.graph.effectiveBudgetMm} mm`;}
    for(const [key,value] of Object.entries(rows)){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=key;dd.textContent=value;$('#provenance').append(dt,dd);}
    for(const url of run.provenance.evidenceUrls){const a=document.createElement('a');a.href=url;a.textContent='Machine-readable evidence ↗';a.target='_blank';a.rel='noopener';$('#provenance').append(a);}
    $<HTMLButtonElement>('#export').disabled=false;
    let meshExport=document.querySelector<HTMLAnchorElement>('#candidate-export');if(!meshExport){meshExport=document.createElement('a');meshExport.id='candidate-export';meshExport.textContent='Download candidate mesh + evidence';$('#export').after(meshExport);}meshExport.href=`/api/runs/${run.runId}/candidate.zip`;meshExport.hidden=!run.candidate;
  }
  function event(e:JobEvent){
    $('.viewport').classList.add('story-active');$('#run-story').hidden=false;text('#story-source',recordedReplay?'RECORDED REPLAY · NVIDIA DoMINO':'LIVE LOCAL SURROGATE · NVIDIA DoMINO');
    const presentation=stageProgress(e.stage,e.completed,e.total,e.detail);
    text('#story-title',presentation.title);text('#story-detail',presentation.detail);
    text('#story-count',presentation.percent===null?(presentation.step?`STEP ${presentation.step} OF 5`:e.stage.toUpperCase()):`${presentation.percent}% OF THIS CALCULATION`);
    const index=e.stage==='complete'?5:Math.max(0,presentation.step-1);
    document.querySelectorAll<HTMLElement>('[data-step], [data-story-stage]').forEach((el,i)=>{const n=i%5,done=index>n&&(n<2||!!run?.candidate)&&(n!==3||run?.validation.geometry==='passed');el.classList.toggle('running',n===index);el.classList.toggle('current',n===index);el.classList.toggle('done',done);const mark=el.querySelector('b');if(mark)mark.textContent=n===3&&run?.validation.geometry==='incomplete'?'!':done?'✓':n===index?'○':'—';});
    if(view!=='airflow'&&run&&e.stage==='candidate')mode('sensitivity');if(view!=='airflow'&&run&&e.stage==='validate')mode('mesh');if(view!=='airflow'&&run&&e.stage==='evaluate')mode('pressure');

    if(e.stage==='complete' && run){text('#story-count',recordedReplay?'RECORDED RESULT · INFERENCE FINISHED':'INFERENCE FINISHED');if(!run.candidate){$('.story-progress').hidden=true;}else $('.story-progress').hidden=false;text('#story-title',trustPresentation(run).headline);text('#story-detail',run.candidate?'The original and changed shapes were both calculated. Compare them below, or ask about the result.':'The original shape was calculated. No changed shape was tested.');mode(view==='airflow'?'airflow':run.candidate?'displacement':'pressure');if(run.candidate)blend(100);}
  }
  async function ensureJobPreview(expected:string){
    if(scene)return;
    const car=cars.find(c=>c.id===selectedId);if(!car)return;
    const value=await fetch(car.preview).then(r=>r.json());
    if(jobId!==expected||scene)return;
    scene=new FlowScene($('#scene'),{baseline:previewSurface(value,selectedId),candidate:null,source:'geometry-preview'});
    scene.setComputation(computingStage);scene.setPaused(true);
  }
  function showComputation(job:Job){
    computingStage=computationActive(job.state)?progressStage(job):undefined;
    scene?.setComputation(computingStage);activity.hidden=!computingStage;
    $('.viewport').classList.toggle('computing',!!computingStage);
    if(computingStage){const last=job.events.at(-1);const p=stageProgress(computingStage,last?.completed,last?.total);activity.textContent=activityCaption(computingStage,p.percent,!!run);}
    else {flowPaused=true;}
    updateMotion();
    flowChoice.hidden=!!computingStage||view!=='airflow';$('.flow-label').hidden=!!computingStage||view!=='airflow';$('#motion').hidden=!!computingStage||view!=='airflow';
    if(computingStage&&!run)text('#legend','Illustrative compute activity · colors are not pressure or evidence of improvement');
    placeRunTools();
  }
  function followStudyRun(id:string,context:string){
    runProgress.setStudyContext(context);
    if(id===jobId)return;
    stopReplay();pair.clear();copilot.reset();active=true;recordedReplay=false;jobId=id;sequence=0;run=undefined;
    baselineLoaded=resultLoaded=explanationRequested=restoredIntent=false;computingStage='queued';
    history.replaceState(null,'',location.pathname);sessionStorage.setItem('zephyr-active-run',id);
    scene?.setStory(undefined);scene?.setBlend(0);mode('airflow');scene?.setComputation('queued');
    for(const key of ['pressure','sensitivity','displacement'])$(`[data-mode="${key}"]`).setAttribute('disabled','');
    for(const s of ['.comparison','.result-controls','#story-result'])$(s).hidden=true;
    for(const s of ['.baseline-value','#candidate-force','#delta','#displacement'])text(s,'—');
    text('#trust-state','Running');text('.proof-value','Running');text('#run-id',id);lockControls(true);void poll();
  }
  async function poll(){
    if(!jobId)return;
    try{
      const expected=jobId,job=await api<Job>(`/api/runs/${expected}`);if(expected!==jobId)return;const events=nextEvents(job,expected,sequence);
      computingStage=computationActive(job.state)?progressStage(job):undefined;
      if(computingStage&&job.geometryId&&cars.some(c=>c.id===job.geometryId)){
        if(selectedId!==job.geometryId){selectedId=job.geometryId;vehicleSelect.value=selectedId;scene?.dispose();scene=undefined;describeCar();}
        await ensureJobPreview(expected);
      }if(expected!==jobId)return;
      if(job.baselineReady&&!baselineLoaded){const payload=validateLiveRun(await api(`/api/runs/${expected}/baseline`),expected);if(expected!==jobId)return;await install(payload);if(expected!==jobId)return;baselineLoaded=true;}
      if(job.state==='complete'&&job.resultReady&&!resultLoaded){const payload=validateLiveRun(await api(`/api/runs/${expected}/result`),expected);if(expected!==jobId)return;if(recordedReplay)payload.source='recorded';await install(payload);if(expected!==jobId)return;resultLoaded=true;}
      for(const e of events){if(e.stage==='complete'&&job.state!=='complete'){event({...e,stage:'publishing'});break;}event(e);sequence=e.sequence;}
      showComputation(job);
      if(canCompare(run,job.state))pair.set(run!,visualSpec);else pair.clear();
      runProgress.update(job,run?.timings.totalSeconds,!!run&&!run.candidate);
      status(job.state==='complete'?'Test complete · result at the top of this panel':job.state==='failed'?'GPU run failed':job.state==='cancelled'?'Run cancelled':'GPU calculation in progress',job.state==='complete'?'The result summary explains what changed, whether it helped, and what still needs checking.':stageProgress(progressStage(job),undefined,undefined,job.detail).detail);
      if(job.state==='complete'&&run?.airflowStatus==='failed')status('Surface results ready · airflow calculation failed',run.airflowError??'The separate volume model did not complete.');
      if(['complete','failed','cancelled'].includes(job.state)){active=exploration.isRunning();lockControls(active);cancel.hidden=true;text('#iterate','Run bounded iteration ↗');}
      else window.setTimeout(()=>void poll(),750);
      if(job.state==='complete' && resultLoaded && !explanationRequested){explanationRequested=true;void copilot.showResult(expected);}
    }catch(error){
      scene?.setComputation(undefined);scene?.setPaused(true);activity.hidden=false;
      activity.textContent='Activity display paused · waiting for verified job updates';
      if(error instanceof Error && error.message.startsWith('Live data rejected:')){active=false;lockControls(false);cancel.hidden=false;status('Result rejected',error.message);return;}
      status('Connection interrupted',`${error instanceof Error?error.message:String(error)}. Job identity retained; polling will retry. Cancel remains available.`);window.setTimeout(()=>void poll(),2500);
    }
  }
  async function start(runMode:'analysis'|'iteration',budgetMm=+budget.value){
    if(active)return;stopReplay();active=true;lockControls(true);
    try{
      const request=getRequest(runMode,budgetMm),plane=cars.find(c=>c.id===selectedId)?.category==='aircraft',plan=plane&&runMode==='analysis'?undefined:await copilot.prepare(request);
      if(plan && plan.graph.status!=='ready')throw new Error(plan.graph.message);
      const job=await api<Job>('/api/runs',{...request,...(plan?{intentId:plan.intentId}:{})});nextEvents(job,job.runId,0);
      copilot.reset();explanationRequested=false;restoredIntent=false;
      active=true;jobId=job.runId;sequence=0;baselineLoaded=resultLoaded=false;budget.disabled=true;cancel.hidden=false;sessionStorage.setItem('zephyr-active-run',jobId);
      pair.clear();recordedReplay=false;history.replaceState(null,'',location.pathname);run=undefined;computingStage='queued';scene?.setStory(undefined);scene?.setBlend(0);scene?.setComputation('queued');for(const key of ['pressure','sensitivity','displacement'])$(`[data-mode="${key}"]`).setAttribute('disabled','');mode('airflow');for(const s of ['.baseline-value','#candidate-force','#delta','#displacement'])text(s,'—');text('#trust-state','Running');text('.proof-value','Running');text('.metric-main p','Waiting for fresh baseline fields');text('#trust-detail','Trust radius uncalibrated');
      for(const s of ['.comparison','.result-controls','#story-result','.cabin-label'])$(s).hidden=true;$<HTMLButtonElement>('#export').disabled=true;document.querySelector<HTMLElement>('#candidate-export')?.setAttribute('hidden','');$('#provenance').replaceChildren();text('#iterate','Running on local GPU…');text('#run-id',jobId);status('DoMINO is starting','The browser requested a real local GPU run.');void poll();
    }catch(error){active=false;lockControls(false);status('Request refused / unavailable',error instanceof Error?error.message:String(error));}
  }
  mode('airflow');
  button.onclick=()=>void start('iteration');analyze.onclick=()=>void start('analysis');$('#refuse').onclick=()=>void start('iteration',12);
  cancel.onclick=async()=>{if(jobId)try{await api(`/api/runs/${jobId}/cancel`,{});status('Cancelling','Waiting for the GPU process to stop.');}catch(error){status('Cancel failed',String(error));}};
  $('#export').onclick=()=>{if(!run)return;const url=URL.createObjectURL(new Blob([JSON.stringify(run)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`${run.runId}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  window.addEventListener('pagehide',()=>scene?.dispose(),{once:true});
  try{cars=(await api<{cars:Car[]}>('/api/geometries')).cars;vehicleSelect.replaceChildren();for(const [category,label] of [['car','Cars'],['aircraft','Aircraft']]){const group=document.createElement('optgroup');group.label=label;group.append(...cars.filter(car=>car.category===category).map(car=>new Option(car.label,car.id)));vehicleSelect.append(group);}vehicleSelect.disabled=false;}catch{status('Car catalog unavailable','Check that the updated local API is running.');return;}
  vehicleSelect.onchange=()=>void loadCar(vehicleSelect.value);
  const requestedReplay=new URLSearchParams(location.search).get('replay');
  if(requestedReplay && /^local-[a-f0-9]{32}$/.test(requestedReplay)){
    try { const job=await api<Job>(`/api/runs/${requestedReplay}`);nextEvents(job,requestedReplay,0);if(job.state!=='complete'||!job.resultReady)throw new Error('Replay requires a completed result');jobId=requestedReplay;recordedReplay=true;void poll();return; }
    catch(error){status('Recorded replay unavailable',String(error));return;}
  }
  const saved=sessionStorage.getItem('zephyr-active-run');
  if(saved&&/^local-[a-f0-9]{32}$/.test(saved)){try{const job=await api<Job>(`/api/runs/${saved}`);nextEvents(job,saved,0);jobId=saved;active=!['complete','failed','cancelled'].includes(job.state);lockControls(active);cancel.hidden=!active;void poll();}catch{sessionStorage.removeItem('zephyr-active-run');}}
  if(!jobId){const chosen=sessionStorage.getItem('zephyr-car');vehicleSelect.value=cars.some(c=>c.id===chosen)?chosen!:'drivaer-1';await loadCar(vehicleSelect.value);}
}
