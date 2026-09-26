"""Allowlisted local car styles. Detailed licensed visual assets with derived closed inference surfaces."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
CARS=[
 {'id':'drivaer-1','label':'DrivAer sedan','description':'Official NVIDIA sample','experimental':False,'preview':'/models/drivaer-preview.json'},
 {'id':'hatchback','label':'Impreza hatchback','description':'Detailed hatchback · gold alloy wheels','experimental':True},
 {'id':'suv','label':'Hummer SUV','description':'Wide off-road body · upright cabin','experimental':True},
 {'id':'wagon','label':'Touring wagon','description':'Adapted Impreza · extended roof and cargo section','experimental':True},
 {'id':'coupe','label':'M3 coupe','description':'Two-door coupe · detailed grille and bodywork','experimental':True},
 {'id':'sports','label':'Veneno sports car','description':'Low supercar · wide stance and rear wing','experimental':True},
 {'id':'van','label':'Sprinter van','description':'Long cargo van · detailed doors and front end','experimental':True},
 {'id':'x57','label':'NASA X-57 plane','description':'Electric research plane · scaled to 3.3 m wingspan','experimental':True,'category':'aircraft'},
 {'id':'global-hawk','label':'NASA Global Hawk','description':'Long-wing research aircraft · scaled to 3.3 m wingspan','experimental':True,'category':'aircraft'},
]
for car in CARS:
 car.setdefault('category','car')
 car.setdefault('preview','/models/cars/'+car['id']+'.json')
 car['airflow']='/models/airflow/'+car['id']+'.json'
IDS=frozenset(c['id'] for c in CARS)
def car_definition(geometry_id):
 if isinstance(geometry_id,str) and geometry_id.startswith('upload-'):
  from zephyr.local.uploads import definition
  return definition(geometry_id)
 if not isinstance(geometry_id,str) or geometry_id not in IDS:raise ValueError('Unknown car style')
 return next(c for c in CARS if c['id']==geometry_id)
def mesh_path(geometry_id):
 car_definition(geometry_id)
 if geometry_id.startswith('upload-'):
  from zephyr.local.uploads import ROOT as UPLOAD_ROOT
  return UPLOAD_ROOT/geometry_id/'surface.vtp'
 return ROOT/'.local/physicsnemo-cfd/workflows/domino_design_sensitivities/geometries/drivaer_1.stl' if geometry_id=='drivaer-1' else ROOT/'.local/cars'/(geometry_id+'.vtp')

def validate_support(geometry_id, mode):
 car = car_definition(geometry_id)
 if car.get('support') == 'baseline-only' and mode != 'analysis':
  raise ValueError('This uploaded car supports baseline analysis only: ' + car['supportReason'])
 return car
