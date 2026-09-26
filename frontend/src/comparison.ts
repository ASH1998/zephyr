import { FlowScene } from './scene';
import { loadDetailedVehicle, disposeVehicle } from './detailed-vehicle';
import type { VisualSpec } from './detailed-vehicle';
import type { LiveRun } from './live-data';
import { maximumMovementMm } from './live-data';
import type { ViewMode } from './data';
import { fieldRange } from './data';
import { comparisonVerdict, playbackClock } from './comparison-data';

export function createComparison() {
  const root = document.createElement('section');
  root.className = 'linked-comparison'; root.hidden = true; root.id = 'linked-comparison';
  root.setAttribute('aria-label', 'Original and changed comparison');
  root.innerHTML = `<header><div><p class="eyebrow">ONE RUN · TWO SHAPES</p><h2>See exactly what changed.</h2><p class="pair-source"></p></div><button class="pair-close">Close comparison</button></header>
    <div class="pair-tools" role="group" aria-label="Comparison field">
      <button data-field="displacement">Change</button><button data-field="pressure">Pressure</button><button data-field="sensitivity">Sensitivity</button><button data-field="airflow">NVIDIA airflow</button><button data-field="illustration">Flow illustration</button>
    </div><div class="pair-options"><label><input type="checkbox" class="pair-magnify" checked> Enlarge Change view ×120 (display only)</label><button class="pair-pause">Pause comparison</button><button class="pair-reset">Reset both views</button></div>
    <p class="pair-legend"></p><div class="pair-views"><article><h3>01 · Original <span>0.00 mm movement</span></h3><div class="pair-scene"></div><p class="pair-field"></p></article><article><h3>02 · Changed <span class="pair-movement"></span></h3><div class="pair-scene"></div><p class="pair-field"></p></article></div>
    <p class="pair-verdict"></p><p class="pair-help">Drag either view to orbit both · scroll to zoom both · arrow keys to orbit, + / − to zoom. Lighting, field scales and playback are shared.</p>`;
  document.querySelector('.metrics')!.before(root);
  const open = document.createElement('button'); open.id = 'open-comparison'; open.textContent = 'Compare Original / Changed ↓'; open.hidden = true;
  document.querySelector('.result-controls')!.prepend(open);
  let scenes: FlowScene[] = [], epoch = 0, current: LiveRun | undefined, visual: VisualSpec | undefined;
  let field = 'displacement', paused = true;
  const magnify = root.querySelector<HTMLInputElement>('.pair-magnify')!;
  const label = (selector: string, text: string) => { root.querySelector(selector)!.textContent = text; };
  function dispose() { ++epoch; scenes.forEach(s => s.dispose()); scenes = []; root.hidden = true; open.disabled = false; }
  function update() {
    if (!current) return;
    const mode: ViewMode = field === 'illustration' ? 'airflow' : field as ViewMode;
    scenes.forEach(s => { s.setMode(mode); s.setFlowStyle(field === 'illustration' ? 'illustration' : 'prediction'); s.setMagnified(magnify.checked, 120);s.setPaused(paused); });
    magnify.disabled = mode !== 'displacement';
    root.querySelectorAll<HTMLButtonElement>('[data-field]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.field === field)));
    label('.pair-pause', paused ? 'Resume comparison' : 'Pause comparison');
    root.querySelector('.pair-pause')!.setAttribute('aria-pressed', String(paused));
    const mm = maximumMovementMm(current);
    label('.pair-movement', `${mm.toFixed(2)} mm actual maximum`);
    let legend = '';
    if (mode === 'displacement') legend = `Actual movement: 0–${mm.toFixed(2)} mm · ${magnify.checked ? 'shape movement enlarged ×120 for visibility' : 'true-size geometry'} · gray cabin stays fixed.`;
    if (mode === 'pressure' || mode === 'sensitivity') {
      const key = mode === 'pressure' ? 'pressurePa' : 'normalSensitivity';
      const b = fieldRange(current.baseline[key]), c = fieldRange(current.candidate![key]);
      legend = `${mode === 'pressure' ? 'Pressure' : 'Normal sensitivity'} · shared scale ${Math.min(b[0], c[0]).toFixed(2)} to ${Math.max(b[1], c[1]).toFixed(2)} ${mode === 'pressure' ? 'Pa' : 'N/m (signed asinh)'} · true-size geometry.`;
    }
    if (field === 'airflow') legend = 'NVIDIA predicted velocity · blue = slower, orange = faster · shared 0–60+ m/s scale · steady field in slow motion · true-size geometry.';
    if (field === 'illustration') legend = 'Original-shape flow illustration repeated on both sides. Trails are unchanged and do not show a calculated improvement. True-size geometry.';
    label('.pair-legend', legend);
    root.querySelectorAll('.pair-field').forEach((p, i) => {
      const ownFlow = i === 0 ? current!.airflow?.baseline : current!.airflow?.candidate;
      p.textContent = field === 'airflow' ? ownFlow ? `${i === 0 ? 'Original' : 'Changed'} shape’s own volume field` : `${i === 0 ? 'Original' : 'Changed'} airflow unavailable · no substitute field shown` : field === 'illustration' ? 'Illustration only · original-shape paths' : `${i === 0 ? 'Original' : 'Changed'} shape’s own ${mode === 'displacement' ? 'movement' : mode} field`;
    });
  }
  open.onclick = async () => {
    if (!current || scenes.length) { root.scrollIntoView({block:'start'}); return; }
    const run = current, generation = ++epoch;
    open.disabled = true; root.hidden = false; label('.pair-source', `Loading comparison · ${run.runId}`);
    label('.pair-verdict', comparisonVerdict(run)); update();
    try {
      // Separate assets own their mutable geometry/materials and can be disposed independently.
      for (const host of root.querySelectorAll<HTMLElement>('.pair-scene')) {
        const asset = visual ? await loadDetailedVehicle(visual, run.baseline) : undefined;
        if (generation !== epoch) { if(asset)disposeVehicle(asset); return; }
        const s = new FlowScene(host, run, asset);
        if (generation !== epoch) { s.dispose(); return; }
        scenes.push(s);
      }
      const clock = playbackClock();
      const sample = (now: number) => clock.tick(now, paused);
      scenes[0].setComparisonSide('original', sample); scenes[1].setComparisonSide('changed', sample);
      scenes.forEach(s => s.resetCamera());
      scenes[0].linkCamera(scenes[1]);
      label('.pair-source', `${run.source === 'recorded' ? 'RECORDED REPLAY' : 'COMPLETED LOCAL GPU RUN'} · ${run.runId}`);
      label('.pair-verdict', comparisonVerdict(run)); update(); root.scrollIntoView({block:'start'});
    } catch (error) { if(generation!==epoch)return; dispose(); label('.pair-source', `Comparison unavailable: ${String(error)}`); root.hidden = false; }
    finally { if (generation === epoch) open.disabled = false; }
  };
  root.querySelectorAll<HTMLButtonElement>('[data-field]').forEach(b => b.onclick = () => { field = b.dataset.field!; update(); });
  magnify.onchange = update;
  root.querySelector<HTMLButtonElement>('.pair-pause')!.onclick = () => { paused = !paused; update(); };
  root.querySelector<HTMLButtonElement>('.pair-reset')!.onclick = () => scenes[0]?.resetCamera();
  root.querySelector<HTMLButtonElement>('.pair-close')!.onclick = () => { dispose(); open.focus(); };
  window.addEventListener('pagehide', dispose, {once:true});
  return {
    clear() { dispose(); current = undefined; open.hidden = true; },
    set(run: LiveRun, spec?: VisualSpec) { if (current?.runId === run.runId) return; dispose(); if(run.research || run.syntheticDent || current?.research || current?.syntheticDent)magnify.checked = !(run.research||run.syntheticDent); current = run; visual = spec; open.hidden = false; }
  };
}
