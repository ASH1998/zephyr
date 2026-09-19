"""Build a watertight, simplified inference surface from each detailed visual mesh."""
from pathlib import Path
import numpy as np, pyvista as pv, trimesh, json
from scipy import ndimage
from zephyr.local.conversion import ROTATION,mesh_hash
from zephyr.local.geometry import rear_basis
ROOT=Path(__file__).resolve().parents[1]
import sys
from zephyr.local.cars import car_definition
for kind in (sys.argv[1:] or ['hatchback','wagon','suv','coupe','sports','van']):
 car_definition(kind)
 (ROOT/'.local/cars').mkdir(parents=True,exist_ok=True)
 (ROOT/'frontend/public/models/cars').mkdir(parents=True,exist_ok=True)
 visual=trimesh.load(ROOT/'.local/vehicle-sources'/f'{kind}-visual.ply',force='mesh')
 vox=visual.voxelized(.035);matrix=np.pad(vox.matrix,3)
 solid=ndimage.binary_fill_holes(ndimage.binary_closing(matrix,iterations=2))
 grid=pv.ImageData(dimensions=solid.shape,spacing=(.035,)*3,origin=vox.translation-3*.035)
 grid.point_data['solid']=ndimage.gaussian_filter(solid.astype(float),.65).ravel(order='F')
 model=grid.contour([.5],scalars='solid').extract_largest().triangulate().clean(tolerance=1e-7,absolute=True)
 print(kind,'raw',model.n_open_edges,flush=True)
 model=model.smooth(n_iter=12,relaxation_factor=.08,boundary_smoothing=False)
 reduced=model.decimate_pro(max(0,1-18000/model.n_points),preserve_topology=True,splitting=False,boundary_vertex_deletion=False)
 if reduced.n_open_edges==0:model=reduced
 # Align the simplified geometry with the canonical visual coordinate frame.
 # All shifts are recorded and applied identically to the detailed GLB.
 ground=float(model.points[:,1].min());center=float((model.bounds[0]+model.bounds[1])/2);side=float((model.bounds[4]+model.bounds[5])/2)
 display=model.points-np.array([center,ground,side])
 upstream=display@ROTATION;upstream[:,0]+=.5*(display[:,0].max()-display[:,0].min())-.8;upstream[:,2]-=.32
 model.points=upstream;model=model.compute_normals(auto_orient_normals=True,consistent_normals=True,split_vertices=False)
 if model.n_open_edges:
  model.save(ROOT/'.local/vehicle-sources/debug.vtp');raise ValueError(f'{kind} open edges {model.n_open_edges}')
 model.save(ROOT/'.local/cars'/f'{kind}.vtp')
 origin=np.array([(model.bounds[0]+model.bounds[1])/2,0,model.bounds[4]])
 _,protected,_=rear_basis(model.points)
 h=mesh_hash(model)
 value={'schemaVersion':'zephyr.geometry-preview.v1','geometryId':kind,'units':'m','meshHash':h,'positions':np.round((model.points-origin)@ROTATION.T,6).ravel().tolist(),'triangles':model.faces.reshape(-1,4)[:,1:].ravel().tolist(),'protectedMask':protected.astype(int).tolist(),'visual':{'url':f'/models/vehicles/{kind}.glb','offset':[-center,-ground,-side]},'provenance':'Detailed licensed visual asset; simplified watertight surface derived from that asset for NVIDIA inference.'}
 (ROOT/'frontend/public/models/cars'/f'{kind}.json').write_text(json.dumps(value,separators=(',',':')))
 print(kind,model.n_points,model.n_cells,'hash',h,'offset',value['visual']['offset'],flush=True)
