"""
Jury Dashboard Screenshot & PDF Compiler
========================================
Captures high-definition full-page screenshots of every tab and component
across the 3 core Jury Dashboards, compiling them into an executive PDF.
"""

import os
import sys
import time

# Ensure UTF-8 output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image
from playwright.sync_api import sync_playwright

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "jury", "dashboard_screenshots")
ROOT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "jury_dashboard_screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ROOT_OUTPUT_DIR, exist_ok=True)

BASE_URL = "http://localhost:8505"

def run_capture():
    print("[*] Launching Playwright (MS Edge Headless, 1920x1080)...")
    screenshots = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1.25
        )
        page = context.new_page()

        def save_shot(filename, title):
            path = os.path.join(OUTPUT_DIR, filename)
            root_path = os.path.join(ROOT_OUTPUT_DIR, filename)
            page.screenshot(path=path, full_page=True)
            page.screenshot(path=root_path, full_page=True)
            print(f"  [+] Captured: {filename} -> {title}")
            screenshots.append((path, title))

        # -------------------------------------------------------------
        # 0. JURY PORTAL EXECUTIVE HUB
        # -------------------------------------------------------------
        print("\n[*] Navigating to: Jury Executive Hub...")
        page.goto(f"{BASE_URL}/", wait_until="networkidle", timeout=30000)
        time.sleep(3)
        save_shot("00_Jury_Executive_Hub.png", "Jury Evaluation Portal - Executive Hub")

        # -------------------------------------------------------------
        # 1. DELIVERABLE 1: PATTERN MATCHING DASHBOARD
        # -------------------------------------------------------------
        print("\n[*] Navigating to: 1. Pattern Matching Dashboard...")
        page.goto(f"{BASE_URL}/Pattern_Matching", wait_until="networkidle", timeout=30000)
        time.sleep(3)

        tabs_p1 = page.locator("button[role='tab']").all()
        print(f"    Found {len(tabs_p1)} tabs on Pattern Matching")

        for i, tab in enumerate(tabs_p1):
            tab_text = tab.inner_text().strip()
            tab.click()
            time.sleep(2.5)
            clean_name = tab_text.replace("⚡", "").replace("🎯", "").replace("🎛️", "").strip()
            clean_slug = clean_name.replace(" ", "_").replace("'", "").replace("=", "_").replace(".", "")
            filename = f"01_Pattern_Matching_Tab{i+1}_{clean_slug[:30]}.png"
            save_shot(filename, f"Deliverable 1 - Pattern Matching: {clean_name}")

        # -------------------------------------------------------------
        # 2. DELIVERABLE 2: MODEL COMPARISON DASHBOARD
        # -------------------------------------------------------------
        print("\n[*] Navigating to: 2. Model Comparison Dashboard...")
        page.goto(f"{BASE_URL}/Classification_Comparison", wait_until="networkidle", timeout=30000)
        time.sleep(3)
        save_shot("02_Model_Comparison_Benchmark_Overview.png", "Deliverable 2 - Multi-Model Benchmarking (9 Algorithms)")

        # -------------------------------------------------------------
        # 3. DELIVERABLE 3: CHAMPION MODEL & PERFORMANCE METRICS
        # -------------------------------------------------------------
        print("\n[*] Navigating to: 3. Champion Model & Metrics Dashboard...")
        page.goto(f"{BASE_URL}/Model_Classification_and_Performance_Metrics", wait_until="networkidle", timeout=30000)
        time.sleep(3)

        tabs_p3 = page.locator("button[role='tab']").all()
        print(f"    Found {len(tabs_p3)} tabs on Champion Model & Metrics")

        for j, tab in enumerate(tabs_p3):
            tab_text = tab.inner_text().strip()
            tab.click()
            time.sleep(2.5)
            clean_name = tab_text.replace("🎛️", "").replace("🌳", "").replace("🏆", "").replace("📉", "").replace("⚡", "").strip()
            clean_slug = clean_name.replace(" ", "_").replace("&", "and").replace(".", "").replace("(", "").replace(")", "")
            filename = f"03_Champion_Model_Tab{j+1}_{clean_slug[:35]}.png"
            save_shot(filename, f"Deliverable 3 - Champion Model & Metrics: {clean_name}")

        browser.close()

    print(f"\n[*] Total screenshots captured: {len(screenshots)}")
    return screenshots

def compile_pdf(screenshots):
    print("\n[*] Compiling all screenshots into executive presentation PDF...")
    if not screenshots:
        print("[!] No screenshots available.")
        return

    images = []
    for path, _ in screenshots:
        try:
            im = Image.open(path)
            if im.mode != "RGB":
                im = im.convert("RGB")
            images.append(im)
        except Exception as e:
            print(f"Error loading {path}: {e}")

    if not images:
        return

    pdf_filename = "F1_Race_Intelligence_Jury_Dashboards.pdf"
    pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
    root_pdf_path = os.path.join(ROOT_OUTPUT_DIR, pdf_filename)

    first_img = images[0]
    rest_imgs = images[1:]

    first_img.save(
        pdf_path,
        "PDF",
        resolution=120.0,
        save_all=True,
        append_images=rest_imgs
    )
    first_img.save(
        root_pdf_path,
        "PDF",
        resolution=120.0,
        save_all=True,
        append_images=rest_imgs
    )

    print("[SUCCESS] PDF successfully generated:")
    print(f"  -> {pdf_path}")
    print(f"  -> {root_pdf_path}")

    # Generate an Index Manifest
    manifest_md = "# 🏎️ Formula 1 Race Intelligence: Jury Dashboard Screenshots & PDF Index\n\n"
    manifest_md += f"**Compiled PDF Document:** [`{pdf_filename}`]({pdf_filename})\n\n"
    manifest_md += "### Captured Screenshots Index:\n\n"
    manifest_md += "| Page # | Screenshot File | Deliverable & Description |\n"
    manifest_md += "| :---: | :--- | :--- |\n"
    for idx, (path, title) in enumerate(screenshots, start=1):
        fname = os.path.basename(path)
        manifest_md += f"| **Page {idx}** | `{fname}` | {title} |\n"

    manifest_path = os.path.join(OUTPUT_DIR, "README.md")
    root_manifest_path = os.path.join(ROOT_OUTPUT_DIR, "README.md")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest_md)
    with open(root_manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest_md)

    print("[SUCCESS] Manifest successfully written.")

if __name__ == "__main__":
    shots = run_capture()
    compile_pdf(shots)
