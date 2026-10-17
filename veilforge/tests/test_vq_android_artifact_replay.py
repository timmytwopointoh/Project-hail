"""Immutable emulator artifact replay rejects tampering and unsupported signoff."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_visual_qa import ROLES, VIEWS, BACKGROUND
from visual_semantics import silhouette, outline_analysis
from vq_android_artifact_replay import verify

SHA = 'de4b059aa8a9dbc665518f253be55d8ba345c7d6'
RUN = 39054441812
APK = 'a' * 64


def evidence(root):
    root = Path(root)
    archives = {}
    all_views = {}
    for role, names in ROLES.items():
        archive = root / (role + '.zip')
        manifest = {'role': role, 'source_commit': SHA, 'device_android_api': 35,
                    'technical_visual_smoke_pass': True, 'artistic_quality_approved': False,
                    'apk_sha256': APK, 'screenshot_count': len(names) * len(VIEWS), 'assets': []}
        with ZipFile(archive, 'w') as z:
            for j, name in enumerate(names):
                views = []
                for i, (yaw, pitch) in enumerate(VIEWS):
                    image = Image.new('RGB', (300, 500), BACKGROUND)
                    d = ImageDraw.Draw(image)
                    d.text((5, 5), name, fill=(200, 200, 200))
                    # Unique accepted frame pixels, stable nonblank silhouette.
                    d.rectangle((70 + i, 110 + j * 4, 110 + i, 165 + j * 4), fill=(150 + i, 90 + j, 70))
                    stream = io.BytesIO(); image.save(stream, format='PNG')
                    raw = stream.getvalue()
                    path = f'{name}/{i:02d}_yaw{yaw}_pitch{pitch}.png'
                    sha = hashlib.sha256(raw).hexdigest()
                    z.writestr(path, raw)
                    view = {'index': i, 'yaw': yaw, 'pitch': pitch, 'image': path,
                            'sha256': sha}
                    views.append(view)
                manifest['assets'].append({'asset': name, 'views': views})
                if name == 'ceremonial_sword':
                    for view in views:
                        with Image.open(io.BytesIO(z.read(view['image']))) as frame:
                            mask, w, h = silhouette(frame)
                        view['coverage'] = outline_analysis(mask, w, h)['coverage']
                    all_views[name] = views
            z.writestr('emulator_visual_qa.json', json.dumps(manifest))
        archives[role] = archive
    views = all_views['ceremonial_sword']
    task = {'asset': 'ceremonial_sword', 'emulator_role': 'props-equipment',
            'source_commit': SHA, 'github_actions_run_id': RUN,
            'automatic_model_edit': False, 'auto_promote': False,
            'source_views': views, 'minimum_foreground_coverage': round(min(v['coverage'] for v in views), 4),
            'maximum_foreground_coverage': round(max(v['coverage'] for v in views), 4),
            'lowest_coverage_view': min(views, key=lambda v: v['coverage'])}
    tasks = {'source_commit': SHA, 'github_actions_run_id': RUN,
             'frames_reviewed': 154, 'emulators_reviewed': 4,
             'ready_for_automated_model_rewrite': False, 'human_signoff_required': True,
             'warning_count': 1, 'tasks': [task]}
    file = root / 'tasks.json'; file.write_text(json.dumps(tasks))
    return file, archives


class ReplayTests(unittest.TestCase):
    def test_replay_all_real_png_bytes_and_review_angles(self):
        with tempfile.TemporaryDirectory() as tmp:
            file, archives = evidence(tmp)
            report = verify(file, archives)
            self.assertEqual(report['accepted_unique_pngs_verified'], 154)
            self.assertEqual(report['review_angles_recomputed'], 14)
            self.assertFalse(report['artistic_quality_approved'])
    def test_reject_tampered_task_sha_and_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            file, archives = evidence(tmp)
            for key, value in [('sha256', '0' * 64), ('coverage', 0.5)]:
                data = json.loads(file.read_text())
                data['tasks'][0]['source_views'][0][key] = value
                file.write_text(json.dumps(data))
                with self.subTest(key=key), self.assertRaises(ValueError):
                    verify(file, archives)
    def test_missing_archive_and_automatic_promotion_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            file, archives = evidence(tmp)
            with self.assertRaisesRegex(ValueError, 'four'):
                verify(file, {k: v for k, v in archives.items() if k != 'characters'})
            data = json.loads(file.read_text())
            data['ready_for_automated_model_rewrite'] = True
            file.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'automatic'):
                verify(file, archives)

if __name__ == '__main__':
    unittest.main()