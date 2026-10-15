#!/usr/bin/env python3
"""Cross-resolution screenshot and touch-regression checks for cinematic Matrix Flap."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

SOURCE = Path("matrix-flap/app/src/main/assets/index.html")
OUT = Path("inspection_output/matrix_flap/browser_qa")
SIZES = [(320, 640), (390, 844), (430, 932)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"version": "1.2", "results": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage",
                                 "--enable-unsafe-swiftshader"])
        try:
            for w, h in SIZES:
                record = {"viewport": f"{w}x{h}", "screenshots": []}
                report["results"].append(record)
                ctx = browser.new_context(viewport={"width": w, "height": h},
                                          device_scale_factor=1,
                                          is_mobile=True, has_touch=True)
                try:
                    page = ctx.new_page()
                    js_errors = []
                    page.on("pageerror", lambda error: js_errors.append(str(error)))
                    page.set_content(SOURCE.read_text(encoding="utf-8"), wait_until="load")
                    page.wait_for_function("typeof window.matrixFlapStatus === 'function'")
                    state = lambda: page.evaluate("window.matrixFlapStatus()")
                    assert state()["state"] == "ready"
                    button = page.locator("#action")
                    rect = button.bounding_box()
                    assert rect and rect["x"] >= 0 and rect["y"] >= 0, "Start button hidden"
                    assert rect["x"] + rect["width"] <= w + 1, "Start button horizontally clipped"
                    assert rect["y"] + rect["height"] <= h + 1, "Start button vertically clipped"
                    animation = page.locator("#sheet .card").evaluate(
                        "e => getComputedStyle(e).animationName")
                    assert "deckLevitate" in animation, "Cinematic depth animation missing"
                    record["menu_animation"] = animation
                    for label in ("menu",):
                        filename = f"{label}_{w}x{h}.png"
                        page.screenshot(path=str(OUT / filename))
                        record["screenshots"].append(filename)
                    page.locator("#menuSettings").click()
                    assert state()["overlay"] == "settings"
                    page.locator("#toggleEffects").click()
                    assert state()["settings"]["effects"] is False
                    assert page.evaluate("document.documentElement.classList.contains('fx-off')")
                    page.locator("#toggleEffects").click()
                    assert state()["settings"]["effects"] is True
                    filename = f"settings_{w}x{h}.png"
                    page.screenshot(path=str(OUT / filename))
                    record["screenshots"].append(filename)
                    page.locator("#closeSettings").click()
                    page.locator("#action").click()
                    assert state()["state"] == "playing", "Menu Start failed"
                    page.wait_for_timeout(250)
                    filename = f"flight_{w}x{h}.png"
                    page.screenshot(path=str(OUT / filename))
                    record["screenshots"].append(filename)
                    page.locator("#pauseBtn").click()
                    assert state()["state"] == "paused"
                    position = state()["birdY"]
                    page.wait_for_timeout(200)
                    assert state()["birdY"] == position, "Flight moved while paused"
                    filename = f"pause_{w}x{h}.png"
                    page.screenshot(path=str(OUT / filename))
                    record["screenshots"].append(filename)
                    page.locator("#resumeBtn").click()
                    assert state()["state"] == "playing"
                    page.locator("#pauseBtn").click()
                    page.locator("#homeBtn").click()
                    assert state()["state"] == "ready"
                    assert not js_errors, "Browser errors: " + "; ".join(js_errors)
                    record["status"] = "passed"
                    record["js_errors"] = js_errors
                    record["fps_diagnostic"] = state()["fps"]
                except Exception as error:
                    record["status"] = "failed"
                    record["error"] = str(error)
                finally:
                    ctx.close()
        finally:
            browser.close()
    report["passed"] = sum(r["status"] == "passed" for r in report["results"])
    report["total"] = len(report["results"])
    (OUT / "browser_qa.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
