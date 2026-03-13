import ccxt
import pandas as pd
import time
import sys

# 強制終端機輸出為 UTF-8，避免 Windows 下的 GBK 編碼錯誤
sys.stdout.reconfigure(encoding='utf-8')

def find_highly_correlated_coins(base_symbol='BTC/USDT:USDT', timeframe='1d', length=20, threshold=0.70):
    print("初始化 Bitget 交易所...")
    exchange = ccxt.bitget({
        'enableRateLimit': True, # 自動處理 API 頻率限制
    })

    # 1. 獲取所有市場資訊
    print("正在獲取所有市場資訊...")
    markets = exchange.load_markets()

    # 2. 篩選出所有 USDT U本位合約 (Perpetual)
    symbols = [s for s in markets.keys() if s.endswith(':USDT') and markets[s]['active']]
    print(f"共找到 {len(symbols)} 個活耀的 USDT 合約交易對。")

    # 3. 抓取 BTC 基準數據
    print(f"正在抓取基準資產 {base_symbol} 的數據...")
    try:
        # fetch_ohlcv 返回: [timestamp, open, high, low, close, volume]
        base_ohlcv = exchange.fetch_ohlcv(base_symbol, timeframe, limit=length)
        base_df = pd.DataFrame(base_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        base_close = base_df['close']
    except Exception as e:
        print(f"無法抓取基準幣種數據: {e}")
        return

    results = {}
    
    # 為了示範，這裡我們先抓前 50 個幣種。如果你想掃描「全市場」，可以把 [:50] 拿掉
    # 注意：全市場掃描大約需要幾分鐘的時間，因為要避免觸發交易所的 API 速率限制
    target_symbols = symbols 
    print(f"\n開始抓取並計算相關係數 (共 {len(target_symbols)} 個合約, 回測週期: {length} 根 K 線, 閾值: {threshold})...")
    
    # 迴圈抓取其他幣種並計算相關係數
    total_symbols = len(target_symbols)
    for i, symbol in enumerate(target_symbols):
        if i % 10 == 0:
            print(f"進度: {i}/{total_symbols} ({(i/total_symbols)*100:.1f}%)")
        if symbol == base_symbol:
            continue
            
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=length)
            
            # 確保抓到的數據長度與基準數據一致
            if len(ohlcv) == len(base_close):
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                
                # 計算皮爾森相關係數 (等同於 TradingView 的 ta.correlation)
                corr = base_close.corr(df['close'])
                
                # 如果相關係數大於等於設定的閾值 (0.7)
                if corr >= threshold:
                    results[symbol] = corr
                    print(f"[符合] {symbol:15} | 相關係數: {corr:.4f}")
            
            # 稍微暫停，避免被交易所封鎖 IP
            time.sleep(0.1)
            
        except Exception as e:
            # 某些幣種可能剛上架，K線數量不足會報錯，直接略過
            continue

    # 5. 將結果依照相關係數由高到低排序並印出
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

    print("\n" + "="*50)
    print("🎯 與 BTC 高度同步的幣種清單 (相關係數 >= 0.70)")
    print("="*50)
    
    # 開啟兩個記事本檔案準備寫入
    with open('correlated_coins_details.txt', 'w', encoding='utf-8') as f_detail, \
         open('correlated_coins_names.txt', 'w', encoding='utf-8') as f_name:
         
        title = "🎯 與 BTC 高度同步的幣種清單 (相關係數 >= 0.70)\n" + "="*50 + "\n"
        f_detail.write(title)
        
        for sym, corr in sorted_results:
            # 寫入詳細資訊 (包含係數)
            detail_line = f"幣種: {sym:15} | 相關係數: {corr:.4f}"
            print(detail_line)
            f_detail.write(detail_line + "\n")
            
            # 將 ccxt 格式 (例: LINK/USDT:USDT) 轉換為 BITGET TradingView 格式 (例: LINKUSDT.P)
            formatted_name = sym.replace('/', '').replace(':USDT', '.P')
            f_name.write(formatted_name + "\n")
            
    print("="*50)
    print("✅ 已成功生成兩個記事本檔案：")
    print("   1. correlated_coins_details.txt (包含詳細相關係數)")
    print("   2. correlated_coins_names.txt (僅包含幣種名稱，例如 LINKUSDT.P)")

if __name__ == "__main__":
    # 執行函數：基準為 BTC，週期為 1天 (1d)，計算最近 20 根 K 線，門檻 0.70
    # 你可以把 timeframe 改為 '1h', '4h', '15m' 等
    find_highly_correlated_coins(base_symbol='BTC/USDT:USDT', timeframe='1d', length=20, threshold=0.70)