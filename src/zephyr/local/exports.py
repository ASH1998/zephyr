"""Export the evaluated full-resolution inference mesh with its evidence."""
from io import BytesIO
import json
import tempfile
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def candidate_bundle(directory):
    import pyvista as pv
    from zephyr.artifacts import _file_sha256
    from zephyr.local.conversion import mesh_hash
    evidence=json.loads((directory/'evidence.json').read_text(encoding='utf-8'))
    path=directory/'evaluate.vtk'
    if evidence['forces'].get('candidateDragN') is None or not path.is_file():
        raise ValueError('No freshly evaluated candidate is available')
    expected=evidence.get('artifacts',{}).get('evaluate.vtk',{}).get('sha256')
    if not expected or _file_sha256(path)!=expected:
        raise ValueError('Candidate artifact hash mismatch')
    mesh=pv.read(path)
    if mesh_hash(mesh)!=evidence['provenance'].get('candidateMeshHash'):
        raise ValueError('Candidate geometry does not match run evidence')
    output=BytesIO()
    with tempfile.TemporaryDirectory(dir=directory) as temporary:
        target=Path(temporary)/'candidate.stl';mesh.save(target,binary=True)
        with ZipFile(output,'w',ZIP_DEFLATED) as bundle:
            bundle.writestr('candidate.stl',target.read_bytes())
            bundle.writestr('evidence.json',json.dumps(evidence,indent=2))
            bundle.writestr('README.txt',
                'Zephyr evaluated inference surface. Units: metres; original upstream X/Y/Z coordinates.\n'
                'STL stores triangles at float32 precision, without units or shared topology metadata.\n'
                'The original evaluate.vtk is included for full precision, topology and predicted fields.\n'
                'This is not the detailed visual GLB or a manufacturing-ready design.\n'
                f"Recorded local decision: {evidence['trust']['decision']}. {evidence['trust']['reason']}\n"
                'Independent physical validation is required. A refused candidate is exported for inspection only.\n')
            bundle.writestr('evaluate.vtk',path.read_bytes())
    return output.getvalue()
