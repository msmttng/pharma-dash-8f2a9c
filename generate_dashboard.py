from datetime import datetime
import json
import os

INPUT_FILE = "pharma_data.json"
OUTPUT_FILE = "index.html"

def generate_html(data):
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="robots" content="noindex, nofollow">
        <title>医薬品調達情報 統合ダッシュボード</title>
        <style>
            :root {{
                --primary: #1976D2; --secondary: #00897B; --tertiary: #5E35B1;
                --bg: #f4f6f8; --surface: #ffffff; --text: #333333;
                --text-secondary: #666666; --border: #e0e0e0;
                --danger: #d32f2f; --warning: #f57c00;
            }}
            body {{ font-family: 'Segoe UI', 'Noto Sans JP', sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 0; }}
            .header {{ background-color: var(--surface); padding: 1.5rem 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }}
            .header h1 {{ margin: 0; font-size: 1.5rem; }}
            .last-updated {{ font-size: 0.9rem; color: var(--text-secondary); background-color: #f0f0f0; padding: 0.4rem 0.8rem; border-radius: 20px; }}
            .container {{ max-width: 1400px; margin: 2rem auto; padding: 0 1rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; }}
            .card {{ background: var(--surface); border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow: hidden; display: flex; flex-direction: column; }}
            .card-header {{ padding: 1rem 1.5rem; color: white; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }}
            .card-collabo {{ background-color: var(--tertiary); }}
            .card-medipal {{ background-color: var(--primary); }}
            .card-alfweb {{ background-color: var(--secondary); }}
            .item-count {{ background: rgba(255,255,255,0.2); padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.85rem; }}
            .table-container {{ overflow-x: auto; flex-grow: 1; max-height: 600px; }}
            table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }}
            th {{ background-color: #f8f9fa; padding: 0.8rem 1rem; position: sticky; top: 0; z-index: 10; border-bottom: 2px solid var(--border); }}
            td {{ padding: 0.8rem 1rem; border-bottom: 1px solid var(--border); vertical-align: top; }}
            .status-badge {{ display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: 600; background-color: var(--warning); color: white; }}
            .status-danger {{ background-color: var(--danger); }}
            .maker-name {{ font-size: 0.8rem; color: var(--text-secondary); display: block; }}
            .product-name {{ font-weight: 600; margin: 0.2rem 0; }}
            .product-code {{ font-size: 0.75rem; color: #888; font-family: monospace; }}
            .remarks {{ font-size: 0.8rem; color: var(--text-secondary); background-color: #fff8e1; padding: 0.3rem 0.5rem; border-radius: 4px; border-left: 3px solid #ffca28; margin-top: 0.4rem; display: inline-block; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>💊 医薬品調達情報 統合ダッシュボード</h1>
            <div class="last-updated">最終更新: {data.get("updated_at", "不明")}</div>
        </div>
        <div class="container">
            <div class="card">
                <div class="card-header card-collabo"><span>Collabo Portal</span><span class="item-count">{len(data.get("collabo", []))}件</span></div>
                <div class="table-container">
                    <table><thead><tr><th>品名/メーカー</th><th>状況</th><th>数量</th></tr></thead><tbody>
                    {"".join([f'<tr><td><span class="maker-name">{i.get("maker")}</span><div class="product-name">{i.get("name")}</div><span class="product-code">JAN: {i.get("code")}</span>' + (f'<div class="remarks">{i.get("remarks")}</div>' if i.get("remarks") else "") + f'</td><td><span class="status-badge {"status-danger" if "辞退" in i.get("status") else ""}">{i.get("status")}</span><div style="font-size:0.8rem;margin-top:4px;">{i.get("date")}</div></td><td>発注:<b>{i.get("order_qty")}</b><br>納品:<b>{i.get("deliv_qty")}</b></td></tr>' for i in data.get("collabo", [])])}
                    </tbody></table>
                </div>
            </div>
            <div class="card">
                <div class="card-header card-medipal"><span>MEDIPAL</span><span class="item-count">{len(data.get("medipal", []))}件</span></div>
                <div class="table-container">
                    <table><thead><tr><th>品名/メーカー</th><th>状況・備考</th></tr></thead><tbody>
                    {"".join([f'<tr><td><span class="maker-name">{i.get("maker")}</span><div class="product-name">{i.get("name")}</div><span class="product-code">{i.get("code")}</span></td><td><span class="status-badge status-danger">入荷未定</span><div style="font-size:0.8rem;margin-top:4px;">{i.get("remarks")}</div></td></tr>' for i in data.get("medipal", [])])}
                    </tbody></table>
                </div>
            </div>
            <div class="card">
                <div class="card-header card-alfweb"><span>ALF-Web</span><span class="item-count">{len(data.get("alfweb", []))}件</span></div>
                <div class="table-container">
                    <table><thead><tr><th>品名/メーカー</th><th>状況</th><th>発注数</th></tr></thead><tbody>
                    {"".join([f'<tr><td><span class="maker-name">{i.get("maker")}</span><div class="product-name">{i.get("name")}</div></td><td><span class="status-badge status-danger">{i.get("status")}</span><div style="font-size:0.8rem;margin-top:4px;">{i.get("date")}</div></td><td><b>{i.get("order_qty")}</b></td></tr>' for i in data.get("alfweb", [])])}
                    </tbody></table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r", encoding="utf-8") as f: data = json.load(f)
        generate_html(data)
