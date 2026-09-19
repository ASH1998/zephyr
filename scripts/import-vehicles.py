"""Import licensed vehicle meshes; retain authored geometry, normals and materials."""
from pathlib import Path
import struct, json, re, configparser
import numpy as np
import trimesh
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'.local/vehicle-sources'
OUT=ROOT/'frontend/public/models/vehicles'
OUT.mkdir(parents=True,exist_ok=True)

def ogre(path):
 b=path.read_bytes()
 def chunk(p):return struct.unpack_from('<HI',b,p)
 def geometry(p):
  typ,size=chunk(p);end=p+size;n=struct.unpack_from('<I',b,p+6)[0];p+=10;elements=[];buffers={}
  while p<end:
   t,s=chunk(p)
   if t==0x5100:
    q=p+6
    while q<p+s:
     _,ss=chunk(q);elements.append(struct.unpack_from('<5H',b,q+6));q+=ss
   elif t==0x5200:
    source,stride=struct.unpack_from('<HH',b,p+6);buffers[source]=(p+16,stride)
   p+=s
  attrs={}
  for source,typ,sem,offset,index in elements:
   if sem not in (1,4,7) or index:continue
   count={0:1,1:2,2:3,3:4}.get(typ)
   if count:
    start,stride=buffers[source];attrs[sem]=np.ndarray((n,count),dtype='<f4',buffer=b,offset=start+offset,strides=(stride,4)).copy()
  return attrs
 p=b.index(b'\n')+1;_,total=chunk(p);p+=7;shared=None;parts=[]
 while p+6<len(b):
  typ,size=chunk(p)
  if size<6:raise ValueError('Invalid Ogre chunk')
  if typ==0x5000:shared=geometry(p)
  if typ==0x4000:
   q=p+6;e=b.index(b'\n',q);name=b[q:e].decode();q=e+1
   use,count,is32=struct.unpack_from('<?I?',b,q);q+=6
   faces=np.frombuffer(b,dtype='<u4' if is32 else '<u2',count=count,offset=q).copy().reshape(-1,3);q+=count*(4 if is32 else 2)
   attrs=shared if use else geometry(q)
   parts.append((name,attrs,faces))
  p+=size
 return parts

PAINT={'hatchback':[70,129,180,255],'wagon':[130,150,163,255],'suv':[108,125,94,255],'coupe':[166,174,185,255],'sports':[234,163,34,255]}

def racing(kind,ident):
 parts=[];base=SOURCE/'stuntrally-v1/data/cars'/ident;tex=SOURCE/'stuntrally/data/cars'/ident/'textures'
 cfg=configparser.ConfigParser(inline_comment_prefixes=('#',));cfg.read_string('[default]\n'+re.sub(r'\[\s*([^]]+?)\s*\]',r'[\1]',(SOURCE/'stuntrally/data/carsim/normal/cars'/f'{ident}.car').read_text()))
 for path in sorted(base.glob('*.mesh')):
  if '_brake' in path.stem:continue
  wheel='_wheel' in path.stem
  offsets=[np.zeros(3)]
  if wheel:
   axles=['F','R'] if path.stem.endswith('_wheel') else ['F' if path.stem.endswith('_front') else 'R']
   offsets=[]
   for axle in axles:
    for side in ['R','L']:
     v=np.array([float(x) for x in cfg[f'wheel-{axle}{side}']['position'].split(',')]);offsets.append((v,side))
  for name,a,faces in ogre(path):
   for idx,offset in enumerate(offsets):
    v=a[1].copy();norm=a.get(4);norm=norm.copy() if norm is not None else None
    # Apply the source car's rot_fix; wheel axles are local X.
    if not wheel and cfg.get('model_ofs','rot_fix',fallback='off')!='on':
     v[:,[1,2]]*=-1
     if norm is not None:norm[:,[1,2]]*=-1
    if wheel or cfg.get('model_ofs','rot_fix',fallback='off')=='on':
     v=v[:,[2,1,0]];v[:,0]*=-1
     if norm is not None:norm=norm[:,[2,1,0]];norm[:,0]*=-1
    if wheel:
     pos,side=offset
     if side=='L':v[:,[0,2]]*=-1;norm[:,[0,2]]*=-1
     v+=np.array([-pos[1],pos[2],pos[0]])
    if kind=='wagon':
     # Documented touring derivative: lengthen the passenger/cargo section;
     # preserve round wheels and the complete original front end.
     if wheel:
      if pos[1]<0:v[:,0]+=.65
     else:
      t=np.clip((v[:,0]+.25)/1.2,0,1);v[:,0]+=.65*t
      norm=None
    m=trimesh.Trimesh(v,faces,vertex_normals=norm,process=False)
    lower=name.lower();image=None
    if 'carpaint' in lower:
     color=PAINT[kind];metal=.4;rough=.3
     tp=tex/(f'{ident}_body_white.png' if ident=='S8' and kind=='wagon' else f'{ident}_body_red.png')
     if tp.exists():image=Image.open(tp).convert('RGBA');color=[255]*4 if kind=='hatchback' else PAINT[kind]
    elif 'glass' in lower:color=[20,36,48,255];metal=.15;rough=.18
    else:
     color=[180,180,180,255];metal=.15;rough=.65
     # Interior meshes include grille, headlights, badges and wheel arches.
     candidates=[tex/(name+'.png'),tex/(name+'.jpg'),tex/(path.stem+'.png'),tex/(path.stem+'.jpg')]
     if wheel:candidates=[tex/f'{ident}_wheel.png',tex/f'{ident}_Tire.png']+candidates
     tp=next((p for p in candidates if p.exists()),None)
     if tp:image=Image.open(tp).convert('RGBA');color=[255]*4
    mat=trimesh.visual.material.PBRMaterial(name=name,baseColorFactor=color,baseColorTexture=image,metallicFactor=metal,roughnessFactor=rough,doubleSided=True)
    uv=a.get(7)
    if uv is not None:uv=uv.copy();uv[:,1]=1-uv[:,1]
    m.visual=trimesh.visual.TextureVisuals(uv=uv,material=mat)
    parts.append((f'{path.stem}-{name}-{idx}',m))
 return parts

def van():
 parts=[];base=SOURCE/'webots'
 names=['coachwork','coachwork_front','roof_and_rear','plastic','windows','mirrors','rear_door_joints','handles','bumper','front_radiator','front_light','tail_lights','braking_side_lights','braking_top_light','backwards_white_lights','rear_fog_lights','left_indicator','right_indicator']
 for name in names:
  m=trimesh.load(base/(name+'.obj'),force='mesh',process=False)
  v=m.vertices.copy()
  # Original OBJ: right=X, up=Y, front=Z. Viewer: front=-X, up=Y.
  m.vertices=np.column_stack((-v[:,2],v[:,1],v[:,0]))
  if name=='front_radiator':m.vertices[:,1]-=.136
  color=[195,205,213,255];metal=.25;rough=.38
  if name in ['plastic','rear_door_joints','handles','bumper','front_radiator']:color=[32,37,41,255];metal=0;rough=.8
  if name in ['windows','mirrors']:color=[20,39,52,255];metal=.12;rough=.19
  if name in ['front_light','backwards_white_lights']:color=[215,235,249,255];metal=.6;rough=.2
  if name in ['tail_lights','braking_side_lights','braking_top_light','rear_fog_lights']:color=[180,10,15,255];metal=.1;rough=.28
  if 'indicator' in name:color=[240,139,20,255]
  m.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(name=name,baseColorFactor=color,metallicFactor=metal,roughnessFactor=rough,doubleSided=True));parts.append((name,m))
 # Reuse licensed detailed SUV wheels, scaled uniformly to the van tire size.
 for name,a,faces in ogre(SOURCE/'stuntrally-v1/data/cars/HR/HR_wheel.mesh'):
  v=a[1].copy();v=v[:,[2,1,0]];v[:,0]*=-1;radius=(v[:,1].max()-v[:,1].min())/2;v*=.4/radius
  for x in [-4.325,0]:
   for side in [-1,1]:
    vv=v.copy()
    if side<0:vv[:,[0,2]]*=-1
    vv+=np.array([x,0,side*.85])
    m=trimesh.Trimesh(vv,faces,process=False);m.visual=trimesh.visual.TextureVisuals(uv=np.column_stack((a[7][:,0],1-a[7][:,1])),material=trimesh.visual.material.PBRMaterial(name='wheel',baseColorTexture=Image.open(SOURCE/'stuntrally/data/cars/HR/textures/HR_wheel.png'),metallicFactor=.05,roughnessFactor=.7));parts.append((f'wheel{x}{side}',m))
 return parts

def write(kind,parts):
 vertices=np.concatenate([m.vertices for _,m in parts]);bounds=np.array([vertices.min(0),vertices.max(0)]);center=(bounds[0]+bounds[1])/2
 shift=np.array([-center[0],-bounds[0,1],-center[2]])
 # Van is a long Sprinter; keep original proportions, uniformly scale to fit the model domain.
 scale=min(1,5.5/(bounds[1,0]-bounds[0,0]),2.65/(bounds[1,1]-bounds[0,1]))
 scene=trimesh.Scene()
 for name,m in parts:m.vertices=(m.vertices+shift)*scale;scene.add_geometry(m,node_name=name,geom_name=name)
 (OUT/(kind+'.glb')).write_bytes(scene.export(file_type='glb'))
 scene.to_geometry().export(SOURCE/(kind+'-visual.ply'))
 print(kind,'bounds',scene.bounds.round(3).tolist(),'triangles',sum(len(m.faces) for _,m in parts),flush=True)
if __name__=='__main__':
 for kind,ident in [('hatchback','S8'),('wagon','S8'),('suv','HR'),('coupe','XZ'),('sports','Y7')]:write(kind,racing(kind,ident))
 write('van',van())
