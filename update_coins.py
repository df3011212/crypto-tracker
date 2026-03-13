import requests
import pandas as pd
from datetime import datetime
import pytz

def get_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?start=1&limit=200&sortBy=market_cap&sortType=desc&convert=USD"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        coin_list = data['data']['cryptoCurrencyList']
        
        stable_keywords = ['USDT', 'USDC', 'FDUSD', 'EURC', 'RLUSD', 'USD1', 'PAXG', 'XAUt', 'DAI', 'PYUSD', 'TUSD', 'USTC', 'BUSD']
        results = []

        for coin in coin_list:
            symbol = coin['symbol']
            slug = coin['slug']
            if any(stable in symbol for stable in stable_keywords): continue

            quotes = coin['quotes'][0]
            mkt_cap = quotes.get('marketCap', 0)
            vol_24h = quotes.get('volume24h', 0)
            
            if mkt_cap > 0:
                ratio = (vol_24h / mkt_cap) * 100
                if ratio >= 10:
                    results.append({
                        "代號": symbol,
                        "網址名": slug,
                        "價格": quotes.get('price', 0),
                        "漲跌": quotes.get('percentChange24h', 0),
                        "比例": ratio
                    })
        return pd.DataFrame(results)
    except Exception as e:
        print(f"抓取錯誤: {e}")
        return pd.DataFrame()

df = get_data()
tw_tz = pytz.timezone('Asia/Taipei')
current_time = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")

# 生成 TXT
if not df.empty:
    df[['代號', '比例']].to_csv('hot_symbols.txt', index=False, sep='\t')
else:
    with open("hot_symbols.txt", "w") as f: f.write("目前無符合標準的幣種")

# 生成 HTML 表格行
rows_html = ""
if not df.empty:
    for _, row in df.iterrows():
        cmc_url = f"https://coinmarketcap.com/zh-tw/currencies/{row['網址名']}/"
        rows_html += f"""
        <tr>
            <td><a href="{cmc_url}" target="_blank" style="color: #38bdf8; text-decoration: none; font-weight: bold;">{row['代號']} 🔗</a></td>
            <td data-sort="{row['價格']}">${row['價格']:.4f}</td>
            <td data-sort="{row['漲跌']}" style="color: {'#4ade80' if row['漲跌'] >= 0 else '#f87171'};">{row['漲跌']:.2f}%</td>
            <td data-sort="{row['比例']}" class="ratio-high">{row['比例']:.2f}%</td>
        </tr>
        """
else:
    rows_html = "<tr><td colspan='4' class='text-center'>目前無符合標準之幣種</td></tr>"

html_template = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CoinMarketCap 放量偵測器</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body {{ background-color: #0f172a; color: #f8fafc; padding: 20px; font-family: sans-serif; }}
        .container {{ max-width: 900px; }}
        .card {{ background-color: #1e293b; border: none; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
        .table {{ color: #e2e8f0; background: #1e293b; }}
        .ratio-high {{ color: #4ade80; font-weight: bold; }}
        th {{ cursor: pointer; color: #38bdf8 !important; }}
        th:hover {{ text-decoration: underline; }}
        .header-title {{ color: #38bdf8; font-weight: 800; }}
        .badge-update {{ background-color: #334155; color: #94a3b8; padding: 8px 12px; border-radius: 20px; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="text-center mb-4">
            <h1 class="header-title">📊 CoinMarketCap 放量偵測器</h1>
            <span class="badge-update">🕒 最後更新 (台灣)：{current_time}</span>
        </div>

        <div class="card">
            <h5 class="text-info">📌 偵測與排序規則</h5>
            <div style="font-size: 0.95rem; color: #cbd5e1;">
                <ul>
                    <li><strong>更新頻率：</strong> 每 30 分鐘更新。</li>
                    <li><strong>排序功能：</strong> 點擊下方表格<strong>藍色標題</strong>即可切換排序方式。</li>
                    <li><strong>放量標準：</strong> Vol/Mkt Cap ≧ 10%。</li>
                </ul>
            </div>
            <a href="hot_symbols.txt" download class="btn btn-info w-100 mt-2" style="font-weight:bold;">📥 下載代號清單 (TXT)</a>
        </div>

        <div class="table-responsive">
            <table class="table table-dark table-hover" id="coinTable">
                <thead>
                    <tr class="table-active">
                        <th onclick="sortTable(0)">代號 ⇅</th>
                        <th onclick="sortTable(1)">價格 ⇅</th>
                        <th onclick="sortTable(2)">24h 漲跌 ⇅</th>
                        <th onclick="sortTable(3)">Vol/Mkt Cap ⇅</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>

    <script>
    function sortTable(n) {{
        var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
        table = document.getElementById("coinTable");
        switching = true;
        dir = "desc"; 
        while (switching) {{
            switching = false;
            rows = table.rows;
            for (i = 1; i < (rows.length - 1); i++) {{
                shouldSwitch = false;
                x = rows[i].getElementsByTagName("TD")[n];
                y = rows[i + 1].getElementsByTagName("TD")[n];
                
                var xVal = x.getAttribute("data-sort") || x.innerText.toLowerCase();
                var yVal = y.getAttribute("data-sort") || y.innerText.toLowerCase();
                
                if (!isNaN(parseFloat(xVal)) && !isNaN(parseFloat(yVal))) {{
                    xVal = parseFloat(xVal);
                    yVal = parseFloat(yVal);
                }}

                if (dir == "asc") {{
                    if (xVal > yVal) {{ shouldSwitch = true; break; }}
                }} else if (dir == "desc") {{
                    if (xVal < yVal) {{ shouldSwitch = true; break; }}
                }}
            }}
            if (shouldSwitch) {{
                rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                switching = true;
                switchcount ++;      
            }} else {{
                if (switchcount == 0 && dir == "desc") {{
                    dir = "asc";
                    switching = true;
                }}
            }}
        }}
    }}
    // 預設以 Vol/Mkt Cap (第3欄) 降序排列
    window.onload = function() {{ sortTable(3); }};
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)
