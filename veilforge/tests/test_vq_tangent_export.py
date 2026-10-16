"""Optional real OBJ -> glTF tangent attribute, seam and fail-closed tests."""
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vq_tangent_export import export
from vq_model_tools import check_gltf

OBJ = """# Two positive-winding geometric triangles with opposite UV handedness
v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
vt 0 0
vt 1 0
vt 1 1
vn 0 0 1
usemtl default
f 1/1/1 2/2/1 3/3/1
f 1/1/1 3/3/1 4/2/1
"""

class TangentExportTest(unittest.TestCase):
    def _fixture(self, root, content=OBJ):
        source=root/'source.obj'
        source.write_text(content)
        return source
    def test_mirrored_seam_split_and_real_gltf_vec4(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=self._fixture(root)
            original=hashlib.sha256(source.read_bytes()).hexdigest()
            output=root/'output'/'candidate.gltf'
            doc=export(source,output,tangents=True)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)
            self.assertTrue(check_gltf(output)['structural_smoke_passed'])
            self.assertFalse(doc['extras']['production_approved'])
            self.assertFalse(doc['extras']['tangent_space_normals_verified'])
            self.assertTrue(doc['extras']['tangent_attribute_generated'])
            self.assertEqual(doc['extras']['source_sha256'],original)
            self.assertNotEqual(doc['extras']['derived_obj_sha256'],original)
            primitive=doc['meshes'][0]['primitives'][0]
            attrs=primitive['attributes']
            self.assertEqual(doc['accessors'][attrs['POSITION']]['count'],6)
            accessor=doc['accessors'][attrs['TANGENT']]
            self.assertEqual(accessor['type'],'VEC4')
            self.assertEqual(accessor['componentType'],5126)
            self.assertEqual(accessor['count'],6)
            view=doc['bufferViews'][accessor['bufferView']]
            values=struct.unpack_from('<24f',(output.parent/'candidate.bin').read_bytes(),view['byteOffset'])
            self.assertEqual([values[i*4+3] for i in range(6)],[1.,1.,1.,-1.,-1.,-1.])
            for i in range(6):
                x,y,z,w=values[i*4:i*4+4]
                self.assertAlmostEqual(x*x+y*y+z*z,1,places=5)
                self.assertAlmostEqual(z,0,places=5)
                self.assertIn(w,(-1.,1.))
    def test_default_export_remains_backward_compatible(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=self._fixture(root)
            doc=export(source,root/'plain.gltf')
            self.assertNotIn('TANGENT',doc['meshes'][0]['primitives'][0]['attributes'])
            self.assertFalse(doc['extras'].get('tangent_attribute_generated',False))
    def test_reject_missing_or_collapsed_uv_before_export(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for idx,content in enumerate((OBJ.replace('3/3/1','3//1'),
                                          OBJ.replace('vt 1 1','vt 0 0'))):
                src=self._fixture(root,content)
                out=root/f'broken_{idx}.gltf'
                with self.assertRaisesRegex(ValueError,'UV'):
                    export(src,out,tangents=True)
                self.assertFalse(out.exists())

if __name__ == '__main__':
    unittest.main()
