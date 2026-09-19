"""Loopback-only API. Start with ../.venv/Scripts/python -m zephyr.local.server."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit
from uuid import uuid4
from zephyr.copilot import Copilot, CopilotBusy, canonical_request
from zephyr.token_factory import TokenFactoryError
from zephyr.local.cars import CARS, IDS

ROOT = Path(__file__).resolve().parents[3]
TERMINAL = {'complete', 'failed', 'cancelled'}


def validate_request(data, *, compiled=False):
    if compiled:
        return canonical_request(data)
    if not isinstance(data, dict) or set(data) - {'geometryId', 'budgetMm', 'brief', 'mode'}:
        raise ValueError('Unknown request fields; paths/uploads are not accepted')
    if not isinstance(data.get('geometryId'),str) or data['geometryId'] not in IDS:
        raise ValueError('Select an installed car style')
    budget = data.get('budgetMm')
    if isinstance(budget, bool) or not isinstance(budget, (int, float)) or not math.isfinite(budget) or not 0 < budget <= 4:
        raise ValueError('Budget must be finite and within (0, 4] mm')
    brief = data.get('brief', '')
    if not isinstance(brief, str) or len(brief) > 500 or brief.strip().lower().rstrip('.') != 'reduce drag. keep the cabin unchanged':
        raise ValueError('Local preset supports exactly: Reduce drag. Keep the cabin unchanged. A language compiler is not connected.')
    if data.get('mode') not in ('analysis', 'iteration'):
        raise ValueError('Mode must be analysis or iteration')
    if data['geometryId'] in ('x57','global-hawk') and data['mode']=='iteration':
        raise ValueError('Aircraft support baseline analysis only')
    return dict(data)


class BusyError(Exception):
    pass


class Jobs:
    def __init__(self, root=None, command=None):
        self.root = root or ROOT / '.local/runs'
        self.root.mkdir(parents=True, exist_ok=True)
        self.command = command or [sys.executable, '-u', '-m', 'zephyr.local.worker']
        self.lock = threading.RLock()
        self.jobs = {}
        self.active = None
        self.process = None
        self.file_lock = None

    def _acquire_gpu(self):
        from zephyr.local.locks import acquire_lock
        try:
            self.file_lock = acquire_lock(self.root / 'gpu.lock')
        except OSError as exc:
            raise BusyError('Another local service owns the GPU job lock') from exc

    def start(self, request, *, intent=None):
        request = validate_request(request, compiled=intent is not None)
        if intent is not None:
            request['intent'] = intent
        with self.lock:
            if self.active is not None:
                raise BusyError('One GPU job is already active; wait or cancel it')
            self._acquire_gpu()
            run_id = 'local-' + uuid4().hex
            directory = self.root / run_id
            try:
                directory.mkdir()
                (directory / 'request.json').write_text(json.dumps(request), encoding='utf-8')
            except Exception:
                self.file_lock.close(); self.file_lock = None
                raise
            job = {'runId': run_id, 'source': 'live', 'state': 'running', 'stage': 'queued', 'detail': 'Worker starting',
                'sequence': 0, 'events': [], 'baselineReady': False, 'resultReady': False,
                'createdAt': datetime.now(timezone.utc).isoformat()}
            self.jobs[run_id] = job
            self.active = run_id
            while len(self.jobs) > 16:
                del self.jobs[next(iter(self.jobs))]
            try:
                env = os.environ.copy()
                for key in ('NEBIUS_API_KEY', 'NEBIUS_AI_PROJECT_ID'):
                    env.pop(key, None)
                env['PYTHONPATH'] = str(ROOT / 'src') + os.pathsep + env.get('PYTHONPATH', '')
                self.process = subprocess.Popen([*self.command, str(directory)], cwd=ROOT, env=env,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            except Exception:
                self.active = None
                self.file_lock.close(); self.file_lock = None
                del self.jobs[run_id]
                raise
            threading.Thread(target=self._monitor, args=(run_id, self.process), daemon=True).start()
            return self.snapshot(run_id)

    def _event(self, job, event):
        job['sequence'] += 1
        event.update(runId=job['runId'], source='live', sequence=job['sequence'])
        job['events'].append(event)
        job['events'] = job['events'][-256:]
        job.update({k: v for k, v in event.items() if k in ('stage', 'detail', 'completed', 'total')})
        if 'completed' not in event:
            job.pop('completed', None); job.pop('total', None)

    def _monitor(self, run_id, process):
        directory = self.root / run_id
        try:
            with (directory / 'worker.log').open('w', encoding='utf-8') as log:
                for line in process.stdout:
                    log.write(line); log.flush()
                    if line.startswith('@ZEPHYR '):
                        event = json.loads(line[len('@ZEPHYR '):])
                        with self.lock:
                            job = self.jobs[run_id]
                            if job['state'] == 'cancelling':
                                continue
                            self._event(job, event)
                            if event.get('artifact') == 'baseline':
                                job['baselineReady'] = (directory / 'baseline.json').is_file()
                code = process.wait()
            with self.lock:
                job = self.jobs[run_id]
                if job['state'] == 'cancelling':
                    state, detail = 'cancelled', 'GPU worker stopped; any completed baseline remains available'
                elif code == 0 and (directory / 'result.json').is_file() and (directory / 'evidence.json').is_file():
                    state, detail = 'complete', job['detail']
                    job['resultReady'] = True
                else:
                    state, detail = 'failed', job['detail'] if job['stage'] == 'failed' else f'GPU worker exited {code}; inspect .local/runs/{run_id}/worker.log'
                job['state'] = state
                self._event(job, {'stage': state, 'detail': detail})
        except Exception as exc:
            process.kill(); process.wait()
            with self.lock:
                self.jobs[run_id]['state'] = 'failed'
                self._event(self.jobs[run_id], {'stage': 'failed', 'detail': str(exc)})
        finally:
            process.stdout.close()
            with self.lock:
                self.active = None; self.process = None
                if self.file_lock:
                    self.file_lock.close(); self.file_lock = None

    def snapshot(self, run_id):
        with self.lock:
            if run_id not in self.jobs:
                if not isinstance(run_id, str) or not re.fullmatch(r'local-[0-9a-f]{32}', run_id):
                    raise KeyError(run_id)
                directory = self.root / run_id
                try:
                    evidence = json.loads((directory / 'evidence.json').read_text(encoding='utf-8'))
                    if not isinstance(evidence, dict) or evidence.get('runId') != run_id or evidence.get('schemaVersion') != 'zephyr.surface.v2' or not (directory / 'result.json').is_file():
                        raise KeyError(run_id)
                    detail = evidence['trust']['reason']
                    job = {'runId':run_id,'source':'live','state':'complete','stage':'complete','detail':detail,
                        'sequence':0,'events':[],'baselineReady':(directory/'baseline.json').is_file(),
                        'resultReady':True,'createdAt':evidence['createdAt'],'restored':True}
                    self._event(job, {'stage':'complete','detail':detail})
                    self.jobs[run_id] = job
                    while len(self.jobs)>16:
                        victim=next((key for key in self.jobs if key not in (self.active,run_id)),None)
                        if victim is None:break
                        self.jobs.pop(victim)
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    raise KeyError(run_id) from exc
            return json.loads(json.dumps(self.jobs[run_id]))

    def cancel(self, run_id):
        with self.lock:
            job = self.snapshot(run_id)
            if job['state'] in TERMINAL:
                return job
            self.jobs[run_id]['state'] = 'cancelling'
            self._event(self.jobs[run_id], {'stage': 'cancelling', 'detail': 'Stopping GPU worker'})
            if self.active == run_id and self.process and self.process.poll() is None:
                self.process.terminate()
            return self.snapshot(run_id)

    def close(self):
        with self.lock:
            active, process = self.active, self.process
        if active:
            self.cancel(active)
        if process:
            process.wait(timeout=20)


def handler_for(jobs, copilot=None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def respond(self, code, data):
            body = json.dumps(data, allow_nan=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def allowed(self):
            host = self.headers.get('Host', '')
            if not re.fullmatch(r'(127\.0\.0\.1|localhost):\d{1,5}', host):
                self.respond(403, {'error': 'Loopback Host required'}); return False
            origin = self.headers.get('Origin')
            if origin and origin not in ('http://127.0.0.1:5173', 'http://localhost:5173', 'http://' + host):
                self.respond(403, {'error': 'Origin not allowed'}); return False
            return True

        def do_GET(self):
            if not self.allowed(): return
            path = urlsplit(self.path).path
            if path == '/api/health':
                return self.respond(200, {'service': 'zephyr-local', 'activeRunId': jobs.active, 'geometryId': 'drivaer-1', 'copilot': copilot.status() if copilot else {'enabled': False}})
            if path == '/api/geometries':
                return self.respond(200, {'cars':CARS})
            match = re.fullmatch(r'/api/runs/(local-[0-9a-f]{32})(?:/(baseline|result|evidence|explanation|summary))?', path)
            if not match:
                return self.respond(404, {'error': 'Not found'})
            run_id, artifact = match.groups()
            try:
                job = jobs.snapshot(run_id)
                if artifact is None:
                    return self.respond(200, job)
                if artifact == 'baseline' and not job['baselineReady'] or artifact != 'baseline' and not job['resultReady']:
                    return self.respond(409, {'error': 'Artifact is not ready'})
                if artifact == 'summary':
                    from zephyr.run_answers import summarize_run
                    evidence = json.loads((jobs.root / run_id / 'evidence.json').read_text(encoding='utf-8'))
                    return self.respond(200, summarize_run(evidence))
                if artifact == 'explanation':
                    explanation = copilot.explanations.get(run_id) if copilot else None
                    return self.respond(200, explanation) if explanation else self.respond(404, {'error': 'No explanation generated yet'})
                file = jobs.root / run_id / (artifact + '.json')
                body = file.read_bytes()
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
            except KeyError:
                self.respond(404, {'error': 'Unknown/expired run; artifacts remain on disk'})

        def do_POST(self):
            if not self.allowed(): return
            try:
                if self.headers.get('Content-Type') != 'application/json':
                    return self.respond(415, {'error': 'application/json required'})
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 2048:
                    return self.respond(413, {'error': 'Request must be 1..2048 bytes'})
                data = json.loads(self.rfile.read(length))
                if self.path == '/api/intent':
                    if not copilot:
                        return self.respond(503, {'error': 'Start the API with --enable-llm to interpret briefs'})
                    return self.respond(200, copilot.compile(data))
                if self.path == '/api/runs':
                    # A baseline measures an allowlisted aircraft without any design intent.
                    # The ordinary validator still enforces exact fields and analysis-only mode.
                    if isinstance(data,dict) and data.get('geometryId') in ('x57','global-hawk') and data.get('mode')=='analysis':
                        return self.respond(202,jobs.start(data))
                    if copilot:
                        if not isinstance(data, dict):
                            raise ValueError('Expected a run request')
                        intent_id = data.pop('intentId', None)
                        authorized = copilot.authorize(intent_id, data)
                        intent = authorized.pop('intent')
                        return self.respond(202, jobs.start(authorized, intent=intent))
                    return self.respond(202, jobs.start(data))
                match = re.fullmatch(r'/api/runs/(local-[0-9a-f]{32})/(explain|questions)', self.path)
                if match:
                    if not copilot:
                        return self.respond(503, {'error': 'Language model is disabled'})
                    if match[2] == 'explain' and data != {}:
                        raise ValueError('Explanation reads server evidence; body must be empty')
                    job = jobs.snapshot(match[1])
                    if job['state'] != 'complete' or not job['resultReady']:
                        return self.respond(409, {'error': 'Completed evidence is required'})
                    evidence = json.loads((jobs.root / match[1] / 'evidence.json').read_text(encoding='utf-8'))
                    return self.respond(200, copilot.ask(evidence, data) if match[2] == 'questions' else copilot.explain(evidence))
                match = re.fullmatch(r'/api/runs/(local-[0-9a-f]{32})/cancel', self.path)
                if match:
                    return self.respond(200, jobs.cancel(match[1]))
                self.respond(404, {'error': 'Not found'})
            except (BusyError, CopilotBusy) as exc:
                self.respond(409, {'error': str(exc)})
            except TokenFactoryError:
                self.respond(502, {'error': 'Language-model request failed; check configured model, endpoint and credentials, then retry'})
            except (ValueError, TypeError) as exc:
                self.respond(400, {'error': str(exc)})
            except KeyError:
                self.respond(404, {'error': 'Unknown run'})
            except Exception:
                self.respond(500, {'error': 'Request failed; check local runtime'})
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--enable-llm', action='store_true', help='Opt in to paid model calls for brief interpretation and evidence explanation')
    args = parser.parse_args()
    copilot = None
    if args.enable_llm:
        from zephyr.config import load_env_file, load_llm_config
        values = os.environ.copy()
        load_env_file(ROOT / '.env', environ=values)
        copilot = Copilot(ROOT / '.local/copilot', load_llm_config(values, require_credentials=True))
    jobs = Jobs()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler_for(jobs, copilot))
    print(f'Zephyr local DoMINO API: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        jobs.close(); server.server_close()


if __name__ == '__main__':
    main()
