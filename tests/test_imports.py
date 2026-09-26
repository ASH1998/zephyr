import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
import threading
from types import SimpleNamespace
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import numpy as np
import trimesh
from zephyr.local import uploads
from zephyr.local.importer import load_mesh, orient_mesh, prepare_surface, training_range, validate_options, MAX_BYTES
from zephyr.local.cars import car_definition, mesh_path, CARS
from zephyr.local.server import handler_for, validate_request, preset_plan
from zephyr.copilot import canonical_request
from zephyr.local.photo_import import VISION_SCHEMA, DECISION_SCHEMA, validate_schema, image_content


class ImportGeometryTests(unittest.TestCase):
    def test_units_orientation_override_and_flip(self):
        for factor, units in [(1, 'm'), (10, 'cm'), (1000, 'mm')]:
            source = trimesh.creation.box([4.5 * factor, 1.8 * factor, 1.45 * factor])
            mesh, report = orient_mesh(source, '.stl', {'lengthM': 4.5} if factor == 10 else {})
            np.testing.assert_allclose(mesh.extents, [4.5, 1.45, 1.8])
            self.assertEqual(report['unitsGuess'], units)
            self.assertGreater(np.linalg.det(report['automaticRotation']), 0)
            resized, _ = orient_mesh(source, '.stl', {'lengthM': 4.8, 'flipFront': True})
            self.assertAlmostEqual(resized.extents[0], 4.8)
        source = trimesh.creation.box([4.5, 1.45, 1.8])
        mesh, _ = orient_mesh(source, '.glb', {})
        np.testing.assert_allclose(mesh.extents, source.extents)
        for options in ({'rotation': [1, 0, 0]}, {'rotation': [True, 0, 0]}, {'lengthM': float('nan')}, {'lengthM': True}, {'flipFront': 'yes'}, {'path': '..'}):
            with self.assertRaises(ValueError): validate_options(options)

    def test_closed_surface_component_merge_and_large_hole(self):
        source = trimesh.creation.box([4.5, 1.45, 1.8])
        # A separate small wheel/part within two voxels should join the body, not be discarded.
        part = trimesh.creation.box([.3, .3, .1]); part.apply_translation([1.4, -.3, .98])
        model, preview, report = prepare_surface(trimesh.util.concatenate([source, part]))
        self.assertEqual(model.n_open_edges, 0)
        self.assertLessEqual(model.n_points, 120000)
        self.assertEqual(len(preview['protectedMask']), model.n_points)
        self.assertIn('nose-width-v1', preview['regionMasks'])
        self.assertEqual(report['trainingRange']['support'], 'shape-tests')
        opened = source.copy(); opened.update_faces(np.arange(2, len(opened.faces)))
        with self.assertRaisesRegex(ValueError, 'holes'): prepare_surface(opened)
        detached = part.copy(); detached.apply_translation([0, 0, 1])
        with self.assertRaisesRegex(ValueError, 'Disconnected'): prepare_surface(trimesh.util.concatenate([source, detached]))

    def test_loader_caps_external_resources_and_range(self):
        mesh = load_mesh(trimesh.creation.box([4.5, 1.8, 1.45]).export(file_type='stl'), '.stl')
        self.assertEqual(len(mesh.faces), 12)
        for data, extension in [(b'', '.stl'), (b'bad', '.exe'), (b'bad', '.stl'), (json.dumps({'buffers': [{'uri': 'file:///private'}]}).encode(), '.gltf')]:
            with self.assertRaises(ValueError): load_mesh(data, extension)
        with patch('zephyr.local.importer.MAX_BYTES', 3):
            with self.assertRaises(ValueError): load_mesh(b'1234', '.stl')
        self.assertEqual(training_range([4.6, 1.8, 1.45])['support'], 'shape-tests')
        self.assertEqual(training_range([6, 2.5, 2.8])['support'], 'baseline-only')
        for body in ('pickup', 'open-wheel', 'other'):
            self.assertEqual(training_range([4.6, 1.8, 1.45], body)['support'], 'baseline-only')


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.override = patch.object(uploads, 'ROOT', self.root); self.override.start()
        self.store = uploads.Uploads(self.root)
        self.source = trimesh.creation.box([4.5, 1.8, 1.45]).export(file_type='stl')

    def tearDown(self):
        self.override.stop(); self.tmp.cleanup()

    def test_create_confirm_immutable_registry_and_gates(self):
        original = json.dumps(CARS)
        result = self.store.create(self.source, 'sedan.stl'); key = result['id']
        with self.assertRaises(ValueError): car_definition(key)
        with self.assertRaises(ValueError): uploads.entry('../surface')
        jobs = Mock(); jobs.start.return_value = {'runId': 'local-' + '1' * 32, 'state': 'running'}
        jobs.snapshot.return_value = jobs.start.return_value
        result = self.store.confirm(key, {}, jobs)
        self.assertTrue(mesh_path(key).is_file())
        self.assertTrue(car_definition(key)['experimental'])
        self.assertEqual(car_definition(key)['support'], 'shape-tests')
        self.store.confirm(key, {}, jobs); self.assertEqual(jobs.start.call_count, 1)
        with self.assertRaises(ValueError): self.store.prepare(key, {})
        request = {'geometryId': key, 'budgetMm': 4, 'brief': 'Reduce drag. Keep the cabin unchanged.', 'mode': 'iteration'}
        validate_request(request); canonical_request(request)
        values = uploads.manifest(); values[key]['report']['trainingRange'].update(support='baseline-only', reason='Test pickup')
        uploads.write_json(self.root / 'manifest.json', values)
        for validate in (validate_request, canonical_request):
            with self.assertRaisesRegex(ValueError, 'baseline'): validate(request)
            validate({**request, 'mode': 'analysis'})
        with self.assertRaises(ValueError): preset_plan({'geometryId': key, 'budgetMm': 4, 'handle': 'nose-width-v1'})
        self.assertEqual(json.dumps(CARS), original)
        self.assertEqual(uploads.Uploads(self.root).get(key)['id'], key)

    def test_http_upload_preview_caps_confirm_and_origin(self):
        jobs = Mock(); jobs.start.return_value = {'runId': 'local-' + '2' * 32, 'state': 'running'}
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(jobs, uploads=self.store))
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        def send(path, body=None, headers=None):
            return urlopen(Request(base + path, data=body, headers=headers or {}), timeout=30)
        try:
            with send('/api/uploads', self.source, {'X-Filename': 'car.stl', 'Content-Type': 'application/octet-stream'}) as response:
                self.assertEqual(response.status, 201); value = json.load(response)
            key = value['id']
            with send(f'/api/uploads/{key}/preview') as response:
                self.assertEqual(json.load(response)['geometryId'], key)
            with send(f'/api/uploads/{key}/confirm', b'{}', {'Content-Type': 'application/json'}) as response:
                self.assertEqual(response.status, 202)
            with send('/api/geometries') as response:
                self.assertEqual(len(json.load(response)['cars']), len(CARS) + 1)
            for headers, expected in [({'Content-Length': str(MAX_BYTES + 1)}, 413), ({'Origin': 'https://evil.example'}, 403)]:
                with self.assertRaises(HTTPError) as caught: send('/api/uploads', b'x', headers)
                self.assertEqual(caught.exception.code, expected)
        finally:
            server.shutdown(); server.server_close(); thread.join()


class PhotoContractTests(unittest.TestCase):
    def test_photo_schema_and_invalid_image_fail_closed(self):
        vision = dict(isCar=True, bodyType='pickup', roof='unknown', makeModelGuess=None,
                      makeModelConfidence=.1, view='side', features=[])
        validate_schema(vision, VISION_SCHEMA)
        for invalid in ({**vision, 'isCar': 'true'}, {**vision, 'makeModelConfidence': float('nan')}, {**vision, 'bodyType': 'motorbike'}):
            with self.assertRaises(ValueError): validate_schema(invalid, VISION_SCHEMA)
        with self.assertRaises(ValueError): image_content(b'not an image')
        decision = dict(templateId='hatchback', dimensionsM=dict(length=4.5, width=1.8, height=1.45), dimensionSource='class-typical', support='baseline-only', reason='Pickup', explanation='Template only')
        validate_schema(decision, DECISION_SCHEMA)
        with self.assertRaises(ValueError): validate_schema({**decision, 'templateId': '../../bad'}, DECISION_SCHEMA)

    def test_two_stage_photo_pipeline_clamps_pickup_and_rejects_non_car(self):
        from PIL import Image
        from io import BytesIO
        from zephyr.local.photo_import import photo_template
        import pyvista as pv
        image = BytesIO(); Image.new('RGB', (32, 32), 'blue').save(image, format='PNG')
        vision = dict(isCar=True, bodyType='pickup', roof='unknown', makeModelGuess=None,
                      makeModelConfidence=.1, view='side', features=[])
        decision = dict(templateId='coupe', dimensionsM=dict(length=4.5, width=1.8, height=1.45),
                        dimensionSource='class-typical', support='shape-tests', reason='Closest template', explanation='Approximation')
        client = Mock(); client.complete_json.side_effect = [(vision, {'model':'vision'}), (decision, {'model':'decision'})]
        copilot = SimpleNamespace(client=client, config=SimpleNamespace(ai_project_id=''))
        template = pv.Box(bounds=(-2.25,2.25,-.9,.9,0,1.45)).triangulate()
        with patch('pyvista.read', return_value=template):
            mesh, report = photo_template(image.getvalue(), copilot)
        np.testing.assert_allclose(mesh.extents, [4.5, 1.45, 1.8])
        self.assertEqual(report['decision']['support'], 'shape-tests')  # Preserve what the model actually said.
        self.assertEqual(report['appliedSupport'], 'baseline-only')  # Deterministic floor cannot be relaxed.
        self.assertEqual(client.complete_json.call_count, 2)
        self.assertIn('Lamborghini Veneno', client.complete_json.call_args.args[2])
        client.reset_mock(); client.complete_json.side_effect = [({**vision, 'isCar': False}, {})]
        with self.assertRaisesRegex(ValueError, 'No car'): photo_template(image.getvalue(), copilot)
        self.assertEqual(client.complete_json.call_count, 1)

    def test_import_summary_distinguishes_initial_baseline_from_access_restriction(self):
        from zephyr.run_answers import run_facts
        evidence = {'forces': {'baselineDragN':100., 'candidateDragN':None}, 'validation': {'independentCfd':'not-run'},
                    'trust': {'decision':'refuse'}, 'car': {'support':'shape-tests', 'importReport': {'label':'Photo template', 'photo': {}}}}
        facts = run_facts(evidence)
        self.assertIn('supports experimental shape tests', facts['next']['text'])
        evidence['car'].update(support='baseline-only', supportReason='Pickup outside limits')
        self.assertIn('unavailable', run_facts(evidence)['next']['text'])


if __name__ == '__main__':
    unittest.main()
