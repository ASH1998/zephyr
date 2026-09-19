"""Prepare NASA aircraft as uniformly scaled, detailed visualization assets."""
from pathlib import Path
import trimesh,numpy as np,pyvista as pv,json
ROOT=Path(__file__).resolve().parents[1];root=ROOT/'.local/vehicle-sources';out=ROOT/'frontend/public/models/vehicles'
for id in ['x57','global-hawk']:
 source=trimesh.load(root/'nasa'/(id+'.glb'));scene=trimesh.Scene();parts=[]
 for i,m in enumerate(source.dump()):
  name=f'{id}-{i}'
  if id=='global-hawk':
   v=m.vertices.copy();m.vertices=np.column_stack((-v[:,2],v[:,1],v[:,0]))
  if len(m.faces)>200000:
   poly=pv.PolyData(m.vertices,np.column_stack((np.full(len(m.faces),3),m.faces))).clean()
   poly=pv.PolyData(poly.points,poly.faces).triangulate().decimate_pro(.92,preserve_topology=True,splitting=False)
   m=trimesh.Trimesh(poly.points,poly.faces.reshape(-1,4)[:,1:],process=False)
  if not isinstance(m.visual,trimesh.visual.TextureVisuals):m.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(name='airframe',baseColorFactor=[185,208,220,255],metallicFactor=.3,roughnessFactor=.38))
  parts.append((name,m))
 v=np.concatenate([m.vertices for _,m in parts]);lo=v.min(0);hi=v.max(0);scale=3.3/(hi[2]-lo[2]);shift=np.array([-(lo[0]+hi[0])/2,-lo[1],-(lo[2]+hi[2])/2])
 for name,m in parts:m.vertices=(m.vertices+shift)*scale;scene.add_geometry(m,node_name=name,geom_name=name)
 (out/(id+'.glb')).write_bytes(scene.export(file_type='glb'));scene.to_geometry().export(root/(id+'-visual.ply'))
 print(id,'bounds',scene.bounds.round(3),'scale',scale,'faces',sum(len(m.faces) for _,m in parts),flush=True)
