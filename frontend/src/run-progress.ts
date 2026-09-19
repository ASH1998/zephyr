import type { Job, JobEvent } from './live-data';
export function stageProgress(stage:string,completed?:number,total?:number) {
  const stages:Record<string,[number,string,string]>={
    queued:[1,'Preparing the test','Starting the local worker.'],
    loading:[1,'Preparing the test','Loading the model and checking the original shape.'],
    baseline:[2,'Testing the original shape','The GPU is calculating pressure and resistance. The geometry stays still during this step.'],
    smoothing:[3,'Choosing a small change','Using the first calculation to choose a change at the rear.'],
    converting:[2,'Preparing the calculated view','Turning the completed calculation into colors you can inspect.'],
    'baseline-ready':[3,'Original-shape result ready','The first calculation is finished. Preparing the next stage of the test.'],
    candidate:[3,'Making a small rear-body change','Moving only the permitted rear area. The passenger cabin stays fixed.'],
    validate:[3,'Checking the changed shape','Checking the movement limit and the surface. The trial may need to become smaller.'],
    evaluate:[4,'Testing the changed car','The GPU is doing a second calculation. The result will tell us whether this change helped.'],
    volume:[4,'Calculating the air around this shape','NVIDIA’s volume model predicts air direction and speed around the shape.'],
    streamlines:[4,'Drawing the predicted airflow','Tracing paths through the calculated velocity field.'],
    'volume-failed':[4,'Airflow calculation unavailable','Surface results remain available.'],
    complete:[5,'Comparing the two results','The test has finished. Read what changed and whether it helped below.'],
    failed:[0,'The calculation stopped','No improvement can be concluded from a failed calculation.'],
    cancelling:[0,'Stopping the calculation','Waiting for the GPU worker to stop.'],
    cancelled:[0,'Calculation cancelled','Any completed original-shape result remains available.']
  };
  const [step,title,detail]=stages[stage]??[1,'Preparing the test','Waiting for the next update from the worker.'];
  const percent=Number.isInteger(completed)&&Number.isInteger(total)&&total!>0&&completed!>=0&&completed!<=total!?Math.floor(completed!/total!*100):null;
  return {step,title,detail,percent};
}
export function createRunProgress(host:HTMLElement) {
  const card=document.createElement('section');card.className='run-progress-card';card.hidden=true;card.setAttribute('aria-label','GPU calculation progress');
  card.innerHTML='<div class="progress-heading"><strong></strong><span class="elapsed"></span></div><p class="progress-detail"></p><div class="progress-number" aria-live="polite"></div><progress max="100"></progress><details><summary>Technical progress</summary><span></span></details>';
  host.append(card);
  let started=Date.now(),active=false,lastId:string|undefined;
  const elapsed=card.querySelector('.elapsed')!;
  const format=(seconds:number)=>`${Math.floor(seconds/60)}m ${Math.floor(seconds%60)}s elapsed`;
  const timer=window.setInterval(()=>{if(active)elapsed.textContent=format(Math.max(0,(Date.now()-started)/1000));},1000);
  window.addEventListener('pagehide',()=>clearInterval(timer),{once:true});
  return {
    update(job:Job,totalSeconds?:number,analysisOnly=false){
      if(lastId!==job.runId){lastId=job.runId;const date=Date.parse(job.createdAt??'');started=Number.isFinite(date)?date:Date.now();}
      active=!['complete','failed','cancelled'].includes(job.state);card.hidden=false;card.classList.toggle('finished',job.state==='complete');
      const e=job.events[job.events.length-1] as JobEvent|undefined;
      const p=stageProgress(job.state==='running'?job.stage:job.state,e?.completed,e?.total);
      if(job.state==='complete'&&analysisOnly){p.step=0;p.title='Baseline analysis complete';p.detail='One original shape was evaluated. No candidate or comparison was created.';}
      card.querySelector('strong')!.textContent=(p.step?`Step ${p.step} of 5 · `:'')+p.title;
      card.querySelector('.progress-detail')!.textContent=p.detail;
      card.querySelector('.progress-number')!.textContent=p.percent===null?({complete:'Finished',failed:'Stopped',cancelled:'Cancelled',cancelling:'Stopping…',running:'Working…'}[job.state]??'Working…'):`${p.percent}% of this calculation`;
      const bar=card.querySelector('progress')!;bar.hidden=!active;if(p.percent===null)bar.removeAttribute('value');else bar.value=p.percent;
      card.querySelector('details span')!.textContent=e?.completed===undefined?job.detail:`${e.completed} of ${e.total} GPU batches · ${job.detail}`;
      elapsed.textContent=totalSeconds!==undefined&&!active?format(totalSeconds):format(Math.max(0,(Date.now()-started)/1000));
    }
  };
}
