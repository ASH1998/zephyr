"""Bake model-driven airflow for immediate switching between the seven cars."""
import os,json,shutil,sys
from pathlib import Path
import numpy as np
import pyvista as pv
from zephyr.local.cars import CARS,ROOT,mesh_path
from zephyr.local.locks import acquire_lock
os.environ['WARP_CACHE_PATH']=str(ROOT.parent/'.cache/warp')
sys.path.insert(0,str(ROOT/'scripts/windows_compat'))
from zephyr.local.volume import predict_airflow
if __name__=='__main__':
 api_lease=acquire_lock(ROOT/'.local/runs/gpu.lock')
 worker_lease=acquire_lock(ROOT/'.local/runs/worker-gpu.lock')
 try:
  output=ROOT/'frontend/public/models/airflow';output.mkdir(parents=True,exist_ok=True)
  for car in CARS:
   if len(sys.argv)>1 and car['id'] not in sys.argv[1:]:continue
   mesh=pv.read(mesh_path(car['id']));origin=np.array([(mesh.bounds[0]+mesh.bounds[1])/2,0,mesh.bounds[4]])
   directory=ROOT/'.local/airflow-cache'/car['id']
   result=predict_airflow(mesh,origin,directory,car['id'],lambda stage,detail,**kw:print(car['id'],stage,detail,flush=True))
   shutil.copyfile(directory/'airflow.json',output/(car['id']+'.json'))
   print('READY',car['id'],len(result['paths']),result['seconds'],flush=True)
 finally:worker_lease.close();api_lease.close()
