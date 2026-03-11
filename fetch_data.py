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
        
        with open(os.path.join(DEBUG_DIR, "medipal_debug.html"), "w", encoding="utf-8") as f:
            f.write(html)

        rows = soup.select("tr")
        print(f"Found {len(rows)} rows in Medipal.")
        
        for row in rows:
            if row.find("th") or row.find("tr"):
                continue

            no_el    = row.select_one("td.MstNo")
            scd_el   = row.select_one("td.MstScd")
            hnm_el   = row.select_one("td.MstHnm")
            sur_el   = row.select_one("td.MstSur")
            haisou_el = row.select_one("td.MstHaisou")
            biko_el  = row.select_one("td.MstBiko")

            if not hnm_el:
                continue

            # メーカーとJANコードはMstScdにくっついているので分離
            scd_text = scd_el.text.strip() if scd_el else ""
            # JANコードは14桁の数字
            import re
            jan_match = re.search(r'(\d{13,14})', scd_text)
            code = jan_match.group(1) if jan_match else ""
            maker = scd_text.replace(code, "").strip() if code else scd_text

            name = hnm_el.text.strip() if hnm_el else ""
            order_qty = sur_el.text.strip() if sur_el else "-"
            deliv_info = haisou_el.text.strip().split("\n")[0].strip() if haisou_el else ""
            biko_text = biko_el.text.strip() if biko_el else ""

            has_error = bool(row.select_one(".MstKpnErr"))
            remarks = "メーカー出荷調整品：入荷未定" if has_error else biko_text

            item = {
                "code": code,
                "maker": maker,
                "name": name,
                "order_qty": order_qty,
                "deliv_qty": deliv_info,
                "remarks": remarks
            }

            if name and not any(d["name"] == name and d["code"] == code for d in data):
                data.append(item)

        print(f"Extraction successful: {len(data)} items found.")
    except Exception as e:
        print(f"Medipal Error: {e}")
    return data
