import type { Job, JobEvent } from './live-data';
export function stageProgress(stage:string,completed?:number,total?:number,detail='') {
  const stages:Record<string,[number,string,string]>={
    queued:[1,'Preparing the test','Starting the local worker.'],
    loading:[1,'Preparing the test','Loading the model and checking the original shape.'],
    baseline:[2,'Testing the original shape','The GPU is calculating pressure and resistance. The moving scan illustrates activity; measured fields appear when ready.'],
    smoothing:[3,'Choosing a shape change','Preparing the calculated sensitivity field.'],
    converting:[2,'Preparing the calculated view','Turning the completed calculation into colors you can inspect.'],
    'baseline-ready':[3,'Original-shape result ready','The first calculation is finished. Preparing the next stage of the test.'],
    candidate:[3,'Changing the selected body region','Moving the selected region within its limit. The cabin stays fixed.'],
    calibration:[3,'Checking the local prediction','Testing smaller changes in both directions before choosing a separate candidate.'],
    repeat:[3,'Repeating the original calculation','Measuring numerical repeatability. This does not validate physical accuracy.'],
    'probe-plus-h':[3,'Testing the positive direction','Measuring how the full calculation responds to the selected region.'],
    'probe-minus-h':[3,'Testing the opposite direction','Checking the opposite direction with fresh geometry inputs.'],
    'probe-plus-half':[3,'Checking a smaller positive change','Testing whether the local slope agrees at half the movement.'],
    'probe-minus-half':[3,'Checking a smaller negative change','Finishing the local slope check before testing the candidate.'],
    validate:[3,'Checking the changed shape','Checking the movement limit and the surface. The trial may need to become smaller.'],
    evaluate:[4,'Testing the changed car','The GPU is doing a second calculation. The result will tell us whether this change helped.'],
    volume:[4,'Calculating the air around this shape','NVIDIA’s volume model predicts air direction and speed around the shape.'],
    streamlines:[4,'Drawing the predicted airflow','Tracing paths through the calculated velocity field.'],
    'volume-failed':[4,'Airflow calculation unavailable','Surface results remain available.'],
    complete:[5,'Calculation finished','Inference has stopped. Viewer animation is separate and can be resumed on demand.'],
    publishing:[5,'Preparing the comparison','Calculations finished. Waiting for the complete result and its evidence to be published.'],
    failed:[0,'The calculation stopped','No improvement can be concluded from a failed calculation.'],
    cancelling:[0,'Stopping the calculation','Waiting for the GPU worker to stop.'],
    cancelled:[0,'Calculation cancelled','Any completed original-shape result remains available.']
  };
  const [step,title,message]=stage==='smoothing' && detail.startsWith('evaluate:')
    ? [4,'Preparing the changed-shape fields','The second calculation has finished. Preparing its surface fields.']
    : stages[stage]??[1,'Preparing the test','Waiting for the next update from the worker.'];
  const percent=Number.isInteger(completed)&&Number.isInteger(total)&&total!>0&&completed!>=0&&completed!<=total!?Math.floor(completed!/total!*100):null;
  return {step,title,detail:message,percent};
}
export function progressStage(job: Pick<Job, 'state'|'stage'>) {
  return job.state==='running' ? job.stage==='complete'?'publishing':job.stage : job.state;
}
export function createRunProgress(host:HTMLElement) {
  const card=document.createElement('section');card.className='run-progress-card';card.hidden=true;card.setAttribute('aria-label','GPU calculation progress');
  card.innerHTML='<div class="progress-heading"><strong></strong><span class="elapsed"></span></div><p class="progress-detail"></p><div class="progress-number" aria-live="polite"></div><progress max="100"></progress><details><summary>Technical progress</summary><span></span></details>';
  host.append(card);
  let started=Date.now(),active=false,lastId:string|undefined,studyContext='';
  const elapsed=card.querySelector('.elapsed')!;
  const format=(seconds:number)=>`${Math.floor(seconds/60)}m ${Math.floor(seconds%60)}s elapsed`;
  const timer=window.setInterval(()=>{if(active)elapsed.textContent=format(Math.max(0,(Date.now()-started)/1000));},1000);
  window.addEventListener('pagehide',()=>clearInterval(timer),{once:true});
  return {
    setStudyContext(context:string){studyContext=context;},
    update(job:Job,totalSeconds?:number,analysisOnly=false){
      if(lastId!==job.runId){lastId=job.runId;const date=Date.parse(job.createdAt??'');started=Number.isFinite(date)?date:Date.now();}
      active=!['complete','failed','cancelled'].includes(job.state);card.hidden=false;card.classList.toggle('finished',job.state==='complete');
      const e=job.events[job.events.length-1] as JobEvent|undefined;
      const p=stageProgress(progressStage(job),e?.completed,e?.total,e?.detail);
      if(job.state==='complete'&&analysisOnly){p.step=0;p.title='Baseline analysis complete';p.detail='One original shape was evaluated. No candidate or comparison was created.';}
      card.querySelector('strong')!.textContent=(studyContext&&active?`${studyContext} · `:'')+(p.step&&active?`${studyContext?'Phase':'Step'} ${p.step} of 5 · `:'')+p.title;
      card.querySelector('.progress-detail')!.textContent=p.detail;
      card.querySelector('.progress-number')!.textContent=p.percent===null?({complete:'Finished',failed:'Stopped',cancelled:'Cancelled',cancelling:'Stopping…',running:'Working…'}[job.state]??'Working…'):`${p.percent}% of ${studyContext?'this GPU pass (resets for each pass)':'this calculation'}`;
      const bar=card.querySelector('progress')!;bar.hidden=!active;if(p.percent===null)bar.removeAttribute('value');else bar.value=p.percent;
      card.querySelector('details span')!.textContent=e?.completed===undefined?job.detail:`${e.completed} of ${e.total} GPU batches · ${job.detail}`;
      elapsed.textContent=totalSeconds!==undefined&&!active?format(totalSeconds):format(Math.max(0,(Date.now()-started)/1000));
    }
  };
}
