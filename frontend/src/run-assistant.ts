import { api } from './live-data.ts';
export interface AnswerFact {id:string;text:string;source:'run'|'application';pointers:string[]}
interface Summary {runId:string;headline:string;decision:string;comparisonOnly?:boolean;facts:AnswerFact[];metrics?:{label:string;value:string}[];technicalFacts?:AnswerFact[];evidenceUrl:string}
export interface RunAnswer {answerId:string;runId:string;question:string;parentAnswerId:string|null;answerable:boolean;facts:AnswerFact[];fallback:string|null;provenance:{model:string};evidenceUrl:string}
function validFacts(facts:AnswerFact[]) {return Array.isArray(facts)&&facts.every(f=>typeof f.id==='string'&&typeof f.text==='string'&&['run','application'].includes(f.source)&&Array.isArray(f.pointers)&&f.pointers.every(p=>typeof p==='string'&&p.startsWith('/')));}
export function validateAnswer(a:RunAnswer,runId:string,question:string,parent:string|null) {
  if(a?.runId!==runId||a.question!==question||a.parentAnswerId!==parent||!/^answer-[a-f0-9]{32}$/.test(a.answerId)||typeof a.answerable!=='boolean'||!validFacts(a.facts)||a.facts.length>4||a.answerable!==!!a.facts.length||(!a.answerable&&typeof a.fallback!=='string')||a.evidenceUrl!==`/api/runs/${runId}/evidence`||!a.provenance?.model)throw new Error('This answer does not match the displayed run. Please try again.');
  return a;
}
export function createRunAssistant() {
  const root=document.createElement('section');root.className='run-assistant';root.hidden=true;root.setAttribute('aria-label','Understand this result');
  root.innerHTML=`<p class="eyebrow">YOUR RESULT, EXPLAINED</p><h3></h3><div class="result-summary"></div><details class="result-sources"><summary>Technical details and recorded numbers</summary><div class="detail-facts"></div><a target="_blank" rel="noopener">Open this run’s evidence ↗</a><p>These numbers belong to the displayed run. Questions do not start a new GPU calculation.</p></details><div class="run-chat"><h4>Ask about this result</h4><p class="chat-help">Ask in your own words. Follow-up questions stay with this run.</p><div class="question-suggestions"></div><div class="chat-transcript" role="log" aria-label="Questions about this run"></div><form><label for="run-question">Your question</label><textarea id="run-question" rows="2" maxlength="500" placeholder="What does this result mean?"></textarea><button type="submit" class="ask-button">Ask Zephyr ↗</button></form><p class="chat-status" role="status"></p></div><button type="button" class="edit-next">Edit brief / run again ↓</button>`;
  document.querySelector('.vehicle-picker')!.after(root);
  const heading=root.querySelector('h3')!,summary=root.querySelector('.result-summary')!,transcript=root.querySelector('.chat-transcript')!,input=root.querySelector<HTMLTextAreaElement>('textarea')!,submit=root.querySelector<HTMLButtonElement>('[type=submit]')!,status=root.querySelector('.chat-status')!,suggestions=root.querySelector('.question-suggestions')!;
  let currentRun:string|undefined,parent:string|null=null,enabled=false,busy=false,generation=0,loaded=false;
  function controls(){input.disabled=submit.disabled=busy||!enabled;suggestions.querySelectorAll<HTMLButtonElement>('button').forEach(b=>b.disabled=busy||!enabled);submit.textContent=busy?'Reading your question…':'Ask Zephyr ↗';}
  function message(who:string,paragraphs:string[]){const article=document.createElement('article'),label=document.createElement('b');article.className=who==='You'?'user-question':'run-answer';label.textContent=who;article.append(label);for(const text of paragraphs){const p=document.createElement('p');p.textContent=text;article.append(p);}transcript.append(article);return article;}
  async function ask(question=input.value.trim()) {
    if(!currentRun||busy||!enabled||!question)return;
    if(question.length>500){status.textContent='Please keep your question under 500 characters.';return;}
    const expected=currentRun,expectedParent=parent,epoch=generation;
    busy=true;controls();status.textContent='Reading the facts from this run…';
    message('You',[question]);input.value='';
    try{
      const answer=validateAnswer(await api<RunAnswer>(`/api/runs/${expected}/questions`,{question,parentAnswerId:expectedParent}),expected,question,expectedParent);
      if(expected!==currentRun||epoch!==generation)return;
      parent=answer.answerId;const article=message('Zephyr',answer.answerable?answer.facts.map(f=>f.text):[answer.fallback!]);
      const details=document.createElement('details'),label=document.createElement('summary');label.textContent='Where this answer comes from';details.append(label);
      const p=document.createElement('p');p.textContent=`${answer.provenance.model} selected the relevant facts. Numbers come from this run; descriptions of available features come from the app.`;details.append(p);
      if(answer.facts.some(f=>f.source==='run')){const a=document.createElement('a');a.href=answer.evidenceUrl;a.textContent='View run evidence ↗';a.target='_blank';a.rel='noopener';details.append(a);}
      article.append(details);article.scrollIntoView({behavior:'smooth',block:'nearest'});status.textContent='You can ask a follow-up question.';
    }catch(error){if(expected===currentRun&&epoch===generation){status.textContent=error instanceof Error?error.message:String(error);input.value=question;}}
    finally{if(epoch===generation){busy=false;controls();}}
  }
  root.querySelector<HTMLButtonElement>('.edit-next')!.onclick=()=>{const brief=document.querySelector<HTMLTextAreaElement>('#brief')!;brief.scrollIntoView({behavior:'smooth',block:'center'});brief.focus({preventScroll:true});};
  root.querySelector('form')!.onsubmit=e=>{e.preventDefault();void ask();};
  for(const question of ['Why was it rejected?','What actually changed?','Is the airflow real?','What should we try next?']){const b=document.createElement('button');b.type='button';b.textContent=question;b.onclick=()=>void ask(question);suggestions.append(b);}
  return {
    setEnabled(value:boolean){enabled=value;controls();if(!value)status.textContent='Questions are available when the API is started with --enable-llm.';},
    reset(){generation++;currentRun=undefined;parent=null;loaded=false;busy=false;transcript.replaceChildren();input.value='';status.textContent='';root.hidden=true;controls();},
    async show(runId:string){
      if(currentRun===runId&&loaded)return;
      if(currentRun!==runId){generation++;parent=null;busy=false;loaded=false;transcript.replaceChildren();input.value='';}
      currentRun=runId;root.hidden=false;controls();heading.textContent='Reading your result…';
      const epoch=generation;
      try{
        const data=await api<Summary>(`/api/runs/${runId}/summary`);
        if(epoch!==generation||currentRun!==runId)return;
        if(data?.runId!==runId||typeof data.headline!=='string'||!validFacts(data.facts)||data.evidenceUrl!==`/api/runs/${runId}/evidence`)throw new Error('Summary does not match this run');
        heading.textContent=data.headline.replace('Original car tested','Original shape tested');summary.replaceChildren();root.querySelector('.detail-facts')!.replaceChildren();
        for(const fact of data.facts){const p=document.createElement('p');p.className=`summary-${fact.id}`;p.textContent=fact.text;summary.append(p);}
        const detail=root.querySelector('.detail-facts')!;
        if(data.metrics){const dl=document.createElement('dl');for(const metric of data.metrics){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=metric.label;dd.textContent=metric.value;dl.append(dt,dd);}detail.append(dl);}
        for(const fact of data.technicalFacts??[]){const p=document.createElement('p');p.textContent=fact.text;detail.append(p);}
        const decisionQuestion=data.comparisonOnly?'What changed in this comparison?':data.decision==='accept'?'Why did the local check pass?':'Why was it rejected?';
        const decisionButton=suggestions.querySelector<HTMLButtonElement>('button')!;decisionButton.textContent=decisionQuestion;decisionButton.onclick=()=>void ask(decisionQuestion);
        root.querySelector<HTMLAnchorElement>('.result-sources a')!.href=data.evidenceUrl;loaded=true;
        status.textContent=enabled?'Answers use this run’s evidence and the app’s current capabilities.':'Questions need the API’s --enable-llm option.';
      }catch(error){if(epoch===generation){heading.textContent='The result summary is unavailable';status.textContent=error instanceof Error?error.message:String(error);}}
    }
  };
}
