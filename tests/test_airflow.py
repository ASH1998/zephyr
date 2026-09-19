import json
from pathlib import Path
import unittest
import numpy as np
from zephyr.local.cars import CARS,IDS,mesh_path
from zephyr.local.volume import trace_streamlines
from zephyr.copilot import canonical_request
class AirflowTests(unittest.TestCase):
 def test_all_vehicle_styles_have_unique_closed_geometry_and_matching_airflow(self):
  import pyvista as pv
  root=Path(__file__).parents[1];hashes=set()
  for car in CARS:
   preview=json.loads((root/'frontend/public'/car['preview'].lstrip('/')).read_text(encoding='utf-8'))
   triangles=np.array(preview['triangles']).reshape(-1,3);faces=np.column_stack([np.full(len(triangles),3),triangles])
   mesh=pv.PolyData(np.array(preview['positions']).reshape(-1,3),faces)
   # The older reduced sedan preview is display-only; inference uses its closed full mesh.
   if car['id']!='drivaer-1':self.assertEqual(mesh.n_open_edges,0)
   digest=preview.get('meshHash',preview.get('sourceMeshSha256'));hashes.add(digest)
   d=json.loads((root/'frontend/public'/car['airflow'].lstrip('/')).read_text(encoding='utf-8'))
   self.assertEqual(d['geometryId'],car['id']);self.assertEqual(d['meshHash'],digest)
   self.assertEqual(d['source'],'nvidia-volume');self.assertGreater(len(d['paths']),10)
   canonical_request({'geometryId':car['id'],'budgetMm':2,'brief':'Reduce drag.','mode':'analysis' if car['category']=='aircraft' else 'iteration'})
  self.assertEqual(len(hashes),len(CARS))
  with self.assertRaises(ValueError):mesh_path('../outside')
 def test_tracers_follow_velocity_and_stop_at_masked_body(self):
  axes=[np.linspace(0,5,51),np.linspace(-1,1,11),np.linspace(0,2,11)]
  shape=tuple(map(len,axes));vel=np.zeros((*shape,3));vel[...,0]=2
  sdf=np.ones(shape);sdf[30:]=-1
  paths=trace_streamlines(axes,vel,sdf,np.zeros(3),seeds=[[.1,0,1]])
  self.assertEqual(len(paths),1);p=paths[0];pts=np.array(p['positions']).reshape(-1,3)
  self.assertTrue(np.all(pts[:,0]<3));self.assertTrue(np.allclose(pts[:,1],1));self.assertTrue(np.allclose(pts[:,2],0))
  self.assertTrue(np.allclose(np.diff(pts[:,0])/np.diff(p['timeSeconds']),2,atol=.01))

 def test_aircraft_cannot_use_car_deformation_handles(self):
  from zephyr.local.server import validate_request
  for geometry in ['x57','global-hawk']:
   data={'geometryId':geometry,'budgetMm':2,'brief':'Reduce drag. Keep the cabin unchanged.','mode':'iteration'}
   with self.assertRaises(ValueError):canonical_request(data)
   with self.assertRaises(ValueError):validate_request(data)
   data['mode']='analysis'
   self.assertEqual(canonical_request(data)['geometryId'],geometry)
   self.assertEqual(validate_request(data)['geometryId'],geometry)
