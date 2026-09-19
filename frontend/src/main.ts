import './style.css';
import { startLive } from './live';
import { HttpRunAdapter, decideRequest, demoAtBudget, fieldRange } from './data';
import type { ViewMode } from './data';
import { FlowScene } from './scene';
import { VehicleDemoAdapter } from './vehicle';
import { vehicleCatalog } from './vehicle-catalog';
import { storyStages, sourceLabel, resultSummary, assertStoryEvent } from './run-story';
import type { RunStoryEvent } from './run-story';

const lock = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="6" y="10" width="12" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/></svg>';
const app = document.querySelector<HTMLDivElement>('#app')!;
app.innerHTML = `
<header class="topbar"><a class="brand" href="./" aria-label="Zephyr home"><svg viewBox="0 0 48 38" fill="none" aria-hidden="true"><path d="M5 10C16 4 25 4 41 8C31 15 19 22 7 29C20 25 31 29 43 27" stroke="currentColor" stroke-width="2.3"/><path d="M7 15C19 10 28 10 36 11M14 29C25 34 34 32 41 32" stroke="currentColor" opacity=".4"/></svg><span>ZEPHYR<small>Shape the flow.</small></span></a><div class="project-name"><span class="dot"></span> AERODYNAMIC DESIGN WORKSPACE <span class="slash">/</span> Z–01</div><button class="quiet" id="evidence">Evidence & provenance ↗</button></header>
<main class="workspace">
  <section class="viewport" aria-label="Vehicle design viewer">
    <div class="intro"><p class="eyebrow">SMALL CHANGES. LESS RESISTANCE.</p><h1>You can’t see the air<br>holding this car back.<br><em>Zephyr can.</em></h1><p class="subcopy">Explore a shape. Protect what matters.<br>Earn every improvement.</p></div>
    <div class="view-tools" role="group" aria-label="Surface view"><button data-mode="airflow" class="active" aria-pressed="true">Airflow</button><button data-mode="pressure" aria-pressed="false">Pressure</button><button data-mode="sensitivity" aria-pressed="false">Sensitivity</button><button data-mode="displacement" aria-pressed="false">Change</button><button data-mode="mesh" aria-pressed="false">Mesh</button></div>
    <section class="run-story" id="run-story" hidden aria-label="Run presentation">
      <div class="story-meta"><span id="story-source"></span><span id="story-count"></span></div>
      <div id="story-narration" role="status" aria-live="polite"><h2 id="story-title"></h2><p id="story-detail"></p></div>
      <div id="story-result" hidden><span id="result-label"></span><div class="result-numbers"><span id="result-before"></span><span class="result-arrow">→</span><strong id="result-after"></strong><b id="result-delta"></b></div></div>
      <ol class="story-progress" aria-label="Run stages">${storyStages.map(stage => `<li data-story-stage="${stage.id}"><span></span>${({intent:'Lock',sensitivity:'Find',candidate:'Change',validate:'Check',evaluate:'Compare'})[stage.id]}</li>`).join('')}</ol>
      <div class="result-controls" hidden><button id="show-baseline" aria-pressed="false">01 Baseline</button><button id="show-candidate" aria-pressed="true">02 Candidate + change map</button><span id="result-scale">Shape ×24 · field in actual mm</span></div>
    </section>
    <div id="scene"></div>
    <div class="rear-callout" hidden><strong>REAR TAPER CHANGED</strong><span id="rear-displacement"></span><small>Cabin 0.00 mm · unchanged</small><small>Cyan outline = original rear</small></div>
    <div class="wake-key" hidden><span><i></i>Baseline wake</span><span><i></i>Candidate wake</span><small>Illustrative flow comparison</small></div>
    <div class="cabin-label">${lock}<span>CABIN PROTECTED<small>0.00 mm displacement</small></span></div>
    <div class="flow-label"><span>→</span><div>32 m/s <small>ILLUSTRATIVE FLOW</small></div></div>
    <div class="legend" id="legend"><span class="legend-line"></span><span>Analytic streamlines · illustrative wake</span></div>
    <div class="scene-actions"><button class="quiet" id="camera">↺ Reset view</button><button class="quiet" id="motion" aria-pressed="false">Ⅱ Pause flow</button><span>Drag to orbit · scroll to zoom</span></div>
    <div class="comparison"><div class="compare-labels"><span>01 <strong>Baseline</strong></span><span id="compare-status">Baseline geometry</span><span><strong>Candidate</strong> 02</span></div><input id="compare" type="range" min="0" max="100" value="0" aria-label="Baseline to candidate comparison"/><div class="compare-bottom"><label><input id="magnify" type="checkbox" checked/> Deformation ×24 for visibility</label><span id="scale-caption">Actual maximum: 3.6 mm</span></div></div>
  </section>
  <aside class="control-panel" aria-label="Design controls">
    <label class="vehicle-picker" for="vehicle">GEOMETRY<select id="vehicle">${vehicleCatalog.map(vehicle => `<option value="${vehicle.id}" ${vehicle.available ? '' : 'disabled'}>${vehicle.label}${vehicle.available ? '' : ' · unavailable'}</option>`).join('')}</select></label>
    <div class="panel-heading"><span class="eyebrow">DESIGN INTENT</span><span class="session" id="run-source">DEMO</span></div>
    <label class="brief-label" for="brief">What should change?</label><textarea id="brief" rows="3" spellcheck="false">Reduce drag. Keep the cabin unchanged.</textarea>
    <div class="constraint"><span>${lock} Protected cabin</span><strong>LOCKED</strong></div>
    <div class="budget-heading"><label for="budget">Displacement budget</label><output id="budget-value">3.6 <small>mm</small></output></div><input id="budget" type="range" min="1" max="4" step="0.2" value="3.6"/><div class="range-labels"><span>1 mm</span><span>Hard limit · 4 mm</span></div>
    <button id="iterate" class="primary">Run bounded iteration <span>↗</span></button>
    <div class="sequence-heading"><span class="eyebrow">THE TRUST LOOP</span><span class="demo-tag">DEMO</span></div>
    <ol class="steps"><li data-step="0"><span>01</span><div>Intent & constraints<small>Protect cabin · allow rear taper</small></div><b>—</b></li><li data-step="1"><span>02</span><div>Surface sensitivity<small>Project onto permitted regions</small></div><b>—</b></li><li data-step="2"><span>03</span><div>Create candidate<small>Move only allowed surfaces</small></div><b>—</b></li><li data-step="3"><span>04</span><div>Check constraints<small>Same connections · fixed cabin</small></div><b>—</b></li><li data-step="4"><span>05</span><div>Evaluate & decide<small>Compare drag · enforce trust</small></div><b>—</b></li></ol>
    <div class="decision" id="decision" role="status" aria-live="polite"><span class="decision-icon">◎</span><div><strong id="decision-title">Ready for a bounded step</strong><p id="decision-copy">The cabin stays fixed. Only permitted surfaces can change.</p></div></div>
    <button id="refuse" class="boundary">Test trust boundary <span>12 mm ↗</span></button>
    <p class="signature">It stops when it stops being trustworthy.</p>
  </aside>
  <section class="metrics" aria-label="Demo evaluation metrics"><div class="metric metric-main"><span class="eyebrow">DRAG FORCE <b>DEMO DATA</b></span><div><span class="baseline-value">412<small>N</small></span><span class="metric-arrow">→</span><strong id="candidate-force">398<small>N</small></strong><span class="delta" id="delta">−3.4%</span></div><p>Illustrative baseline vs candidate · not a prediction</p></div><div class="metric"><span class="eyebrow">MAX. DISPLACEMENT</span><div><strong id="displacement">3.6<small>mm</small></strong><span class="within">/ 4 mm</span></div><p>Cabin <span class="mint">0.00 mm · unchanged</span></p></div><div class="metric"><span class="eyebrow">TRUST STATE</span><div><strong class="trust-value" id="trust-state">Preview only</strong></div><p id="trust-detail">Demo error 3.6% / 10% threshold</p></div><div class="metric"><span class="eyebrow">PROOF STATUS</span><div><span class="pending-dot"></span><strong class="proof-value">Not validated</strong></div><p>DoMINO not run · independent CFD pending</p></div></section>
</main><footer><span>CONCEPT VEHICLE / Z–01</span><span id="run-id">DEMO-Z01-001</span><span>Intent → bounded change → evidence</span></footer>
<dialog id="evidence-dialog"><div class="dialog-heading"><span class="eyebrow">EVIDENCE & PROVENANCE</span><button id="close-dialog" class="quiet" aria-label="Close evidence dialog">✕</button></div><h2>A preview is not proof.</h2><p>This workspace demonstrates the design interaction. Its licensed concept vehicle, analytic flow, pressure, sensitivity and numerical results are illustrative. They are not CFD, measured drag, or validated engineering output.</p><dl id="provenance"></dl><p class="asset-credit">Car Concept © 2024 Darmstadt Graphics Group GmbH · Eric Chadwick. <a href="https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/CarConcept" target="_blank" rel="noopener">Source</a> · <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY 4.0</a>. Modified display materials and geometry. Concept car is illustrative, outside the claimed validated model envelope.</p><h3>The path to a trustworthy result</h3><p>Versioned DoMINO surface fields → deterministic geometry checks → fresh surrogate evaluation → independent CFD comparison. Surrogate output is never ground truth.</p><p class="dialog-note">No cloud endpoint is started. No paid API is called. The downloaded checkpoint has not been executed by this app.</p><button id="export" class="primary">Download demo run JSON <span>↓</span></button></dialog>`;

const $ = <T extends HTMLElement>(selector: string) => document.querySelector<T>(selector)!;
const dialog = $<HTMLDialogElement>('#evidence-dialog');
$('#evidence').onclick = () => dialog.showModal(); $('#close-dialog').onclick = () => dialog.close();
dialog.addEventListener('click', e => { if (e.target === dialog) { const r = dialog.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close(); } });

async function start() {
  const endpoint = new URLSearchParams(location.search).get('run');
  app.classList.add('is-loading');
  $('#run-source').textContent = 'LOADING';
  const pendingControls = [...document.querySelectorAll<HTMLInputElement | HTMLButtonElement | HTMLTextAreaElement | HTMLSelectElement>('.workspace button, .workspace input, .workspace textarea, .workspace select')];
  pendingControls.forEach(control => control.disabled = true);
  // Real runs are opt-in; a failed fetch/schema never substitutes demo data.
  const demoAdapter = new VehicleDemoAdapter($<HTMLSelectElement>('#vehicle').value);
  let run = await (endpoint ? new HttpRunAdapter(endpoint) : demoAdapter).load();
  const seedRun = structuredClone(run);
  pendingControls.forEach(control => control.disabled = false);
  $('#run-source').textContent = run.source === 'illustrative' ? 'DEMO' : `${run.source.toUpperCase()} SURROGATE`;
  const real = run.source !== 'illustrative';
  if (real) {
    $('#vehicle').replaceChildren(new Option('Supplied run geometry', 'recorded'));
    $('#vehicle').setAttribute('disabled', '');
    $('#iterate').setAttribute('disabled', ''); $('#refuse').setAttribute('disabled', ''); $('#budget').setAttribute('disabled', ''); $('#brief').setAttribute('disabled', '');
    $('.demo-tag').textContent = run.source.toUpperCase(); $('.metric-main .eyebrow b').textContent = 'SURROGATE';
    $('.metric-main p').textContent = 'Recorded baseline vs candidate · surrogate output';
    $('.flow-label').style.display = 'none'; $('[data-mode="airflow"]').setAttribute('disabled', '');
    $('#magnify').removeAttribute('checked');
  }
  let scene: FlowScene;
  try { scene = new FlowScene($('#scene'), run, demoAdapter.asset); } catch (error) { throw new Error(`3D viewer unavailable. WebGL2 is required. ${error instanceof Error ? error.message : ''}`); }
  app.classList.remove('is-loading');
  let storyComplete = false;
  const mode = (value: ViewMode) => {
    scene.setMode(value);
    $('.flow-label').hidden = value !== 'airflow' || real;
    document.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach(b => { const active = b.dataset.mode === value; b.classList.toggle('active', active); b.setAttribute('aria-pressed', String(active)); });
    const [pLo, pHi] = fieldRange(run.baseline.pressurePa), [cLo, cHi] = fieldRange(run.candidate.pressurePa), [sLo, sHi] = fieldRange(run.baseline.normalSensitivity);
    const labels = { airflow: '<span class="legend-line"></span>Analytic streamlines · illustrative wake', pressure: `<span class="color-scale pressure"></span>Pressure · ${Math.min(pLo, cLo).toFixed(0)} to ${Math.max(pHi, cHi).toFixed(0)} Pa`, sensitivity: `<span class="color-scale sensitivity"></span>Normal sensitivity · ${sLo.toFixed(0)} to ${sHi.toFixed(0)} N/m · signed normal arrows`, displacement: `<span class="color-scale displacement"></span>Actual movement · 0 to ${(fieldRange(run.candidate.displacementM)[1] * 1000).toFixed(1)} mm · gray cabin locked`, mesh: `<span class="legend-line"></span>Fixed topology · ${(run.baseline.positions.length / 3).toLocaleString()} vertices · ${(run.baseline.triangles.length / 3).toLocaleString()} triangles` };
    $('#legend').innerHTML = labels[value] + (value !== 'airflow' ? (real ? ' · recorded field' : ' · demo field') : '');
  };
  document.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach(b => b.onclick = () => {
    const value = b.dataset.mode as ViewMode; mode(value);
    if (storyComplete) { const comparing = value === 'displacement' || value === 'airflow'; scene.setStory(comparing ? 'result' : undefined); $('.rear-callout').hidden = $('.wake-key').hidden = !comparing; }
  });
  const compare = $<HTMLInputElement>('#compare');
  const setBlend = (v: number) => { compare.value = String(v); scene.setBlend(v / 100); $('#compare-status').textContent = v === 0 ? 'Baseline geometry' : v === 100 ? 'Candidate geometry' : `Comparison · ${v}% candidate`; };
  compare.oninput = () => { setBlend(+compare.value); if (storyComplete) $('.rear-callout').hidden = +compare.value === 0; $('#show-baseline').setAttribute('aria-pressed', String(+compare.value === 0)); $('#show-candidate').setAttribute('aria-pressed', String(+compare.value === 100)); };
  $('#show-baseline').onclick = () => { setBlend(0); $('.rear-callout').hidden = true; $('#show-baseline').setAttribute('aria-pressed', 'true'); $('#show-candidate').setAttribute('aria-pressed', 'false'); };
  $('#show-candidate').onclick = () => { mode('displacement'); scene.setStory('result'); setBlend(100); $('.rear-callout').hidden = $('.wake-key').hidden = false; $('#show-baseline').setAttribute('aria-pressed', 'false'); $('#show-candidate').setAttribute('aria-pressed', 'true'); };
  $<HTMLInputElement>('#magnify').onchange = e => { const on = (e.target as HTMLInputElement).checked; scene.setMagnified(on); $('#result-scale').textContent = on ? 'Shape ×24 · field in actual mm' : 'True-scale shape · field in actual mm'; $('#scale-caption').textContent = `${on ? 'Actual maximum' : 'True-scale geometry'}: ${(Math.max(...run.candidate.displacementM) * 1000).toFixed(1)} mm`; };
  $('#camera').onclick = () => scene.resetCamera();
  let paused = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const motion = $('#motion');
  const updateMotion = () => { scene.setPaused(paused); motion.textContent = paused ? '▷ Resume flow' : 'Ⅱ Pause flow'; motion.setAttribute('aria-pressed', String(paused)); };
  updateMotion(); motion.onclick = () => { paused = !paused; updateMotion(); };
  const budget = $<HTMLInputElement>('#budget'); budget.oninput = () => $('#budget-value').innerHTML = `${(+budget.value).toFixed(1)} <small>mm</small>`;
  const baseline = run.forces.baselineN[0], candidate = run.forces.candidateN[0];
  $('.baseline-value').innerHTML = `${baseline.toFixed(0)}<small>N</small>`;
  $('#candidate-force').innerHTML = `${candidate.toFixed(0)}<small>N</small>`;
  $('#delta').textContent = `${((candidate - baseline) / Math.abs(baseline) * 100).toFixed(1)}%`;
  const actualMm = fieldRange(run.candidate.displacementM)[1] * 1000;
  $('#displacement').innerHTML = `${actualMm.toFixed(1)}<small>mm</small>`;
  $('#scale-caption').textContent = `Actual maximum: ${actualMm.toFixed(1)} mm`;
  $('#run-id').textContent = run.runId;
  const row = (name: string, value: string) => { const dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent = name; dd.textContent = value; $('#provenance').append(dt, dd); };
  row('Run', run.runId); row('Source', run.source); row('Schema', run.schemaVersion); row('Artifact', run.provenance.artifactVersion); row('Model', run.provenance.modelVersion); row('Created', run.createdAt); row('Coordinates', 'Metres · +Y up · +X streamwise · vertex fields'); row('Air density', `${run.conditions.densityKgM3} kg/m³`);
  if (real) {
    mode('pressure'); scene.setMagnified(false);
    $('#trust-state').textContent = run.trust.calibrated ? run.trust.decision : 'Uncalibrated';
    $('#trust-detail').textContent = `Error ${run.trust.predictionErrorPercent}% / ${run.trust.thresholdPercent}% threshold`;
    $('.proof-value').textContent = run.validation.independentCfd === 'passed' ? 'CFD compared' : run.validation.independentCfd === 'disagreed' ? 'CFD disagreed' : 'CFD pending';
    $('.metrics .metric:last-child p').textContent = `Geometry: ${run.validation.geometry} · fresh evaluation: ${run.validation.freshEvaluation}`;
    $('#decision-title').textContent = 'Recorded run loaded'; $('#decision-copy').textContent = 'Read-only comparison. Run orchestration is not connected.';
    $('#evidence-dialog > p').textContent = 'This is a versioned surrogate run. Aerodynamic surface fields come from the supplied payload. A surrogate is not ground truth; inspect its validation state and source evidence.';
    $('.dialog-note').textContent = 'The browser loaded a supplied artifact. It did not execute a solver or start cloud compute.';
    $('#export').innerHTML = 'Download run JSON <span>↓</span>';
    run.provenance.evidenceUrls.forEach((url, i) => row(`Evidence ${i + 1}`, url));
  }
  $('#export').onclick = () => { const url = URL.createObjectURL(new Blob([JSON.stringify(run)], { type: 'application/json' })); const a = document.createElement('a'); a.href = url; a.download = `${run.runId.replace(/[^a-z0-9_-]/gi, '_')}.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); };
  // This renderer accepts explicit stage events. The timer below is ONLY the offline
  // walkthrough driver; a backend integration must replace it with actual events.
  function present(event: RunStoryEvent) {
    assertStoryEvent(run, event);
    const stageIndex = storyStages.findIndex(stage => stage.id === event.stage), stage = storyStages[stageIndex];
    $('.viewport').classList.add('story-active'); $('#run-story').hidden = false;
    $('#story-source').textContent = sourceLabel(event.source);
    $('#story-count').textContent = stage ? `${stageIndex + 1} / 5` : event.stage === 'refused' ? 'STOPPED' : 'COMPLETE';
    $('#story-title').textContent = stage?.title || (event.stage === 'refused' ? 'Stopped. Your boundary holds.' : 'Rear changed. Cabin unchanged.');
    $('#story-detail').textContent = event.detail || stage?.detail || '';
    $('#story-result').hidden = event.stage !== 'result'; $('.result-controls').hidden = event.stage !== 'result';
    $('.rear-callout').hidden = !['candidate', 'result'].includes(event.stage);
    $('.wake-key').hidden = !['evaluate', 'result'].includes(event.stage);
    $('.flow-label').hidden = true;
    document.querySelectorAll<HTMLElement>('[data-story-stage]').forEach((item, index) => { item.classList.toggle('current', index === stageIndex); item.classList.toggle('done', event.stage === 'result' || index < stageIndex); });
    scene.setStory(event.stage);
  }
  const emit = (stage: RunStoryEvent['stage'], detail?: string) => present({ runId: run.runId, source: run.source, stage, detail });
  const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
  let busy = false;
  async function iterate(forced = false) {
    if (busy || real) return; busy = true; storyComplete = false;
    const controls = [...document.querySelectorAll<HTMLButtonElement | HTMLInputElement | HTMLTextAreaElement>('[data-mode], #iterate, #refuse, #budget, #brief, #compare, #show-baseline, #show-candidate')];
    controls.forEach(control => control.disabled = true);
    const button = $<HTMLButtonElement>('#iterate'); button.innerHTML = 'Playing illustrative run <span class="spinner">↻</span>';
    const decision = decideRequest($<HTMLTextAreaElement>('#brief').value, forced ? 12 : +budget.value);
    if (decision.decision !== 'refuse') setBlend(0);
    const steps = [...document.querySelectorAll<HTMLElement>('[data-step]')];
    steps.forEach(el => { el.className = ''; el.querySelector('b')!.textContent = '—'; });
    $('#decision').className = 'decision'; $('#decision-title').textContent = 'Illustrative run in progress'; $('#decision-copy').textContent = 'Watch the vehicle: lock → find → change → check → compare. No model is running.';
    mode('airflow'); emit('intent');
    $('.viewport').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' });
    for (let i = 0; i < (decision.decision === 'refuse' ? 1 : storyStages.length); i++) {
      const stage = storyStages[i]; steps[i].className = 'running'; steps[i].querySelector('b')!.textContent = '○';
      if (i === 2) {
        run = demoAtBudget(Math.min(3.6, +budget.value), seedRun); scene.setRun(run);
        const mm = resultSummary(run).maximumMm;
        $('#displacement').innerHTML = `${mm.toFixed(1)}<small>mm</small>`; $('#scale-caption').textContent = `Actual maximum: ${mm.toFixed(1)} mm`;
        $('#rear-displacement').textContent = `${mm.toFixed(1)} mm actual movement`;
        setBlend(0); await wait(120); setBlend(100);
      }
      mode(stage.mode); emit(stage.id);
      await wait(stage.duration);
      steps[i].className = 'done'; steps[i].querySelector('b')!.textContent = '✓';
    }
    if (decision.decision === 'shrink') {
      for (const i of [3, 4]) { mode(storyStages[i].mode); emit(storyStages[i].id, '4 mm was too large for this demo trust threshold. Retry at 3.6 mm, check and compare again.'); await wait(1600); }
    }
    if (decision.decision === 'refuse') {
      steps[4].className = 'refused'; steps[4].querySelector('b')!.textContent = '×'; emit('refused', decision.message);
    } else {
      setBlend(100); mode('displacement'); storyComplete = true;
      $('#show-baseline').setAttribute('aria-pressed', 'false'); $('#show-candidate').setAttribute('aria-pressed', 'true');
      const result = resultSummary(run);
      $('#candidate-force').innerHTML = `${result.candidate.toFixed(0)}<small>N</small>`; $('#delta').textContent = `${result.deltaPercent?.toFixed(1) ?? '—'}%`;
      $('#result-label').textContent = result.label;
      $('#result-before').innerHTML = `${result.baseline.toFixed(0)}<small>N · baseline</small>`;
      $('#result-after').innerHTML = `${result.candidate.toFixed(0)}<small>N · candidate</small>`;
      $('#result-delta').textContent = result.deltaPercent === null ? '—' : `${result.deltaPercent.toFixed(1)}%`;
      emit('result', `Rear surfaces changed → illustrative wake narrowed → demo drag decreased. ${decision.decision === 'shrink' ? 'Step reduced to 3.6 mm.' : ''}`);
    }
    $('#decision').className = `decision ${decision.decision}`;
    $('#decision-title').textContent = decision.decision === 'refuse' ? 'Refused. The boundary holds.' : decision.decision === 'shrink' ? 'Step shrunk & re-evaluated · demo' : 'Candidate accepted · demo only';
    $('#decision-copy').textContent = decision.message;
    $('#trust-state').textContent = decision.decision === 'refuse' ? 'Refused' : decision.decision === 'shrink' ? 'Step shrunk' : 'Demo accepted';
    $('#trust-detail').textContent = decision.decision === 'refuse' ? 'Hard constraint violated · no new evaluation' : decision.decision === 'shrink' ? 'Demo trust threshold exceeded · 4 → 3.6 mm' : 'Demo error 3.6% / 10% · uncalibrated';
    button.innerHTML = 'Replay illustrative run <span>↗</span>'; controls.forEach(control => control.disabled = false); busy = false;
  }
  $('#iterate').onclick = () => void iterate(); $('#refuse').onclick = () => void iterate(true);
  window.addEventListener('pagehide', () => scene.dispose(), { once: true });
}
(new URLSearchParams(location.search).has('demo') || new URLSearchParams(location.search).has('run') ? start() : startLive()).catch(error => {
  $('#run-source').textContent = 'UNAVAILABLE';
  $('#run-id').textContent = 'NO RUN LOADED';
  $<HTMLButtonElement>('#evidence').disabled = true;
  const failure = document.createElement('div'); failure.className = 'load-error'; failure.setAttribute('role', 'alert');
  const title = document.createElement('h2'); title.textContent = 'This run cannot be displayed.';
  const message = document.createElement('p'); message.textContent = error instanceof Error ? error.message : String(error);
  failure.append(title, message); $('.workspace').replaceChildren(failure);
});

