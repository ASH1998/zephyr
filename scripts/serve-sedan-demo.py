"""Dependency-free recorded demo server, copied into a prepared deployment bundle."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit


def verify_manifest(root, manifest):
    root = root.resolve()
    for name, expected in manifest['files'].items():
        path = (root/name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Deployment artifact is missing or changed: '+name)
    if any(name not in manifest['files'] for name in manifest['routes'].values()):
        raise ValueError('An API route lacks a verified artifact')


def handler(root, routes, default_run):
    class Handler(SimpleHTTPRequestHandler):
        def list_directory(self, path):
            self.send_error(404); return None

        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == '/' and not url.query:
                self.send_response(302); self.send_header('Location', '/?replay=' + default_run); self.end_headers(); return
            if url.path.startswith('/api/'):
                file = routes.get(url.path)
                if not file:
                    self.send_error(404); return
                target = (root / file).resolve()
                if not target.is_relative_to(root.resolve()) or not target.is_file():
                    self.send_error(404); return
                body = target.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'application/zip' if target.suffix == '.zip' else 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers(); self.wfile.write(body); return
            super().do_GET()

        def do_POST(self):
            body = json.dumps({'error': 'This deployment serves recorded evidence. Fresh inference and model calls run in the local workstation app.'}).encode()
            self.send_response(409); self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)

        def log_message(self, *_): pass
    return partial(Handler, directory=str(root / 'web'))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--host', default='127.0.0.1'); p.add_argument('--port', type=int, default=8780)
    args = p.parse_args()
    manifest = json.loads((args.root / 'manifest.json').read_text())
    verify_manifest(args.root, manifest)
    server = ThreadingHTTPServer((args.host, args.port), handler(args.root, manifest['routes'], manifest['defaultRunId']))
    print(f"Recorded Zephyr demo: http://{args.host}:{args.port}/", flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == '__main__': main()
