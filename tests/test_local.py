import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys
import numpy as np
import pyvista as pv
from zephyr.local.conversion import ROTATION, cell_to_point, display_mapping, mesh_hash, surface
from zephyr.local.geometry import rear_basis, propose, validate_geometry
from zephyr.local.server import Jobs, BusyError, handler_for, validate_request

REQUEST = {'geometryId':'drivaer-1','budgetMm':3.6,'brief':'Reduce drag. Keep the cabin unchanged.','mode':'iteration'}

class ConversionTests(unittest.TestCase):
    def test_transform_and_area_weighted_fields(self):
        p=np.array([[0,0,0],[1,0,0],[0,1,0],[0,-2,0]],float)
        m=pv.PolyData(p,[3,0,1,2,3,1,0,3])
        np.testing.assert_allclose(cell_to_point(m,[10,40]),[30,30,10,40])
        m.cell_data['pred_surf_pressure']=[10.,40.]
        m.cell_data['pred_surf_wall_shear_stress']=np.tile([1.,2.,3.],(2,1))
        m.point_data['smooth_sensitivity_point']=np.tile([4.,5.,6.],(4,1))
        m.point_data['smooth_sensitivity_normal_point']=[-1.,0.,1.,2.]
        ids,tri,_=display_mapping(m)
        result,_=surface(m,ids,tri,np.ones(4),np.zeros(3))
        self.assertEqual(result['wallShearPa'][:3],[1.,3.,-2.])
        self.assertEqual(result['sensitivity'][:3],[4.,6.,-5.])
        self.assertEqual(result['normalSensitivity'],[-1.,0.,1.,2.])
        self.assertEqual(np.linalg.det(ROTATION),1)
        m.cell_data['pred_surf_pressure'][0]=np.nan
        with self.assertRaises(ValueError):surface(m,ids,tri,np.ones(4),np.zeros(3))

    def test_reduction_is_deterministic_and_retains_points(self):
        m=pv.Sphere(theta_resolution=60,phi_resolution=60)
        a,faces,info=display_mapping(m,limit=1500)
        b,other,again=display_mapping(m,limit=1500)
        self.assertLessEqual(len(a),1500)
        np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(faces,other)
        self.assertEqual(info,again);self.assertEqual(info['maximumRetainedPointErrorM'],0)
        self.assertEqual(mesh_hash(m),mesh_hash(m.copy()))

class GeometryTests(unittest.TestCase):
    def mesh(self):
        m=pv.Sphere(radius=1,theta_resolution=40,phi_resolution=40)
        m.points=np.asarray(m.points,dtype=float)*[2.35,1.,.75]+[1.58,0,.45]
        m.cell_data['smooth_sensitivity_cell']=np.tile([0.,1.,0.],(m.n_cells,1))*np.sign(m.cell_centers().points[:,1,None])
        m.cell_data['geometry_sensitivity']=m.cell_data['smooth_sensitivity_cell'].copy()
        return m
    def test_fixed_cabin_topology_bounds_and_refusal_checks(self):
        m=self.mesh();c,mask,report=propose(m,.004)
        np.testing.assert_array_equal(m.faces,c.faces)
        np.testing.assert_array_equal(m.points[mask],c.points[mask])
        self.assertLessEqual(np.linalg.norm(c.points-m.points,axis=1).max(),.004+1e-12)
        self.assertEqual(report['checks']['selfIntersection']['status'],'not-run')
        for key in ['bounds','protected','topology','watertight','normals','triangleArea']:
            self.assertEqual(report['checks'][key]['status'],'passed',key)
        c.points[np.flatnonzero(mask)[0],0]+=.001
        self.assertEqual(validate_geometry(m,c,mask,.004)['protected']['status'],'failed')
    def test_symmetric_handle_and_boundary(self):
        m=self.mesh();a,_,_=rear_basis(m.points)
        reflected=m.points.copy();reflected[:,1]*=-1
        b,_,_=rear_basis(reflected)
        np.testing.assert_array_equal(a[:,1],-b[:,1]);self.assertTrue(np.all(a[:,[0,2]]==0))
        with self.assertRaises(ValueError):propose(m,.005)
        with self.assertRaises(ValueError):propose(m,float('nan'))

class LeaseTests(unittest.TestCase):
    def test_worker_lease_survives_independent_api_lease_release(self):
        from zephyr.local.locks import acquire_lock
        with tempfile.TemporaryDirectory(dir=Path(__file__).parents[1]/'.local') as directory:
            root=Path(directory)
            api_lease=acquire_lock(root/'api.lock')
            worker_lease=acquire_lock(root/'worker.lock')
            api_lease.close()
            with self.assertRaises(OSError):acquire_lock(root/'worker.lock')
            worker_lease.close()
            acquire_lock(root/'worker.lock').close()

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parents[1]/'.local')
        script="import sys,time,json;from pathlib import Path;p=Path(sys.argv[1]);print('@ZEPHYR '+json.dumps({'stage':'baseline','detail':'test only','completed':1,'total':2}),flush=True);time.sleep(.2);(p/'result.json').write_text('{}');(p/'evidence.json').write_text('{}')"
        self.jobs=Jobs(Path(self.tmp.name),[sys.executable,'-u','-c',script])
        self.server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(self.jobs))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        self.jobs.close();self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def request(self,path,body=None,headers=None):
        r=Request(self.url+path,data=None if body is None else json.dumps(body).encode(),headers=headers or {'Content-Type':'application/json'})
        try:
            with urlopen(r) as response:return response.status,json.load(response)
        except HTTPError as error:return error.code,json.load(error)
    def wait(self,run):
        for _ in range(150):
            job=self.jobs.snapshot(run)
            if job['state'] in ('complete','failed','cancelled') and self.jobs.active is None:return job
            time.sleep(.02)
        self.fail('worker did not finish')
    def test_lifecycle_lock_and_provenance(self):
        code,job=self.request('/api/runs',REQUEST);self.assertEqual(code,202)
        self.assertEqual(self.request('/api/runs',REQUEST)[0],409)
        other=Jobs(Path(self.tmp.name),self.jobs.command)
        with self.assertRaises(BusyError):other.start(REQUEST)
        self.assertEqual(self.request('/api/runs/'+job['runId']+'/result')[0],409)
        result=self.wait(job['runId']);self.assertEqual(result['state'],'complete')
        self.assertTrue(all(e['runId']==job['runId'] and e['source']=='live' for e in result['events']))
        self.assertEqual(self.request('/api/runs/'+job['runId']+'/result')[0],200)
    def test_failure_and_cancel_release_lock(self):
        self.jobs.command=[sys.executable,'-c','raise RuntimeError("test worker failure")']
        failed=self.wait(self.jobs.start(REQUEST)['runId']);self.assertEqual(failed['state'],'failed')
        self.jobs.command=[sys.executable,'-c','import time;time.sleep(60)']
        job=self.jobs.start(REQUEST);self.jobs.cancel(job['runId']);self.assertEqual(self.wait(job['runId'])['state'],'cancelled')
    def test_compiled_api_rejects_bypass_and_binds_worker_request(self):
        from zephyr.copilot import Copilot, HANDLE
        from zephyr.config import LlmConfig
        from unittest.mock import Mock
        client = Mock()
        client.complete_json.return_value = ({'status':'ready','objective':'reduce_drag','protectedRegions':['cabin'],'handle':HANDLE,'requestedMaxMm':2,'evidenceQuotes':['Reduce drag'],'message':'Rear taper with 2 mm ceiling.'}, {'model':'test','seconds':0})
        copilot = Copilot(Path(self.tmp.name)/'copilot', LlmConfig('https://example.invalid','test','secret',''), client)
        self.server.RequestHandlerClass = handler_for(self.jobs, copilot)
        request = REQUEST | {'brief':'Reduce drag with a rear taper. Maximum 2 mm.'}
        self.assertEqual(self.request('/api/runs', request)[0],400)
        code, plan = self.request('/api/intent',request)
        self.assertEqual(code,200)
        self.assertEqual(self.request('/api/runs',request|{'intentId':plan['intentId'],'budgetMm':4})[0],400)
        code, job = self.request('/api/runs',request|{'intentId':plan['intentId']})
        self.assertEqual(code,202)
        stored = json.loads((self.jobs.root/job['runId']/'request.json').read_text())
        self.assertEqual(stored['budgetMm'],2)
        self.assertEqual(stored['intent']['intentId'],plan['intentId'])
        self.assertEqual(self.request('/api/runs/'+job['runId']+'/explain',{})[0],409)
        self.assertEqual(self.request('/api/runs/'+job['runId']+'/questions',{'question':'What changed?'})[0],409)
        self.wait(job['runId'])
        self.assertEqual(self.request('/api/runs/'+job['runId']+'/explanation')[0],404)
        self.assertEqual(self.request('/api/runs/'+job['runId']+'/explain',{'forces':{}})[0],400)
        self.assertEqual(client.complete_json.call_count,1)
        evidence = {'runId':job['runId'],'forces':{'baselineDragN':100,'candidateDragN':101},'constraints':{'maxDisplacementM':.002},'validation':{'independentCfd':'not-run','checks':{}},'trust':{'decision':'refuse','reason':'Trust uncalibrated','calibrated':False}}
        (self.jobs.root/job['runId']/'evidence.json').write_text(json.dumps(evidence))
        client.complete_json.return_value = ({'factIds':['force']}, {'model':'test','seconds':0})
        code, explanation = self.request('/api/runs/'+job['runId']+'/explain',{})
        self.assertEqual(code,200)
        self.assertEqual(explanation['decision'],'refuse')
        self.assertEqual(self.request('/api/runs/'+job['runId']+'/explanation')[1],explanation)
        self.assertEqual(self.request('/api/runs/'+job['runId']+'/explain',{})[1],explanation)
        self.assertEqual(client.complete_json.call_count,2)
        self.assertEqual(self.request('/api/runs/'+job['runId']+'/summary')[1]['headline'],'This change did not help')
        self.assertEqual(client.complete_json.call_count,2)
        self.assertEqual(self.request('/api/runs/'+job['runId']+'/questions',{'question':'Help','forces':{}})[0],400)
        client.complete_json.return_value=({'answerable':True,'factIds':['decision']},{'model':'test'})
        code,answer=self.request('/api/runs/'+job['runId']+'/questions',{'question':'Did it help?'})
        self.assertEqual(code,200);self.assertEqual(answer['runId'],job['runId']);self.assertIsNone(self.jobs.active)

    def test_input_paths_origin_content_type(self):
        for patch in [{'geometryId':'../../secret'},{'budgetMm':True},{'budgetMm':float('nan')},{'budgetMm':12},{'inputPath':'x'},{'brief':'Move cabin'}]:
            with self.assertRaises(ValueError):validate_request(REQUEST|patch)
        self.assertEqual(self.request('/api/runs',REQUEST,{'Content-Type':'application/json','Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.request('/api/runs',REQUEST,{'Content-Type':'text/plain'})[0],415)
        self.assertEqual(self.request('/api/runs/../../secrets')[0],404)

if __name__=='__main__':unittest.main()
