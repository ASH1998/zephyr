import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from io import BytesIO
from zipfile import ZipFile
import numpy as np
import pyvista as pv
from zephyr.local.geometry import HANDLES,REAR_HANDLES,rear_basis,deform,validate_geometry
from zephyr.local.conversion import mesh_hash
from zephyr.artifacts import _file_sha256
from zephyr.local.exports import candidate_bundle
from zephyr.copilot import validate_interpretation
from test_copilot import REQUEST,VALUE


class ExplorationTests(unittest.TestCase):
    def test_profiles_are_distinct_bounded_and_never_unlock_original_protection(self):
        mesh=pv.Sphere(radius=1,center=(0,0,.6),theta_resolution=60,phi_resolution=60)
        original_mask=rear_basis(mesh.points)[1]
        variants=[]
        for handle in REAR_HANDLES:
            trial,mask,_=deform(mesh,.0001,.001,handle)
            self.assertTrue(np.array_equal(mesh.points[original_mask],trial.points[original_mask]))
            self.assertTrue(np.array_equal(mesh.faces,trial.faces))
            self.assertLessEqual(np.linalg.norm(trial.points-mesh.points,axis=1).max(),.001)
            self.assertTrue(all(c['status']=='passed' for c in validate_geometry(mesh,trial,mask,.001).values()))
            self.assertTrue(np.array_equal(mesh.points[:,[0,2]],trial.points[:,[0,2]]))
            variants.append(trial.points)
        for i in range(3):
            for j in range(i):self.assertFalse(np.array_equal(variants[i],variants[j]))
        with self.assertRaises(ValueError):deform(mesh,.001,.002,'invented-tool')

    def test_comparison_tool_requires_exploration_and_refusal_is_preserved(self):
        value=VALUE|{'handle':'compare-rear-tapers'}
        with self.assertRaises(ValueError):validate_interpretation(value,REQUEST)
        self.assertEqual(validate_interpretation(value,REQUEST|{'mode':'exploration'})['status'],'ready')
        value=VALUE|{'status':'refuse','requestedMaxMm':None,'message':'Cabin movement unsupported'}
        req=REQUEST|{'brief':REQUEST['brief']+' Move cabin 2 mm.'}
        self.assertEqual(validate_interpretation(value,req)['status'],'refuse')

    def test_export_verifies_source_hash_and_keeps_refusal(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);mesh=pv.Sphere();path=root/'evaluate.vtk';mesh.save(path)
            evidence={'forces':{'candidateDragN':10},'provenance':{'candidateMeshHash':mesh_hash(mesh)},
                      'artifacts':{'evaluate.vtk':{'sha256':_file_sha256(path)}},'trust':{'decision':'refuse','reason':'Experimental'}}
            (root/'evidence.json').write_text(json.dumps(evidence))
            bundle=candidate_bundle(root)
            with ZipFile(BytesIO(bundle)) as z:
                self.assertIn('candidate.stl',z.namelist());self.assertIn('refuse',z.read('README.txt').decode())
                self.assertEqual(z.read('evaluate.vtk'),path.read_bytes())
            path.write_bytes(b'tampered')
            with self.assertRaises(ValueError):candidate_bundle(root)

    def test_study_reserves_queue_and_rejects_uncompiled_mode(self):
        from zephyr.local.server import Jobs,BusyError
        with tempfile.TemporaryDirectory() as folder:
            jobs=Jobs(Path(folder))
            jobs.studies.current='study-'+'a'*32
            with self.assertRaises(BusyError):jobs.start(REQUEST,intent={'graph':VALUE})
            jobs.studies.current=None
            with self.assertRaises(ValueError):jobs.studies.start(REQUEST|{'intent':{'graph':VALUE}})
            with self.assertRaises(KeyError):jobs.studies.get('../outside')

    def test_study_serial_expansion_records_refused_candidates(self):
        from zephyr.local.server import Jobs
        with tempfile.TemporaryDirectory() as folder:
            jobs=Jobs(Path(folder));intent={'intentId':'intent-'+'a'*32,'graph':VALUE|{'handle':'compare-rear-tapers'}}
            with patch('zephyr.local.studies.threading.Thread'):
                study=jobs.studies.start(REQUEST|{'mode':'exploration','intent':intent})
            self.assertEqual(len(study['plannedHandles']),3)
            self.assertEqual(jobs.studies.current,study['studyId'])
            jobs.studies.cancel(study['studyId']);self.assertTrue(jobs.studies.cancelled.is_set())
            jobs.studies._run(study,REQUEST|{'mode':'exploration','intent':intent})
            self.assertEqual(jobs.studies.get(study['studyId'])['state'],'cancelled')
            self.assertIsNone(jobs.studies.current)
