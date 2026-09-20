"""Check all installed surfaces and bounded body tools against pinned input metadata."""
import argparse
import json
from pathlib import Path
import pyvista as pv
from omegaconf import OmegaConf
from zephyr.artifacts import _file_sha256
from zephyr.local.cars import CARS, mesh_path
from zephyr.local.compatibility import check_surface_input
from zephyr.local.geometry import BODY_HANDLES, deform

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
if args.output.exists(): parser.error('Choose a fresh output to preserve evidence')
root=Path(__file__).resolve().parents[1]
config=root/'.local/domino-assets/config.yaml'
box=OmegaConf.to_container(OmegaConf.load(config).data.bounding_box_surface)
rows=[]
for car in CARS:
    path=mesh_path(car['id']);mesh=pv.read(path)
    row={'geometryId':car['id'],'inputSha256':_file_sha256(path),
         'baseline':check_surface_input(mesh,box,experimental=car['experimental']),'candidates':[]}
    if car['category']=='car':
        for handle in BODY_HANDLES:
            for sign in (-1,1):
                candidate,_,_=deform(mesh,sign*.004,.004,handle)
                row['candidates'].append({'handle':handle,'amplitudeMm':sign*4,
                    **check_surface_input(candidate,box,experimental=car['experimental'])})
    rows.append(row)
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps({'trainingConfigSha256':_file_sha256(config),
    'scope':'Static input contract only, not geometry acceptance, model inference or accuracy.', 'cases':rows},indent=2))
print(json.dumps({'baselines':len(rows),'candidates':sum(len(r['candidates']) for r in rows),
    'outsideTrainingBounds':[r['geometryId'] for r in rows if not r['baseline']['withinTrainingBounds']]}))
