"""
Capture crisp UI screenshots for presentation slides.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

BASE_DIR = Path(__file__).resolve().parent.parent
PRES_DIR = BASE_DIR / "presentation" / "assets"
PRES_DIR.mkdir(parents=True, exist_ok=True)

def capture_screens():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=2)
        
        # 1. Main Monitor
        page.goto("http://127.0.0.1:8000")
        page.wait_for_timeout(3000)
        # Capture video canvas + controls
        page.screenshot(path=str(PRES_DIR / "screen_monitor.png"))
        print("[OK] Captured screen_monitor.png")
        
        # 2. Scenario 1 (Zero-Click)
        page.click("button:has-text('1. Zero-Click')")
        page.wait_for_timeout(2000)
        page.screenshot(path=str(PRES_DIR / "screen_zeroclick.png"))
        print("[OK] Captured screen_zeroclick.png")
        
        # 3. Fiscal Receipt Modal
        page.click("button:has-text('Электронный фискальный чек')")
        page.wait_for_timeout(600)
        page.screenshot(path=str(PRES_DIR / "screen_receipt.png"))
        print("[OK] Captured screen_receipt.png")
        page.click("#receiptModal button:has-text('✕')")
        page.wait_for_timeout(300)
        
        # 4. Scenario 2 (E-STOP Alarm)
        page.click("button:has-text('2. Риск обрыва')")
        page.wait_for_timeout(9500) # Wait for vehicle to move at t=28.5s
        page.screenshot(path=str(PRES_DIR / "screen_estop.png"))
        print("[OK] Captured screen_estop.png")
        
        # 5. ROI Tab
        page.click("button:has-text('Экономический эффект')")
        page.wait_for_timeout(1000)
        page.screenshot(path=str(PRES_DIR / "screen_roi.png"))
        print("[OK] Captured screen_roi.png")
        
        browser.close()

if __name__ == "__main__":
    capture_screens()
