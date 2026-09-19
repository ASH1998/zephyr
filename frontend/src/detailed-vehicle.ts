import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import type { Surface } from './data';
import type { VehicleAsset } from './vehicle';
export interface VisualSpec {url:string;offset:[number,number,number]}
/** Detailed visual mesh, aligned to the simplified surface used for inference. */
export async function loadDetailedVehicle(spec:VisualSpec,surface:Surface):Promise<VehicleAsset>{
  if(!/^\/models\/vehicles\/[a-z0-9-]+\.glb$/.test(spec.url)||spec.offset.length!==3||!spec.offset.every(Number.isFinite))throw new Error('Invalid visual asset');
  const gltf=await new GLTFLoader().loadAsync(spec.url);gltf.scene.updateMatrixWorld(true);
  const group=new THREE.Group(),exterior:VehicleAsset['exterior']=[];
  const cells=new Map<string,number[]>(),cellSize=.12,p=surface.positions;
  const key=(x:number,y:number,z:number)=>`${x},${y},${z}`;
  for(let i=0;i<p.length;i+=3){const k=key(Math.floor(p[i]/cellSize),Math.floor(p[i+1]/cellSize),Math.floor(p[i+2]/cellSize));const ids=cells.get(k)??[];ids.push(i/3);cells.set(k,ids);}
  gltf.scene.traverse(o=>{
    if(!(o instanceof THREE.Mesh))return;
    const geometry=o.geometry.clone().applyMatrix4(o.matrixWorld);geometry.translate(...spec.offset);
    const position=geometry.getAttribute('position');const basePositions=new Float32Array(position.array),surfaceIndices=new Int32Array(position.count).fill(-1);
    for(let i=0;i<position.count;i++){
      const x=position.getX(i),y=position.getY(i),z=position.getZ(i),cx=Math.floor(x/cellSize),cy=Math.floor(y/cellSize),cz=Math.floor(z/cellSize);let best=.3*.3;
      for(let dx=-2;dx<=2;dx++)for(let dy=-2;dy<=2;dy++)for(let dz=-2;dz<=2;dz++)for(const id of cells.get(key(cx+dx,cy+dy,cz+dz))??[]){const d=(x-p[id*3])**2+(y-p[id*3+1])**2+(z-p[id*3+2])**2;if(d<best){best=d;surfaceIndices[i]=id;}}
    }
    const materials=(Array.isArray(o.material)?o.material:[o.material]).map(original=>{const m=original.clone();if(m instanceof THREE.MeshStandardMaterial){m.envMapIntensity=.7;if(/glass|windows/i.test(m.name)){m.color.setHex(0x142a38);m.map=null;m.roughness=.22;m.metalness=.08;}}return m;});
    const mesh=new THREE.Mesh(geometry,Array.isArray(o.material)?materials:materials[0]);mesh.name=o.name;group.add(mesh);exterior.push({mesh,offset:0,count:position.count,basePositions,surfaceIndices});
  });
  return {group,exterior,aircraft:/x57|global-hawk/.test(spec.url)};
}
