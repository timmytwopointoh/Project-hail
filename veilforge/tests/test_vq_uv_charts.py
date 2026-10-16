"""M33 coherent UV chart tests against real sculpt sources."""
import hashlib
from pathlib import Path
import sys, tempfile, unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vq_uv_charts import unwrap
from vq_sculpt_detail_patch import build
from vq_uv_transfer import transfer
from vq_mesh_baker import bake, raster, uv_rows

class ConnectedChartTests(unittest.TestCase):
    def test_real_sculpt_bake_and_determinism(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build(root/'source')
            low=root/'source/source_low.obj';original=low.read_bytes()
            out=root/'low_coherent.obj'
            r=unwrap(low,out,texture_size=256,padding=4)
            self.assertEqual(r['charts'],1)
            self.assertEqual(r['uv_seams'],{'seam_edges':0,'continuous_edges':40})
            self.assertLessEqual(r['maximum_area_stretch_ratio'],1.08)
            self.assertGreater(r['minimum_triangle_area_texels'],100)
            self.assertEqual(low.read_bytes(),original)
            rows,normals=uv_rows(out)
            self.assertGreater(sum(x is not None for x in raster(rows,normals,256)),256*256*.80)
            t=transfer(out,root/'source/source_high.obj',root/'projected.obj',cage_distance=.06)
            self.assertEqual(t['high_faces'],3200)
            b=bake(out,root/'projected.obj',root/'baked',size=256)
            self.assertGreater(b['meaningful_normal_variation_texels'],100)
            self.assertGreater(b['textured_coverage_fraction'],.80)
            self.assertFalse(b['android_emulator_verified'])
            again=unwrap(low,root/'again.obj',texture_size=256,padding=4)
            self.assertEqual(r['candidate_sha256'],again['candidate_sha256'])
            self.assertEqual(r['candidate_sha256'],hashlib.sha256(out.read_bytes()).hexdigest())

    def test_dihedral_and_material_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'bent.obj'
            src.write_text('v 0 0 0\nv 1 0 0\nv 0 0 1\nv 1 0.25 1\nusemtl stone\nf 1 3 2\nf 2 3 4\n')
            a=unwrap(src,root/'split.obj',texture_size=256,max_angle_degrees=10)
            self.assertEqual(a['charts'],2)
            self.assertEqual(a['uv_seams']['seam_edges'],1)
            b=unwrap(src,root/'joined.obj',texture_size=256,max_angle_degrees=20)
            self.assertEqual(b['charts'],1)
            self.assertEqual(b['uv_seams']['continuous_edges'],1)
            src.write_text(src.read_text().replace('f 2 3 4','usemtl leather\nf 2 3 4'))
            c=unwrap(src,root/'materials.obj',texture_size=256,max_angle_degrees=20)
            self.assertEqual(c['charts'],2)

    def test_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build(root/'source')
            src=root/'source/source_low.obj';original=src.read_bytes()
            for kw in ({'texture_size':300},{'padding':0},{'padding':True},
                       {'max_angle_degrees':float('nan')},{'max_stretch':.8}):
                with self.subTest(kw=kw),self.assertRaises(ValueError):
                    unwrap(src,root/'invalid.obj',**kw)
            with self.assertRaisesRegex(ValueError,'Never overwrite'):
                unwrap(src,src)
            self.assertEqual(src.read_bytes(),original)
            self.assertFalse((root/'invalid.obj').exists())
            malformed=root/'nonmanifold.obj'
            malformed.write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 -1 0\nv 0 0 1\nf 1 2 3\nf 2 1 4\nf 1 2 5\n')
            with self.assertRaisesRegex(ValueError,'topology|Nonmanifold'):
                unwrap(malformed,root/'bad.obj')
            self.assertFalse((root/'bad.obj').exists())

if __name__=='__main__':unittest.main()
