import json
import os
from datetime import datetime

INPUT_FILE = "pharma_data.json"
OUTPUT_FILE = "index.html"

def get_safe_name(item):
    """医薬品名が不明な場合に、コードを強調して表示する"""
    name = item.get("name", "Unknown")
    code = item.get("code", "不明")
    
    if not name or name.lower() == "unknown":
        return f'<span style="color: #ef4444; font-weight: bold;">【名称取得失敗】</span><br><small>コード: {code}</small>'
    return name

def generate_html(data):
    collabo = data.get("collabo", [])
    medipal = data.get("medipal", [])
    alfweb = data.get("alfweb", [])
    updated_at = data.get("updated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>医薬品調達 統合ダッシュボード</title>
        <style>
            :root {{
                --primary: #42A5F5; --secondary: #66BB6A; --tertiary: #4FC3F7;
                --bg: #f1f5f9; --surface: #ffffff; --text: #0f172a; --border: #e2e8f0;
            }}
            body {{ font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', sans-serif; background: var(--bg); margin: 0; font-size: 14px; }}
            .header {{ background: white; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--primary); }}
            .container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 10px; padding: 10px; }}
            .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; flex-direction: column; height: 90vh; }}
            .card-header {{ padding: 10px; color: white; font-weight: bold; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; }}
            .table-container {{ overflow-y: auto; flex-grow: 1; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ position: sticky; top: 0; background: #f8fafc; z-index: 1; padding: 8px; text-align: left; border-bottom: 2px solid var(--border); }}
            td {{ padding: 8px; border-bottom: 1px solid var(--border); vertical-align: top; }}
            .status-badge {{ background: #fee2e2; color: #b91c1c; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
            .maker {{ font-size: 11px; color: #64748b; }}
            .product-name {{ font-weight: 600; line-height: 1.4; }}
            .remarks {{ font-size: 11px; background: #fffbeb; color: #92400e; padding: 4px; border-radius: 4px; margin-top: 4px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin:0">💊 医薬品調達情報 統合ダッシュボード</h2>
            <div style="font-size: 12px; color: #64748b;">最終更新: {updated_at}</div>
        </div>
        <div class="container">
            <div class="card">
                <div class="card-header" style="background: var(--tertiary)">Collabo Portal ({len(collabo)}件)</div>
                <div class="table-container">
                    <table>
                        <thead><tr><th>品名/メーカー</th><th>状況</th><th>数量</th></tr></thead>
                        <tbody>
                            {"".join([f'<tr><td><div class="maker">{item.get("maker")}</div><div class="product-name">{get_safe_name(item)}</div><div class="remarks">{item.get("remarks")}</div></td><td><span class="status-badge">{item.get("status")}</span></td><td>{item.get("order_qty")} / {item.get("deliv_qty")}</td></tr>' for item in collabo])}
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="card">
                <div class="card-header" style="background: var(--secondary)">MEDIPAL ({len(medipal)}件)</div>
                <div class="table-container">
                    <table>
                        <thead><tr><th>品名/メーカー</th><th>備考</th></tr></thead>
                        <tbody>
                            {"".join([f'<tr><td><div class="maker">{item.get("maker")}</div><div class="product-name">{get_safe_name(item)}</div></td><td><span class="status-badge">入荷未定</span></td></tr>' for item in medipal])}
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="card">
                <div class="card-header" style="background: var(--primary)">ALF-Web ({len(alfweb)}件)</div>
                <div class="table-container">
                    <table>
                        <thead><tr><th>品名/メーカー</th><th>状況</th></tr></thead>
                        <tbody>
                            {"".join([f'<tr><td><div class="maker">{item.get("maker")}</div><div class="product-name">{get_safe_name(item)}</div></td><td><span class="status-badge">{item.get("status")}</span></td></tr>' for item in alfweb])}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Success: {OUTPUT_FILE} generated.")

if __name__ == "__main__":
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            generate_html(json.load(f))
    else:
        print(f"Error: {INPUT_FILE} not found.")
