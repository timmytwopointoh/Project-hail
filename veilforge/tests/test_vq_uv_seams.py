"""M32 real-mesh seam continuity gate: connected UVs versus M31 charts."""
import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vq_uv_seams import seam_counts
from vq_sculpt_detail_patch import build
from vq_uv_atlas import unwrap

class UVSeamGateTests(unittest.TestCase):
    def test_actual_sculpt_low_mesh_and_triangle_atlas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            build(root/"source")
            low=root/"source"/"source_low.obj"
            original=low.read_bytes()
            before=seam_counts(low)
            self.assertEqual(before,{"seam_edges":0,"continuous_edges":40})
            unwrap(low,root/"atlas.obj",texture_size=256,padding=2)
            after=seam_counts(root/"atlas.obj")
            self.assertEqual(after,{"seam_edges":40,"continuous_edges":0})
            self.assertEqual(low.read_bytes(),original)
    def test_missing_uv_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/"missing.obj"
            src.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            with self.assertRaisesRegex(ValueError,"Missing source UV"):
                seam_counts(src)

if __name__=="__main__":unittest.main()
