"""Bounded, serial exploration of server-owned shape tools; all outcomes retained."""
from copy import deepcopy
from datetime import datetime, timezone
import json
import threading
import time
from uuid import uuid4
from zephyr.local.geometry import HANDLES, COMPARISONS


class Studies:
    def __init__(self, jobs):
        self.jobs = jobs
        self.root = jobs.root / 'studies'
        self.root.mkdir(parents=True, exist_ok=True)
        self.current = None
        self.cancelled = threading.Event()

    def save(self, study):
        path = self.root / (study['studyId']+'.json')
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(study, allow_nan=False), encoding='utf-8')
        temporary.replace(path)

    def start(self, authorized):
        from zephyr.local.server import BusyError
        with self.jobs.lock:
            if self.current or self.jobs.active:
                raise BusyError('Wait for the current GPU run or exploration to finish')
            if authorized['mode'] != 'exploration':
                raise ValueError('Compile an exploration brief first')
            tool = authorized['intent']['graph']['handle']
            handles = list(COMPARISONS[tool]) if tool in COMPARISONS else [tool]
            if any(h not in HANDLES for h in handles):
                raise ValueError('Unsupported exploration tool')
            study = {'studyId':'study-'+uuid4().hex, 'createdAt':datetime.now(timezone.utc).isoformat(),
                     'state':'running', 'intent':authorized['intent'], 'runs':[], 'plannedHandles':handles,
                     'currentRunId':None, 'scope':'Separate trials from the same original; model estimates, not independent CFD.'}
            self.current = study['studyId']; self.cancelled.clear()
            self.save(study)
            threading.Thread(target=self._run, args=(study, authorized), daemon=True).start()
            return deepcopy(study)

    def _run(self, study, authorized):
        try:
            for handle in study['plannedHandles']:
                if self.cancelled.is_set(): break
                request = {k:authorized[k] for k in ('geometryId','budgetMm','brief','mode')}
                request['mode'] = 'iteration'
                intent = deepcopy(authorized['intent'])
                intent['parentIntentId'] = intent['intentId']
                intent['studyId'] = study['studyId']
                intent['executionTool'] = handle
                intent['graph']['handle'] = handle
                # Preserve the user-approved source plan above; this child is a
                # server expansion of that plan, not another claimed model call.
                job = self.jobs.start(request, intent=intent, study_id=study['studyId'])
                rid = job['runId']; study['currentRunId'] = rid
                row = {'runId':rid, 'handle':handle, 'label':HANDLES[handle], 'state':'running'}
                study['runs'].append(row); self.save(study)
                while True:
                    if self.cancelled.is_set(): self.jobs.cancel(rid)
                    job = self.jobs.snapshot(rid)
                    if job['state'] in ('complete','failed','cancelled'): break
                    time.sleep(.5)
                row['state'] = job['state']
                if job['state'] == 'complete':
                    e = json.loads((self.jobs.root/rid/'evidence.json').read_text(encoding='utf-8'))
                    row.update(forces=e['forces'], trust=e['trust'], validation=e['validation'],
                               movementMm=e['validation']['checks'].get('bounds',{}).get('maximumM',0)*1000,
                               seconds=e['timings']['totalSeconds'], meshHash=e['provenance']['meshHash'])
                else: row['detail'] = job['detail']
                study['currentRunId'] = None; self.save(study)
                # The monitor publishes terminal state before releasing its lease.
                while self.jobs.active is not None: time.sleep(.05)
            study['state'] = 'cancelled' if self.cancelled.is_set() else 'complete'
            eligible = [r for r in study['runs'] if r.get('trust',{}).get('decision') == 'accept']
            study['recommendedRunId'] = min(eligible,key=lambda r:r['forces']['candidateDragN'])['runId'] if eligible else None
            study['conclusion'] = 'Candidate for independent validation; physical improvement unproven.' if eligible else 'No candidate passed all local checks. Keep the original.'
        except Exception as exc:
            study['state'] = 'failed'; study['error'] = type(exc).__name__+': '+str(exc)
        finally:
            study['currentRunId'] = None; self.save(study)
            with self.jobs.lock: self.current = None

    def get(self, study_id):
        import re
        if not re.fullmatch(r'study-[a-f0-9]{32}',study_id): raise KeyError(study_id)
        try:
            study=json.loads((self.root/(study_id+'.json')).read_text(encoding='utf-8'))
            if study['state']=='running' and self.current!=study_id:
                study['state']='interrupted';study['conclusion']='Service restarted. Completed trials are retained; no further profiles were started.'
            return study
        except FileNotFoundError: raise KeyError(study_id)

    def cancel(self, study_id):
        with self.jobs.lock:
            if self.current == study_id: self.cancelled.set()
            return self.get(study_id)


def run_history(root):
    rows=[]
    for path in sorted(root.glob('local-*/evidence.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:100]:
        try:
            e=json.loads(path.read_text(encoding='utf-8'))
            if e.get('runId') != path.parent.name or not (path.parent/'result.json').is_file(): continue
            rows.append({'runId':e['runId'],'geometryId':e['geometryId'],'createdAt':e['createdAt'],
                         'handle':e.get('handle',{}).get('handle'), 'forces':e['forces'],'decision':e['trust']['decision'],
                         'movementMm':e['validation']['checks'].get('bounds',{}).get('maximumM',0)*1000})
        except (OSError,ValueError,KeyError,TypeError): continue
    return rows
