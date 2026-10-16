#!/usr/bin/env python3
"""Opt-in, source-safe glTF tangent VEC4 packaging around the M29 exporter.

Mirrored UV orientation is split using derived OBJ normal-index seams; the
original OBJ, original multi-material exporter and referenced source maps stay
untouched. This is area-weighted tangent math, not exact MikkTSpace, AO,
physical Android shading verification, or production approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
from tempfile import TemporaryDirectory

from engine import read_obj
from vq_model_tools import check_gltf
from vq_multimaterial_export import export as export_preserved_materials
from vq_tangent_space import generate_tangents, triangle_handedness

def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _derived_obj(src, dest):
    verts, uv, normals, faces = read_obj(src)
    signs = []
    for face in faces:
        if any(c[1] is None for c in face):
            raise ValueError('Tangent export requires UV on every face corner')
        signs.append(triangle_handedness(
            [verts[c[0]][:3] for c in face],
            [uv[c[1]][:2] for c in face]))
    duplicate_normals = bool(normals and -1 in signs)
    rows = []
    injected = False
    face_index = 0
    for line in src.read_text(encoding='utf-8').splitlines(keepends=True):
        parts = line.partition('#')[0].strip().split()
        kind = parts[0] if parts else ''
        if kind == 'f':
            if duplicate_normals and not injected:
                rows.extend('vn ' + ' '.join(format(v, '.17g') for v in n[:3]) + '\n'
                            for n in normals)
                injected = True
            face = faces[face_index]
            if duplicate_normals and signs[face_index] < 0:
                refs = []
                for vi, ui, ni in face:
                    refs.append(f'{vi+1}/{ui+1}/{ni+len(normals)+1}'
                                if ni is not None else f'{vi+1}/{ui+1}')
                rows.append('f ' + ' '.join(refs) + '\n')
            else:
                rows.append(line)
            face_index += 1
        else:
            rows.append(line)
    if face_index != len(faces):
        raise ValueError('OBJ face ordering changed during derived seam split')
    dest.write_text(''.join(rows), encoding='utf-8')
    return {'source_sha256': _sha(src), 'derived_obj_sha256': _sha(dest),
            'mirrored_uv_faces': signs.count(-1),
            'normal_index_seam_split': duplicate_normals}

def _unpack(doc, payload, accessor_id, components, component_type):
    acc = doc['accessors'][accessor_id]
    if acc['type'] != {1:'SCALAR',2:'VEC2',3:'VEC3'}[components] or acc['componentType'] != component_type:
        raise ValueError('Unexpected source glTF attribute format')
    view = doc['bufferViews'][acc['bufferView']]
    if 'byteStride' in view:
        raise ValueError('Interleaved source glTF needs explicit tangent adapter')
    start = view.get('byteOffset',0) + acc.get('byteOffset',0)
    fmt = 'f' if component_type == 5126 else 'I'
    length = acc['count']*components
    if start < 0 or start + length*4 > len(payload):
        raise ValueError('Source glTF attribute outside verified binary')
    return struct.unpack_from('<'+fmt*length,payload,start)

def export(src, out, *, source_gltf=None, source_manifest=None, tangents=False):
    src, out = Path(src), Path(out)
    if not tangents:
        return export_preserved_materials(src, out,
            source_gltf=source_gltf, source_manifest=source_manifest)
    if src.is_symlink() or not src.is_file() or out.resolve() == src.resolve():
        raise ValueError('Tangent source must be a distinct real OBJ file')
    if out.exists():
        raise ValueError('Refuse to overwrite an existing tangent output')
    if source_gltf is not None and out.parent.resolve() == Path(source_gltf).parent.resolve():
        raise ValueError('Output directory must differ from original material source')
    with TemporaryDirectory(prefix='vq-tangent-') as temp:
        root = Path(temp)
        derived = root/'derived.obj'
        provenance = _derived_obj(src, derived)
        stage = root/'package'
        stage.mkdir()
        staged_gltf = stage/out.name
        doc = export_preserved_materials(derived, staged_gltf,
            source_gltf=source_gltf, source_manifest=source_manifest)
        binary = stage/(out.stem+'.bin')
        payload = bytearray(binary.read_bytes())
        tangent_vertices = 0
        for primitive in doc['meshes'][0]['primitives']:
            attrs = primitive['attributes']
            pos = _unpack(doc,payload,attrs['POSITION'],3,5126)
            normals = _unpack(doc,payload,attrs['NORMAL'],3,5126)
            uv = _unpack(doc,payload,attrs['TEXCOORD_0'],2,5126)
            indices = _unpack(doc,payload,primitive['indices'],1,5125)
            generated = generate_tangents(pos,normals,uv,indices)
            while len(payload)%4: payload.append(0)
            offset = len(payload)
            payload.extend(struct.pack('<'+'f'*len(generated),*generated))
            doc['bufferViews'].append({'buffer':0,'byteOffset':offset,
                'byteLength':len(generated)*4,'target':34962})
            doc['accessors'].append({'bufferView':len(doc['bufferViews'])-1,
                'componentType':5126,'count':len(generated)//4,'type':'VEC4'})
            attrs['TANGENT'] = len(doc['accessors'])-1
            tangent_vertices += len(generated)//4
        doc['buffers'][0]['byteLength'] = len(payload)
        doc['extras'].update(provenance)
        doc['extras'].update({'source_sha256':provenance['source_sha256'],
            'tangent_attribute_generated':True,'tangent_vertices':tangent_vertices,
            'tangent_basis_math_checked':True,'exact_mikktspace_verified':False,
            'tangent_space_normals_verified':False,'android_emulator_tested':False,
            'production_approved':False})
        staged_gltf.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
        binary.write_bytes(payload)
        report = stage/(out.stem+'_export_review.json')
        review = json.loads(report.read_text(encoding='utf-8'))
        review.update(provenance)
        review.update({'source_sha256':provenance['source_sha256'],
            'gltf_sha256':_sha(staged_gltf),'binary_sha256':_sha(binary),
            'tangent_attribute_generated':True,'tangent_vertices':tangent_vertices,
            'exact_mikktspace_verified':False,'android_emulator_tested':False,
            'production_approved':False})
        report.write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
        if not check_gltf(staged_gltf)['structural_smoke_passed']:
            raise ValueError('Tangent glTF failed structural QA')
        # All candidate bytes are validated before copying out of staging.
        outputs = [p for p in stage.rglob('*') if p.is_file()]
        for p in outputs:
            dest = out.parent/p.relative_to(stage)
            if dest.exists() or dest.is_symlink():
                raise ValueError('Refuse to overwrite existing package file')
        for p in outputs:
            dest = out.parent/p.relative_to(stage)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,dest)
        return doc

def main():
    parser = argparse.ArgumentParser(description='VQ opt-in glTF tangent VEC4 export')
    parser.add_argument('--obj',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--source-gltf',type=Path)
    parser.add_argument('--source-manifest',type=Path)
    parser.add_argument('--tangents',action='store_true')
    args = parser.parse_args()
    doc = export(args.obj,args.out,source_gltf=args.source_gltf,
                 source_manifest=args.source_manifest,tangents=args.tangents)
    print('VQ_TANGENT_EXPORT_PASS',doc['extras'].get('tangent_attribute_generated',False),
          'triangles',doc['extras']['triangles'])

if __name__ == '__main__':
    main()
