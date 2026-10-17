#!/usr/bin/env python3
"""VEYLQUORIN bounded shape-only sculpt of real GLB 2.0 mesh primitives.

Applies deterministic local-space falloff displacements to glTF mesh primitives,
without changing triangle indices, UVs, skin weights, skeletons, animations
or source bytes. Output is a separate review-only GLB.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct

MAX_BYTES = 256 * 1024 * 1024
MAX_VERTICES_PER_PRIMITIVE = 500_000
MAX_LAYERS = 16
SAFE_NAME = re.compile(r"^[A-Za-z0-9_:-]{1,100}$")
FLOAT3 = struct.Struct('<fff')
COMPONENTS = {5121: ('B', 1), 5123: ('H', 2), 5125: ('I', 4)}

def _unpack(path):
    raw = Path(path).read_bytes()
    if not 28 <= len(raw) <= MAX_BYTES:
        raise ValueError('GLB outside bounded size')
    magic, version, total = struct.unpack_from('<4sII', raw)
    if magic != b'glTF' or version != 2 or total != len(raw):
        raise ValueError('Not a valid GLB 2.0 header')
    at, chunks = 12, []
    while at < len(raw):
        if at + 8 > len(raw):
            raise ValueError('Truncated GLB chunk header')
        n, tag = struct.unpack_from('<I4s', raw, at)
        at += 8
        if n % 4 or at + n > len(raw):
            raise ValueError('Misaligned/truncated GLB chunk')
        chunks.append((tag, raw[at:at+n]))
        at += n
    if [tag for tag, _ in chunks] != [b'JSON', b'BIN\x00']:
        raise ValueError('Only single-buffer JSON+BIN GLBs are supported')
    doc = json.loads(chunks[0][1].decode('utf-8'))
    if len(doc.get('buffers', [])) != 1 or 'uri' in doc['buffers'][0]:
        raise ValueError('GLB must contain one embedded binary buffer')
    if doc['buffers'][0]['byteLength'] > len(chunks[1][1]):
        raise ValueError('Declared GLB binary data exceeds actual buffer')
    return raw, doc, bytearray(chunks[1][1])

def _write(doc, binary):
    doc['buffers'][0]['byteLength'] = len(binary)
    j = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    j += b' ' * (-len(j) % 4)
    b = bytes(binary)
    b += b'\x00' * (-len(b) % 4)
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(j) + len(b))
            + struct.pack('<I4s', len(j), b'JSON') + j
            + struct.pack('<I4s', len(b), b'BIN\x00') + b)

def _accessor(doc, binary, index, kind):
    if type(index) is not int or index < 0 or index >= len(doc.get('accessors', [])):
        raise ValueError('Missing accessor')
    a = doc['accessors'][index]
    if a.get('sparse') is not None or a.get('type') != kind:
        raise ValueError('Unsupported sparse/accessor type')
    comp = a.get('componentType')
    if kind == 'VEC3':
        if comp != 5126:
            raise ValueError('Positions/normals must be float32 VEC3')
        fmt, width = '<fff', 12
    elif comp in COMPONENTS:
        letter, width = COMPONENTS[comp]
        fmt = '<' + letter
    else:
        raise ValueError('Unsupported glTF index component type')
    count = a.get('count')
    if type(count) is not int or not 0 < count <= MAX_VERTICES_PER_PRIMITIVE * 3:
        raise ValueError('Accessor count outside bounded range')
    view_index = a.get('bufferView')
    if type(view_index) is not int or not 0 <= view_index < len(doc.get('bufferViews', [])):
        raise ValueError('Missing bufferView')
    view = doc['bufferViews'][view_index]
    if view.get('buffer') != 0:
        raise ValueError('External binary buffer unsupported')
    stride = view.get('byteStride', width)
    if type(stride) is not int or stride < width or stride % (4 if kind == 'VEC3' else width):
        raise ValueError('Unsupported accessor stride')
    start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
    view_start = view.get('byteOffset', 0)
    view_end = view_start + view['byteLength']
    if start < view_start or start + (count-1)*stride + width > min(view_end, len(binary)):
        raise ValueError('Accessor reads beyond buffer view')
    return [struct.unpack_from(fmt, binary, start+i*stride)[0 if kind == 'SCALAR' else slice(None)]
            for i in range(count)]

def _append_float3(doc, binary, values, *, position=False):
    while len(binary) % 4:
        binary.append(0)
    start = len(binary)
    for v in values:
        binary.extend(FLOAT3.pack(*v))
    view = len(doc.setdefault('bufferViews', []))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': start,
                               'byteLength': len(values)*12})
    a = {'bufferView': view, 'componentType': 5126,
         'count': len(values), 'type': 'VEC3'}
    if position:
        a['min'] = [min(v[k] for v in values) for k in range(3)]
        a['max'] = [max(v[k] for v in values) for k in range(3)]
    idx = len(doc.setdefault('accessors', []))
    doc['accessors'].append(a)
    return idx

def _validate_recipe(recipe):
    if not isinstance(recipe, dict) or set(recipe) != {'schema_version', 'layers'} or recipe['schema_version'] != 1:
        raise ValueError('Unsupported shape recipe schema')
    layers = recipe['layers']
    if not isinstance(layers, list) or not 1 <= len(layers) <= MAX_LAYERS:
        raise ValueError('Expected 1-16 shape layers')
    ids = set()
    for layer in layers:
        if not isinstance(layer, dict) or set(layer) != {'id', 'mesh', 'center', 'radius', 'delta', 'strength'}:
            raise ValueError('Layer requires id, mesh, center, radius, delta, strength')
        if any(not isinstance(layer[k], str) or not SAFE_NAME.fullmatch(layer[k]) for k in ('id','mesh')):
            raise ValueError('Invalid layer or mesh name')
        if layer['id'] in ids:
            raise ValueError('Duplicate layer identity')
        ids.add(layer['id'])
        for field in ('center', 'delta'):
            vals = layer[field]
            if (not isinstance(vals, list) or len(vals) != 3 or
                    any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 1000 for v in vals)):
                raise ValueError('Invalid layer '+field)
        for field, low, high in (('radius', .001, 10.), ('strength', .00001, 1.)):
            v = layer[field]
            if type(v) not in (float, int) or not math.isfinite(v) or not low <= v <= high:
                raise ValueError('Invalid layer '+field)
        if math.dist(layer['delta'], (0,0,0)) > .045:
            raise ValueError('A single shape-layer displacement is too large')
        if math.dist(layer['delta'], (0,0,0)) < 1e-10:
            raise ValueError('A shape layer cannot be zero')
    return layers

def _triangles(doc, binary, prim, nverts):
    if prim.get('mode', 4) != 4:
        raise ValueError('Only glTF triangle-list primitives are supported')
    if 'indices' in prim:
        ids = _accessor(doc, binary, prim['indices'], 'SCALAR')
    else:
        ids = list(range(nverts))
    if len(ids) % 3 or any(v >= nverts for v in ids):
        raise ValueError('Invalid triangle index stream')
    return [(ids[k], ids[k+1], ids[k+2]) for k in range(0, len(ids), 3)]

def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def _face_normal(positions, triangle):
    a,b,c = (positions[i] for i in triangle)
    return _cross(tuple(b[i]-a[i] for i in range(3)),
                  tuple(c[i]-a[i] for i in range(3)))

def _normals(positions, faces, original):
    sums = [[0., 0., 0.] for _ in positions]
    for tri in faces:
        n = _face_normal(positions, tri)
        for i in tri:
            for k in range(3):
                sums[i][k] += n[k]
    out = []
    for s, fallback in zip(sums, original):
        length = math.sqrt(sum(x*x for x in s))
        out.append(tuple(v/length for v in s) if length > 1e-10 else tuple(fallback))
    return out

def mesh_inventory(path):
    _, doc, binary = _unpack(path)
    rows = []
    for mesh in doc.get('meshes', []):
        points = []
        triangles = 0
        for prim in mesh['primitives']:
            verts = _accessor(doc, binary, prim['attributes']['POSITION'], 'VEC3')
            points.extend(verts)
            triangles += len(_triangles(doc, binary, prim, len(verts)))
        rows.append({'mesh': mesh.get('name',''), 'vertices': len(points),
                     'triangles': triangles,
                     'bounds_min': [round(min(p[k] for p in points), 5) for k in range(3)] if points else None,
                     'bounds_max': [round(max(p[k] for p in points), 5) for k in range(3)] if points else None})
    return rows

def shape_glb(source, recipe, output, *, max_total_displacement=.055):
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve():
        raise ValueError('Never overwrite an original GLB')
    if type(max_total_displacement) not in (float, int) or not .001 <= max_total_displacement <= .06:
        raise ValueError('Unsafe total displacement bound')
    layers = _validate_recipe(recipe)
    raw, doc, binary = _unpack(source)
    meshes = doc.get('meshes', [])
    match_counts = {layer['id']: 0 for layer in layers}
    before_triangles = after_triangles = changed_vertices = 0
    largest = 0.
    changed = []
    for mesh in meshes:
        active = [layer for layer in layers if layer['mesh'] == mesh.get('name')]
        for prim in mesh['primitives']:
            positions = _accessor(doc, binary, prim['attributes']['POSITION'], 'VEC3')
            if len(positions) > MAX_VERTICES_PER_PRIMITIVE:
                raise ValueError('Primitive too large')
            triangles = _triangles(doc, binary, prim, len(positions))
            before_triangles += len(triangles)
            if not active:
                after_triangles += len(triangles)
                continue
            modified = []
            for p in positions:
                delta = [0.,0.,0.]
                for layer in active:
                    radius = layer['radius']
                    normalized = math.dist(p, layer['center']) / radius
                    if normalized >= 1:
                        continue
                    t = 1-normalized
                    falloff = t*t*(3-2*t)
                    for k in range(3):
                        delta[k] += layer['delta'][k]*layer['strength']*falloff
                length = math.sqrt(sum(v*v for v in delta))
                if length > max_total_displacement:
                    delta = [v*max_total_displacement/length for v in delta]
                    length = max_total_displacement
                largest = max(largest, length)
                if length > 1e-8:
                    changed_vertices += 1
                modified.append(tuple(p[i]+delta[i] for i in range(3)))
            for layer in active:
                match_counts[layer['id']] += 1
            for tri in triangles:
                a, b = _face_normal(positions, tri), _face_normal(modified, tri)
                am, bm = sum(v*v for v in a), sum(v*v for v in b)
                if am > 1e-18 and (bm <= 1e-18 or sum(a[k]*b[k] for k in range(3)) <= .25*math.sqrt(am*bm)):
                    raise ValueError('Rejected: a triangle collapsed or reversed')
            if any(not all(math.isfinite(v) for v in p) for p in modified):
                raise ValueError('Nonfinite output position')
            prim['attributes']['POSITION'] = _append_float3(doc, binary, modified, position=True)
            if 'NORMAL' in prim['attributes']:
                original_normals = _accessor(doc, binary, prim['attributes']['NORMAL'], 'VEC3')
                if len(original_normals) != len(modified):
                    raise ValueError('Normal count mismatch')
                prim['attributes']['NORMAL'] = _append_float3(
                    doc, binary, _normals(modified, triangles, original_normals))
            after_triangles += len(triangles)
            changed.append({'mesh': mesh.get('name',''), 'vertices': len(positions),
                            'triangles': len(triangles)})
    if any(not matches for matches in match_counts.values()):
        raise ValueError('At least one recipe mesh name did not match an existing GLB mesh')
    if not changed_vertices:
        raise ValueError('No GLB vertices were moved by the requested layers')
    if before_triangles != after_triangles:
        raise ValueError('Triangle count regression')
    rendered = _write(doc, binary)
    if len(rendered) > MAX_BYTES:
        raise ValueError('Result exceeds bounded GLB size')
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + '.candidate.tmp')
    try:
        temp.write_bytes(rendered)
        _, verify, verify_buf = _unpack(temp)
        if len(verify.get('skins',[])) != len(doc.get('skins',[])) or len(verify.get('animations',[])) != len(doc.get('animations',[])):
            raise ValueError('Rig or animation metadata changed')
        temp.replace(output)
    finally:
        temp.unlink(missing_ok=True)
    return {'schema_version': 1, 'engine': 'VEYLQUORIN',
            'tool': 'vq_glb_shape_refine',
            'source_sha256': hashlib.sha256(raw).hexdigest(),
            'candidate_sha256': hashlib.sha256(rendered).hexdigest(),
            'source_triangles': before_triangles, 'candidate_triangles': after_triangles,
            'triangles_added': 0, 'vertices_displaced': changed_vertices,
            'max_displacement_m': round(largest, 8), 'layers': list(match_counts),
            'modified_primitives': changed, 'skins_preserved': len(doc.get('skins', [])),
            'animations_preserved': len(doc.get('animations', [])),
            'uv_skin_weights_and_indices_reused': True,
            'android_emulator_verified': False, 'reference_likeness_verified': False,
            'game_ready': False, 'human_approval_required': True}

def main():
    p = argparse.ArgumentParser(description='VQ: zero-new-triangle GLB refinement (review only)')
    p.add_argument('--glb', required=True, type=Path)
    p.add_argument('--list-meshes', action='store_true')
    p.add_argument('--recipe', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--report', type=Path)
    a = p.parse_args()
    if a.list_meshes:
        print(json.dumps(mesh_inventory(a.glb), indent=2))
    else:
        if a.recipe is None or a.out is None:
            p.error('--recipe and --out are required for refinement')
        result = shape_glb(a.glb, json.loads(a.recipe.read_text(encoding='utf-8')), a.out)
        if a.report:
            a.report.parent.mkdir(parents=True, exist_ok=True)
            a.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
