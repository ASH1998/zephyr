import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { createDemoRun, validateRun, demoAtBudget } from './data';
import type { SimulationAdapter, SimulationRun, Surface } from './data';
import { cabinLift } from './vehicle-shape';
import { requireVehicle } from './vehicle-catalog';

export interface VehicleAsset { group: THREE.Group; exterior: { mesh: THREE.Mesh; offset: number; count: number }[] }

/** Licensed visual asset -> same validated surface contract used for real runs. */
export class VehicleDemoAdapter implements SimulationAdapter {
  asset?: VehicleAsset;
  constructor(private vehicleId = 'concept-coupe') {}
  async load(): Promise<SimulationRun> {
    const definition = requireVehicle(this.vehicleId);
    const gltf = await new GLTFLoader().loadAsync(definition.assetPath);
    gltf.scene.updateMatrixWorld(true);
    const front = gltf.scene.getObjectByName('BodyHeadlights')!;
    const rear = gltf.scene.getObjectByName('BodyTaillights')!;
    const direction = new THREE.Box3().setFromObject(rear).getCenter(new THREE.Vector3()).sub(new THREE.Box3().setFromObject(front).getCenter(new THREE.Vector3()));
    const orient = new THREE.Matrix4().makeRotationY(Math.atan2(direction.z, direction.x));
    const originals: { geometry: THREE.BufferGeometry; material: THREE.Material; name: string }[] = [];
    const bounds = new THREE.Box3();
    gltf.scene.traverse(o => {
      if (!(o instanceof THREE.Mesh) || /Wipers|License|Emblem/.test(o.name)) return;
      const geometry = o.geometry.clone().applyMatrix4(o.matrixWorld).applyMatrix4(orient);
      geometry.computeBoundingBox(); bounds.union(geometry.boundingBox!);
      const material = (Array.isArray(o.material) ? o.material[0] : o.material).clone();
      originals.push({ geometry, material, name: o.name });
    });
    const size = bounds.getSize(new THREE.Vector3()), center = bounds.getCenter(new THREE.Vector3());
    const scale = 4.65 / size.x;
    const transform = new THREE.Matrix4().makeScale(scale, scale, scale).multiply(new THREE.Matrix4().makeTranslation(-center.x, -bounds.min.y + .035 / scale, -center.z));
    const group = new THREE.Group(), exterior: VehicleAsset['exterior'] = [];
    const baseline: Surface = { positions: [], triangles: [], pressurePa: [], wallShearPa: [], sensitivity: [], normalSensitivity: [], protectedMask: [], displacementM: [] };
    for (const part of originals) {
      part.geometry.applyMatrix4(transform);
      // A documented baseline-only cabin adaptation. Preserve the source normals
      // through the deformation Jacobian instead of destroying authored smoothing.
      if (!/Tire|Rim|Brake|Disc/.test(part.material.name) && !/Wheel|Axles|Engine/.test(part.name)) {
        const positions = part.geometry.getAttribute('position') as THREE.BufferAttribute;
        const normals = part.geometry.getAttribute('normal') as THREE.BufferAttribute;
        const lift = cabinLift;
        const n = new THREE.Vector3();
        for (let i = 0; i < positions.count; i++) {
          const x = positions.getX(i), y = positions.getY(i), e = .0001;
          const dx = (lift(x + e, y) - lift(x - e, y)) / (2 * e);
          const dy = 1 + (lift(x, y + e) - lift(x, y - e)) / (2 * e);
          positions.setY(i, y + lift(x, y));
          if (normals) { n.fromBufferAttribute(normals, i); n.set(n.x - n.y * dx / dy, n.y / dy, n.z).normalize(); normals.setXYZ(i, n.x, n.y, n.z); }
        }
      }
      let material = part.material;
      const name = material.name;
      if (/Paint/.test(name)) material = new THREE.MeshPhysicalMaterial({ color: 0x819aaa, metalness: .65, roughness: .32, clearcoat: .8, clearcoatRoughness: .23 });
      if (/Glass/.test(name)) material = new THREE.MeshPhysicalMaterial({ color: 0x07131f, metalness: 0, roughness: .3, clearcoat: .12, specularIntensity: .3, side: THREE.DoubleSide });
      if (/Interior/.test(name) && material instanceof THREE.MeshStandardMaterial) { material.color.setHex(0x121c26); material.metalness = .15; material.roughness = .8; }
      if (material instanceof THREE.MeshStandardMaterial) material.envMapIntensity = .8;
      if (/Glass/.test(name) && material instanceof THREE.MeshStandardMaterial) material.envMapIntensity = .28;
      const mesh = new THREE.Mesh(part.geometry, material); mesh.name = part.name; group.add(mesh);
      if (!/Paint|Glass/.test(name)) continue;
      const p = part.geometry.getAttribute('position'), offset = baseline.positions.length / 3;
      exterior.push({ mesh, offset, count: p.count });
      for (let i = 0; i < p.count; i++) {
        const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
        const locked = /Glass|Roof|Pillar/.test(name + part.name) || (x > -1.15 && x < 1.2 && y > .72);
        const sensitivity = Math.exp(-Math.pow((x - 1.6) / .6, 2)) * Math.max(0, y - .2) * 110;
        baseline.positions.push(x, y, z);
        baseline.pressurePa.push(440 * Math.exp(-Math.pow((x + 2.2) / .4, 2)) - 290 * Math.exp(-Math.pow((x + .25) / 1.05, 2)) * y - 70 * Math.exp(-Math.pow((x - 1.6) / .6, 2)));
        baseline.wallShearPa.push(2.4, .12 * y, .15 * z); baseline.sensitivity.push(sensitivity * .25, -sensitivity, -.3 * z * sensitivity);
        baseline.normalSensitivity.push(sensitivity); baseline.protectedMask.push(locked ? 1 : 0); baseline.displacementM.push(0);
      }
      const index = part.geometry.index;
      if (index) for (let i = 0; i < index.count; i++) baseline.triangles.push(index.getX(i) + offset);
      else for (let i = 0; i < p.count; i++) baseline.triangles.push(i + offset);
    }
    const candidate = structuredClone(baseline);
    for (let i = 0; i < candidate.displacementM.length; i++) {
      const x = baseline.positions[i * 3], y = baseline.positions[i * 3 + 1], z = baseline.positions[i * 3 + 2];
      const w = baseline.protectedMask[i] ? 0 : Math.exp(-Math.pow((x - 1.75) / .48, 2)) * Math.min(1, Math.max(0, (y - .25) / .4));
      const dy = -.0028 * w, dz = -.0017 * z * w;
      candidate.positions[i * 3 + 1] += dy; candidate.positions[i * 3 + 2] += dz;
      candidate.displacementM[i] = Math.hypot(dy, dz); candidate.pressurePa[i] += 35 * w;
    }
    const run = createDemoRun(); run.baseline = baseline; run.candidate = candidate;
    run.provenance.artifactVersion = definition.artifactVersion;
    run.provenance.meshHash = definition.meshHash;
    run.provenance.evidenceUrls = [definition.evidenceUrl];
    this.asset = { group, exterior };
    return demoAtBudget(3.6, validateRun(run));
  }
}

