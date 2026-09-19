import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { previewSurface } from '../src/geometry-preview.ts';
const asset=JSON.parse(readFileSync(new URL('../public/models/drivaer-preview.json',import.meta.url),'utf8'));
test('bundled preview is real geometry only, with no simulated results',()=>{
  const surface=previewSurface(asset);
  assert.equal(surface.positions.length/3,15373);
  for(const key of ['forces','pressurePa','sensitivity','velocity','trust'])assert.equal(key in asset,false);
  for(const patch of [{geometryId:'other'},{units:'mm'},{positions:[0,NaN,1]},{triangles:[0,1,1e9]},{protectedMask:[]}])assert.throws(()=>previewSurface({...asset,...patch}));
});
