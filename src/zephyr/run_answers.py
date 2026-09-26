"""Readable, evidence-bound answers. The LLM selects facts; it cannot invent results."""
from __future__ import annotations


def run_facts(e):
    f, v, t = e['forces'], e['validation'], e['trust']
    facts = {}
    def add(key, text, pointers=(), source='run'):
        facts[key] = {'id': key, 'text': text, 'source': source, 'pointers': list(pointers)}
    baseline, candidate = f['baselineDragN'], f.get('candidateDragN')
    if candidate is None:
        add('comparison', 'Only the original car was calculated. There is no tested new shape to compare yet.', ['/forces'])
        add('decision', 'There is no new design to accept or reject in this baseline-only run.', ['/trust', '/forces'])
    else:
        delta = candidate-baseline
        percent = delta/baseline*100 if baseline else None
        direction = 'more' if delta > 0 else 'less' if delta < 0 else 'the same'
        change = f' ({abs(percent):.3f}% {direction})' if percent is not None and delta else ''
        add('comparison', f'The original car was estimated at {baseline:.2f} newtons of air resistance; the changed car at {candidate:.2f} newtons{change}. Lower resistance is the goal.', ['/forces'])
        if t['decision']=='accept':
            decision='This tested step was accepted for further evaluation only: local surrogate agreement and geometry checks passed. Engineering performance still requires independent validation.'
        elif delta>0:
            decision='This change did not help: the model predicted slightly more air resistance, so it was not accepted. The GPU completed its work; this is a rejected design, not a failed calculation.'
        elif delta==0:
            decision='The model found no reduction in air resistance. This step was not accepted.'
        else:
            decision='The model predicted less air resistance, but the design was not accepted. ' + t.get('reason', 'The required validation checks are incomplete.').split(' Research gates:')[0]
        add('decision', decision, ['/trust','/forces','/validation'])
    checks=v.get('checks', {})
    maximum=checks.get('bounds', {}).get('maximumM')
    if maximum is not None:
        mm=maximum*1000
        region=e.get('handle',{}).get('label','selected body region')
        scale_note = 'The research replay opens at true scale.' if e.get('research') else 'At normal scale, a movement this small is easy to miss.'
        add('movement', f'The biggest actual movement was {mm:.3f} mm, using {region}. {scale_note} Orange in the Change view marks movement; it is not heat.', ['/validation/checks/bounds','/constraints','/handle'])
    if checks.get('protected', {}).get('status')=='passed':
        add('cabin', 'The protected part of the car, including the passenger cabin, stayed exactly in place.', ['/validation/checks/protected'])
    intent=e.get('intent', {})
    effective=e.get('constraints', {}).get('maxDisplacementM')
    if effective is not None:
        slider=intent.get('request', {}).get('budgetMm')
        text=f'This run allowed at most {effective*1000:.3f} mm of movement.'
        if slider is not None and slider>effective*1000:
            text+=f' The slider allowed {slider:.3f} mm, but the brief set a stricter limit. The smaller limit won.'
        if maximum is not None and maximum<effective-1e-10 and not e.get('research'):
            text+=' Shape checks required a smaller trial before the GPU tested it.'
        add('budget', text, ['/constraints','/intent','/validation/checks/bounds'])
    times=e.get('timings', {})
    if times:
        text=(f"Generating this recorded replay's fields took {times.get('totalSeconds',0):.1f} seconds. Search and independent CFD timings are separate."
              if e.get('research') else f"The local run took {times.get('totalSeconds',0):.1f} seconds including preparation and checks.")
        if 'baselineSeconds' in times:text+=f" The original-car calculation took {times['baselineSeconds']:.1f} seconds."
        if 'evaluateSeconds' in times:text+=f" Testing the changed car took {times['evaluateSeconds']:.1f} seconds."
        add('time', text, ['/timings'])
    if e.get('research'):
        numerical = 'passed' if e['research']['numericalResearchPassed'] else 'did not pass'
        detail = ('The search was stopped early by the user. This is a provisional demonstration; matched controls and finalist repeats are incomplete. ' if e['research'].get('provisional') else f'The equal-budget forward-search numerical gates {numerical}. ')
        add('confidence', detail + 'Training-distribution mapping remains unverified. Numerical repeatability does not establish physical accuracy.', ['/research', '/trust'])
    elif not t.get('calibrated'):
        add('confidence', 'We have not yet established how reliably the model predicts the effect of these small shape changes. A tiny numerical improvement is not enough to claim a better real car.', ['/trust'])
    elif t.get('calibrationScope')=='local-surrogate-handle-only':
        add('confidence', 'The small-probe prediction agreed with a separate fresh candidate evaluation for this run. This checks local numerical behavior; it does not measure physical model accuracy or establish a reusable trust radius.', ['/trust','/calibration'])
    if t.get('predictionErrorN') is not None:
        predicted,actual,percentage=t.get('predictedDragDeltaN'),t.get('actualDragDeltaN'),t.get('predictionErrorPercent')
        text=f"The predicted change and freshly calculated change differed by {t['predictionErrorN']:.3f} N. "
        if predicted is not None and actual is not None:
            text+=f"Small test changes predicted {predicted:+.5f} N; a separate calculation of the final shape found {actual:+.5f} N. "
        if percentage is not None:
            text+=f"Disagreement is {percentage:.2f}%: the absolute difference divided by the size of the predicted change, times 100. "
        else:
            text+='The predicted change is too small to report a reliable disagreement percentage. '
        text+='This compares two model estimates. It is not real-world model accuracy or the percentage improvement in the car.'
        add('prediction', text, ['/trust','/forces'])
    if checks.get('selfIntersection',{}).get('status')!='passed':
        text = 'The triangle audit found surface intersections. The geometry check failed.' if checks.get('selfIntersection',{}).get('status')=='failed' else 'A complete check that the surface does not fold through itself is still missing. Passing the other shape checks is not enough to approve a design.'
        add('geometry_check', text, ['/validation/checks'])
    cfd=v['independentCfd']
    if cfd=='not-run':
        add('physics', 'This run used a trained prediction model. It has not been checked by an independent physics-based flow simulation or a wind tunnel.', ['/validation/independentCfd'])
    else:add('physics', f'The recorded independent simulation status is {cfd}. Read the linked evidence before drawing a physical-performance conclusion.', ['/validation/independentCfd'])
    add('gpu', 'The GPU calculates predicted surface pressure and air friction for the original car, and calculates them again for a surviving changed shape. It also calculates where small shape changes might affect resistance. A separate volume model then predicts air movement around each tested shape. The car can stay still while these calculations run.', source='application')
    if e.get('airflow'):
        description='These paths come from NVIDIA’s separate volume model, which predicts air direction and speed around the car. The particles follow that steady field in slow motion; their colors show predicted speed, not temperature.'
        if e['airflow'].get('candidate'):description+=' Both the original and changed shapes received their own volume calculation.'
        else:description+=' Only the original car has a recorded volume result in this run.'
        add('airflow',description,['/airflow'])
    else:
        add('airflow','This older run has no recorded volume calculation. The viewer may load a saved NVIDIA volume result for its original car; check the airflow label. Any illustrative preview is labelled explicitly.',source='application')
    add('pressure', 'Pressure means how strongly air presses on the surface. In Pressure view, warmer colors mean higher predicted pressure and cooler colors mean lower pressure. They are not temperature or a good/bad score.', source='application')
    add('sensitivity', 'Sensitivity highlights where the model thinks a small shape change could affect air resistance. It is a suggestion to test, not proof that a change will help.', source='application')
    if e.get('research'):
        add('magnify', 'This research replay opens at true scale. Show me the change replays the actual movement unless you explicitly enable Enlarge movement. Compare Original / Changed opens linked views of the two shapes. Any enabled enlargement affects display only.', ['/research'], source='application')
        if e['research'].get('provisional'):
            counts = e['research']['phaseCounts']
            search_text = f"The user stopped the search after {counts['lhs']} legal Latin-hypercube samples and {counts['tpe']} TPE evaluations. There are {counts['random']} random controls and {counts['confirm']} finalist repeats. The selected saved candidate received fresh display-field evaluation. This does not complete the planned experiment."
        else:
            search_text = 'This recorded study used 100 legal Latin-hypercube samples followed by 100 TPE optimization evaluations, against 200 independent random legal controls. The top three distinct optimized shapes received three fresh repeats each.'
        add('search', search_text + ' Sensitivity explains the model response; it did not control shape steps. Geometry refusals remain in the study evidence.', ['/research', '/researchSummary'])
    else:
        add('magnify', 'Choose Show me the change to replay movement in the selected body region, enlarged 120 times for visibility. This exaggerates the shape only on screen; the GPU tested the real movement. Turn off Enlarge movement to see the actual size. Open Compare Original / Changed to inspect the linked views at the same scale.', source='application')
        add('search', 'A single iteration tests positive and negative probes, then a separate candidate. Explore the body compares nose width, hood contour, side shoulders, rear-deck height and upper rear taper from the same original. Each has fresh probes and checks. The cabin and lower wheel/ground envelope remain fixed. Refused candidates stay visible. Repeating the same inputs can repeat the same result.', source='application')
    add('cars', 'Choose from the DrivAer sedan and six generic demo bodies: hatchback, SUV, wagon, coupe, sports car, and van. Each has its own saved NVIDIA airflow result and can run a fresh calculation. The six demo styles are outside the sedan training examples; treat their predictions as experimental. Uploads are not connected yet.', source='application')
    add('scans', 'A scan can be the starting shape, but it is not ready to simulate just because it looks like a car. We need real dimensions, a complete surface, repaired gaps, and the underside and wheel details. Upload and scan preparation are not implemented in this build.', source='application')
    add('units', 'Drag is the air resistance opposing motion. Newtons, shown as N, measure force. Millimetres, shown as mm, measure how far the shape moved. Lower predicted drag is the aim; a large-looking colored area does not imply a large movement.', source='application')
    add('range_limits', 'This run cannot calculate battery range or fuel savings. It has no vehicle energy model, driving cycle, powertrain efficiency or independent confirmation of the aerodynamic change.', source='application')
    add('assistant', 'The text assistant reads your brief and chooses relevant explanations from the recorded facts. It does not move mesh points, change safety limits, run a new test through chat, or approve the design.', source='application')
    if candidate is None:
        next_step='Run a bounded shape test to obtain an original/changed comparison.'
    elif e.get('research'):
        next_step=('Use this provisional candidate for the demonstration. The user stopped optimization; no further search is scheduled. Keep the original as the reference. The predicted reduction is not a validated physical improvement.' if e['research'].get('provisional') else 'Keep the original as the reference. Review the matched random controls, repeats, training-distribution limits and independent comparison in the linked research evidence before interpreting the proposed shape as a physical improvement.')
    elif t['decision']=='accept':
        next_step='Keep this candidate for independent CFD comparison. The local checks passed, but this run does not establish fuel savings, battery range or manufacturing readiness.'
    elif e.get('car',{}).get('experimental'):
        next_step='Use the supported DrivAer sedan to test the workflow. This demonstration shape is outside the model’s supported domain; a lower predicted force cannot make it validated.'
    else:
        next_step='Keep the original shape. Inspect the failed checks before trying another bounded body region. A smaller movement is not guaranteed to pass: very small changes can be lost in numerical noise.'
    add('next',next_step,['/trust','/validation','/forces'])
    if e.get('syntheticDent'):
        add('decision', 'This is a prescribed synthetic hood dent. Its geometry passed screening and the original and dented surfaces were evaluated separately. It is an aerodynamic demonstration, not a simulation of a crash or an assessment of structural damage or roadworthiness.', ['/syntheticDent','/validation'])
        add('confidence', 'The model was trained for aerodynamic prediction, not collision damage assessment. A dent is an unverified input shape. Neither a small drag change nor a passing geometry check establishes that a damaged vehicle is safe.', ['/syntheticDent','/trust'])
        add('search', 'One fixed hood-dent geometry was selected before evaluating forces. No optimization, impact speed, collision forces, material deformation or hidden damage were simulated.', ['/syntheticDent/preset'])
        add('magnify', 'The synthetic dent opens at true scale. Compare Original / Changed shows the intact and dented shapes with shared pressure, sensitivity and airflow scales. Enlarge movement is a display-only option.', ['/syntheticDent'], source='application')
        add('next', 'Inspect the localized movement, pressure and predicted airflow differences. Home photo or scan inspection is not implemented. This demonstration cannot identify internal damage, estimate repair costs or decide whether a real car is safe to drive.', ['/syntheticDent'])
        add('budget', f"The prescribed dent has a {e['syntheticDent']['preset']['depthMm']:.0f} mm ceiling. It is a separate recorded scenario; the interactive design slider does not control it.", ['/syntheticDent/preset','/constraints'])
        if maximum is not None:
            add('movement', f'The synthetic hood dent moved the surface inward by at most {maximum*1000:.3f} mm. The viewer opens at true scale. The colored patch shows geometric displacement, not measured damage severity.', ['/validation/checks/bounds','/syntheticDent'])
        if candidate is not None:
            add('comparison', f'The model predicts {baseline:.2f} N for the original car and {candidate:.2f} N for the synthetically dented car: {candidate-baseline:+.3f} N ({(candidate-baseline)/baseline*100:+.3f}%). This is predicted aerodynamic change, not a damage or safety score.', ['/forces','/syntheticDent'])
    return facts


def summarize_run(e):
    facts=run_facts(e)
    f=e['forces']; candidate=f.get('candidateDragN')
    if e.get('syntheticDent'): headline='Synthetic dent: aerodynamic comparison'
    elif candidate is None: headline='Original car tested'
    elif e['trust']['decision']=='accept':headline='Tested step accepted'
    elif candidate>f['baselineDragN']:headline='This change did not help'
    elif candidate==f['baselineDragN']:headline='No improvement found'
    else:headline='Lower predicted resistance; step not accepted' if e['trust'].get('policyVersion') else 'Lower predicted resistance; checks still pending'
    ids=['comparison','decision','movement','cabin','next','physics']
    metrics=[]
    def metric(label,value): metrics.append({'label':label,'value':value})
    metric('Original drag',f"{f['baselineDragN']:.5f} N")
    if candidate is not None:
        delta=candidate-f['baselineDragN']
        metric('Changed drag',f'{candidate:.5f} N')
        metric('Change in drag',f'{delta:+.5f} N'+(f" ({delta/f['baselineDragN']*100:+.4f}%)" if f['baselineDragN'] else ''))
    if e['trust'].get('predictionErrorPercent') is not None:
        metric('Prediction disagreement',f"{e['trust']['predictionErrorPercent']:.2f}%")
    metric('Independent CFD',e['validation']['independentCfd'])
    return {'runId':e['runId'],'headline':headline,'decision':e['trust']['decision'],
            'facts':[facts[i] for i in ids if i in facts], 'metrics':metrics,
            'technicalFacts':[facts[i] for i in ['prediction','confidence','geometry_check','time','sensitivity'] if i in facts],
            'evidenceUrl':'/api/runs/'+e['runId']+'/evidence'}
