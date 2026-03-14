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

# 執行抓取
df = get_data()

# 區分流入與流出
df_inflow = df[df['漲跌'] >= 0] if not df.empty else pd.DataFrame()
df_outflow = df[df['漲跌'] < 0] if not df.empty else pd.DataFrame()

# 設定台灣時間
tw_tz = pytz.timezone('Asia/Taipei')
current_time = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")

def generate_rows(target_df):
    if target_df.empty:
        return "<tr><td colspan='4' class='text-center text-secondary'>目前無符合條件之幣種</td></tr>"
    html = ""
    for _, row in target_df.iterrows():
        cmc_url = f"https://coinmarketcap.com/zh-tw/currencies/{row['網址名']}/"
        change_color = "#4ade80" if row['漲跌'] >= 0 else "#f87171"
        html += f"""
        <tr>
            <td><a href="{cmc_url}" target="_blank" style="color: #38bdf8; text-decoration: none; font-weight: bold;">{row['代號']} 🔗</a></td>
            <td data-sort="{row['價格']}">${row['價格']:.4f}</td>
            <td data-sort="{row['漲跌']}" style="color: {change_color};">{row['漲跌']:.2f}%</td>
            <td data-sort="{row['比例']}" style="color: #4ade80; font-weight: bold;">{row['比例']:.2f}%</td>
        </tr>
        """
    return html

# 生成 HTML 模板
html_template = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CoinMarketCap 多空動向偵測器</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body {{ background-color: #0f172a; color: #f8fafc; padding: 20px; font-family: sans-serif; }}
        .container {{ max-width: 1000px; }}
        .card {{ background-color: #1e293b; border: none; border-radius: 12px; padding: 20px; margin-bottom: 30px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); }}
        .header-title {{ color: #38bdf8; font-weight: 800; }}
        .badge-update {{ background-color: #334155; color: #94a3b8; padding: 8px 15px; border-radius: 20px; font-size: 0.85rem; }}
        th {{ cursor: pointer; color: #38bdf8 !important; text-align: center; }}
        td {{ text-align: center; vertical-align: middle; border-bottom: 1px solid #334155 !important; }}
        .table {{ margin-bottom: 0; }}
        .section-label {{ font-size: 1.25rem; font-weight: bold; margin-bottom: 15px; padding-left: 10px; border-left: 5px solid #38bdf8; }}
        .label-inflow {{ border-left-color: #4ade80; color: #4ade80; }}
        .label-outflow {{ border-left-color: #f87171; color: #f87171; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="text-center mb-4">
            <h1 class="header-title">📊 CMC 多空資金動向偵測</h1>
            <span class="badge-update">🕒 最後更新 (台灣)：{current_time}</span>
        </div>

        <div class="card p-3" style="font-size: 0.9rem;">
            <p class="mb-1">💡 <strong>偵測規則：</strong> 篩選 CMC 前 200 名，Vol/Mkt Cap ≧ 10% 之幣種。</p>
            <p class="mb-0">🟢 <strong>流入：</strong> 放量且價格上漲。 🔴 <strong>流出：</strong> 放量且價格下跌。</p>
        </div>

        <div class="section-label label-inflow">🚀 資金流入 (放量上漲 - 多頭預警)</div>
        <div class="card overflow-hidden p-0">
            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0" id="inflowTable">
                    <thead>
                        <tr class="table-active">
                            <th onclick="sortTable('inflowTable', 0)">代號 ⇅</th>
                            <th onclick="sortTable('inflowTable', 1)">價格 ⇅</th>
                            <th onclick="sortTable('inflowTable', 2)">24h 漲跌 ⇅</th>
                            <th onclick="sortTable('inflowTable', 3)">Vol/Mkt Cap ⇅</th>
                        </tr>
                    </thead>
                    <tbody>{generate_rows(df_inflow)}</tbody>
                </table>
            </div>
        </div>

        <div class="section-label label-outflow">📉 資金流出 (放量下跌 - 空頭預警)</div>
        <div class="card overflow-hidden p-0">
            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0" id="outflowTable">
                    <thead>
                        <tr class="table-active">
                            <th onclick="sortTable('outflowTable', 0)">代號 ⇅</th>
                            <th onclick="sortTable('outflowTable', 1)">價格 ⇅</th>
                            <th onclick="sortTable('outflowTable', 2)">24h 漲跌 ⇅</th>
                            <th onclick="sortTable('outflowTable', 3)">Vol/Mkt Cap ⇅</th>
                        </tr>
                    </thead>
                    <tbody>{generate_rows(df_outflow)}</tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
    function sortTable(tableId, n) {{
        var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
        table = document.getElementById(tableId);
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
                    xVal = parseFloat(xVal); yVal = parseFloat(yVal);
                }}
                if (dir == "asc") {{ if (xVal > yVal) {{ shouldSwitch = true; break; }} }}
                else if (dir == "desc") {{ if (xVal < yVal) {{ shouldSwitch = true; break; }} }}
            }}
            if (shouldSwitch) {{
                rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                switching = true;
                switchcount ++;      
            }} else {{
                if (switchcount == 0 && dir == "desc") {{ dir = "asc"; switching = true; }}
            }}
        }}
    }}
    // 初始排序
    window.onload = function() {{ sortTable('inflowTable', 3); sortTable('outflowTable', 3); }};
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)
