import json
import os
from datetime import datetime, timezone, timedelta

INPUT_FILE = "pharma_data.json"
OUTPUT_FILE = "index.html"

def generate_html(data):
    collabo_data = data.get("collabo", [])
    medipal_data = data.get("medipal", [])
    alfweb_data = data.get("alfweb", [])
    JST = timezone(timedelta(hours=9), 'JST')
    updated_at = data.get("updated_at", datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S"))

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
                --primary: #42A5F5; /* ALF-Web Blue */
                --secondary: #008B3E; /* MEDIPAL Green */
                --tertiary: #4FC3F7; /* Collabo Water Blue */
                --bg: #f8fafc;
                --surface: #ffffff;
                --text: #1e293b;
                --text-secondary: #64748b;
                --border: #e2e8f0;
                --danger: #ef4444;
                --warning: #f59e0b;
                --status-bg-danger: #fee2e2;
                --status-text-danger: #b91c1c;
                --status-bg-warning: #fef3c7;
                --status-text-warning: #b45309;
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
                padding: 1rem 1.5rem;
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
                font-size: 1.2rem;
                color: var(--text);
                font-weight: 600;
            }}
            
            .last-updated {{
                font-size: 0.8rem;
                color: var(--text-secondary);
                background-color: #f0f0f0;
                padding: 0.3rem 0.6rem;
                border-radius: 20px;
            }}
            
            .container {{
                max-width: 100%;
                margin: 0.5rem auto;
                padding: 0 0.5rem;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 0.75rem;
            }}
            
            .card {{
                background: var(--surface);
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                overflow: hidden;
                display: flex;
                flex-direction: column;
                height: calc(100vh - 100px); /* Fill most of the screen height */
            }}
            
            .card-header {{
                padding: 0.75rem 1rem;
                color: white;
                font-weight: 600;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 0.9rem;
            }}
            
            .card-collabo {{ background-color: #0000cd; }}
            .card-medipal {{ background-color: var(--secondary); }}
            .card-alfweb {{ background-color: var(--primary); }}
            
            .item-count {{
                background: rgba(255,255,255,0.2);
                padding: 0.1rem 0.5rem;
                border-radius: 12px;
                font-size: 0.8rem;
            }}
            
            /* High density for vertical monitors */
            .table-container {{
                overflow-x: auto;
                flex-grow: 1;
                overflow-y: auto;
                max-height: none;
            }}

            .fullscreen-btn {{
                background-color: var(--primary);
                color: white;
                border: none;
                padding: 0.4rem 0.8rem;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 600;
                font-size: 0.8rem;
                display: flex;
                align-items: center;
                gap: 0.4rem;
                transition: background-color 0.2s;
            }}
            
            .fullscreen-btn:hover {{
                background-color: #1565C0;
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
                white-space: nowrap;
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
                padding: 0.2rem 0.6rem;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 600;
                background-color: var(--status-bg-warning);
                color: var(--status-text-warning);
                border: 1px solid rgba(180, 83, 9, 0.1);
                white-space: nowrap;
            }}
            
            .status-danger {{
                background-color: var(--status-bg-danger);
                color: var(--status-text-danger);
                border: 1px solid rgba(185, 28, 28, 0.1);
            }}
            
            .status-success {{
                background-color: #dcfce7;
                color: #166534;
                border: 1px solid rgba(22, 101, 52, 0.1);
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
            
            function toggleWarningsOnly() {{
                const btn = document.getElementById("filter-btn");
                const isFiltering = btn.dataset.filtering === "true";
                
                // Toggle state
                btn.dataset.filtering = !isFiltering;
                btn.innerHTML = !isFiltering ? "🔄 すべて表示" : "⚠️ 警告・保留・調達中のみ";
                btn.style.backgroundColor = !isFiltering ? "var(--status-bg-warning)" : "#fff";
                btn.style.color = !isFiltering ? "var(--status-text-warning)" : "var(--text)";
                btn.style.border = !isFiltering ? "none" : "1px solid var(--border)";
                
                // Filter rows
                const rows = document.querySelectorAll("tbody tr");
                rows.forEach(row => {{
                    if (!isFiltering) {{
                        // Only show rows that contain danger OR warning statuses (調達中, 保留)
                        const hasDanger = row.querySelector(".status-danger") !== null;
                        const textContent = row.innerText;
                        const hasWarning = textContent.includes("保留") || textContent.includes("調達中");
                        
                        if (!hasDanger && !hasWarning) {{
                            row.style.display = "none";
                        }}
                    }} else {{
                        // Show all
                        row.style.display = "";
                    }}
                }});
                
                // Update counts on cards based on visible rows
                document.querySelectorAll('.card').forEach(card => {{
                    const visibleRows = card.querySelectorAll("tbody tr:not([style*='display: none'])").length;
                    const countSpan = card.querySelector(".item-count");
                    if (countSpan && card.querySelector("tbody")) {{
                        countSpan.innerText = visibleRows + "件";
                    }}
                }});
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
                <button id="filter-btn" data-filtering="false" onclick="toggleWarningsOnly()" style="
                    background-color: #fff;
                    color: var(--text);
                    border: 1px solid var(--border);
                    padding: 0.4rem 0.8rem;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 0.8rem;
                    transition: all 0.2s;
                ">⚠️ 警告・保留・調達中のみ</button>
            </div>
            <div class="last-updated">最終更新: {updated_at}</div>
        </div>
        
        <div class="container">
    """

    # Collabo Card
    html += f"""
            <div class="card">
                <div class="card-header card-collabo">
                    <span>Collabo Portal (全ステータス表示)</span>
                    <span class="item-count">{len(collabo_data)}件</span>
                </div>
                <div class="table-container">
    """
    if collabo_data:
        html += "<table><thead><tr><th>品名/メーカー</th><th>状況/納期</th><th style='min-width:110px;white-space:nowrap;'>数量</th></tr></thead><tbody>"
        for item in collabo_data:
            remarks_html = f'<div class="remarks">{item.get("remarks", "")}</div>' if item.get("remarks") else ""
            
            # Badge color logic
            status_text = item.get("status", "")
            if "辞退" in status_text or "停止" in status_text:
                status_class = "status-danger"
            elif "納品済" in status_text or "出荷準備中" in status_text or "本日" in status_text or "明日" in status_text:
                status_class = "status-success"
            else:
                status_class = ""
                
            date_html = f'<div style="font-size:0.8rem; margin-top:4px;">受付: {item.get("date")}</div>' if item.get("date") else ""
            
            html += f"""
                        <tr>
                            <td>
                                <span class="maker-name">{item.get("maker", "")}</span>
                                <div class="product-name">{item.get("name", "")}</div>
                                <span class="product-code">JAN: {item.get("code", "")}</span>
                                {remarks_html}
                            </td>
                            <td style="white-space: nowrap;">
                                <span class="status-badge {status_class}">{item.get("status", "")}</span>
                                {date_html}
                            </td>
                            <td style="white-space: nowrap; min-width: 110px;">
                                <div>発注: <b>{item.get("order_qty", "-")}</b></div>
                                <div>納品予定: <b>{item.get("deliv_qty", "-")}</b></div>
                            </td>
                        </tr>
        """
        html += "</tbody></table>"
    else:
        html += '<div class="empty-state">該当データなし</div>'
    html += "</div></div>"

    # Medipal Card
    html += f"""
            <div class="card">
                <div class="card-header card-medipal">
                    <span>MEDIPAL (全ステータス表示)</span>
                    <span class="item-count">{len(medipal_data)}件</span>
                </div>
                <div class="table-container">
    """
    if medipal_data:
        html += "<table><thead><tr><th>品名/メーカー</th><th>状況・備考</th><th style=\'white-space:nowrap;\'>数量</th></tr></thead><tbody>"
        for item in medipal_data:
            remarks = item.get("remarks", "")
            is_warning = "調整" in remarks or "未定" in remarks or "欠品" in remarks
            status_class = "status-danger" if is_warning else "status-success"
            status_label = "入荷未定" if is_warning else "通常"
            # 「通常」のときは備考テキストを非表示
            remarks_html = f'<div style="font-size:0.8rem; margin-top:4px; white-space:normal;">{remarks}</div>' if is_warning else ""

            html += f"""
                        <tr>
                            <td>
                                <span class="maker-name">{item.get("maker", "")}</span>
                                <div class="product-name">{item.get("name", "")}</div>
                                <span class="product-code">{item.get("code", "")}</span>
                            </td>
                            <td style="white-space: nowrap;">
                                <span class="status-badge {status_class}">{status_label}</span>
                                {remarks_html}
                            </td>
                            <td style="white-space: nowrap;">
                                <div>発注: <b>{item.get("order_qty", "-")}</b></div>
                                <div>納品予定: <b>{item.get("deliv_qty", "-")}</b></div>
                            </td>
                        </tr>
        """
        html += "</tbody></table>"
    else:
        html += '<div class="empty-state">該当データなし</div>'
    html += "</div></div>"

    # ALF-Web Card
    html += f"""
            <div class="card">
                <div class="card-header card-alfweb">
                    <span>ALF-Web (出荷停止・入荷未定)</span>
                    <span class="item-count">{len(alfweb_data)}件</span>
                </div>
                <div class="table-container">
    """
    if alfweb_data:
        html += "<table><thead><tr><th>品名/メーカー</th><th>状況・備考</th><th>数量</th></tr></thead><tbody>"
        for item in alfweb_data:
            date_html = f'<div style="font-size:0.8rem; margin-top:4px;">更新: {item.get("date")}</div>' if item.get("date") else ""
            html += f"""
                        <tr>
                            <td>
                                <span class="maker-name">{item.get("maker", "")}</span>
                                <div class="product-name">{item.get("name", "")}</div>
                            </td>
                            <td style="white-space: nowrap;">
                                <span class="status-badge status-danger">{item.get("status", "入荷未定")}</span>
                                {date_html}
                            </td>
                            <td>
                                <div>発注: <b>{item.get("order_qty", "-")}</b></div>
                                <div>納品予定: <b>{item.get("deliv_qty", "-")}</b></div>
                            </td>
                        </tr>
        """
        html += "</tbody></table>"
    else:
        html += '<div class="empty-state">該当データなし</div>'
    html += "</div></div>"

    html += """
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
