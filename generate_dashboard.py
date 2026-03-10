from datetime import datetime
import json
import os

INPUT_FILE = "pharma_data.json"
OUTPUT_FILE = "index.html"

def generate_html(data):
    # Try to load secrets from JSON string first
    config_json = os.environ.get("PHARMA_CONFIG")
    if config_json:
        try:
            ext_config = json.loads(config_json)
            for k, v in ext_config.items():
                os.environ[k] = str(v)
        except Exception:
            pass
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="robots" content="noindex, nofollow"> <!-- Prevent Search Engine Indexing -->
        <title>医薬品調達情報 統合ダッシュボード</title>
        <style>
            :root {{
                --primary: #1976D2;
                --secondary: #00897B;
                --tertiary: #5E35B1;
                --bg: #f4f6f8;
                --surface: #ffffff;
                --text: #333333;
                --text-secondary: #666666;
                --border: #e0e0e0;
                --danger: #d32f2f;
                --warning: #f57c00;
            }}
            
            body {{
                font-family: 'Segoe UI', 'Noto Sans JP', sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 0;
                line-height: 1.6;
            }}
            
            .header {{
                background-color: var(--surface);
                padding: 1.5rem 2rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: sticky;
                top: 0;
                z-index: 100;
            }}
            
            .header h1 {{
                margin: 0;
                font-size: 1.5rem;
                color: var(--text);
                font-weight: 600;
            }}
            
            .last-updated {{
                font-size: 0.9rem;
                color: var(--text-secondary);
                background-color: #f0f0f0;
                padding: 0.4rem 0.8rem;
                border-radius: 20px;
            }}
            
            .container {{
                max-width: 100%;
                margin: 1rem auto;
                padding: 0 1rem;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 1rem;
            }}
            
            .card {{
                background: var(--surface);
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                overflow: hidden;
                display: flex;
                flex-direction: column;
                height: 100%;
            }}
            
            .card-header {{
                padding: 1rem 1.5rem;
                color: white;
                font-weight: 600;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .card-collabo {{ background-color: var(--tertiary); }}
            .card-medipal {{ background-color: var(--primary); }}
            .card-alfweb {{ background-color: var(--secondary); }}
            
            .item-count {{
                background: rgba(255,255,255,0.2);
                padding: 0.2rem 0.6rem;
                border-radius: 12px;
                font-size: 0.85rem;
            }}
            
            /* Vertical monitor optimization */
            @media (min-aspect-ratio: 1/1) {{
                .table-container {{
                    max-height: 60vh;
                }}
            }}
            
            @media (max-aspect-ratio: 1/1) {{
                .container {{
                    grid-template-columns: 1fr;
                }}
                .table-container {{
                    max-height: none; /* Let it expand on vertical monitors */
                }}
            }}

            .fullscreen-btn {{
                background-color: var(--primary);
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 600;
                font-size: 0.85rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                transition: background-color 0.2s;
            }}
            
            .fullscreen-btn:hover {{
                background-color: #1565C0;
            }}

            .table-container {{
                overflow-x: auto;
                flex-grow: 1;
                overflow-y: auto;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                text-align: left;
                font-size: 0.9rem;
            }}
            
            th {{
                background-color: #f8f9fa;
                padding: 0.8rem 1rem;
                font-weight: 600;
                color: var(--text-secondary);
                border-bottom: 2px solid var(--border);
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            
            td {{
                padding: 0.8rem 1rem;
                border-bottom: 1px solid var(--border);
                vertical-align: top;
            }}
            
            tr:hover td {{
                background-color: #f5f8ff;
            }}
            
            .status-badge {{
                display: inline-block;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.8rem;
                font-weight: 600;
                background-color: var(--warning);
                color: white;
            }}
            
            .status-danger {{
                background-color: var(--danger);
            }}
            
            .maker-name {{
                font-size: 0.8rem;
                color: var(--text-secondary);
                display: block;
                margin-bottom: 0.2rem;
            }}
            
            .product-name {{
                font-weight: 600;
                color: var(--text);
                margin-bottom: 0.2rem;
            }}
            
            .product-code {{
                font-size: 0.75rem;
                color: #888;
                font-family: monospace;
            }}
            
            .remarks {{
                font-size: 0.8rem;
                color: var(--text-secondary);
                background-color: #fff8e1;
                padding: 0.3rem 0.5rem;
                border-radius: 4px;
                border-left: 3px solid #ffca28;
                margin-top: 0.4rem;
                display: inline-block;
            }}
            
            .empty-state {{
                padding: 3rem;
                text-align: center;
                color: var(--text-secondary);
                font-style: italic;
            }}
        </style>
        <script>
            function toggleFullScreen() {{
                if (!document.fullscreenElement) {{
                    document.documentElement.requestFullscreen().catch(err => {{
                        alert(`Error attempting to enable full-screen mode: ${{err.message}} (${{err.name}})`);
                    }});
                }} else {{
                    if (document.exitFullscreen) {{
                        document.exitFullscreen();
                    }}
                }}
            }}
        </script>
    </head>
    <body>
        <div class="header">
            <div style="display: flex; align-items: center; gap: 1.5rem;">
                <h1>💊 医薬品調達情報 統合ダッシュボード</h1>
                <button class="fullscreen-btn" onclick="toggleFullScreen()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path></svg>
                    全画面表示
                </button>
            </div>
            <div class="last-updated">最終更新: {data.get("updated_at", "不明")}</div>
        </div>
        
        <div class="container">
    """
    
    # 1. Collaboportal
    collabo_data = data.get("collabo", [])
    html += f"""
            <div class="card">
                <div class="card-header card-collabo">
                    <span>Collabo Portal (調達中・受注辞退)</span>
                    <span class="item-count">{{len(collabo_data)}}件</span>
                </div>
                <div class="table-container">
                    {{"<table><thead><tr><th>品名/メーカー</th><th>状況/納期</th><th>数量</th></tr></thead><tbody>" if collabo_data else '<div class="empty-state">該当データなし</div>'}}
    """
    for item in collabo_data:
        status_class = "status-danger" if "辞退" in item.get("status", "") else ""
        remarks_html = f'<div class="remarks">{{item.get("remarks")}}</div>' if item.get("remarks") else ""
        date_html = f'<div style="font-size:0.8rem; margin-top:4px;">受付: {{item.get("date")}}</div>' if item.get("date") else ""
        
        html += f"""
                        <tr>
                            <td>
                                <span class="maker-name">{{item.get("maker", "")}}</span>
                                <div class="product-name">{{item.get("name", "")}}</div>
                                <span class="product-code">JAN: {{item.get("code", "")}}</span>
                                {{remarks_html}}
                            </td>
                            <td>
                                <span class="status-badge {{status_class}}">{{item.get("status", "")}}</span>
                                {{date_html}}
                            </td>
                            <td>
                                <div>発注: <b>{{item.get("order_qty", "-")}}</b></div>
                                <div>納品予定: <b>{{item.get("deliv_qty", "-")}}</b></div>
                            </td>
                        </tr>
        """
    if collabo_data: html += "</tbody></table>"
    html += "</div></div>"

    # 2. Medipal
    medipal_data = data.get("medipal", [])
    html += f"""
            <div class="card">
                <div class="card-header card-medipal">
                    <span>MEDIPAL (メーカー出荷調整品：入荷未定)</span>
                    <span class="item-count">{{len(medipal_data)}}件</span>
                </div>
                <div class="table-container">
                    {{"<table><thead><tr><th>品名/メーカー</th><th>状況・備考</th></tr></thead><tbody>" if medipal_data else '<div class="empty-state">該当データなし</div>'}}
    """
    for item in medipal_data:
        html += f"""
                        <tr>
                            <td>
                                <span class="maker-name">{{item.get("maker", "")}}</span>
                                <div class="product-name">{{item.get("name", "")}}</div>
                                <span class="product-code">{{item.get("code", "")}}</span>
                            </td>
                            <td>
                                <span class="status-badge status-danger">入荷未定</span>
                                <div style="font-size:0.8rem; margin-top:4px;">{{item.get("remarks", "")}}</div>
                            </td>
                        </tr>
        """
    if medipal_data: html += "</tbody></table>"
    html += "</div></div>"

    # 3. ALF-Web
    alfweb_data = data.get("alfweb", [])
    html += f"""
            <div class="card">
                <div class="card-header card-alfweb">
                    <span>ALF-Web (出荷停止・入荷未定)</span>
                    <span class="item-count">{{len(alfweb_data)}}件</span>
                </div>
                <div class="table-container">
                    {{"<table><thead><tr><th>品名/メーカー</th><th>状況</th><th>発注数</th></tr></thead><tbody>" if alfweb_data else '<div class="empty-state">該当データなし</div>'}}
    """
    for item in alfweb_data:
        date_html = f'<div style="font-size:0.8rem; margin-top:4px;">更新: {{item.get("date")}}</div>' if item.get("date") else ""
        html += f"""
                        <tr>
                            <td>
                                <span class="maker-name">{{item.get("maker", "")}}</span>
                                <div class="product-name">{{item.get("name", "")}}</div>
                            </td>
                            <td>
                                <span class="status-badge status-danger">{{item.get("status", "")}}</span>
                                {{date_html}}
                            </td>
                            <td>
                                <b>{{item.get("order_qty", "-")}}</b>
                            </td>
                        </tr>
        """
    if alfweb_data: html += "</tbody></table>"
    
    html += """
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Dashboard generated at: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        generate_html(data)
    else:
        print(f"Error: {INPUT_FILE} not found. Please run fetch_data.py first.")
