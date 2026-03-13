import requests
import pandas as pd
from datetime import datetime
import os

def get_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?start=1&limit=200&sortBy=market_cap&sortType=desc&convert=USD"
    
    response = requests.get(url, headers=headers)
    data = response.json()
    coin_list = data['data']['cryptoCurrencyList']
    
    stable_keywords = ['USDT', 'USDC', 'FDUSD', 'EURC', 'RLUSD', 'USD1', 'PAXG', 'XAUt', 'DAI', 'PYUSD', 'TUSD', 'USTC']
    results = []

    for coin in coin_list:
        symbol = coin['symbol']
        if any(stable in symbol for stable in stable_keywords): continue

        quotes = coin['quotes'][0]
        ratio = (quotes.get('volume24h', 0) / quotes.get('marketCap', 1)) * 100
        
        if ratio >= 10:
            results.append({
                "代號": symbol,
                "價格": f"${quotes.get('price', 0):.4f}",
                "24h漲跌": f"{quotes.get('percentChange24h', 0):.2f}%",
                "Vol/Mkt Cap": f"{ratio:.2f}%"
            })
    return pd.DataFrame(results)

df = get_data()
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 1. 生成 TXT 下載檔
df[['代號', 'Vol/Mkt Cap']].to_csv('hot_symbols.txt', index=False, sep='\t')

# 2. 生成 HTML 網頁
html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>大仁老師放量偵測器</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body {{ background-color: #121212; color: white; padding: 20px; }}
        .table {{ color: white; background: #1e1e1e; }}
        .ratio-high {{ color: #00ff00; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h2 class="mb-3">🔥 資金流入偵測 (Vol/Mkt Cap > 10%)</h2>
        <p>最後更新時間：{current_time}</p>
        <a href="hot_symbols.txt" download class="btn btn-primary mb-3">📥 下載代號 TXT</a>
        <table class="table table-dark table-striped">
            <thead><tr><th>代號</th><th>價格</th><th>24h漲跌</th><th>Vol/Mkt Cap</th></tr></thead>
            <tbody>
                {''.join([f"<tr><td>{row['代號']}</td><td>{row['價格']}</td><td>{row['24h漲跌']}</td><td class='ratio-high'>{row['Vol/Mkt Cap']}</td></tr>" for _, row in df.iterrows()])}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)