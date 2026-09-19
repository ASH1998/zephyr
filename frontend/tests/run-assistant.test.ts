import test from 'node:test';
import assert from 'node:assert/strict';
import {validateAnswer} from '../src/run-assistant.ts';
import {stageProgress} from '../src/run-progress.ts';
const rid='local-'+'a'.repeat(32),question='What changed?';
const answer={answerId:'answer-'+'b'.repeat(32),runId:rid,question,parentAnswerId:null,answerable:true,facts:[{id:'movement',text:'0.5 mm',source:'run' as const,pointers:['/validation/checks/bounds']}],fallback:null,provenance:{model:'test'},evidenceUrl:`/api/runs/${rid}/evidence`};
test('answers stay bound to run, question, and conversation',()=>{
 assert.equal(validateAnswer(answer,rid,question,null),answer);
 assert.throws(()=>validateAnswer(answer,'local-'+'c'.repeat(32),question,null));
 assert.throws(()=>validateAnswer(answer,rid,'Other question',null));
 assert.throws(()=>validateAnswer(answer,rid,question,'answer-'+'d'.repeat(32)));
 assert.throws(()=>validateAnswer({...answer,answerable:false},rid,question,null));
 assert.throws(()=>validateAnswer({...answer,evidenceUrl:'https://other.invalid'},rid,question,null));
});
test('progress is scoped to actual batch counts and resets for the second calculation',()=>{
 assert.equal(stageProgress('baseline',46,92).percent,50);
 assert.equal(stageProgress('evaluate',0,92).percent,0);
 for(const counts of [[undefined,undefined],[2,0],[3,2],[-1,2],[1.5,2]])assert.equal(stageProgress('loading',...counts).percent,null);
 assert.equal(stageProgress('complete').step,5);
 assert.equal(stageProgress('failed').step,0);
});
