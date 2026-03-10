import asyncio
import json
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

OUTPUT_FILE = "pharma_data.json"

# テキストクレンジング用ヘルパー
def clean(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip()

async def fetch_collabo(page):
    print("\n--- Starting Collaboportal Scrape ---")
    data = []
    try:
        url = "https://szgp-app1.collaboportal.com/frontend#/NoukiSearch"
        await page.goto(url, wait_until="networkidle", timeout=60000)
        
        if "login" in page.url or await page.locator('input[type="password"]').count() > 0:
            print("Attempting login to Collaboportal...")
            await page.fill('input[type="text"], input[placeholder="ID"]', os.environ.get("COLLABO_ID", ""))
            await page.fill('input[type="password"]', os.environ.get("COLLABO_PW", ""))
            await page.click('button:has-text("ログイン"), .el-button--primary')
            await page.wait_for_url("**/NoukiSearch", timeout=30000)
        
        # データの読み込み完了を待機
        await page.wait_for_selector(".nouki_table", timeout=20000)
        await asyncio.sleep(2) # レンダリングの安定待ち
        
        soup = BeautifulSoup(await page.content(), "html.parser")
        rows = soup.select(".nouki_table tbody tr.management_content_base, .nouki_table tbody tr.management_content_stock_out")
        
        for row in rows:
            cols = row.select("td")
            if len(cols) >= 11:
                item = {
                    "date": clean(cols[1].text),
                    "code": clean(cols[3].text),
                    "maker": clean(cols[4].text),
                    "name": clean(cols[5].text) or "Unknown",
                    "order_qty": clean(cols[6].text),
                    "deliv_qty": clean(cols[7].text),
                    "status": clean(cols[9].text),
                    "remarks": clean(cols[10].text)
                }
                if any(x in item["status"] for x in ["調達中", "受注辞退", "保留"]):
                    data.append(item)
    except Exception as e:
        print(f"Collabo Error: {e}")
    return data

async def fetch_medipal(page):
    print("\n--- Starting Medipal Scrape ---")
    data = []
    try:
        url = "https://www.medipal-app.com/App/servlet/InvokerServlet"
        await page.goto(url, wait_until="networkidle")
        
        await page.fill('input[placeholder="ID"], input[type="text"]', os.environ.get("MEDIPAL_ID", ""))
        await page.fill('input[placeholder="パスワード"], input[type="password"]', os.environ.get("MEDIPAL_PW", ""))
        await page.click('img[src*="login"], button:has-text("ログイン")')
        
        # メインコンテンツの表示待ち
        await page.wait_for_selector(".MstKpnErr, #cFooter", timeout=30000)
        
        soup = BeautifulSoup(await page.content(), "html.parser")
        items_raw = soup.select(".MstKpnErr")
        
        for err_icon in items_raw:
            row = err_icon.find_parent("div", class_="row") or err_icon.find_parent("tr") or err_icon.find_parent("div")
            if row:
                name_el = row.select_one("[id^='hnmy']")
                # 名称が空の場合、title属性やテキスト全体から抽出を試みる
                name = clean(name_el.get_text()) if name_el else ""
                if not name and name_el: name = name_el.get("title", "")
                
                texts = [t.strip() for t in row.stripped_strings if t.strip()]
                data.append({
                    "code": texts[1] if len(texts) > 1 else "Unknown",
                    "maker": texts[2] if len(texts) > 2 else "",
                    "name": name or "Unknown",
                    "remarks": "メーカー出荷調整品：入荷未定"
                })
    except Exception as e:
        print(f"Medipal Error: {e}")
    return data

async def fetch_alfweb(page):
    print("\n--- Starting ALF-Web Scrape ---")
    data = []
    try:
        await page.goto("https://www.alf-web.com/portal2/portalLogin/select.do", wait_until="networkidle")
        if await page.locator("text=alf-web ログイン画面へ").count() > 0:
            await page.click("text=alf-web ログイン画面へ")
        
        await page.fill("#loginId", os.environ.get("ALFWEB_ID", ""))
        await page.fill("#password", os.environ.get("ALFWEB_PW", ""))
        await page.click("input[type='image'][src*='login']")
        
        # 未納品情報ページへ移動
        await page.goto("https://www.alf-web.com/portal2/contents/noDeliveryContentsDetailAction_init.do", wait_until="networkidle")
        await page.wait_for_selector(".pageDelivList", timeout=20000)
        
        soup = BeautifulSoup(await page.content(), "html.parser")
        rows = soup.select(".pageDelivList tbody tr")
        
        for row in rows:
            cols = row.select("td")
            if len(cols) >= 6:
                if "出荷調整" in str(cols[5]) or "i" in cols[5].text:
                    name_el = cols[2]
                    # span内のテキストを優先し、改行で分割して1行目（薬品名）を取得
                    name = name_el.get_text(separator="\n").split("\n")[0].strip()
                    data.append({
                        "date": clean(cols[0].text),
                        "maker": clean(cols[1].text),
                        "name": name or "Unknown",
                        "order_qty": clean(cols[3].text),
                        "status": "出荷停止・入荷未定",
                    })
    except Exception as e:
        print(f"ALF-Web Error: {e}")
    return data

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        results = {
            "collabo": await fetch_collabo(await context.new_page()),
            "medipal": await fetch_medipal(await context.new_page()),
            "alfweb": await fetch_alfweb(await context.new_page()),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\nFinished. Total: {len(results['collabo'])+len(results['medipal'])+len(results['alfweb'])} items.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
