import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { Box3, Matrix4, Quaternion, Vector3 } from 'three';
import { cabinLift } from '../src/vehicle-shape.ts';
import { requireVehicle } from '../src/vehicle-catalog.ts';

test('the actual imported roof receives the lift, while tires stay unchanged', () => {
  const bytes = readFileSync(new URL('../public/models/car-concept.glb', import.meta.url));
  const jsonLength = bytes.readUInt32LE(12);
  const gltf = JSON.parse(bytes.subarray(20, 20 + jsonLength).toString());
  const binary = bytes.subarray(28 + jsonLength);
  const parts: { name: string; points: Vector3[]; box: Box3 }[] = [];
  function visit(index: number, parent: Matrix4) {
    const node = gltf.nodes[index];
    const local = node.matrix ? new Matrix4().fromArray(node.matrix) : new Matrix4().compose(
      new Vector3(...(node.translation || [0, 0, 0])),
      new Quaternion(...(node.rotation || [0, 0, 0, 1])), new Vector3(...(node.scale || [1, 1, 1])));
    local.premultiply(parent);
    if (node.mesh !== undefined && !/Wipers|License|Emblem/.test(node.name)) {
      const points: Vector3[] = [];
      for (const primitive of gltf.meshes[node.mesh].primitives) {
        const accessor = gltf.accessors[primitive.attributes.POSITION];
        assert.equal(accessor.componentType, 5126);
        const view = gltf.bufferViews[accessor.bufferView];
        for (let i = 0; i < accessor.count; i++) {
          const offset = (view.byteOffset || 0) + (accessor.byteOffset || 0) + i * (view.byteStride || 12);
          points.push(new Vector3(binary.readFloatLE(offset), binary.readFloatLE(offset + 4), binary.readFloatLE(offset + 8)).applyMatrix4(local));
        }
      }
      parts.push({ name: node.name, points, box: new Box3().setFromPoints(points) });
    }
    for (const child of node.children || []) visit(child, local);
  }
  visit(gltf.scenes[0].nodes[0], new Matrix4());
  const front = parts.find(part => part.name === 'BodyHeadlights')!;
  const rear = parts.find(part => part.name === 'BodyTaillights')!;
  const direction = rear.box.getCenter(new Vector3()).sub(front.box.getCenter(new Vector3()));
  const orient = new Matrix4().makeRotationY(Math.atan2(direction.z, direction.x));
  parts.forEach(part => part.points.forEach(point => point.applyMatrix4(orient)));
  const bounds = new Box3().setFromPoints(parts.flatMap(part => part.points));
  const center = bounds.getCenter(new Vector3()), scale = 4.65 / bounds.getSize(new Vector3()).x;
  parts.forEach(part => part.points.forEach(point => point.set((point.x - center.x) * scale, (point.y - bounds.min.y) * scale + .035, (point.z - center.z) * scale)));
  const roof = parts.find(part => part.name === 'BodyRoofPanel')!.points;
  const highest = roof.reduce((a, b) => a.y > b.y ? a : b);
  assert.ok(highest.y < 1.3, 'fixture must reproduce the low source canopy');
  assert.ok(highest.y + cabinLift(highest.x, highest.y) > 1.5, 'the styling must reach the real roof vertices');
  const wheels = parts.filter(part => /Wheel/.test(part.name) && !/Interior/.test(part.name));
  assert.ok(wheels.length >= 4, 'verify wheel coordinates from the asset, not an empty selection');
  for (const part of wheels) {
    for (const point of part.points) assert.equal(cabinLift(point.x, point.y), 0);
  }
  for (const part of parts) for (const point of part.points) {
    const lift = cabinLift(point.x, point.y);
    assert.ok(Number.isFinite(lift) && lift >= 0 && lift <= .28);
  }
});

test('unavailable and unknown geometry cannot silently load the hero asset', () => {
  assert.equal(requireVehicle('concept-coupe').assetPath, '/models/car-concept.glb');
  assert.throws(() => requireVehicle('sedan'), /unavailable/);
  assert.throws(() => requireVehicle('suv'), /unavailable/);
  assert.throws(() => requireVehicle('missing'), /Unknown vehicle/);
});
