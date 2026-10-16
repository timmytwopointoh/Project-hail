from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vq_uv_distortion import audit_obj

class UVDistortionTests(unittest.TestCase):
    def test_smoke(self):
        self.assertTrue(callable(audit_obj))
