"""
Convert Theodore's World character SVGs to PNG training images.
Uses Playwright headless Chromium to render each SVG at 768x768.
"""

import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ASSETS = Path(r"C:\Users\mamar\tw-working\clothing-assets")
OUT = Path(r"C:\Users\mamar\OneDrive\Desktop\theo-training-images")
OUT.mkdir(exist_ok=True)

# Characters to export
SVGS = [
    ("everyday-theo.svg",       "theo_everyday",  "white"),
    ("super-theo.svg",          "theo_super",     "white"),
    ("flutter-and-theo.svg",    "theo_flutter",   "white"),
    ("dr-norm.svg",             "dr_norm",        "white"),
    ("sensory-siren.svg",       "sensory_siren",  "#111"),
    ("mask-master.svg",         "mask_master",    "#1a1020"),
    ("the-isolator.svg",        "the_isolator",   "#08080f"),
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  html, body {{ margin:0; padding:0; width:768px; height:768px; background:{bg}; }}
  svg {{ width:768px; height:768px; display:block; }}
</style></head>
<body>{svg_content}</body></html>"""

def export_svgs():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 768, "height": 768})

        for svg_file, name, bg in SVGS:
            svg_path = ASSETS / svg_file
            if not svg_path.exists():
                print(f"  SKIP (not found): {svg_file}")
                continue

            svg_content = svg_path.read_text(encoding="utf-8")
            html = HTML_TEMPLATE.format(svg_content=svg_content, bg=bg)

            page.set_content(html, wait_until="networkidle")
            page.wait_for_timeout(500)

            out_path = OUT / f"{name}.png"
            page.screenshot(path=str(out_path), full_page=False)
            print(f"  Exported: {name}.png")

        browser.close()

    print(f"\nAll done! Images saved to:\n{OUT}")

if __name__ == "__main__":
    export_svgs()
