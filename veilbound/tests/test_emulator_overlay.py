"""Regress the exact Android 14 fullscreen tutorial from failed parallel shard.

The test loads ONLY pure stdlib functions from emulator_test.py with AST,
so CI need not install Pillow merely to validate system-UI parsing.
"""
import ast
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "scripts/emulator_test.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
defs = [node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in ("system_overlay_button", "dismiss_android_overlay")]
scope = {"re": __import__("re"), "time": __import__("time"),
         "subprocess": __import__("subprocess"), "OUT": Path("/tmp")}
exec(compile(ast.Module(body=defs, type_ignores=[]), str(SOURCE), "exec"), scope)
detect = scope["system_overlay_button"]
dismiss = scope["dismiss_android_overlay"]


def overlay(button="GOT IT", resource="android:id/ok"):
    return ("""<hierarchy rotation="0"><node package="android" text=""
     bounds="[0,0][1280,720]"><node package="android" text="Viewing full screen"
     resource-id="android:id/immersive_cling_title" bounds="[355,78][925,187]"/>
     <node package="android" text="%s" resource-id="%s"
     bounds="[733,266][865,338]"/></node></hierarchy>""" % (button, resource)).encode()


class SystemOverlayTests(unittest.TestCase):
    def test_android14_uppercase_got_it_uses_real_bounds(self):
        self.assertEqual(((799, 302), True), detect(overlay()))

    def test_case_insensitive_and_resource_id_fallback(self):
        self.assertEqual(((799, 302), True), detect(overlay("Got it")))
        self.assertEqual(((799, 302), True),
                         detect(overlay("Accept", "android:id/ok")))

    def test_does_not_tap_game_overlays(self):
        xml = b'<hierarchy><node package="game.ashenveil.veilbound" text="GOT IT" bounds="[0,0][500,500]"/></hierarchy>'
        self.assertEqual((None, False), detect(xml))

    def test_known_overlay_without_android_button_is_not_silently_cleared(self):
        xml = b'<hierarchy><node package="android" text="Viewing full screen" bounds="[0,0][500,500]"/></hierarchy>'
        self.assertEqual((None, True), detect(xml))

    def test_anr_wait_is_safe_and_case_insensitive(self):
        xml = (b'<hierarchy><node package="android" text="App is not responding"'
               b' bounds="[0,0][500,500]"/><node package="android" text="WAIT"'
               b' bounds="[20,40][120,90]"/></hierarchy>')
        self.assertEqual(((70,65), True), detect(xml))

    def test_dismiss_retries_until_popup_is_actually_absent(self):
        xmls = [overlay(), overlay(), b'<hierarchy><node package="game" text="READY"/></hierarchy>']
        taps = []
        def fake_adb(*args, **kwargs):
            if args[0] == "exec-out":
                return xmls.pop(0)
            return b"OK"
        with __import__("tempfile").TemporaryDirectory() as d, \
             patch.dict(scope, {"adb": fake_adb, "touch": lambda x,y:taps.append((x,y)),
                                "OUT": Path(d)}), \
             patch.object(scope["time"],"sleep",return_value=None):
            dismiss()
        self.assertEqual([(799,302),(799,302)], taps)

if __name__ == "__main__":
    unittest.main()
