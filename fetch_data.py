import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

OUTPUT_FILE = "pharma_data.json"
DEBUG_DIR = "debug"

os.makedirs(DEBUG_DIR, exist_ok=True)

# Try to load secrets from a single JSON string environment variable (for easier setup)
config_json = os.environ.get("PHARMA_CONFIG")
if config_json:
    try:
        ext_config = json.loads(config_json)
        for k, v in ext_config.items():
            os.environ[k] = str(v)
    except Exception as e:
        print(f"Warning: Failed to parse PHARMA_CONFIG JSON: {e}")

async def fetch_collabo(page):
    print("\n--- Starting Collaboportal Scrape ---")
    data = []
    try:
        url = "https://szgp-app1.collaboportal.com/frontend#/NoukiSearch"
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)
        print(f"Current URL: {page.url}")
        
        if "login" in page.url or await page.locator('input[type="password"]').count() > 0:
            print("Login required for Collaboportal. Attempting login...")
            collabo_id = os.environ.get("COLLABO_ID")
            collabo_pw = os.environ.get("COLLABO_PW")
            if not collabo_id or not collabo_pw:
                print("Error: COLLABO_ID or COLLABO_PW not set in environment.")
                return []
                
            await page.fill('input[type="text"], input[placeholder="ID"]', collabo_id)
            await page.fill('input[type="password"]', collabo_pw)
            await page.click('button:has-text("ログイン"), .el-button--primary')
            print("Login button clicked. Waiting for redirection...")
            await page.wait_for_timeout(7000)
            print(f"URL after login: {page.url}")
            
            # Re-navigate if needed
            if "NoukiSearch" not in page.url:
                print("Redirecting to NoukiSearch manually...")
                await page.goto(url, wait_until="networkidle")
        
        await page.wait_for_timeout(5000)
        print("Scanned page for data...")
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        rows = soup.select(".nouki_table tbody tr.management_content_base, .nouki_table tbody tr.management_content_stock_out")
        print(f"Found {len(rows)} rows in Collaboportal table.")
            
        for row in rows:
            cols = row.select("td")
            if len(cols) >= 11:
                texts = [c.text.strip() for c in cols]
                item = {
                    "date": texts[1],
                    "code": texts[3].replace(" ", ""),
                    "maker": texts[4].replace(" ", ""),
                    "name": texts[5],
                    "order_qty": texts[6],
                    "deliv_qty": texts[7],
                    "deliv_date": texts[8],
                    "status": texts[9],
                    "remarks": texts[10] if len(texts) > 10 else ""
                }
                data.append(item)
                    
        print(f"Extraction successful: {len(data)} items found.")
    except Exception as e:
        print(f"Collabo Error: {e}")
    return data

async def fetch_medipal(page):
    print("\n--- Starting Medipal Scrape ---")
    data = []
    try:
        url = "https://www.medipal-app.com/App/servlet/InvokerServlet"
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        
        medipal_id = os.environ.get("MEDIPAL_ID")
        medipal_pw = os.environ.get("MEDIPAL_PW")
        if not medipal_id:
            print("Error: MEDIPAL_ID not set.")
            return []

        print("Filling login form...")
        await page.fill('input[placeholder="ID"], input[type="text"]', medipal_id)
        await page.fill('input[placeholder="パスワード"], input[type="password"]', medipal_pw)
        await page.click('img[src*="login"], button:has-text("ログイン"), .btnLogin')
        
        print("Waiting for Medipal dashboard...")
        await page.wait_for_timeout(8000)
        print(f"Current URL: {page.url}")
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Save debug HTML for inspection
        with open(os.path.join(DEBUG_DIR, "medipal_debug.html"), "w", encoding="utf-8") as f:
            f.write(html)

        rows = soup.select("tr")
        print(f"Found {len(rows)} rows in Medipal.")

        import re
        for row in rows:
            if row.find("th") or row.find("tr"):
                continue

            hnm_el   = row.select_one("td.MstHnm")
            if not hnm_el:
                continue

            scd_el    = row.select_one("td.MstScd")
            sur_el    = row.select_one("td.MstSur")
            haisou_el = row.select_one("td.MstHaisou")
            biko_el   = row.select_one("td.MstBiko")

            # メーカーとJANコードを分離
            scd_text = scd_el.text.strip() if scd_el else ""
            jan_match = re.search(r'(\d{13,14})', scd_text)
            code = jan_match.group(1) if jan_match else ""
            maker = scd_text.replace(code, "").strip() if code else scd_text

            name      = hnm_el.text.strip()
            order_qty = sur_el.text.strip() if sur_el else "-"
            deliv_qty = haisou_el.text.strip().split("\n")[0].strip() if haisou_el else "-"
            biko_text = biko_el.text.strip() if biko_el else ""

            has_error = bool(row.select_one(".MstKpnErr"))
            remarks   = "メーカー出荷調整品：入荷未定" if has_error else biko_text

            item = {
                "code": code,
                "maker": maker,
                "name": name,
                "order_qty": order_qty,
                "deliv_qty": deliv_qty,
                "remarks": remarks
            }

            if name and not any(d["name"] == name and d["code"] == code for d in data):
                data.append(item)

        print(f"Extraction successful: {len(data)} items found.")
    except Exception as e:
        print(f"Medipal Error: {e}")
    return data

async def fetch_alfweb(page):
    print("\n--- Starting ALF-Web Scrape ---")
    data = []
    try:
        url = "https://www.alf-web.com/portal2/portalLogin/select.do"
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Check if we need to click to login form
        login_btn = await page.locator("text=alf-web ログイン画面へ").count()
        if login_btn > 0:
            print("Clicking 'Go to login form' button...")
            await page.click("text=alf-web ログイン画面へ")
            await page.wait_for_timeout(2000)
        
        alfweb_id = os.environ.get("ALFWEB_ID")
        alfweb_pw = os.environ.get("ALFWEB_PW")
        if not alfweb_id:
            print("Error: ALFWEB_ID not set.")
            return []
            
        print("Filling ALF-Web login form...")
        await page.fill("input[name='loginId'], input[type='text'], #loginId", alfweb_id)
        await page.fill("input[name='password'], input[type='password'], #password", alfweb_pw)
        
        async with page.expect_navigation(wait_until="networkidle", timeout=30000):
            await page.click("input[type='image'][src*='login'], .loginBtn, a:has-text('ログイン')")
        
        print("Login complete. Proceeding to delivery info page...")
        await page.wait_for_timeout(5000)
        await page.goto("https://www.alf-web.com/portal2/contents/noDeliveryContentsDetailAction_init.do", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        print(f"Current URL: {page.url}")
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one(".pageDelivList tbody") or soup.select_one(".pageDelivList")
        rows = table.select("tr") if table else []
        print(f"Found {len(rows)} rows in ALF-Web table.")
        
        for row in rows:
            cols = row.select("td")
            if len(cols) >= 6:
                deliv_date_html = str(cols[5])
                if "出荷調整" in deliv_date_html or "icon" in deliv_date_html or "i" in cols[5].text or "pageDelivList__ic_i" in deliv_date_html:
                    name_el = cols[2]
                    name_text = name_el.select_one("span").contents[0].strip() if name_el.select_one("span") else name_el.text.strip().split('\n')[0]
                    item = {
                        "date": cols[0].text.strip(),
                        "maker": cols[1].text.strip(),
                        "name": name_text,
                        "order_qty": cols[3].text.strip(),
                        "deliv_qty": cols[4].text.strip() if len(cols) > 4 else "-",
                        "status": "出荷停止・入荷未定",
                    }
                    data.append(item)
        print(f"Extraction successful: {len(data)} items found.")
    except Exception as e:
        print(f"ALF-Web Error: {e}")
    return data

async def main():
    async with async_playwright() as p:
        JST = timezone(timedelta(hours=9), 'JST')
        print(f"--- Starting Browser (Time: {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')}) ---")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        
        collabo_data = await fetch_collabo(await context.new_page())
        medipal_data = await fetch_medipal(await context.new_page())
        alfweb_data = await fetch_alfweb(await context.new_page())
        
        result = {
            "collabo": collabo_data,
            "medipal": medipal_data,
            "alfweb": alfweb_data,
            "updated_at": datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if not any(result[k] for k in ["collabo", "medipal", "alfweb"] if isinstance(result[k], list)):
            print("WARNING: No data extracted from any site. Check your credentials or network status.")
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        print(f"Data extraction process finished. Total items in JSON: {len(collabo_data) + len(medipal_data) + len(alfweb_data)}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
