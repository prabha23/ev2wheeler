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
    print(f"[*] Initializing headless browser session for Vahan 4 Dashboard...")
    with sync_playwright() as p:
        # headless=True is REQUIRED for GitHub Actions cloud servers
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        print("[*] Navigating to report view URL...")
        page.goto("https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml")
        time.sleep(4)
        
        # -------------------------------------------------------------
        # Dropdown Handler
        # -------------------------------------------------------------
        def change_dropdown(dropdown_combo_id, option_text):
            print(f"[#] Changing {dropdown_combo_id} -> '{option_text}'...")
            dropdown = page.locator(f"div[id*='{dropdown_combo_id}']").first
            dropdown.locator(".ui-selectonemenu-trigger").click()
            time.sleep(1.5)
            
            option = page.locator(f"div[id*='{dropdown_combo_id}_panel'] li[data-label='{option_text}']")
            option.scroll_into_view_if_needed()
            option.click()
            time.sleep(4)

        # 1. Select Y-Axis and X-Axis
        change_dropdown("yaxisVar", "Maker")
        change_dropdown("xaxisVar", "Month Wise")
        
        # 2. FIRST REFRESH: Apply base axes mapping
        print("[*] Clicking main 'Refresh' to apply axes before opening filters...")
        page.locator("button", has_text="Refresh").first.click()
        time.sleep(8)
        
        # 3. Open Filter Sidebar Panel
        print("[*] Opening the left side filter panel...")
        try:
            page.locator(".ui-layout-unit-expand-icon").first.click()
            time.sleep(4) 
        except Exception:
            print("[-] Sidebar toggle not found, assuming it is already open.")

        # -------------------------------------------------------------
        # Globally Grounded Content Checklist Function
        # -------------------------------------------------------------
        def expand_and_check_filter(section_name, option_name):
            print(f"[#] Locating filter: '{option_name}' under '{section_name}'...")
            
            header = page.locator(".ui-accordion-header").filter(has_text=section_name).first
            if header.count() > 0:
                header_class = header.get_attribute("class") or ""
                if "ui-state-active" not in header_class:
                    print(f"    -> Expanding accordion section panel: '{section_name}'...")
                    header.scroll_into_view_if_needed()
                    header.click(force=True)
                    time.sleep(3) 
            
            target_row = page.locator("tr, li").filter(has=page.get_by_text(option_name, exact=False)).first
            
            if target_row.count() == 0:
                target_row = page.get_by_text(option_name, exact=False).first
                
            if target_row.count() == 0:
                print(f"    [!] Warning: Could not find text match for '{option_name}' on page.")
                return

            target_row.scroll_into_view_if_needed()
            
            clicked = False
            selectors = [
                ".ui-chkbox-box",         
                "input[type='checkbox']", 
                "div[role='checkbox']",   
                "td:first-child"          
            ]
            
            for selector in selectors:
                checkbox_element = target_row.locator(selector).first
                if checkbox_element.count() > 0:
                    try:
                        checkbox_element.click(force=True)
                        clicked = True
                        print(f"    [✔] Checked successfully via selector: '{selector}'")
                        break
                    except:
                        continue
            
            if not clicked:
                try:
                    target_row.click(force=True)
                    print(f"    [✔] Checked successfully via direct block click.")
                except Exception as e:
                    print(f"    [-] Intercept click failed: {e}")
            
            time.sleep(3) 

        # 4. Select Target Vehicle Categories
        expand_and_check_filter("Vehicle Category", "TWO WHEELER (Invalid Carriage)")
        expand_and_check_filter("Vehicle Category", "TWO WHEELER(NT)")
        expand_and_check_filter("Vehicle Category", "TWO WHEELER(T)")
        
        # 5. Select Target Fuel Typologies
        expand_and_check_filter("Fuel", "ELECTRIC(BOV)")
        expand_and_check_filter("Fuel", "PURE EV")
        
        # -------------------------------------------------------------
        # 6. SECOND REFRESH & EXCEL GENERATION
        # -------------------------------------------------------------
        print("[*] Clicking sidebar 'Refresh' button to process final filtered dataset...")
        page.locator("button", has_text="Refresh").last.click(force=True)
        time.sleep(12) 
        
        print("[*] Initiating download listener for the Excel export link...")
        try:
            with page.expect_download(timeout=60000) as download_info:
                excel_btn = page.locator("input[src*='excel' i], img[src*='excel' i], [title*='Excel' i]").first
                excel_btn.wait_for(state="visible", timeout=15000)
                excel_btn.scroll_into_view_if_needed()
                excel_btn.click(force=True)
            
            download = download_info.value
            download.save_as(EXCEL_FILE_PATH)
            print(f"\n[+] Success! Clean processed sheet saved directly to: {EXCEL_FILE_PATH}")
            
        except Exception as e:
            print(f"\n[-] Download stream timed out or was blocked by layout change: {e}")

        browser.close()

# =====================================================================
# INVOCATION
# =====================================================================
if __name__ == "__main__":
    try:
        download_raw_vahan_sheet() # Removed TARGET_YEAR from here
        print("\n[✔] Script cycle complete.")
    except Exception as err:
        print(f"\n[✘] Unexpected critical exception occurred: {err}")
