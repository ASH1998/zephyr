import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import type { SimulationRun, Surface, ViewMode } from './data';
import type { VehicleAsset } from './vehicle';
import { fieldRange } from './data';
import type { StoryState } from './run-story';
import { FlowRibbons } from './flow-ribbons';
import { illustrateFlow } from './flow-illustration';
import type { Airflow } from './airflow';
import { previewWake } from './flow-preview';

type SurfaceRun = Pick<SimulationRun, 'baseline'> & { source: SimulationRun['source'] | 'geometry-preview'; candidate: Surface | null; airflow?:{baseline:Airflow;candidate?:Airflow} };

export class FlowScene {
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(36, 1, .1, 100);
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  private geometry = new THREE.BufferGeometry();
  private material = new THREE.MeshPhysicalMaterial({ metalness: .52, roughness: .3, vertexColors: true, side: THREE.DoubleSide, clearcoat: .8 });
  private wire: THREE.LineSegments;
  private flow = new THREE.Group();
  private arrows = new THREE.Group();
  private envelope = new THREE.Group();
  private flowMaterials: THREE.ShaderMaterial[] = [];
  private flowCurves: THREE.CatmullRomCurve3[] = [];
  private flowParticles?: THREE.Points;
  private computedAirflow?: Airflow;
  private flowStyle:'illustration'|'prediction'='illustration';
  private illustratedFlow?:FlowRibbons;
  private predictedFlow?:FlowRibbons;
  private surfaceMesh: THREE.Mesh;
  private mode: ViewMode = 'airflow';
  private blend = 0;
  private target = 0;
  private magnification = 24;
  private paused = false;
  private reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  private lastTime = performance.now();
  private elapsed = 0;
  private resizeObserver: ResizeObserver;
  private frame = 0;
  private disposed = false;
  private cabinTop = 1.4;
  private fitScale=1;
  private story?: StoryState;
  private changeOverlay?: THREE.Mesh;
  private lockOverlay?: THREE.Mesh;
  private baselineGhost?: THREE.LineSegments;
  private cameraDestination?: THREE.Vector3;
  private flowGhost = new THREE.Group();
  private rearMarker = new THREE.Group();
  private flowBlend = 0;
  private flowTarget = 0;
  constructor(private host: HTMLElement, private run: SurfaceRun, private vehicle?: VehicleAsset) {
    this.cabinTop = run.baseline.protectedMask.reduce((top, locked, i) => locked ? Math.max(top, run.baseline.positions[i * 3 + 1]) : top, .9);
    const xs=run.baseline.positions.filter((_,i)=>i%3===0);const range=fieldRange(xs);this.fitScale=vehicle?.aircraft? .78 : Math.max(1,(range[1]-range[0])/4.45,this.cabinTop/1.7);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 1.7));
    this.renderer.setClearColor(0x07111d, 0);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping; this.renderer.toneMappingExposure = 1.0;
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    const room = new RoomEnvironment(); this.scene.environment = pmrem.fromScene(room, .05).texture; room.dispose(); pmrem.dispose();
    this.renderer.domElement.setAttribute('aria-label', run.source === 'illustrative' ? 'Rotatable passenger car with illustrative airflow and protected cabin. Use arrow keys to orbit; plus and minus to zoom.' : 'DrivAerML geometry with illustrative airflow; pressure and sensitivity are available after inference. Use arrow keys to orbit; plus and minus to zoom.');
    this.renderer.domElement.tabIndex = 0;
    host.appendChild(this.renderer.domElement);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = !this.reduced; this.controls.enablePan = false;
    this.controls.minDistance = 5; this.controls.maxDistance = 16;
    this.controls.maxPolarAngle = Math.PI * .49; this.controls.minPolarAngle = .25;
    this.resetCamera();
    this.renderer.domElement.addEventListener('keydown', e => {
      if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '-', '='].includes(e.key)) {
        e.preventDefault(); const offset = this.camera.position.clone().sub(this.controls.target);
        const spherical = new THREE.Spherical().setFromVector3(offset);
        if (e.key === 'ArrowLeft') spherical.theta -= .12;
        if (e.key === 'ArrowRight') spherical.theta += .12;
        if (e.key === 'ArrowUp') spherical.phi = Math.max(.25, spherical.phi - .1);
        if (e.key === 'ArrowDown') spherical.phi = Math.min(Math.PI * .49, spherical.phi + .1);
        if (e.key === '+ ' || e.key === '+' || e.key === '=') spherical.radius = Math.max(5, spherical.radius - .5);
        if (e.key === '-') spherical.radius = Math.min(16, spherical.radius + .5);
        this.camera.position.copy(new THREE.Vector3().setFromSpherical(spherical).add(this.controls.target)); this.controls.update();
      }
    });
    this.scene.add(new THREE.HemisphereLight(0xc4e7ff, 0x101823, run.source === 'illustrative' ? .55 : .3));
    const key = new THREE.DirectionalLight(0xfff2df, run.source === 'illustrative' ? 3 : 1.5); key.position.set(-3, 6, 5); this.scene.add(key);
    const rim = new THREE.DirectionalLight(0x8cd9f2, run.source === 'illustrative' ? 2.3 : 1); rim.position.set(2, 4, -4); this.scene.add(rim);
    this.geometry.setAttribute('position', new THREE.Float32BufferAttribute(run.baseline.positions, 3));
    this.geometry.setIndex(run.baseline.triangles); this.geometry.computeVertexNormals();
    this.geometry.setAttribute('color', new THREE.Float32BufferAttribute(new Float32Array(run.baseline.positions.length), 3));
    this.surfaceMesh = new THREE.Mesh(this.geometry, this.material); this.scene.add(this.surfaceMesh);
    if (vehicle) { this.scene.add(vehicle.group); this.surfaceMesh.visible = false; }
    this.wire = new THREE.LineSegments(new THREE.WireframeGeometry(this.geometry), new THREE.LineBasicMaterial({ color: 0x6fdaeb, transparent: true, opacity: .27 }));
    this.wire.visible = false; this.scene.add(this.wire);
    if (run.source === 'illustrative') { if (!vehicle) { this.addWheels(); this.addDetails(); } this.addCabin(); }
    else {
      const points: THREE.Vector3[] = [];
      run.baseline.protectedMask.forEach((locked, i) => { if (locked && run.baseline.positions[i * 3 + 1] > .95 && Math.abs(run.baseline.positions[i * 3]) < 1.05) points.push(new THREE.Vector3().fromArray(run.baseline.positions, i * 3)); });
      if (points.length && !vehicle?.aircraft) this.scene.add(new THREE.Box3Helper(new THREE.Box3().setFromPoints(points), 0x8be7df));
    }
    const grid = new THREE.GridHelper(18, 36, 0x203c50, 0x112a3d); grid.position.y = .01; (grid.material as THREE.Material).transparent = true; (grid.material as THREE.Material).opacity = .18; this.scene.add(grid);
    const shadowCanvas = document.createElement('canvas'); shadowCanvas.width = shadowCanvas.height = 128;
    const ctx = shadowCanvas.getContext('2d')!;
    const gradient = ctx.createRadialGradient(64, 64, 10, 64, 64, 64); gradient.addColorStop(0, '#000e'); gradient.addColorStop(.55, '#0009'); gradient.addColorStop(1, '#0000'); ctx.fillStyle = gradient; ctx.fillRect(0, 0, 128, 128);
    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(6.7, 3.8), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(shadowCanvas), transparent: true, depthWrite: false })); shadow.rotation.x = -Math.PI / 2; shadow.position.y = .05; this.scene.add(shadow);
    if(run.source==='illustrative')this.addFlow();
    else {
      const points=run.baseline.positions;const rear=Math.max(...points.filter((_,i)=>i%3===0));
      this.illustratedFlow=new FlowRibbons(illustrateFlow(points,vehicle?.aircraft),false,rear,vehicle?.aircraft?.65:1);
      this.scene.add(this.illustratedFlow);
    }
    this.scene.add(this.flow, this.flowGhost, this.rearMarker); this.flowGhost.visible = false;
    if (run.source !== 'geometry-preview') this.addSensitivity(); this.scene.add(this.arrows); this.arrows.visible = false;
    this.updateSurface();
    this.addStoryOverlays();
    this.resizeObserver = new ResizeObserver(() => this.resize()); this.resizeObserver.observe(host);
    if(run.airflow?.baseline)this.setAirflow(run.airflow.baseline);
    this.resize(); this.animate();
  }
  setAirflow(value:Airflow) {
    if(this.computedAirflow?.meshHash===value.meshHash)return;
    this.computedAirflow=value;
    this.predictedFlow?.dispose();if(this.predictedFlow)this.scene.remove(this.predictedFlow);
    const points=this.run.baseline.positions;
    const xs=points.filter((_,i)=>i%3===0), ys=points.filter((_,i)=>i%3===1), zs=points.filter((_,i)=>i%3===2);
    const front=Math.min(...xs),rear=Math.max(...xs),top=Math.max(...ys),side=Math.max(...zs.map(Math.abs));
    // Keep the measured paths near the body; remove remote-box clutter only.
    const paths=value.paths.filter(p=>{for(let i=0;i<p.positions.length;i+=3)if(p.positions[i]>front-.4&&p.positions[i]<rear+.8&&p.positions[i+1]<top+.65&&Math.abs(p.positions[i+2])<side+.6)return true;return false;}).slice(0,48);
    this.predictedFlow=new FlowRibbons(paths,true,rear,this.vehicle?.aircraft?.65:1);this.scene.add(this.predictedFlow);
    this.setFlowStyle(this.flowStyle);
    this.updateSurface();
  }
  setFlowStyle(style:'illustration'|'prediction') {
    this.flowStyle=style;
    if(this.illustratedFlow)this.illustratedFlow.visible=this.mode==='airflow'&&style==='illustration';
    if(this.predictedFlow)this.predictedFlow.visible=this.mode==='airflow'&&style==='prediction';
    if(this.run.source!=='illustrative')this.flow.visible=false;
    this.renderer.domElement.setAttribute('aria-label',`${this.vehicle?.aircraft?'Aircraft':'Car'} with ${style==='illustration'?'illustrated airflow bending around the shape; amber trails explain the wake, not a computed field':'NVIDIA predicted velocity paths in slow motion'}. Use arrow keys to orbit; plus and minus to zoom.`);
  }
  private addWheels() {
    for (const x of [-1.47, 1.48]) for (const z of [-.88, .88]) {
      const group = new THREE.Group(); group.position.set(x, .43, z);
      const tire = new THREE.Mesh(new THREE.TorusGeometry(.3, .105, 16, 48), new THREE.MeshStandardMaterial({ color: 0x090e15, roughness: .87 })); group.add(tire);
      const rim = new THREE.Mesh(new THREE.CylinderGeometry(.245, .245, .19, 40), new THREE.MeshStandardMaterial({ color: 0x718697, metalness: .9, roughness: .27 })); rim.rotation.x = Math.PI / 2; group.add(rim);
      const face = new THREE.Mesh(new THREE.CircleGeometry(.2, 40), new THREE.MeshStandardMaterial({ color: 0x0b1825, metalness: .5, roughness: .45, side: THREE.DoubleSide })); face.position.z = Math.sign(z) * .104; group.add(face);
      for (let i = 0; i < 10; i++) {
        const spoke = new THREE.Mesh(new THREE.BoxGeometry(.032, .38, .018), new THREE.MeshStandardMaterial({ color: 0xa0b0bc, metalness: .85, roughness: .24 })); spoke.rotation.z = i * Math.PI / 5; spoke.position.z = Math.sign(z) * .115; group.add(spoke);
      }
      const hub = new THREE.Mesh(new THREE.SphereGeometry(.075, 16, 8), new THREE.MeshStandardMaterial({ color: 0x24384b, metalness: .8, roughness: .3 })); hub.position.z = Math.sign(z) * .12; group.add(hub); this.scene.add(group);
    }
  }
  private line(points: THREE.Vector3[], color: number, opacity = 1) { return new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), new THREE.LineBasicMaterial({ color, transparent: true, opacity })); }
  private addCabin() {
    // A single anchor conveys the lock without drawing a false second roofline.
    const sphere = new THREE.Mesh(new THREE.SphereGeometry(.018, 12, 8), new THREE.MeshBasicMaterial({ color: 0xb8fff5 })); sphere.position.set(.15, this.cabinTop + .03, .15); this.envelope.add(sphere);
    this.envelope.add(this.line([new THREE.Vector3(.15, this.cabinTop + .03, .15), new THREE.Vector3(.15, this.cabinTop + .38, .15)], 0x8be7df, .32));
    this.scene.add(this.envelope);
  }
  private addDetails() {
    for (const z of [-.57, .57]) {
      const light = new THREE.Mesh(new THREE.BoxGeometry(.028, .038, .43), new THREE.MeshBasicMaterial({ color: 0xe3faff })); light.position.set(-2.33, .67, z); this.scene.add(light);
      const rear = new THREE.Mesh(new THREE.BoxGeometry(.025, .035, .41), new THREE.MeshBasicMaterial({ color: 0xd75f58 })); rear.position.set(2.305, .7, z); this.scene.add(rear);
    }
    for (const z of [-.947, .947]) {
      this.scene.add(this.line([new THREE.Vector3(-.98, .73, z), new THREE.Vector3(.82, .73, z)], 0x293f50, .55));
    }
  }
  private addFlow() {
    // Deliberately authored analytic flow ribbons. No volume solution is inferred.
    const make = (height: number, lane: number, kind: 'top' | 'side', phase: number) => {
      const points: THREE.Vector3[] = [];
      for (let i = 0; i <= 160; i++) {
        const x = -5.4 + i / 160 * 11.4;
        const body = Math.exp(-Math.pow((x + .05) / 2.35, 4));
        const roof = Math.exp(-Math.pow((x + .05) / 1.65, 4));
        const wake = Math.max(0, x - 2.3) / 3.7;
        let y = height, z = lane;
        if (kind === 'top') {
          y += Math.max(.6, this.cabinTop - .65) * roof;
          z += lane * .055 * body;
          y += .035 * Math.sin(x * 1.6 + phase) * wake;
        } else {
          z += Math.sign(lane) * .33 * body;
          z += Math.sign(lane) * .075 * Math.sin(x * 1.8 + phase) * wake;
          y += .025 * Math.sin(x * 1.8 + phase) * wake;
        }
        points.push(new THREE.Vector3(x, y, z));
      }
      const curve = new THREE.CatmullRomCurve3(points);
      const material = new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: false,
        depthTest: true,
        blending: THREE.AdditiveBlending,
        uniforms: { time: { value: 0 }, phase: { value: phase }, morph: { value: 0 }, comparison: { value: 0 }, tint: { value: new THREE.Color(kind === 'top' ? 0x82efff : 0x39c9f2) } },
        vertexShader: `uniform float morph; uniform float comparison; uniform float phase; varying float progress; varying float clearance; varying float wakeVisibility; void main(){progress=uv.x;
          float nearBody=(1.-smoothstep(2.1,2.9,abs(position.x)))*(1.-smoothstep(1.8,2.3,position.y));
          clearance=1.-.42*nearBody;vec3 pos=position;
          wakeVisibility=mix(1.,smoothstep(2.05,2.8,pos.x),comparison);float wake=smoothstep(2.15,4.65,pos.x)*comparison;
          pos.y+=sin(pos.x*4.2+phase*6.28)*.22*wake*(1.-morph);
          pos.z=pos.z*(1.-.17*wake*morph)+sin(pos.x*3.8+phase*6.28)*.38*wake*(1.-morph);
          gl_Position=projectionMatrix*modelViewMatrix*vec4(pos,1.0);}`,
        fragmentShader: `uniform float time; uniform float phase; uniform vec3 tint; varying float progress; varying float clearance; varying float wakeVisibility;
          void main(){float p=fract(progress*4.0-time*.48+phase);float head=smoothstep(.48,.74,p)*(1.-smoothstep(.74,.96,p));
          float fade=smoothstep(0.,.09,progress)*(1.-smoothstep(.92,1.,progress));
          vec3 glow=mix(tint,vec3(.92,1.,1.),head*.88);gl_FragColor=vec4(glow,(.065+head*.86)*fade*clearance*wakeVisibility);}`,
      });
      const ghostPoints = curve.getPoints(120).filter(p => p.x >= 2.15).map(p => new THREE.Vector3(...previewWake(p.x, p.y, p.z, phase, 0)));
      const ghost = new THREE.Line(new THREE.BufferGeometry().setFromPoints(ghostPoints), new THREE.LineDashedMaterial({ color: 0x77cddd, transparent: true, opacity: .28, dashSize: .06, gapSize: .045, depthWrite: false }));
      ghost.computeLineDistances(); this.flowGhost.add(ghost);
      this.flowCurves.push(curve);
      this.flowMaterials.push(material);
      this.flow.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 180, .011, 6, false), material));
    };
    // A bold but organized flow field: two roof sheets plus four trails on each
    // flank. Depth testing keeps the vehicle solid while the additive heads make
    // direction legible in the first second of the demo.
    for (let layer = 0; layer < 2; layer++) for (let lane = -2; lane <= 2; lane++) {
      make(.96 + layer * .24, lane * .35, 'top', lane * .075 + layer * .18);
    }
    for (const side of [-1, 1]) for (let lane = 0; lane < 4; lane++) {
      make(.38 + lane * .22, side * (1.30 + lane * .22), 'side', lane * .09 + (side > 0 ? .12 : 0));
    }

    // Bright tracer heads make the direction and speed legible. The paths remain
    // deterministic and illustrative; a recorded/live run can replace this group
    // with solver-provided streamlines through the existing adapter seam.
    const tracersPerCurve = 10;
    const tracerPositions = new Float32Array(this.flowCurves.length * tracersPerCurve * 3);
    const glowCanvas = document.createElement('canvas'); glowCanvas.width = glowCanvas.height = 64;
    const glowContext = glowCanvas.getContext('2d')!;
    const glow = glowContext.createRadialGradient(32, 32, 1, 32, 32, 31);
    glow.addColorStop(0, '#ffffff'); glow.addColorStop(.18, '#c8fbff'); glow.addColorStop(.5, '#43d9f6cc'); glow.addColorStop(1, '#43d9f600');
    glowContext.fillStyle = glow; glowContext.fillRect(0, 0, 64, 64);
    this.flowParticles = new THREE.Points(
      new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(tracerPositions, 3)),
      new THREE.PointsMaterial({
        color: 0xb9f8ff,
        map: new THREE.CanvasTexture(glowCanvas),
        size: .09,
        transparent: true,
        opacity: .95,
        depthTest: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        sizeAttenuation: true,
      }),
    );
    this.flow.add(this.flowParticles);
  }
  private addSensitivity() {
    const s = this.run.baseline;
    const normals = this.geometry.getAttribute('normal');
    const [lo, hi] = fieldRange(s.normalSensitivity), max = Math.max(Math.abs(lo), Math.abs(hi), 1e-9);
    for (let i = 0; i < s.positions.length / 3; i += Math.max(35, Math.ceil(s.normalSensitivity.length / 180))) {
      if (Math.abs(s.normalSensitivity[i]) < max * .05 || s.protectedMask[i] || s.positions[i * 3 + 1] < .65) continue;
      const origin = new THREE.Vector3().fromArray(s.positions, i * 3);
      const direction = new THREE.Vector3().fromBufferAttribute(normals, i).normalize().multiplyScalar(Math.sign(s.normalSensitivity[i]));
      const arrow = new THREE.ArrowHelper(direction, origin, .10 + Math.abs(s.normalSensitivity[i]) / max * .28, 0xf5bc76, .055, .027); this.arrows.add(arrow);
    }
  }
  private addStoryOverlays() {
    const b = this.run.baseline, c = this.run.candidate ?? this.run.baseline;
    const changed: number[] = [], locked: number[] = [];
    const max = Math.max(fieldRange(c.displacementM)[1], 1e-9);
    for (let i = 0; i < b.triangles.length; i += 3) {
      const triangle = b.triangles.slice(i, i + 3);
      if (triangle.every(v => !b.protectedMask[v]) && triangle.some(v => c.displacementM[v] > max * .12)) changed.push(...triangle);
      if (triangle.every(v => b.protectedMask[v])) locked.push(...triangle);
    }
    const makeOverlay = (indices: number[], color: number, opacity: number) => {
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', this.geometry.getAttribute('position')); geometry.setIndex(indices);
      const mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ color, toneMapped: false, transparent: true, opacity, side: THREE.DoubleSide, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
      mesh.visible = false; mesh.renderOrder = 2; this.scene.add(mesh); return mesh;
    };
    this.changeOverlay = makeOverlay(changed, 0xffffff, .82);
    const colors: number[] = [], low = new THREE.Color(0xffdb85), high = new THREE.Color(0xf27936);
    c.displacementM.forEach(d => { const color = low.clone().lerp(high, d / max); colors.push(color.r, color.g, color.b); });
    this.changeOverlay.geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    (this.changeOverlay.material as THREE.MeshBasicMaterial).vertexColors = true;
    this.lockOverlay = makeOverlay(locked, 0x71e4d4, .34);
    const baseline = new THREE.BufferGeometry(); baseline.setAttribute('position', new THREE.Float32BufferAttribute(b.positions, 3)); baseline.setIndex(changed);
    this.baselineGhost = new THREE.LineSegments(new THREE.EdgesGeometry(baseline, 32), new THREE.LineBasicMaterial({ color: 0x83eff4, transparent: true, opacity: .8, depthTest: false, depthWrite: false }));
    this.rearMarker.add(this.line([new THREE.Vector3(1.75, .9, 1.05), new THREE.Vector3(2.15, 1.75, 1.05)], 0xf6ba66, .65));
    this.rearMarker.visible = false;
    baseline.dispose(); this.baselineGhost.renderOrder = 3; this.baselineGhost.visible = false; this.scene.add(this.baselineGhost);
  }
  setStory(stage?: StoryState) {
    this.story = stage;
    if (this.lockOverlay) this.lockOverlay.visible = stage === 'intent' || stage === 'validate';
    const compare = stage === 'candidate' || stage === 'result';
    this.rearMarker.visible = compare;
    const demoFlow = this.run.source === 'illustrative' && (stage === 'evaluate' || stage === 'result');
    this.flowGhost.visible = demoFlow;
    this.flowTarget = this.flowGhost.visible ? 1 : 0;
    if (stage === 'evaluate') this.flowBlend = 0;
    this.flowMaterials.forEach(m => { m.uniforms.comparison.value = this.flowGhost.visible ? 1 : 0; m.uniforms.tint.value.setHex(this.flowGhost.visible ? 0xf1c478 : 0x65dff7); });
    if (this.changeOverlay) this.changeOverlay.visible = compare;
    if (this.baselineGhost) this.baselineGhost.visible = compare;
    if (stage) {
      this.flow.visible = demoFlow || (this.run.source !== 'illustrative' && this.mode === 'airflow');
      const destination = stage === 'intent' ? new THREE.Vector3(-3.4, 3.1, 6.7) : new THREE.Vector3(3.6, 2.5, 5.7);
      destination.multiplyScalar(this.fitScale);this.controls.target.set(.15, .8, 0);
      if (this.reduced) this.camera.position.copy(destination); else this.cameraDestination = destination;
    }
  }
  private updateSurface() {
    const b = this.run.baseline, c = this.run.candidate ?? this.run.baseline;
    const p = this.geometry.getAttribute('position') as THREE.BufferAttribute;
    const colors = this.geometry.getAttribute('color') as THREE.BufferAttribute;
    const color = new THREE.Color();
    const [pLo, pHi] = fieldRange(b.pressurePa), [cLo, cHi] = fieldRange(c.pressurePa), [sLo, sHi] = fieldRange(b.normalSensitivity);
    const low = Math.min(pLo, cLo), high = Math.max(pHi, cHi);
    const maximumDisplacement = Math.max(fieldRange(c.displacementM)[1], 1e-9);
    for (let i = 0; i < b.positions.length / 3; i++) {
      for (let k = 0; k < 3; k++) p.array[i * 3 + k] = b.positions[i * 3 + k] + (c.positions[i * 3 + k] - b.positions[i * 3 + k]) * (this.computedAirflow&&this.mode==='airflow'&&this.run.candidate&&!this.run.airflow?.candidate?0:this.blend) * (this.computedAirflow&&this.mode==='airflow'?1:this.magnification);
      const x = b.positions[i * 3], y = b.positions[i * 3 + 1], z = b.positions[i * 3 + 2];
      if (this.mode === 'pressure') { const v = (b.pressurePa[i] + (c.pressurePa[i] - b.pressurePa[i]) * this.blend - low) / Math.max(high - low, 1e-9); color.setHSL(.64 - Math.max(0, Math.min(1, v)) * .62, .8, .4); }
      else if (this.mode === 'sensitivity') {
        if (this.run.source === 'illustrative') { const v = (b.normalSensitivity[i] - sLo) / Math.max(sHi - sLo, 1e-9); color.setHSL(.53 - v * .46, .75, .3 + v * .15); if (b.protectedMask[i]) color.setHex(0x2e5766); }
        else { const v = b.normalSensitivity[i], max = Math.max(Math.abs(sLo), Math.abs(sHi), 1e-9); const t = Math.asinh(Math.abs(v) / (max * .02)) / Math.asinh(50); color.setHex(0x526273).lerp(new THREE.Color(v < 0 ? 0x246bdd : 0xf26d25), t); }
      }
      else if (this.mode === 'displacement') {
        const v = c.displacementM[i] / maximumDisplacement * this.blend;
        if (b.protectedMask[i]) color.setHex(0x30434e);
        else if (v < .07) color.setHex(0x172d3b);
        else color.setHex(0xffdd85).lerp(new THREE.Color(0xee642b), v);
      }
      else if(b.displayColor && this.mode==='airflow'){color.fromArray(b.displayColor,i*3);}
      else { const glass = b.protectedMask[i] && y > .98 && y < 1.40 && (Math.abs(z) > .44 || x < -.5 || x > .5); color.setHex(glass ? 0x102331 : this.mode === 'mesh' ? 0x142b3b : 0x9eafbc); }
      colors.setXYZ(i, color.r, color.g, color.b);
    }
    p.needsUpdate = true; colors.needsUpdate = true; this.geometry.computeVertexNormals();
    if (this.vehicle) for (const part of this.vehicle.exterior) {
      const positions = part.mesh.geometry.getAttribute('position') as THREE.BufferAttribute;
      for (let i = 0; i < part.count; i++) {
        if(part.basePositions && part.surfaceIndices){const id=part.surfaceIndices[i],base=part.basePositions;positions.setXYZ(i,base[i*3]+(id<0?0:p.getX(id)-b.positions[id*3]),base[i*3+1]+(id<0?0:p.getY(id)-b.positions[id*3+1]),base[i*3+2]+(id<0?0:p.getZ(id)-b.positions[id*3+2]));}
        else positions.setXYZ(i, p.getX(part.offset + i), p.getY(part.offset + i), p.getZ(part.offset + i));
      }
      positions.needsUpdate = true;
    }
    if (this.mode === 'mesh') { this.wire.geometry.dispose(); this.wire.geometry = new THREE.WireframeGeometry(this.geometry); }
  }
  setMode(mode: ViewMode) { if(this.run.source === 'geometry-preview' && !['airflow','mesh'].includes(mode)) return; this.mode = mode; this.wire.visible = mode === 'mesh'; this.arrows.visible = mode === 'sensitivity'; this.flow.visible = mode === 'airflow'; this.material.roughness = mode === 'airflow' ? .48 : .7; this.material.metalness = mode === 'airflow' ? .2 : .1; this.material.clearcoat = mode === 'airflow' ? .4 : 0; this.material.envMapIntensity = mode === 'airflow' ? 1 : .2; this.renderer.toneMappingExposure = mode === 'airflow' ? 1 : .7;
    if (this.vehicle) { this.surfaceMesh.visible = mode !== 'airflow'; this.vehicle.exterior.forEach(p => p.mesh.visible = mode === 'airflow'); }
    this.setFlowStyle(this.flowStyle);this.updateSurface(); }
  setBlend(value: number) { this.target = value; if(this.run.airflow){const field=value>=.5?this.run.airflow.candidate??this.run.airflow.baseline:this.run.airflow.baseline;this.setAirflow(field);} if (this.story === 'result' && this.run.source === 'illustrative') this.flowTarget = value; if (this.story === 'result' || this.story === 'candidate') this.rearMarker.visible = value > 0; if (this.reduced) { this.blend = value; this.updateSurface(); } }
  setMagnified(on: boolean, factor = 24) { this.magnification = on ? factor : 1; this.updateSurface(); }
  setPaused(on: boolean) { this.paused = on; }
  setRun(run: SurfaceRun) { this.run = run; this.updateSurface(); }
  resetCamera() { this.cameraDestination = undefined; this.camera.position.set(...(this.vehicle?.aircraft?[-3.6,3.1,3.7] as [number,number,number]:[-5.5*this.fitScale,2.45*this.fitScale,5.5*this.fitScale] as [number,number,number])); this.controls.target.set(this.vehicle?.aircraft?.4:0,this.vehicle?.aircraft ? .35 : .85,0); this.controls.update(); }
  private resize() { const { width, height } = this.host.getBoundingClientRect(); this.camera.aspect = width / Math.max(1, height); this.camera.zoom = Math.min(1.28, this.camera.aspect * .93); this.camera.updateProjectionMatrix(); this.renderer.setSize(width, height); }
  private animate = () => {
    if (this.disposed) return;
    this.frame = requestAnimationFrame(this.animate);
    const now = performance.now(); const dt = Math.min((now - this.lastTime) / 1000, .04); this.lastTime = now;
    if (this.cameraDestination) {
      this.camera.position.lerp(this.cameraDestination, Math.min(1, dt * 3.5));
      if (this.camera.position.distanceTo(this.cameraDestination) < .015) this.cameraDestination = undefined;
    }
    if (this.changeOverlay) (this.changeOverlay.material as THREE.MeshBasicMaterial).opacity = .72 * this.blend;
    if (!this.paused && !this.reduced) this.elapsed += dt;
    this.flowBlend = this.reduced ? this.flowTarget : THREE.MathUtils.lerp(this.flowBlend, this.flowTarget, Math.min(1, dt * .9));
    this.flowMaterials.forEach(m => { m.uniforms.time.value = this.elapsed; m.uniforms.morph.value = this.flowBlend; });
    this.illustratedFlow?.tick(this.elapsed);this.predictedFlow?.tick(this.elapsed,this.computedAirflow?.playbackTimeScale??1);
    if (this.flowParticles) {
      const positions = this.flowParticles.geometry.getAttribute('position') as THREE.BufferAttribute;
      const point = new THREE.Vector3();
      const tracersPerCurve = positions.count / this.flowCurves.length;
      for (let curveIndex = 0; curveIndex < this.flowCurves.length; curveIndex++) {
        for (let tracer = 0; tracer < tracersPerCurve; tracer++) {
          // A mild time warp gives a visible acceleration over the body without
          // pretending to be a computed velocity field.
          const base = (tracer / tracersPerCurve + this.elapsed * .14 + curveIndex * .027) % 1;
          const accelerated = base + .035 * Math.sin((base - .43) * Math.PI * 2);
          this.flowCurves[curveIndex].getPoint(THREE.MathUtils.clamp(accelerated, 0, 1), point);
          if (this.flowGhost.visible && point.x < 2.15) point.y = -1000;
          if (this.flowGhost.visible) point.set(...previewWake(point.x, point.y, point.z, this.flowMaterials[curveIndex].uniforms.phase.value, this.flowBlend));
          positions.setXYZ(curveIndex * tracersPerCurve + tracer, point.x, point.y, point.z);
        }
      }
      positions.needsUpdate = true;
    }
    const label = this.host.parentElement?.querySelector<HTMLElement>('.cabin-label');
    if (label) { const anchor = new THREE.Vector3(.15, this.cabinTop + .38, .15).project(this.camera); label.style.left = `${(anchor.x * .5 + .5) * this.host.clientWidth + this.host.offsetLeft}px`; label.style.top = `${(-anchor.y * .5 + .5) * this.host.clientHeight + this.host.offsetTop - 45}px`; }
    const rearLabel = this.host.parentElement?.querySelector<HTMLElement>('.rear-callout');
    if (rearLabel && this.rearMarker.visible) {
      const anchor = new THREE.Vector3(2.15, 1.75, 1.05).project(this.camera);
      rearLabel.style.left = `${Math.max(8, Math.min(this.host.clientWidth - rearLabel.offsetWidth - 8, (anchor.x * .5 + .5) * this.host.clientWidth + this.host.offsetLeft))}px`;
      rearLabel.style.top = `${(-anchor.y * .5 + .5) * this.host.clientHeight + this.host.offsetTop - 40}px`;
    }
    if (Math.abs(this.blend - this.target) > .0005) { this.blend += (this.target - this.blend) * Math.min(1, dt * (this.story === 'candidate' ? 1.4 : 7)); this.updateSurface(); }
    this.controls.update(); this.renderer.render(this.scene, this.camera);
  };
  dispose() { this.disposed = true; cancelAnimationFrame(this.frame); this.resizeObserver.disconnect(); this.controls.dispose(); this.scene.traverse(o => { if (o instanceof THREE.Mesh || o instanceof THREE.Line || o instanceof THREE.Points) { o.geometry.dispose(); const mats = Array.isArray(o.material) ? o.material : [o.material]; mats.forEach(m => {Object.values(m).forEach(value=>{if(value instanceof THREE.Texture)value.dispose();});m.dispose();}); } }); this.scene.environment?.dispose(); this.renderer.dispose(); this.renderer.domElement.remove(); }
}


