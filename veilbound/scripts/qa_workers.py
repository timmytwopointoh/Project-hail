#!/usr/bin/env python3
"""Small, deterministic CI workers. Every lane is independent and read-only."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "veilbound/app/src/main/java/game/ashenveil/veilbound"
TESTS = ROOT / "veilbound/tests/game/ashenveil/veilbound"
PURE = ["WorldState", "CombatMotion", "CharacterRig", "EnvironmentKit",
        "ModelStudio", "ArtKit", "DetailArtKit", "CinematicArtKit",
        "SurfaceAtlas", "ObjMeshLoader", "MaterialTextures", "HeroPose", "ShapeEngine", "BellwardenAnatomy", "HumanAnatomy", "M24BodyRetarget", "HumanHandSculpt", "HumanSkeleton", "ContinuousHuman", "MaterialMapping", "BootAssets"]
SUITES = {
    "combat": ["WorldRules", "CombatMotion", "CharacterRig", "CombatGameplay"],
    "assets": ["EnvironmentKit", "ModelStudio", "ArtKit", "DetailArtKit",
               "CinematicArtKit", "SurfaceAtlas", "ObjMeshLoader", "MaterialTextures", "ShapeEngine", "BellwardenAnatomy", "ForgedPlate", "ArticulatedJoint", "HumanAnatomy", "M24BodyRetarget", "HumanHandSculpt", "HumanSkeleton", "ContinuousHuman", "MaterialMapping", "BootAssets"],
}

def command(*args):
    result = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=150)
    if result.returncode:
        raise RuntimeError("%s failed (%d):\n%s" % (args, result.returncode, result.stdout[-14000:]))
    return result.stdout[-14000:]

def run(role, output):
    output.mkdir(parents=True, exist_ok=True)
    report = {"role": role, "status": "failed", "checks": [], "timestamp": int(time.time())}
    try:
        if role in SUITES:
            sources = [PACKAGE / (name + ".java") for name in PURE]
            tests = [TESTS / (name + "Test.java") for name in SUITES[role]]
            for path in sources + tests:
                if not path.is_file():
                    raise RuntimeError("Missing Java dependency or test: " + str(path))
            destination = output / "classes"
            destination.mkdir(exist_ok=True)
            command("javac", "-d", str(destination), *map(str, sources + tests))
            report["checks"].append("compiled " + str(len(sources)) + " pure-Java classes")
            for name in SUITES[role]:
                command("java", "-cp", str(destination), "game.ashenveil.veilbound." + name + "Test")
                report["checks"].append(name + "Test passed")
        elif role == "integrity":
            manifest = (ROOT / "veilbound/app/src/main/AndroidManifest.xml").read_text()
            gradle = (ROOT / "veilbound/app/build.gradle").read_text()
            native = (PACKAGE / "ValeRenderer.java").read_text()
            smoke = (ROOT / "veilbound/scripts/emulator_test.py").read_text()
            conditions = {
                "native Android application": "<application" in manifest,
                "launcher activity": "MainActivity" in manifest,
                "Android plugin defined": "com.android.application" in gradle,
                "OpenGL renderer present": "GLES20" in native,
                "emulator screenshot smoke present": "screencap" in smoke,
                "all deterministic modules present": all((PACKAGE / (x + ".java")).is_file() for x in PURE),
                "realism master plan present": (ROOT / "veilbound/REALISM_MASTER_PLAN.md").is_file(),
            }
            report["checks"] = [{"name": k, "passed": v} for k, v in conditions.items()]
            if not all(conditions.values()):
                raise RuntimeError("Required game/testing component missing")
            for script in (ROOT / "veilbound/scripts/emulator_test.py",
                           ROOT / "veilbound/scripts/qa_analyze.py",
                           ROOT / "veilbound/scripts/qa_workers.py"):
                command(sys.executable, "-m", "py_compile", str(script))
        else:
            raise ValueError("Unknown worker role: " + role)
        report["status"] = "passed"
    except Exception as error:
        report["error"] = str(error)
    (output / (role + ".json")).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--role", choices=["combat", "assets", "integrity"], required=True)
    p.add_argument("--out", type=Path, default=Path("inspection_output/worker-farm"))
    args = p.parse_args()
    sys.exit(run(args.role, args.out))
