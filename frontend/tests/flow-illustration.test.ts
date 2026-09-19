import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {illustrateFlow} from '../src/flow-illustration.ts';
import {TraceCurve} from '../src/flow-ribbons.ts';

test('illustrative paths go around a solid box, with detached wake behind it',()=>{
  const points:number[]=[];
  for(let x=-2;x<=2.001;x+=.04)for(let z=-1;z<=1.001;z+=.04){points.push(x,1.6,z,x,0,z);}
  for(let x=-2;x<=2.001;x+=.04)for(let y=0;y<=1.601;y+=.04)points.push(x,y,-1,x,y,1);
  for(const path of illustrateFlow(points))for(let i=0;i<path.positions.length;i+=3){
    const [x,y,z]=path.positions.slice(i,i+3);
    assert.ok(!(x>-2&&x<2&&y>0&&y<1.6&&z>-1&&z<1),'a trail entered the solid');
    if(path.wake)assert.ok(x>2,'wake must start behind the body');
  }
});
test('every detailed car and aircraft gets finite, forward-moving illustrative paths without changing the source geometry',()=>{
 for(const id of ['hatchback','suv','wagon','coupe','sports','van','x57','global-hawk']){
  const {positions}=JSON.parse(readFileSync(new URL(`../public/models/cars/${id}.json`,import.meta.url),'utf8'));const original=positions.slice();
  const paths=illustrateFlow(positions,id==='x57'||id==='global-hawk');assert.ok(paths.length>=20);
  for(const path of paths){assert.ok(path.positions.every(Number.isFinite));for(let i=3;i<path.positions.length;i+=3)assert.ok(path.positions[i]>path.positions[i-3]);}
  assert.deepEqual(positions,original);
 }
});
test('rendered prediction rings retain raw sample positions, without spline overshoot or arc-length retiming',()=>{
 const path=new TraceCurve([0,0,0,1,1,0,10,1,0]);
 assert.deepEqual(path.getPointAt(.5).toArray(),[1,1,0]);
 assert.deepEqual(path.getPointAt(.25).toArray(),[.5,.5,0]);
 assert.deepEqual(path.getPointAt(.75).toArray(),[5.5,1,0]);
});


test('aircraft vortices originate at opposite wing tips and rotate in opposite directions',()=>{
 for(const id of ['x57','global-hawk']) {
  const {positions}=JSON.parse(readFileSync(new URL(`../public/models/cars/${id}.json`,import.meta.url),'utf8'));
  const xs=positions.filter((_:number,i:number)=>i%3===0),zs=positions.filter((_:number,i:number)=>i%3===2);
  const width=Math.max(...zs)-Math.min(...zs),center=(Math.max(...zs)+Math.min(...zs))/2,rear=Math.max(...xs);
  const vortices=illustrateFlow(positions,true).filter(p=>p.vortexSide!==undefined);
  assert.deepEqual([...new Set(vortices.map(p=>p.vortexSide))].sort(),[-1,1]);
  for(const path of vortices) {
    assert.ok(Math.abs(path.positions[2]-center)>width*.44,'spiral must start near a wing tip');
    assert.ok(path.positions[0]<rear,'spiral starts at the wing, not behind the tail');
    assert.ok(path.positions.at(-3)!>rear,'spiral trails behind the aircraft');
    let rotation=0;
    for(let j=30;j<100;j++) {
      const y=path.positions[j*3+1]-path.positions[1]+width*.028*j/240,z=path.positions[j*3+2]-path.positions[2];
      const nextY=path.positions[(j+1)*3+1]-path.positions[1]+width*.028*(j+1)/240,nextZ=path.positions[(j+1)*3+2]-path.positions[2];
      rotation+=z*nextY-y*nextZ;
    }
    assert.ok(rotation*path.vortexSide!>0,'the two wake tubes must counter-rotate');
  }
 }
});

test('car illustration spans at least twice the body width',()=>{
 for(const id of ['hatchback','suv','wagon','coupe','sports','van']) {
  const {positions}=JSON.parse(readFileSync(new URL(`../public/models/cars/${id}.json`,import.meta.url),'utf8'));
  const zs=positions.filter((_:number,i:number)=>i%3===2),width=Math.max(...zs)-Math.min(...zs);
  const shown=illustrateFlow(positions).flatMap(p=>p.positions.filter((_,i)=>i%3===2));
  assert.ok(Math.max(...shown)-Math.min(...shown)>width*2,id+' flow corridor is too narrow');
 }
});
