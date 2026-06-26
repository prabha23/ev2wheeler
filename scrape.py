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
        
        # Helper 1: Main Dropdowns
        def change_dropdown(dropdown_combo_id, option_text):
            dropdown = page.locator(f"div[id*='{dropdown_combo_id}']").first
            dropdown.locator(".ui-selectonemenu-trigger").click()
            time.sleep(1)
            page.locator(f"div[id*='{dropdown_combo_id}_panel'] li[data-label='{option_text}']").click()
            time.sleep(3)

        change_dropdown("yaxisVar", "Maker")
        change_dropdown("xaxisVar", "Month Wise")
        
        # 1. Main Refresh
        print("[*] Performing main refresh...")
        page.locator("button", has_text="Refresh").first.click()
        time.sleep(8)
        
        # 2. Resilient Sidebar Expansion
        print("[*] Checking sidebar status...")
        try:
            # Check if icon exists and is visible before clicking
            expand_icon = page.locator(".ui-layout-unit-expand-icon").first
            if expand_icon.is_visible(timeout=5000):
                expand_icon.click(force=True)
                time.sleep(3)
                print("[+] Sidebar opened.")
            else:
                print("[+] Sidebar appears to be already open.")
        except: 
            print("[+] Sidebar toggle skipped.")

        # Helper 2: Checkbox logic
        def expand_and_check_filter(section_name, option_name):
            header = page.locator(".ui-accordion-header").filter(has_text=section_name).first
            if header.count() > 0 and "ui-state-active" not in (header.get_attribute("class") or ""):
                header.click(force=True)
                time.sleep(2)
            
            # Find the row and the checkbox within it
            target_row = page.locator("tr, li").filter(has=page.get_by_text(option_name, exact=False)).first
            box = target_row.locator(".ui-chkbox-box, input[type='checkbox'], div[role='checkbox']").first
            
            if box.count() > 0:
                box.click(force=True)
                time.sleep(2)
            else:
                target_row.click(force=True)
                time.sleep(2)

        # Select items
        expand_and_check_filter("Vehicle Category", "TWO WHEELER (Invalid Carriage)")
        expand_and_check_filter("Vehicle Category", "TWO WHEELER(NT)")
        expand_and_check_filter("Vehicle Category", "TWO WHEELER(T)")
        expand_and_check_filter("Fuel", "ELECTRIC(BOV)")
        expand_and_check_filter("Fuel", "PURE EV")
        
        # 3. Sidebar Refresh
        print("[*] Clicking sidebar refresh...")
        page.locator("button", has_text="Refresh").last.click(force=True)
        time.sleep(12)
        
        # 4. Download
        for attempt in range(3):
            try:
                print(f"[*] Attempting download ({attempt+1}/3)...")
                with page.expect_download(timeout=45000) as download_info:
                    excel_btn = page.locator("input[src*='excel' i], img[src*='excel' i], [title*='Excel' i]").first
                    excel_btn.click(force=True)
                download_info.value.save_as(EXCEL_FILE_PATH)
                print("[+] Success!")
                break
            except Exception as e:
                print(f"[-] Attempt {attempt+1} failed: {e}")
                time.sleep(5)
        
        browser.close()

if __name__ == "__main__":
    download_raw_vahan_sheet()
