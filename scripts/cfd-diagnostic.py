"""Linux/OpenFOAM 1912 diagnostic. Coarse RANS is NOT validation of a tiny delta.

Inputs: an unused output directory containing baseline.stl and candidate.stl,
exported in metres with the same ground translation. Requires --live.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

HEADER='FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }\n'


def main():
    p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--directory',type=Path,required=True)
    args=p.parse_args()
    if not args.live:p.error('CFD execution requires --live')
    root=args.directory.resolve()
    template=Path('/usr/share/doc/openfoam-examples/examples/incompressible/simpleFoam/motorBike')
    report={'solver':'OpenFOAM 1912 simpleFoam kOmegaSST','purpose':'coarse independent pipeline diagnostic',
            'physicalValidation':'inconclusive','inletMps':38.889,'densityKgM3':1.205,
            'limitations':['No mesh convergence study','No boundary-layer cells','Fixed nonrotating wheels',
                          'Coarse mesh cannot establish a 0.375 mm design improvement','RANS differs from model training flow'],
            'cases':{}}
    # Freeze assumptions before running either geometry.
    (root/'plan.json').write_text(json.dumps(report,indent=2))
    for name in ['baseline','candidate']:
        case=root/name
        if case.exists():raise ValueError('Use a fresh directory; existing CFD evidence is not overwritten')
        case.mkdir()
        for folder in ['system','constant','0.orig']:
            shutil.copytree(template/folder,case/('0' if folder=='0.orig' else folder))
        for packed in case.rglob('*.gz'):
            packed.with_suffix('').write_bytes(gzip.decompress(packed.read_bytes()))
        surface=case/'constant/triSurface/zephyr.stl'
        shutil.copyfile(root/(name+'.stl'),surface)
        # Keep tutorial patch-group name for its wall boundary conditions.
        snappy=case/'system/snappyHexMeshDict';s=snappy.read_text()
        s=s.replace('motorBike.obj','zephyr.stl').replace('addLayers       true','addLayers       false')
        s=re.sub(r'features\s*\(.*?\);','features ();',s,count=1,flags=re.S)
        s=s.replace('level (5 6)','level (2 3)').replace('levels ((1E15 4))','levels ((1E15 1))')
        s=s.replace('min  (-1.0 -0.7 0.0)','min  (-2 -2 0)').replace('max  ( 8.0  0.7 2.5)','max  (10 2 3)')
        s=s.replace('explicitFeatureSnap true','explicitFeatureSnap false').replace('implicitFeatureSnap false','implicitFeatureSnap true')
        snappy.write_text(s)
        quality=case/'system/meshQualityDict'
        quality.write_text(quality.read_text()+'\nmaxBoundarySkewness 3.5;\nmaxInternalSkewness 3.5;\n')
        block=case/'system/blockMeshDict';s=block.read_text()
        s=re.sub(r'vertices\s*\(.*?\);','vertices ((-15 -10 0) (35 -10 0) (35 10 0) (-15 10 0) (-15 -10 10) (35 -10 10) (35 10 10) (-15 10 10));',s,count=1,flags=re.S)
        s=s.replace('(20 8 8)','(50 20 10)');block.write_text(s)
        initial=case/'0/include/initialConditions';s=initial.read_text().replace('(20 0 0)','(38.889 0 0)').replace('0.24','0.2269').replace('1.78','1.37');initial.write_text(s)
        # Incompressible pressure is kinematic; rhoInf scales forces to N.
        (case/'system/controlDict').write_text(HEADER+'''application simpleFoam;
startFrom startTime; startTime 0; stopAt endTime; endTime 300; deltaT 1;
writeControl timeStep; writeInterval 300; purgeWrite 1; writeFormat binary;
writePrecision 10; writeCompression off; timeFormat general; timePrecision 6;
runTimeModifiable false;
functions { aerodynamicForces { type forces; libs ("libforces.so");
patches ("motorBike.*"); rho rhoInf; rhoInf 1.205; CofR (0 0 0);
writeControl timeStep; writeInterval 1; log true; } }
''')
        entry={'inputSha256':hashlib.sha256(surface.read_bytes()).hexdigest(),'commands':[],'status':'running'}
        report['cases'][name]=entry
        for command in ['blockMesh','snappyHexMesh','checkMesh','simpleFoam']:
            started=time.monotonic()
            with (case/('log.'+command)).open('w') as log:
                try:
                    result=subprocess.run([command,*(['-overwrite'] if command=='snappyHexMesh' else [])],cwd=case,stdout=log,stderr=subprocess.STDOUT,timeout=600)
                    code=result.returncode
                except subprocess.TimeoutExpired:code=124
            entry['commands'].append({'command':command,'exitCode':code,'seconds':time.monotonic()-started})
            print(name,command,code,flush=True)
            (root/'report.json').write_text(json.dumps(report,indent=2))
            if code:entry['status']='failed';break
            if command=='checkMesh' and 'Mesh OK.' not in (case/'log.checkMesh').read_text():
                entry['status']='mesh-quality-failed';break
        else:
            entry['status']='diagnostic-complete'
            files=list((case/'postProcessing').glob('aerodynamicForces/*/force.dat'))
            if files:
                rows=[re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',line) for line in files[0].read_text().splitlines() if line and not line.startswith('#')]
                drag=[float(row[1]) for row in rows[-50:]]
                if drag:entry.update(last50MeanDragN=sum(drag)/len(drag),last50RangeN=max(drag)-min(drag),forceSamples=len(rows))
        (root/'report.json').write_text(json.dumps(report,indent=2))


if __name__=='__main__':main()
