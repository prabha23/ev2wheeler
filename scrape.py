import os
import time
from playwright.sync_api import sync_playwright

# =====================================================================
# CONFIGURATION
# =====================================================================
DOWNLOAD_DIR = os.getcwd()
EXCEL_FILE_PATH = os.path.join(DOWNLOAD_DIR, "vahan_raw_latest.xlsx")

# =====================================================================
# CORE AUTOMATION ROUTINE
# =====================================================================
def download_raw_vahan_sheet():
    print(f"[*] Initializing browser session...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto("https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml")
        time.sleep(5)
        
        def change_dropdown(dropdown_combo_id, option_text):
            dropdown = page.locator(f"div[id*='{dropdown_combo_id}']").first
            dropdown.locator(".ui-selectonemenu-trigger").click()
            time.sleep(1)
            page.locator(f"div[id*='{dropdown_combo_id}_panel'] li[data-label='{option_text}']").click()
            time.sleep(3)

        change_dropdown("yaxisVar", "Maker")
        change_dropdown("xaxisVar", "Month Wise")
        page.locator("button", has_text="Refresh").first.click()
        time.sleep(8)
        
        try:
            page.locator(".ui-layout-unit-expand-icon").first.click()
            time.sleep(3)
        except: pass

        def expand_and_check_filter(section_name, option_name):
            header = page.locator(".ui-accordion-header").filter(has_text=section_name).first
            if "ui-state-active" not in (header.get_attribute("class") or ""):
                header.click(force=True)
                time.sleep(2)
            
            # Find the row, then look for any clickable box inside it
            row = page.locator("tr, li").filter(has=page.get_by_text(option_name, exact=False)).first
            box = row.locator(".ui-chkbox-box, input[type='checkbox'], td:first-child").first
            box.click(force=True)
            time.sleep(2)

        expand_and_check_filter("Vehicle Category", "TWO WHEELER (Invalid Carriage)")
        expand_and_check_filter("Vehicle Category", "TWO WHEELER(NT)")
        expand_and_check_filter("Vehicle Category", "TWO WHEELER(T)")
        expand_and_check_filter("Fuel", "ELECTRIC(BOV)")
        expand_and_check_filter("Fuel", "PURE EV")
        
        # FINAL REFRESH
        page.locator("button", has_text="Refresh").last.click(force=True)
        time.sleep(12)
        
        # RETRY LOOP FOR DOWNLOAD
        for attempt in range(3):
            try:
                print(f"[*] Attempting download (Attempt {attempt+1}/3)...")
                with page.expect_download(timeout=30000) as download_info:
                    excel_btn = page.locator("input[src*='excel' i], img[src*='excel' i], [title*='Excel' i]").first
                    excel_btn.click(force=True)
                download = download_info.value
                download.save_as(EXCEL_FILE_PATH)
                print("[+] Success!")
                break
            except Exception as e:
                print(f"[-] Attempt {attempt+1} failed: {e}")
                time.sleep(5)
        
        browser.close()

if __name__ == "__main__":
    download_raw_vahan_sheet()
