#!/usr/bin/env python3
"""Offline APK Vision Inspector report generator (stdlib only)."""
import argparse, hashlib, json, pathlib, re, subprocess, zipfile

def inspect(apk, output):
    apk = pathlib.Path(apk)
    output = pathlib.Path(output)
    output.mkdir(parents=True, exist_ok=True)
    result = {"apk": apk.name, "findings": [], "files": [], "package": None}
    if not apk.is_file():
        result["findings"].append({"severity":"error","message":"APK file not found"})
    elif not zipfile.is_zipfile(apk):
        result["findings"].append({"severity":"error","message":"File is not a valid ZIP-format APK"})
    else:
        result["size_bytes"] = apk.stat().st_size
        result["sha256"] = hashlib.sha256(apk.read_bytes()).hexdigest()
        with zipfile.ZipFile(apk) as z:
            names = z.namelist()
            result["files"] = names
            dex = [n for n in names if re.fullmatch(r"classes(\d*)\.dex", n)]
            result["dex_count"] = len(dex)
            result["native_libraries"] = [n for n in names if n.startswith("lib/") and n.endswith(".so")]
            result["assets"] = [n for n in names if n.startswith("assets/")]
            for required in ("AndroidManifest.xml", "resources.arsc"):
                if required not in names:
                    result["findings"].append({"severity":"warning","message":f"Missing {required}"})
            if not dex:
                result["findings"].append({"severity":"info","message":"No classes.dex found (may be a special APK)"})
            if any(n.endswith(".html") for n in names):
                result["findings"].append({"severity":"info","message":"HTML assets detected; inspect WebView rendering"})
        try:
            p = subprocess.run(["aapt", "dump", "badging", str(apk)], capture_output=True, text=True, timeout=30)
            if p.returncode == 0:
                match = re.search(r"package: name='([^']+)'", p.stdout)
                if match: result["package"] = match.group(1)
                result["badging"] = p.stdout[:16000]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            result["findings"].append({"severity":"info","message":"aapt unavailable"})
    (output/"static_report.json").write_text(json.dumps(result, indent=2))
    lines = ["# APK Vision Inspector Report", "", f"APK: `{apk.name}`", f"Package: `{result['package'] or 'unknown'}`", "", "## Findings"]
    lines += [f"- **{f['severity']}**: {f['message']}" for f in result["findings"]] or ["- No structural warnings detected."]
    lines += ["", "## Suggested repairs", "- Review screenshots for clipping, alignment, and rendering errors.", "- Verify launch behavior and inspect logcat for crashes.", "- Re-test on multiple screen sizes and API levels."]
    (output/"repair_report.md").write_text("\n".join(lines)+"\n")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("apk")
    parser.add_argument("--output", default="inspection_output")
    args = parser.parse_args()
    report = inspect(args.apk, args.output)
    print(json.dumps({"package":report["package"],"findings":report["findings"]}, indent=2))
