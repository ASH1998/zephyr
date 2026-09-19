import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validateAirflow,sampleFlowPath} from '../src/airflow.ts';
import {previewSurface} from '../src/geometry-preview.ts';
test('all vehicle and aircraft saved fields bind to their selected car',()=>{
 for(const id of ['drivaer-1','hatchback','suv','wagon','coupe','sports','van','x57','global-hawk']){
  const flow=JSON.parse(readFileSync(new URL(`../public/models/airflow/${id}.json`,import.meta.url),'utf8'));
  assert.equal(validateAirflow(flow,id),flow);assert.throws(()=>validateAirflow(flow,'wrong'));
  assert.throws(()=>validateAirflow(flow,id,'0'.repeat(64)));
  if(id!=='drivaer-1') {const preview=JSON.parse(readFileSync(new URL(`../public/models/cars/${id}.json`,import.meta.url),'utf8'));assert.equal(previewSurface(preview,id).positions.length,preview.positions.length);assert.equal(flow.meshHash,preview.meshHash);}
 }
});
test('particles use travel time, so slow parts do not advance at uniform distance',()=>{
 const path={positions:[0,0,0,1,0,0,2,0,0],speedMps:[1,1,.5],timeSeconds:[0,1,3]};
 assert.deepEqual(sampleFlowPath(path,.5),[.5,0,0]);assert.deepEqual(sampleFlowPath(path,2),[1.5,0,0]);assert.deepEqual(sampleFlowPath(path,3.5),[.5,0,0]);
});
test('invalid timing or velocities cannot reach the renderer',()=>{
 const flow=JSON.parse(readFileSync(new URL('../public/models/airflow/suv.json',import.meta.url),'utf8'));
 flow.paths[0].timeSeconds[1]=0;assert.throws(()=>validateAirflow(flow,'suv'));
});
