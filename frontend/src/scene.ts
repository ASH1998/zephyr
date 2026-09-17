import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import type { SimulationRun, ViewMode } from './data';
import type { VehicleAsset } from './vehicle';
import { fieldRange } from './data';

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
  constructor(private host: HTMLElement, private run: SimulationRun, private vehicle?: VehicleAsset) {
    this.cabinTop = run.baseline.protectedMask.reduce((top, locked, i) => locked ? Math.max(top, run.baseline.positions[i * 3 + 1]) : top, .9);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 1.7));
    this.renderer.setClearColor(0x07111d, 0);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping; this.renderer.toneMappingExposure = 1.0;
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    const room = new RoomEnvironment(); this.scene.environment = pmrem.fromScene(room, .05).texture; room.dispose(); pmrem.dispose();
    this.renderer.domElement.setAttribute('aria-label', 'Rotatable passenger car with illustrative airflow and protected cabin. Use arrow keys to orbit; plus and minus to zoom.');
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
    this.scene.add(new THREE.HemisphereLight(0xc4e7ff, 0x101823, .55));
    const key = new THREE.DirectionalLight(0xfff2df, 3); key.position.set(-3, 6, 5); this.scene.add(key);
    const rim = new THREE.DirectionalLight(0x8cd9f2, 2.3); rim.position.set(2, 4, -4); this.scene.add(rim);
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
      run.baseline.protectedMask.forEach((locked, i) => { if (locked) points.push(new THREE.Vector3().fromArray(run.baseline.positions, i * 3)); });
      if (points.length) this.scene.add(new THREE.Box3Helper(new THREE.Box3().setFromPoints(points), 0x8be7df));
    }
    const grid = new THREE.GridHelper(18, 36, 0x203c50, 0x112a3d); grid.position.y = .01; (grid.material as THREE.Material).transparent = true; (grid.material as THREE.Material).opacity = .18; this.scene.add(grid);
    const shadowCanvas = document.createElement('canvas'); shadowCanvas.width = shadowCanvas.height = 128;
    const ctx = shadowCanvas.getContext('2d')!;
    const gradient = ctx.createRadialGradient(64, 64, 10, 64, 64, 64); gradient.addColorStop(0, '#000e'); gradient.addColorStop(.55, '#0009'); gradient.addColorStop(1, '#0000'); ctx.fillStyle = gradient; ctx.fillRect(0, 0, 128, 128);
    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(6.7, 3.8), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(shadowCanvas), transparent: true, depthWrite: false })); shadow.rotation.x = -Math.PI / 2; shadow.position.y = .05; this.scene.add(shadow);
    this.addFlow();
    this.scene.add(this.flow);
    this.addSensitivity(); this.scene.add(this.arrows); this.arrows.visible = false;
    this.updateSurface();
    this.resizeObserver = new ResizeObserver(() => this.resize()); this.resizeObserver.observe(host);
    this.resize(); this.animate();
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
        uniforms: { time: { value: 0 }, phase: { value: phase }, tint: { value: new THREE.Color(kind === 'top' ? 0x82efff : 0x39c9f2) } },
        vertexShader: `varying float progress; varying float clearance; void main(){progress=uv.x;
          float nearBody=(1.-smoothstep(2.1,2.9,abs(position.x)))*(1.-smoothstep(1.8,2.3,position.y));
          clearance=1.-.42*nearBody;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
        fragmentShader: `uniform float time; uniform float phase; uniform vec3 tint; varying float progress; varying float clearance;
          void main(){float p=fract(progress*4.0-time*.48+phase);float head=smoothstep(.48,.74,p)*(1.-smoothstep(.74,.96,p));
          float fade=smoothstep(0.,.09,progress)*(1.-smoothstep(.92,1.,progress));
          vec3 glow=mix(tint,vec3(.92,1.,1.),head*.88);gl_FragColor=vec4(glow,(.065+head*.86)*fade*clearance);}`,
      });
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
  private updateSurface() {
    const b = this.run.baseline, c = this.run.candidate;
    const p = this.geometry.getAttribute('position') as THREE.BufferAttribute;
    const colors = this.geometry.getAttribute('color') as THREE.BufferAttribute;
    const color = new THREE.Color();
    const [pLo, pHi] = fieldRange(b.pressurePa), [cLo, cHi] = fieldRange(c.pressurePa), [sLo, sHi] = fieldRange(b.normalSensitivity);
    const low = Math.min(pLo, cLo), high = Math.max(pHi, cHi);
    for (let i = 0; i < b.positions.length / 3; i++) {
      for (let k = 0; k < 3; k++) p.array[i * 3 + k] = b.positions[i * 3 + k] + (c.positions[i * 3 + k] - b.positions[i * 3 + k]) * this.blend * this.magnification;
      const x = b.positions[i * 3], y = b.positions[i * 3 + 1], z = b.positions[i * 3 + 2];
      if (this.mode === 'pressure') { const v = (b.pressurePa[i] + (c.pressurePa[i] - b.pressurePa[i]) * this.blend - low) / Math.max(high - low, 1e-9); color.setHSL(.64 - Math.max(0, Math.min(1, v)) * .62, .8, .4); }
      else if (this.mode === 'sensitivity') { const v = (b.normalSensitivity[i] - sLo) / Math.max(sHi - sLo, 1e-9); color.setHSL(.53 - v * .46, .75, .3 + v * .15); if (b.protectedMask[i]) color.setHex(0x2e5766); }
      else { const glass = b.protectedMask[i] && y > .98 && y < 1.40 && (Math.abs(z) > .44 || x < -.5 || x > .5); color.setHex(glass ? 0x102331 : this.mode === 'mesh' ? 0x142b3b : 0x9eafbc); }
      colors.setXYZ(i, color.r, color.g, color.b);
    }
    p.needsUpdate = true; colors.needsUpdate = true; this.geometry.computeVertexNormals();
    if (this.vehicle) for (const part of this.vehicle.exterior) {
      const positions = part.mesh.geometry.getAttribute('position') as THREE.BufferAttribute;
      for (let i = 0; i < part.count; i++) positions.setXYZ(i, p.getX(part.offset + i), p.getY(part.offset + i), p.getZ(part.offset + i));
      positions.needsUpdate = true;
    }
    if (this.mode === 'mesh') { this.wire.geometry.dispose(); this.wire.geometry = new THREE.WireframeGeometry(this.geometry); }
  }
  setMode(mode: ViewMode) { this.mode = mode; this.wire.visible = mode === 'mesh'; this.arrows.visible = mode === 'sensitivity'; this.flow.visible = mode === 'airflow'; this.material.roughness = mode === 'airflow' ? .3 : .7; this.material.metalness = mode === 'airflow' ? .52 : .1; this.renderer.toneMappingExposure = mode === 'airflow' ? 1 : .85;
    if (this.vehicle) { this.surfaceMesh.visible = mode !== 'airflow'; this.vehicle.exterior.forEach(p => p.mesh.visible = mode === 'airflow'); }
    this.updateSurface(); }
  setBlend(value: number) { this.target = value; if (this.reduced) { this.blend = value; this.updateSurface(); } }
  setMagnified(on: boolean) { this.magnification = on ? 24 : 1; this.updateSurface(); }
  setPaused(on: boolean) { this.paused = on; }
  setRun(run: SimulationRun) { this.run = run; this.updateSurface(); }
  resetCamera() { this.camera.position.set(-5.5, 2.45, 5.5); this.controls.target.set(0, .85, 0); this.controls.update(); }
  private resize() { const { width, height } = this.host.getBoundingClientRect(); this.camera.aspect = width / Math.max(1, height); this.camera.zoom = Math.min(1.28, this.camera.aspect * .93); this.camera.updateProjectionMatrix(); this.renderer.setSize(width, height); }
  private animate = () => {
    if (this.disposed) return;
    this.frame = requestAnimationFrame(this.animate);
    const now = performance.now(); const dt = Math.min((now - this.lastTime) / 1000, .04); this.lastTime = now;
    if (!this.paused && !this.reduced) this.elapsed += dt;
    this.flowMaterials.forEach(m => m.uniforms.time.value = this.elapsed);
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
          positions.setXYZ(curveIndex * tracersPerCurve + tracer, point.x, point.y, point.z);
        }
      }
      positions.needsUpdate = true;
    }
    const label = this.host.parentElement?.querySelector<HTMLElement>('.cabin-label');
    if (label) { const anchor = new THREE.Vector3(.15, this.cabinTop + .38, .15).project(this.camera); label.style.left = `${(anchor.x * .5 + .5) * this.host.clientWidth + this.host.offsetLeft}px`; label.style.top = `${(-anchor.y * .5 + .5) * this.host.clientHeight + this.host.offsetTop - 45}px`; }
    if (Math.abs(this.blend - this.target) > .0005) { this.blend += (this.target - this.blend) * Math.min(1, dt * 7); this.updateSurface(); }
    this.controls.update(); this.renderer.render(this.scene, this.camera);
  };
  dispose() { this.disposed = true; cancelAnimationFrame(this.frame); this.resizeObserver.disconnect(); this.controls.dispose(); this.scene.traverse(o => { if (o instanceof THREE.Mesh || o instanceof THREE.Line || o instanceof THREE.Points) { o.geometry.dispose(); const mats = Array.isArray(o.material) ? o.material : [o.material]; mats.forEach(m => m.dispose()); } }); this.renderer.dispose(); }
}


