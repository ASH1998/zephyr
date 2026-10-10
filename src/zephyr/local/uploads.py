"""Local upload registry. Only generated identifiers can resolve to stored geometry."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import re
import threading
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[3] / '.local/uploads'
ID_PATTERN = r'upload-[0-9a-f]{32}'
_lock = threading.RLock()
_preparing = threading.Lock()


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, allow_nan=False, separators=(',', ':')), encoding='utf-8')
    temporary.replace(path)


def manifest(root=None):
    path = (root or ROOT) / 'manifest.json'
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict) or any(not re.fullmatch(ID_PATTERN, key) for key in value):
        raise ValueError('Invalid upload manifest')
    return value


def entry(upload_id, *, confirmed=False, root=None):
    if not isinstance(upload_id, str) or not re.fullmatch(ID_PATTERN, upload_id):
        raise ValueError('Invalid upload identifier')
    with _lock:
        value = manifest(root).get(upload_id)
    if not isinstance(value, dict) or value.get('id') != upload_id or value.get('state') not in ('ready', 'confirmed'):
        raise ValueError('Unknown upload')
    if confirmed and value['state'] != 'confirmed':
        raise ValueError('Confirm the uploaded geometry first')
    return value


def definition(upload_id):
    value = entry(upload_id, confirmed=True)
    report = value['report']
    return {'id': upload_id, 'label': 'Your car · experimental', 'description': report.get('label', 'Uploaded mesh') + ' · DoMINO estimate, experimental geometry',
        'category': 'car', 'experimental': True, 'support': report['trainingRange']['support'],
        'supportReason': report['trainingRange']['reason'], 'preview': f'/api/uploads/{upload_id}/preview',
        'airflow': f'/api/uploads/{upload_id}/airflow', 'importReport': report}


def definitions():
    with _lock:
        return [definition(key) for key, value in manifest().items() if value.get('state') == 'confirmed']


class Uploads:
    def __init__(self, root=None, photo_client=None):
        self.root = root or ROOT
        self.photo_client = photo_client

    def _save(self, value):
        with _lock:
            values = manifest(self.root); values[value['id']] = value
            write_json(self.root / 'manifest.json', values)

    def get(self, upload_id):
        value = entry(upload_id, root=self.root)
        preview = json.loads((self.root / upload_id / 'preview.json').read_text(encoding='utf-8'))
        return {**value, 'preview': preview}

    def create(self, data, filename, options=None):
        from zephyr.local.importer import MESH_EXTENSIONS, MAX_BYTES, load_mesh, orient_mesh, validate_options
        options = validate_options(options or {})
        if not isinstance(filename, str) or len(filename) > 240 or '/' in filename or '\\' in filename:
            raise ValueError('Use a plain filename with an extension')
        extension = Path(filename).suffix.lower()
        if not 0 < len(data) <= MAX_BYTES:
            raise ValueError('Upload must be between 1 byte and 50 MB')
        if extension not in MESH_EXTENSIONS | {'.png', '.jpg', '.jpeg', '.webp'}:
            raise ValueError('Choose a mesh (STL/OBJ/GLB/GLTF/PLY) or photo (PNG/JPEG/WebP)')
        if not _preparing.acquire(blocking=False):
            raise ValueError('Another upload is preparing. Retry when it finishes.')
        try:
            upload_id = 'upload-' + uuid4().hex
            photo = None
            if extension in MESH_EXTENSIONS:
                mesh, orientation = orient_mesh(load_mesh(data, extension), extension, options)
            else:
                if self.photo_client is None:
                    raise ValueError('Photo import requires starting the API with --enable-llm; mesh upload works locally')
                from zephyr.local.photo_import import photo_template
                mesh, photo = photo_template(data, self.photo_client)
                orientation = {'unitsGuess': 'm', 'scale': 1., 'rotation': [0, 0, 0], 'flipFront': False, 'lengthM': None}
            self.root.mkdir(parents=True, exist_ok=True)
            directory = self.root / upload_id; directory.mkdir()
            (directory / ('source' + extension)).write_bytes(data)
            if photo:
                mesh.export(directory / 'template.ply')
                write_json(directory / 'photo.json', photo)
            value = {'id': upload_id, 'state': 'ready', 'extension': extension, 'sourceSha256': sha256(data).hexdigest(), 'photo': bool(photo)}
            self._prepare(value, mesh, orientation, photo)
            return self.get(upload_id)
        finally:
            _preparing.release()

    def _prepare(self, value, mesh, orientation, photo=None):
        from zephyr.local.importer import prepare_surface, training_range
        model, preview, report = prepare_surface(mesh, geometry_id=value['id'])
        report.update(orientation=orientation, sourceSha256=value['sourceSha256'],
                      label='Uploaded mesh · experimental')
        if photo:
            report['photo'] = photo
            report['trainingRange'] = training_range([report['trainingRange']['values'][k] for k in ('lengthM', 'widthM', 'heightM')], photo['vision']['bodyType'])
            if photo['appliedSupport'] == 'baseline-only':
                report['trainingRange']['support'] = 'baseline-only'
                report['trainingRange']['reason'] = photo['decision']['reason']
            dimensions = report['trainingRange']['values']
            report['label'] = ('Approximated from photo · ' + photo['decision']['templateId'] + ' scaled to ' +
                ' × '.join(f'{dimensions[k]:.2f}' for k in ('lengthM', 'widthM', 'heightM')) + ' m · experimental')
        directory = self.root / value['id']
        model.save(directory / 'surface.vtp')
        report['surfaceSha256'] = sha256((directory / 'surface.vtp').read_bytes()).hexdigest()
        write_json(directory / 'preview.json', preview); write_json(directory / 'report.json', report)
        value['report'] = report
        self._save(value)

    def prepare(self, upload_id, options):
        from zephyr.local.importer import load_mesh, orient_mesh, validate_options
        options = validate_options(options)
        if not _preparing.acquire(blocking=False):
            raise ValueError('Another upload is preparing. Retry when it finishes.')
        try:
            value = entry(upload_id, root=self.root)
            if value['state'] == 'confirmed':
                raise ValueError('Confirmed geometry is immutable. Upload again to change orientation or size.')
            directory = self.root / upload_id
            photo = json.loads((directory / 'photo.json').read_text()) if value['photo'] else None
            source = directory / ('template.ply' if photo else 'source' + value['extension'])
            extension = '.ply' if photo else value['extension']
            mesh = load_mesh(source.read_bytes(), extension)
            # Photo templates are already canonical Y-up.
            mesh, orientation = orient_mesh(mesh, '.obj' if photo else extension, options)
            self._prepare(value, mesh, orientation, photo)
            return self.get(upload_id)
        finally:
            _preparing.release()

    def confirm(self, upload_id, options, jobs):
        from zephyr.local.importer import validate_options
        options = validate_options(options)
        with _lock:
            value = entry(upload_id, root=self.root)
            saved_options = {key: value['report']['orientation'][key] for key in options}
            if value['state'] != 'confirmed':
                if options != saved_options:
                    value = self.prepare(upload_id, options)
                    value.pop('preview', None)
                value['state'] = 'confirmed'; self._save(value)
            elif options != saved_options:
                raise ValueError('Confirmed geometry is immutable')
            if value.get('runId'):
                return {**self.get(upload_id), 'job': jobs.snapshot(value['runId'])}
            job = jobs.start({'geometryId': upload_id, 'budgetMm': 4,
                             'brief': 'Reduce drag. Keep the cabin unchanged.', 'mode': 'analysis'})
            value['runId'] = job['runId']; self._save(value)
            return {**self.get(upload_id), 'job': job}
