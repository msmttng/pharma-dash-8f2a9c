import asyncio
import json
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

OUTPUT_FILE = "pharma_data.json"

async def save_debug_screenshot(page, name):
    """デバッグ用に現在の画面を保存する"""
    path = f"debug_{name}_{datetime.now().strftime('%H%M%S')}.png"
    await page.screenshot(path=path)
    print(f"DEBUG: Saved screenshot to {path}")

async def fetch_collabo(page):
    print("\n--- Collaboportal Scrape ---")
    data = []
    try:
        await page.goto("https://szgp-app1.collaboportal.com/frontend#/NoukiSearch", wait_until="networkidle")
        # ログイン判定
        if await page.locator('input[type="password"]').count() > 0:
            await page.fill('input[type="text"]', os.environ.get("COLLABO_ID", ""))
            await page.fill('input[type="password"]', os.environ.get("COLLABO_PW", ""))
            await page.click('button:has-text("ログイン")')
            await page.wait_for_timeout(5000)

        # データのテーブルが表示されるまで最大30秒待機
        try:
            await page.wait_for_selector("table", timeout=30000)
        except:
            await save_debug_screenshot(page, "collabo_fail")
            return []

        soup = BeautifulSoup(await page.content(), "html.parser")
        # 修正：クラス名に頼らず、tr要素を広めに取得
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 10:
                # 文字列が含まれる列を動的に判定
                txt = [c.get_text(strip=True) for c in cols]
                # 調達中などのステータスがある行のみ抽出
                if any(s in txt[9] for s in ["調達中", "受注辞退", "保留"]):
                    data.append({
                        "date": txt[1], "code": txt[3], "maker": txt[4],
                        "name": txt[5] if txt[5] else "Unknown",
                        "order_qty": txt[6], "deliv_qty": txt[7],
                        "status": txt[9], "remarks": txt[10] if len(txt) > 10 else ""
                    })
    except Exception as e:
        print(f"Collabo Error: {e}")
    return data

async def fetch_medipal(page):
    print("\n--- Medipal Scrape ---")
    data = []
    try:
        await page.goto("https://www.medipal-app.com/App/servlet/InvokerServlet")
        await page.fill('input[type="text"]', os.environ.get("MEDIPAL_ID", ""))
        await page.fill('input[type="password"]', os.environ.get("MEDIPAL_PW", ""))
        await page.click('button:has-text("ログイン"), img[src*="login"]')
        
        # 画面の描画を待つ
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(5000)
        
        await save_debug_screenshot(page, "medipal_after_login")

        soup = BeautifulSoup(await page.content(), "html.parser")
        # 修正：特定のクラス名(MstKpnErr)がない場合を想定し、エラーアイコンや特定のキーワードで探す
        for row in soup.find_all(["div", "tr"]):
            if "入荷未定" in row.get_text() or "出荷調整" in row.get_text():
                # その行に含まれるテキスト群から「長い文字列」を薬品名とみなす
                texts = [t.strip() for t in row.stripped_strings if len(t.strip()) > 2]
                if len(texts) >= 3:
                    data.append({
                        "code": texts[0], "maker": texts[1], "name": texts[2],
                        "remarks": "メーカー出荷調整品：入荷未定"
                    })
    except Exception as e:
        print(f"Medipal Error: {e}")
    return data

async def fetch_alfweb(page):
    print("\n--- ALF-Web Scrape ---")
    data = []
    try:
        await page.goto("https://www.alf-web.com/portal2/portalLogin/select.do")
        if await page.locator("text=alf-web ログイン画面へ").count() > 0:
            await page.click("text=alf-web ログイン画面へ")
        
        await page.fill("#loginId", os.environ.get("ALFWEB_ID", ""))
        await page.fill("#password", os.environ.get("ALFWEB_PW", ""))
        await page.click("input[type='image']")
        
        # 未納品ページへ遷移
        await page.goto("https://www.alf-web.com/portal2/contents/noDeliveryContentsDetailAction_init.do")
        await page.wait_for_selector("table", timeout=20000)
        
        await save_debug_screenshot(page, "alfweb_list")

        soup = BeautifulSoup(await page.content(), "html.parser")
        rows = soup.select("table tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 5:
                # 3列目が品名であることが多いため、そこを取得
                name = cols[2].get_text(separator=" ", strip=True).split("\n")[0]
                if "出荷調整" in row.get_text() or "i" in cols[-1].get_text():
                    data.append({
                        "date": cols[0].get_text(strip=True),
                        "maker": cols[1].get_text(strip=True),
                        "name": name if name else "Unknown",
                        "status": "出荷調整中/未納",
                    })
    except Exception as e:
        print(f"ALF-Web Error: {e}")
    return data

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # 失敗時はここをFalseにして目視確認
        context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        results = {
            "collabo": await fetch_collabo(await context.new_page()),
            "medipal": await fetch_medipal(await context.new_page()),
            "alfweb": await fetch_alfweb(await context.new_page()),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("Done.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
