"""NVIDIA DoMINO volume inference and velocity-driven display streamlines.

Uses the pinned upstream volume adapter. Tracer playback is slowed down for
viewing; coordinates and speeds originate from the predicted steady field.
"""
from pathlib import Path
import json
import os
import time
import sys
import numpy as np
from zephyr.local.conversion import ROTATION, mesh_hash
ROOT=Path(__file__).resolve().parents[3]
ASSETS=ROOT/'.local/domino-volume'
MODEL=None

def trace_streamlines(axes, velocity, sdf, origin, *, seeds=None):
    from scipy.interpolate import RegularGridInterpolator
    vel=RegularGridInterpolator(axes,velocity,bounds_error=False,fill_value=np.nan)
    distance=RegularGridInterpolator(axes,sdf,bounds_error=False,fill_value=-1)
    if seeds is None:
        seeds=[[axes[0][1],y,z] for y in np.linspace(-1.9,1.9,11) for z in (.05,.35,.65,.95,1.25,1.55,1.95)]
        seeds += [[x,y,z] for x in (4.2,4.7,5.4) for y in (-.55,0,.55) for z in (.35,.85)]
    paths=[]
    for seed in seeds:
        pos=np.array(seed,dtype=float);points=[];speeds=[];times=[];elapsed=0.
        for _ in range(240):
            v=vel(pos[None])[0];speed=float(np.linalg.norm(v))
            if not np.isfinite(v).all() or speed<.15 or float(distance(pos[None])[0])<=.003:break
            points.append(((pos-origin)@ROTATION.T).tolist());speeds.append(speed);times.append(elapsed)
            dt=min(.01,.075/speed)
            half=pos+v*dt*.5;mid=vel(half[None])[0]
            if not np.isfinite(mid).all():break
            pos=pos+mid*dt;elapsed+=dt
        if len(points)>=12:
            paths.append({'positions':np.round(points,5).reshape(-1).tolist(),'speedMps':np.round(speeds,3).tolist(),'timeSeconds':np.round(times,5).tolist()})
    return paths

def predict_airflow(mesh, origin, directory, geometry_id, emit=lambda *a,**k:None):
    global MODEL
    import pyvista as pv
    import torch
    from omegaconf import OmegaConf
    from zephyr.artifacts import validate_bundle,bundle_ready
    from physicsnemo.models.domino import DoMINO
    from physicsnemo.cfd.evaluation.models.wrappers.domino.inference import build_domin_volume_datadict,domino_volume_test_step
    from physicsnemo.cfd.evaluation.models.wrappers.domino.scaling import load_scaling_factors_tensors
    started=time.perf_counter();directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    import subprocess
    pin=json.loads((ROOT/'config/upstream-lock.json').read_text(encoding='utf-8'))['physicsnemo_cfd']['commit']
    checkout=ROOT/'.local/physicsnemo-cfd'
    if subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()!=pin:raise ValueError('Volume adapter checkout differs from the pinned NVIDIA revision')
    if subprocess.check_output(['git','-C',str(checkout),'diff','HEAD','--','physicsnemo/cfd/evaluation/models/wrappers/domino'],text=True).strip():raise ValueError('Pinned volume adapter has tracked edits')
    checks=validate_bundle(ROOT/'config/domino-volume-artifacts.json',ASSETS)
    if not bundle_ready(checks) or not all(c.checksum_matches for c in checks):raise ValueError('Volume bundle failed checksum verification')
    cfg=OmegaConf.load(ASSETS/'config.yaml');cfg.data.scaling_factors=str(ASSETS/'scaling_factors.pkl')
    device=torch.device('cuda')
    if MODEL is None:
        emit('volume','Loading the NVIDIA air-movement model')
        MODEL=DoMINO.from_checkpoint(str(ASSETS/'DoMINO.0.501.mdlus')).to(device).eval()
    mesh.save(directory/'drivaer_1.stl')
    axes=[np.linspace(-3.3,8.2,96,dtype=np.float32),np.linspace(-2.2,2.2,40,dtype=np.float32),np.linspace(-.30,2.7,36,dtype=np.float32)]
    coords=np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1).reshape(-1,3)
    emit('volume','Preparing 138,240 air samples around this car')
    with torch.inference_mode():
        data=build_domin_volume_datadict(cfg,directory,'',1,device,reference_mesh=pv.PolyData(coords))
        data['global_params_values'][:,0,:]=38.889
        factors,_=load_scaling_factors_tensors(cfg,device)
        emit('volume','Predicting air direction and speed on the GPU')
        output=domino_volume_test_step(data,MODEL,cfg,factors,device,2048)
        torch.cuda.synchronize()
        values=output[0].cpu().numpy();sdf=data['sdf_nodes'][0,:,0].cpu().numpy()
    if not np.isfinite(values).all():raise ValueError('Volume model returned non-finite values')
    shape=tuple(len(a) for a in axes);velocity=values[:,:3].reshape(*shape,3)
    fluid_speeds=np.linalg.norm(values[sdf>.003,:3],axis=1)
    emit('streamlines','Tracing visible paths through the predicted air movement')
    paths=trace_streamlines(axes,velocity,sdf.reshape(shape),np.asarray(origin))
    if len(paths)<5:raise ValueError('Too few usable predicted streamlines')
    np.savez_compressed(directory/'volume-field.npz',x=axes[0],y=axes[1],z=axes[2],fields=values,sdf=sdf)
    result={'schemaVersion':'zephyr.airflow.v1','geometryId':geometry_id,'meshHash':mesh_hash(mesh),'createdAt':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'source':'nvidia-volume','model':'DoMINO volume 0.501','checkpointSha256':checks[0].actual_sha256,'upstreamCommit':pin,'units':'m/s','streamVelocityMps':38.889,'gridShape':list(shape),'paths':paths,'seconds':round(time.perf_counter()-started,3),'speedRangeMps':[float(fluid_speeds.min()),float(fluid_speeds.max())],'playbackTimeScale':.055,'note':'Steady AI-predicted velocity field; particles trace that field in slow motion. Not a time-resolved CFD simulation.'}
    (directory/'airflow.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False),encoding='utf-8')
    del data,output;torch.cuda.empty_cache()
    return result

if __name__=='__main__':
    import pyvista as pv
    os.environ['WARP_CACHE_PATH']=str(ROOT.parent/'.cache/warp')
    sys.path.insert(0,str(ROOT/'scripts/windows_compat'))
    mesh=pv.read(ROOT/'.local/physicsnemo-cfd/workflows/domino_design_sensitivities/geometries/drivaer_1.stl')
    origin=np.array([(mesh.bounds[0]+mesh.bounds[1])/2,0,mesh.bounds[4]])
    from zephyr.local.locks import acquire_lock
    with acquire_lock(ROOT/'.local/runs/gpu.lock'),acquire_lock(ROOT/'.local/runs/worker-gpu.lock'):
        result=predict_airflow(mesh,origin,ROOT/'.local/volume-smoke','drivaer-1',lambda stage,detail,**k:print(stage,detail,flush=True))
    print('VOLUME_RESULT',json.dumps({k:v for k,v in result.items() if k!='paths'}),'paths',len(result['paths']),flush=True)
