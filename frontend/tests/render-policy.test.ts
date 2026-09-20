import test from 'node:test';
import assert from 'node:assert/strict';
import {framePolicy,activityCaption,computationActive} from '../src/render-policy.ts';
const idle={visible:true,hidden:false,dirty:false,moving:false,busy:false,now:1000,last:900};
test('static or paused views do not draw or schedule more frames',()=>{
  assert.deepEqual(framePolicy(idle),{draw:false,again:false});
  assert.deepEqual(framePolicy({...idle,dirty:true}),{draw:true,again:false});
});
test('invisible and background views stop even if dirty or animated',()=>{
  for(const patch of [{visible:false},{hidden:true}])assert.deepEqual(framePolicy({...idle,...patch,dirty:true,moving:true}),{draw:false,again:false});
});
test('motion caps at 30 fps, compute activity at 20 fps',()=>{
  assert.equal(framePolicy({...idle,moving:true,now:925}).draw,false);
  assert.equal(framePolicy({...idle,moving:true,now:934}).draw,true);
  assert.equal(framePolicy({...idle,moving:true,busy:true,now:940}).draw,false);
  assert.equal(framePolicy({...idle,moving:true,busy:true,now:950}).draw,true);
});
test('activity is tied to an active job and never presented as a pressure measurement',()=>{
  assert.equal(computationActive('running'),true);
  for(const state of ['complete','failed','cancelled','cancelling','recorded'])assert.equal(computationActive(state),false);
  assert.match(activityCaption('baseline',25,false),/25%.*Illustrative.*not a pressure result/);
  assert.match(activityCaption('probe-plus-h',null,true),/Recorded baseline field.*illustrative/);
  assert.doesNotMatch(activityCaption('loading',null,false),/%/);
});
