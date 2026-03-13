import requests
import pandas as pd
from datetime import datetime
import pytz

def get_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    # 抓取市值前 200 名
    url = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?start=1&limit=200&sortBy=market_cap&sortType=desc&convert=USD"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        coin_list = data['data']['cryptoCurrencyList']
        
        # 定義穩定幣與錨定幣過濾清單
        stable_keywords = ['USDT', 'USDC', 'FDUSD', 'EURC', 'RLUSD', 'USD1', 'PAXG', 'XAUt', 'DAI', 'PYUSD', 'TUSD', 'USTC', 'BUSD']
        results = []

        for coin in coin_list:
            symbol = coin['symbol']
            # 過濾穩定幣
            if any(stable in symbol for stable in stable_keywords): continue

            quotes = coin['quotes'][0]
            mkt_cap = quotes.get('marketCap', 0)
            vol_24h = quotes.get('volume24h', 0)
            
            if mkt_cap > 0:
                ratio = (vol_24h / mkt_cap) * 100
                # 篩選標準：Vol/Mkt Cap ≧ 10%
                if ratio >= 10:
                    results.append({
                        "代號": symbol,
                        "價格": f"${quotes.get('price', 0):.4f}",
                        "24h漲跌": f"{quotes.get('percentChange24h', 0):.2f}%",
                        "Vol/Mkt Cap": f"{ratio:.2f}%"
                    })
        return pd.DataFrame(results)
    except Exception as e:
        print(f"抓取錯誤: {e}")
        return pd.DataFrame()

# 執行抓取
df = get_data()

# 設定台灣時間
tw_tz = pytz.timezone('Asia/Taipei')
current_time = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")

# 1. 生成 TXT 下載檔 (僅含代號與比例)
if not df.empty:
    df[['代號', 'Vol/Mkt Cap']].to_csv('hot_symbols.txt', index=False, sep='\t')
else:
    with open("hot_symbols.txt", "w") as f: f.write("目前無符合標準的幣種")

# 2. 生成 HTML 網頁
html_template = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CoinMarketCap 放量偵測器</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body {{ background-color: #0f172a; color: #f8fafc; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        .container {{ max-width: 900px; }}
        .card {{ background-color: #1e293b; border: none; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
        .table {{ color: #e2e8f0; background: #1e293b; border-radius: 8px; overflow: hidden; }}
        .ratio-high {{ color: #4ade80; font-weight: bold; }}
        .header-title {{ color: #38bdf8; font-weight: 800; }}
        .badge-update {{ background-color: #334155; color: #94a3b8; padding: 8px 12px; border-radius: 20px; font-size: 0.85rem; }}
        .rules-text {{ font-size: 0.95rem; color: #cbd5e1; line-height: 1.6; }}
        .btn-download {{ background-color: #38bdf8; color: #0f172a; font-weight: bold; border: none; }}
        .btn-download:hover {{ background-color: #0ea5e9; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="text-center mb-4">
            <h1 class="header-title">📊 CoinMarketCap 放量偵測器</h1>
            <span class="badge-update">🕒 最後更新 (台灣時間)：{current_time}</span>
        </div>

        <div class="card">
            <h5 class="text-info">📌 偵測規則說明</h5>
            <div class="rules-text">
                <ul>
                    <li><strong>更新頻率：</strong> 每 <strong>30 分鐘</strong> 自動重新抓取數據。</li>
                    <li><strong>篩選範圍：</strong> CoinMarketCap 市值前 <strong>200 名</strong> 幣種。</li>
                    <li><strong>過濾機制：</strong> 已自動剔除穩定幣及法定貨幣錨定幣。</li>
                    <li><strong>放量標準：</strong> Vol/Mkt Cap (24h) <strong>≧ 10%</strong> 代表資金流入活躍。</li>
                </ul>
            </div>
            <a href="hot_symbols.txt" download class="btn btn-download w-100 mt-2">📥 下載代號清單 (TXT)</a>
        </div>

        <div class="table-responsive">
            <table class="table table-dark table-hover">
                <thead>
                    <tr class="table-active">
                        <th>代號</th>
                        <th>價格</th>
                        <th>24h 漲跌</th>
                        <th>Vol/Mkt Cap</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f"<tr><td><strong>{row['代號']}</strong></td><td>{row['價格']}</td><td>{row['24h漲跌']}</td><td class='ratio-high'>{row['Vol/Mkt Cap']}</td></tr>" for _, row in df.iterrows()]) if not df.empty else "<tr><td colspan='4' class='text-center'>目前無符合標準之幣種</td></tr>"}
                </tbody>
            </table>
        </div>
        
        <p class="text-center text-secondary mt-4" style="font-size: 0.8rem;">本工具僅供策略參考，不構成任何投資建議。</p>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)
