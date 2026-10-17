"""Synthetic GLB regression for shape-only preservation of character assets."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vq_glb_shape_refine import _accessor, _append_float3, _unpack, _write, mesh_inventory, shape_glb

def fixture(path):
    doc = {'asset': {'version':'2.0'}, 'buffers':[{'byteLength':0}],
           'bufferViews':[], 'accessors':[], 'meshes':[],
           'nodes':[{'name':'Head', 'mesh':0}, {'name':'Torso', 'mesh':1}],
           'skins':[{'name':'Existing_tail_skin','joints':[0]}],
           'animations':[{'name':'Existing_idle','channels':[], 'samplers':[]}],
           'materials':[{'name':'skin'}]}
    binary = bytearray()
    pts = [(x/4-.5, y/4-.5, 0.) for y in range(5) for x in range(5)]
    normal = [(0., 0., 1.)]*25
    faces = []
    for y in range(4):
        for x in range(4):
            a=y*5+x
            faces.extend([a,a+1,a+6,a,a+6,a+5])
    for name, z in [('Kaiyu_Head_skin',0.), ('Kaiyu_Torso_skin',2.)]:
        ps = [(x,y,z+oldz) for x,y,oldz in pts]
        ai = _append_float3(doc,binary,ps,position=True)
        ni = _append_float3(doc,binary,normal)
        from struct import pack
        uv_bytes = b''.join(pack('<ff', x+.5, y+.5) for x,y,_ in ps)
        uv_start = len(binary); binary.extend(uv_bytes)
        vi = len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':uv_start,'byteLength':len(uv_bytes)})
        ui = len(doc['accessors']);doc['accessors'].append({'bufferView':vi,'componentType':5126,'count':len(ps),'type':'VEC2'})
        start = len(binary);binary.extend(pack('<'+'H'*len(faces),*faces))
        vi=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(faces)*2})
        ii=len(doc['accessors']);doc['accessors'].append({'bufferView':vi,'componentType':5123,'count':len(faces),'type':'SCALAR'})
        doc['meshes'].append({'name':name, 'primitives':[{'attributes':{'POSITION':ai,'NORMAL':ni,'TEXCOORD_0':ui},'indices':ii,'material':0}]})
    path.write_bytes(_write(doc, binary))
    return path

def recipe(mesh='Kaiyu_Head_skin', delta=None):
    return {'schema_version':1, 'layers':[{'id':'cheek-shape','mesh':mesh,
        'center':[0.,0.,0.], 'radius':.55,'delta':delta or [0.,0.,.035], 'strength':1.}]}

class ShapeRefineTest(unittest.TestCase):
    def test_vertex_only_refine_retains_topology_skin_uv_and_animation(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=fixture(Path(tmp)/'source.glb'); out=Path(tmp)/'candidate.glb'
            initial=src.read_bytes(); initial_sha=hashlib.sha256(initial).hexdigest()
            report=shape_glb(src,recipe(),out)
            self.assertEqual(src.read_bytes(),initial)
            self.assertEqual(report['source_sha256'],initial_sha)
            self.assertEqual(report['triangles_added'],0)
            self.assertEqual(report['source_triangles'],64)
            self.assertEqual(report['source_triangles'],report['candidate_triangles'])
            self.assertGreater(report['vertices_displaced'],0)
            self.assertLessEqual(report['max_displacement_m'],.035)
            _, before, old_binary = _unpack(src)
            _, after, new_binary = _unpack(out)
            self.assertEqual(after['skins'],before['skins'])
            self.assertEqual(after['animations'],before['animations'])
            self.assertEqual(after['nodes'],before['nodes'])
            self.assertEqual(after['materials'],before['materials'])
            for m in range(2):
                a,b=before['meshes'][m]['primitives'][0],after['meshes'][m]['primitives'][0]
                for key in ('indices','material','mode'):
                    self.assertEqual(a.get(key),b.get(key))
                self.assertEqual(a['attributes']['TEXCOORD_0'],b['attributes']['TEXCOORD_0'])
                self.assertEqual(_accessor(after,new_binary,b['indices'],'SCALAR'),_accessor(before,old_binary,a['indices'],'SCALAR'))
            p0=before['meshes'][0]['primitives'][0]['attributes']['POSITION']
            p1=after['meshes'][0]['primitives'][0]['attributes']['POSITION']
            self.assertNotEqual(_accessor(before,old_binary,p0,'VEC3'),_accessor(after,new_binary,p1,'VEC3'))
            self.assertEqual(after['meshes'][1], before['meshes'][1])
            self.assertTrue(new_binary.startswith(old_binary))
            self.assertFalse(report['android_emulator_verified'])
            self.assertFalse(report['game_ready'])

    def test_listing_reports_local_coordinate_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=fixture(Path(tmp)/'source.glb')
            meshes=mesh_inventory(src)
            self.assertEqual(len(meshes),2)
            self.assertEqual(meshes[0]['bounds_min'],[-.5,-.5,0.])
            self.assertEqual(meshes[1]['bounds_max'],[.5,.5,2.])
            self.assertEqual(meshes[0]['triangles'],32)

    def test_deterministic_replay_and_second_layer(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=fixture(Path(tmp)/'source.glb')
            r=recipe()
            r['layers'].append({'id':'chin-shape','mesh':'Kaiyu_Head_skin','center':[.0,.0,.0],
                                'radius':.3,'delta':[0,0,-.02],'strength':.5})
            a=Path(tmp)/'a.glb';b=Path(tmp)/'b.glb'
            x=shape_glb(src,r,a);y=shape_glb(src,r,b)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            self.assertEqual(x['candidate_sha256'],y['candidate_sha256'])
            self.assertEqual(len(x['layers']),2)

    def test_fail_closed_and_preserve_original_on_invalid_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=fixture(Path(tmp)/'source.glb'); orig=src.read_bytes();out=Path(tmp)/'candidate.glb'
            bad=[recipe('missing_mesh'),recipe(delta=[0,0,1.]),
                 {'schema_version':1,'layers':[dict(recipe()['layers'][0],radius=float('nan'))]},
                 {'schema_version':1,'layers':[dict(recipe()['layers'][0],delta=[0,0,0])]},
                 {'schema_version':1,'layers':[dict(recipe()['layers'][0],id='not safe!')]},
                 {'schema_version':1,'layers':recipe()['layers']*2},
                 {'schema_version':2,'layers':recipe()['layers']}]
            for row in bad:
                with self.subTest(row=str(row)[:100]),self.assertRaises(ValueError):
                    shape_glb(src,row,out)
            with self.assertRaises(ValueError):
                shape_glb(src,recipe(),src)
            self.assertEqual(src.read_bytes(),orig)
            self.assertFalse(out.exists())

if __name__=='__main__':
    unittest.main()
