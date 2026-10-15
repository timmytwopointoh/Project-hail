#!/usr/bin/env python3
"""Compare Android screenshots and generate pixel-difference diagnostics."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageEnhance

def compare(before, after, output):
    before, after, output = Path(before), Path(after), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with Image.open(before) as img_a, Image.open(after) as img_b:
        a, b = img_a.convert("RGB"), img_b.convert("RGB")
    if a.size != b.size:
        report = {"status": "different_dimensions", "before_size": list(a.size),
                  "after_size": list(b.size), "changed_fraction": None,
                  "meaningful_change": None}
    else:
        diff = ImageChops.difference(a, b)
        mask = diff.convert("L").point(lambda pixel: 255 if pixel > 12 else 0)
        changed = mask.histogram()[255]
        total = a.width * a.height
        bbox = mask.getbbox()
        report = {"status": "ok", "before_size": list(a.size),
                  "after_size": list(b.size), "changed_pixels": changed,
                  "total_pixels": total, "changed_fraction": round(changed / total, 6),
                  "meaningful_change": changed / total >= 0.005,
                  "change_bounds": list(bbox) if bbox else None}
        ImageEnhance.Contrast(diff).enhance(3).save(output / "visual_difference.png")
    (output / "visual_comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--output", default="inspection_output")
    args = parser.parse_args()
    print(json.dumps(compare(args.before, args.after, args.output), indent=2))
