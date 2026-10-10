import './upload-car.css';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { previewSurface } from './geometry-preview';
import type { GeometryPreview } from './geometry-preview';
import type { Job } from './live-data';
import { api } from './live-data';
import { bodyRegions } from './body-regions';

type Imported = {id:string;state:string;preview:GeometryPreview & {regionMasks?:Record<string,number[]>};job?:Job;
  report:{label:string;thinFeatureWarning:string;orientation:{lengthM:number|null;rotation:number[];flipFront:boolean};
    trainingRange:{support:string;reason:string;values:{lengthM:number;widthM:number;heightM:number}}}};

/** An isolated preview owns and releases all its WebGL resources when the dialog closes. */
export function createCarUpload(opened:(id:string,job:Job)=>Promise<void>, photoEnabled:boolean) {
  const dialog=document.createElement('dialog');dialog.className='upload-car';
  dialog.innerHTML=`<header><div><p class="eyebrow">YOUR CAR · EXPERIMENTAL</p><h2>Bring your own car</h2></div><button data-close aria-label="Close upload">×</button></header>
    <p>Upload a mesh, or approximate a photo using a scaled catalog template. Every drag result is a DoMINO estimate on experimental geometry.</p>
    <label>Known mesh length in metres (optional, overrides unit guess)<input data-initial-length type="number" min="2.5" max="7" step="0.01" placeholder="e.g. 4.5"></label>
    <label class="upload-drop">Drop a car file here, or choose a file<input type="file" accept=".stl,.obj,.glb,.gltf,.ply,.png,.jpg,.jpeg,.webp"></label>
    <p class="upload-help">Meshes: STL, OBJ, GLB, embedded GLTF or PLY · up to 50 MB. Photos: PNG, JPEG or WebP · up to 10 MB and 12 MP.</p>
    <p data-photo-note></p><p role="status" aria-live="polite" data-status>Choose a file to begin.</p>
    <section data-review hidden><div class="upload-preview" aria-label="Car orientation, ground plane, and sedan size reference"></div>
      <p>Air travels along +X → from the nose toward the rear. Dashed box: 4.61 × 1.79 × 1.42 m sedan reference. Cyan: protected for the selected tool. Amber: editable envelope.</p>
      <div class="upload-options"><button data-rotate="0">Rotate X 90°</button><button data-rotate="1">Rotate Y 90°</button><button data-rotate="2">Rotate Z 90°</button><button data-flip>Flip front / back</button>
      <label>Car length (m)<input data-length type="number" min="2.5" max="7" step="0.01"></label>
      <label>Region overlay<select data-region></select></label><button data-prepare>Apply orientation & size</button></div>
      <p data-report></p><p data-warning></p><button data-confirm>Confirm & run baseline + airflow</button>
    </section>`;
  document.body.append(dialog);
  const el=<T extends HTMLElement>(s:string)=>dialog.querySelector<T>(s)!;
  const file=el<HTMLInputElement>('input[type=file]'), length=el<HTMLInputElement>('[data-length]'), region=el<HTMLSelectElement>('[data-region]');
  region.append(...bodyRegions.filter(([id])=>!id.includes('quintic')&&!id.includes('lower')).map(([id,label])=>new Option(label,id)));
  el('[data-photo-note]').textContent=photoEnabled?'Photos are sent to Gemma and Nemotron via Nebius Token Factory. Dimensions are estimates; this is a template approximation.':'Mesh import is local. Photo import requires the API’s --enable-llm option.';
  let current:Imported|undefined,busy=false,dirty=false,rotation=[0,0,0],flip=false,dispose:(()=>void)|undefined;
  const controls=()=>dialog.querySelectorAll<HTMLButtonElement|HTMLInputElement|HTMLSelectElement>('button,input,select').forEach(e=>e.disabled=busy||(e.hasAttribute('data-confirm')&&dirty));
  const options=()=>({rotation,flipFront:flip,lengthM:Number(length.value)});
  function draw(){
    dispose?.();if(!current)return;
    const preview=previewSurface(current.preview,current.id),host=el('[class=upload-preview]');
    const scene=new THREE.Scene();scene.background=new THREE.Color(0x091824);
    const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.append(renderer.domElement);
    const camera=new THREE.PerspectiveCamera(38,1,.1,80);camera.position.set(-7,4,7);camera.lookAt(0,.7,0);
    const orbit=new OrbitControls(camera,renderer.domElement);orbit.target.set(0,.7,0);orbit.enableDamping=false;
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(preview.positions,3));geometry.setIndex(preview.triangles);geometry.computeVertexNormals();
    const mask=current.preview.regionMasks?.[region.value]??preview.protectedMask,colors:number[]=[];
    mask.forEach(locked=>new THREE.Color(locked?0x63b7b9:0xf4b26c).toArray(colors,colors.length));geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
    scene.add(new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.72,side:THREE.DoubleSide})));
    scene.add(new THREE.HemisphereLight(0xffffff,0x344052,3));const light=new THREE.DirectionalLight(0xffffff,2);light.position.set(-4,6,5);scene.add(light);
    scene.add(new THREE.GridHelper(10,20,0x446471,0x213b48));
    const reference=new THREE.EdgesGeometry(new THREE.BoxGeometry(4.61,1.42,1.79));const outline=new THREE.LineSegments(reference,new THREE.LineDashedMaterial({color:0x8aa1ac,dashSize:.1,gapSize:.08}));outline.position.y=.71;outline.computeLineDistances();scene.add(outline);
    scene.add(new THREE.ArrowHelper(new THREE.Vector3(1,0,0),new THREE.Vector3(-3,.15,1.6),6,0x9ee9dc,.28,.15));
    const render=()=>renderer.render(scene,camera),resize=()=>{const w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();render();};
    orbit.addEventListener('change',render);const observer=new ResizeObserver(resize);observer.observe(host);resize();
    dispose=()=>{observer.disconnect();orbit.dispose();scene.traverse(o=>{if(o instanceof THREE.Mesh||o instanceof THREE.Line){o.geometry.dispose();for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose();}});renderer.dispose();renderer.forceContextLoss();renderer.domElement.remove();};
  }
  function install(value:Imported){current=value;dirty=false;rotation=[...value.report.orientation.rotation];flip=value.report.orientation.flipFront;
    const r=value.report.trainingRange;length.value=r.values.lengthM.toFixed(2);el('[data-review]').hidden=false;
    el('[data-report]').textContent=`${value.report.label}. ${r.values.lengthM.toFixed(2)} × ${r.values.widthM.toFixed(2)} × ${r.values.heightM.toFixed(2)} m. ${r.support==='shape-tests'?'Bounded shape tests available.':'Baseline only.'} ${r.reason}`;
    el('[data-warning]').textContent=value.report.thinFeatureWarning;el('[data-status]').textContent='Surface prepared · geometry screening complete. Check size and orientation before continuing.';draw();
  }
  async function action(message:string,work:()=>Promise<void>){if(busy)return;busy=true;controls();el('[data-status]').textContent=message;
    try{await work();}catch(error){el('[data-status]').textContent=error instanceof Error?error.message:String(error);}finally{busy=false;controls();}}
  async function upload(value:File){await action('Preparing surface → checking geometry limits…',async()=>{
    current=undefined;dispose?.();dispose=undefined;el('[data-review]').hidden=true;
    if(value.size>50*1024*1024)throw new Error('Choose a file under 50 MB');
    const knownLength=el<HTMLInputElement>('[data-initial-length]').value;
    const response=await fetch('/api/uploads',{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Filename':`car.${value.name.split('.').pop()?.toLowerCase()}`,...(knownLength?{'X-Car-Length':knownLength}:{})},body:value});
    const result=await response.json();if(!response.ok)throw new Error(result.error??'Upload failed');install(result);
  });}
  file.onchange=()=>{const selected=file.files?.[0];file.value='';if(selected)void upload(selected);};
  const drop=el('.upload-drop');drop.ondragover=e=>{e.preventDefault();};drop.ondrop=e=>{e.preventDefault();if(e.dataTransfer?.files[0]&&!busy)void upload(e.dataTransfer.files[0]);};
  function changed(){dirty=true;controls();el('[data-status]').textContent=`Pending rotation: ${rotation.join(' / ')}°. Front/back: ${flip?'flipped':'original'}. Apply to preview before confirming.`;}
  dialog.querySelectorAll<HTMLButtonElement>('[data-rotate]').forEach(b=>b.onclick=()=>{const axis=Number(b.dataset.rotate);rotation[axis]=(rotation[axis]+90)%360;changed();});
  el('[data-flip]').onclick=()=>{flip=!flip;changed();};length.oninput=changed;region.onchange=draw;
  el('[data-prepare]').onclick=()=>void action('Preparing updated surface → checking geometry limits…',async()=>{if(current)install(await api<Imported>(`/api/uploads/${current.id}/prepare`,options()));});
  el('[data-confirm]').onclick=()=>void action('Confirming geometry → starting baseline drag → airflow…',async()=>{
    if(!current)return;
    // Use the exact options that produced this preview, avoiding a second rounded-length rescale.
    const o=current.report.orientation;
    const value=await api<Imported>(`/api/uploads/${current.id}/confirm`,{rotation:o.rotation,flipFront:o.flipFront,lengthM:o.lengthM});
    if(!value.job)throw new Error('Baseline job was not returned');await opened(value.id,value.job);dialog.close();
    current=undefined;file.value='';el<HTMLInputElement>('[data-initial-length]').value='';el('[data-review]').hidden=true;el('[data-status]').textContent='Choose a file to begin.';
  });
  el('[data-close]').onclick=()=>dialog.close();dialog.oncancel=e=>{if(busy)e.preventDefault();};dialog.onclose=()=>{dispose?.();dispose=undefined;};
  return {open(){dialog.showModal();if(current)draw();},dispose(){dispose?.();dialog.remove();}};
}
