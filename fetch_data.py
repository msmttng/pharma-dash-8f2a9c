import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

OUTPUT_FILE = "pharma_data.json"
DEBUG_DIR = "debug"

os.makedirs(DEBUG_DIR, exist_ok=True)

async def fetch_collabo(page):
    print("Fetching Collaboportal...")
    data = []
    try:
        await page.goto("https://szgp-app1.collaboportal.com/frontend#/NoukiSearch", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # Check if login is required (if we are on login screen)
        if "login" in page.url or await page.locator('input[type="password"]').count() > 0:
            print("Logging into Collaboportal...")
            collabo_id = os.environ.get("COLLABO_ID", "6330967")
            collabo_pw = os.environ.get("COLLABO_PW", "m1m1m1m1")
            await page.fill('input[type="text"], input[placeholder="ID"]', collabo_id)
            await page.fill('input[type="password"]', collabo_pw)
            
            # Try to find and click the login button
            await page.click('button:has-text("ログイン"), .el-button--primary')
            await page.wait_for_timeout(5000)
            
        await page.goto("https://szgp-app1.collaboportal.com/frontend#/NoukiSearch", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        await page.screenshot(path=f"{DEBUG_DIR}/collabo.png")
        
        # We need to extract the table data
        html = await page.content()
        with open(f"{DEBUG_DIR}/collabo.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        soup = BeautifulSoup(html, "html.parser")
        
        # Collabo uses multiple nested loops, elements are in td > span
        rows = soup.select(".nouki_table tbody tr.management_content_base, .nouki_table tbody tr.management_content_stock_out")
            
        for row in rows:
            cols = row.select("td")
            if len(cols) >= 11:
                # Use span text inside td
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
                # Filter specific statuses
                if "調達中" in item["status"] or "受注辞退" in item["status"] or "保留" in item["status"]:
                    data.append(item)
    except Exception as e:
        print(f"Collabo Error: {e}")
    return data

async def fetch_medipal(page):
    print("Fetching Medipal...")
    data = []
    try:
        await page.goto("https://www.medipal-app.com/App/servlet/InvokerServlet", wait_until="networkidle")
        await page.screenshot(path=f"{DEBUG_DIR}/medipal_login.png")
        
        # Login
        # Medipal form uses placeholders 'ID' and 'パスワード'
        medipal_id = os.environ.get("MEDIPAL_ID", "000877242")
        medipal_pw = os.environ.get("MEDIPAL_PW", "m1m1m1m1")
        await page.fill('input[placeholder="ID"], input[type="text"]', medipal_id)
        await page.fill('input[placeholder="パスワード"], input[type="password"]', medipal_pw)
        await page.click('img[src*="login"], button:has-text("ログイン"), input[type="button"][value="ログイン"], .btnLogin')
        
        await page.wait_for_timeout(5000)
        # Select "欠品のみ" in filter if possible
        try:
            # We don't know the exact selector, so we will just dump HTML and see
            await page.select_option('select', label='欠品のみ')
            await page.wait_for_timeout(2000)
        except Exception:
            pass
            
        await page.screenshot(path=f"{DEBUG_DIR}/medipal_data.png")
        html = await page.content()
        with open(f"{DEBUG_DIR}/medipal.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        soup = BeautifulSoup(html, "html.parser")
        # "section#cFooter" and Target Status Identifier: links (icons) with the class `.MstKpnErr`
        container = soup.select_one("section#cFooter") or soup
        # We need to extract the data rows. Based on subagent, they are div elements.
        for err_icon in container.select(".MstKpnErr"):
            # Find the parent row
            row = err_icon.find_parent("div", class_="row") or err_icon.find_parent("tr") or err_icon.find_parent("div")
            if row:
                name_el = row.select_one("[id^='hnmy']")
                name = name_el.text.strip() if name_el else "Unknown"
                
                # Try to extract other fields by their relative positions or classes
                texts = [t.strip() for t in row.stripped_strings]
                item = {
                    "code": texts[1] if len(texts) > 1 else "",
                    "maker": texts[2] if len(texts) > 2 else "",
                    "name": name,
                    "remarks": "メーカー出荷調整品：入荷未定"
                }
                if item not in data:
                    data.append(item)
                    
    except Exception as e:
        print(f"Medipal Error: {e}")
    return data

async def fetch_alfweb(page):
    print("Fetching ALF-Web...")
    data = []
    try:
        await page.goto("https://www.alf-web.com/portal2/portalLogin/select.do", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        # Sometimes there's a button to go to login form
        try:
            await page.click("text=alf-web ログイン画面へ", timeout=3000)
        except:
            pass
            
        await page.screenshot(path=f"{DEBUG_DIR}/alfweb_login.png")
        
        # Login Form Fields
        alfweb_id = os.environ.get("ALFWEB_ID", "100104554")
        alfweb_pw = os.environ.get("ALFWEB_PW", "m1m1m1m1")
        await page.fill("input[name='loginId'], input[type='text'], #loginId", alfweb_id)
        await page.fill("input[name='password'], input[type='password'], #password", alfweb_pw)
        
        # Wait for any navigation
        async with page.expect_navigation(wait_until="networkidle", timeout=30000):
            await page.click("input[type='image'][src*='login'], .loginBtn, a:has-text('ログイン')")
        
        await page.wait_for_timeout(5000)
        await page.goto("https://www.alf-web.com/portal2/contents/noDeliveryContentsDetailAction_init.do", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        await page.screenshot(path=f"{DEBUG_DIR}/alfweb_data.png")
        html = await page.content()
        with open(f"{DEBUG_DIR}/alfweb.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one(".pageDelivList tbody")
        rows = table.select("tr") if table else soup.select(".pageDelivList tr")
        
        for row in rows:
            cols = row.select("td")
            if len(cols) >= 6:
                deliv_date_html = str(cols[5])
                # Check for the info icon which indicates supply issues
                if "出荷調整" in deliv_date_html or "icon" in deliv_date_html or "i" in cols[5].text or "pageDelivList__ic_i" in deliv_date_html:
                    # Clean up the name string which might have inline elements
                    name_el = cols[2]
                    # Get only direct text nodes, or the first span text
                    name_text = name_el.select_one("span").contents[0].strip() if name_el.select_one("span") else name_el.text.strip().split('\n')[0]
                    
                    item = {
                        "date": cols[0].text.strip(),
                        "maker": cols[1].text.strip(),
                        "name": name_text,
                        "order_qty": cols[3].text.strip(),
                        "status": "出荷停止・入荷未定",
                    }
                    data.append(item)
    except Exception as e:
        print(f"ALF-Web Error: {e}")
    return data

async def main():
    async with async_playwright() as p:
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
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        print("Data extraction complete.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
