import pandas as pd
import numpy as np

def calculate_sma(data: list[float], period: int) -> list[float]:
    if len(data) < period:
        return [0.0] * len(data)
    s = pd.Series(data)
    sma = s.rolling(window=period).mean()
    return sma.fillna(0.0).tolist()

def calculate_ema(closes: list[float], period: int) -> list[float]:
    if len(closes) < period:
        return [0.0] * len(closes)
    s = pd.Series(closes)
    ema = s.ewm(span=period, adjust=False).mean()
    return ema.tolist()

def calculate_rsi(closes: list[float], period: int = 14) -> list[float]:
    if len(closes) <= period:
        return [50.0] * len(closes)
    
    s = pd.Series(closes)
    delta = s.diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50.0) # Fill NaN with neutral 50
    return rsi.tolist()

def calculate_atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> list[float]:
    if len(closes) <= period:
        return [0.0] * len(closes)
        
    df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['prev_close']).abs()
    df['tr3'] = (df['low'] - df['prev_close']).abs()
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    atr = df['tr'].rolling(window=period).mean()
    return atr.fillna(0.0).tolist()

def calculate_adx(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> list[float]:
    if len(closes) <= period:
        return [0.0] * len(closes)
        
    df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
    df['prev_close'] = df['close'].shift(1)
    df['prev_high'] = df['high'].shift(1)
    df['prev_low'] = df['low'].shift(1)
    
    # Calculate True Range
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['prev_close']).abs()
    df['tr3'] = (df['low'] - df['prev_close']).abs()
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    
    # Calculate Directional Movement
    df['up_move'] = df['high'] - df['prev_high']
    df['down_move'] = df['prev_low'] - df['low']
    
    df['+dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0.0)
    df['-dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0.0)
    
    # Wilder's Smoothing
    tr_smoothed = df['tr'].ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * (df['+dm'].ewm(alpha=1/period, adjust=False).mean() / tr_smoothed)
    minus_di = 100 * (df['-dm'].ewm(alpha=1/period, adjust=False).mean() / tr_smoothed)
    
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    
    return adx.fillna(0.0).tolist()

def calculate_supertrend(highs: list[float], lows: list[float], closes: list[float], period: int = 10, multiplier: float = 3.0) -> list[dict]:
    if len(closes) <= period:
        return [{"value": 0.0, "dir": 1} for _ in closes]
        
    df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
    
    # Calculate ATR
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['prev_close']).abs()
    df['tr3'] = (df['low'] - df['prev_close']).abs()
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    df['atr'] = df['tr'].rolling(window=period).mean()
    
    hl2 = (df['high'] + df['low']) / 2
    
    df['basic_ub'] = hl2 + (multiplier * df['atr'])
    df['basic_lb'] = hl2 - (multiplier * df['atr'])
    
    df['final_ub'] = 0.00
    df['final_lb'] = 0.00
    
    for i in range(period, len(df)):
        df.loc[i, 'final_ub'] = df.loc[i, 'basic_ub'] if df.loc[i, 'basic_ub'] < df.loc[i - 1, 'final_ub'] or df.loc[i - 1, 'close'] > df.loc[i - 1, 'final_ub'] else df.loc[i - 1, 'final_ub']
        df.loc[i, 'final_lb'] = df.loc[i, 'basic_lb'] if df.loc[i, 'basic_lb'] > df.loc[i - 1, 'final_lb'] or df.loc[i - 1, 'close'] < df.loc[i - 1, 'final_lb'] else df.loc[i - 1, 'final_lb']
        
    df['st'] = 0.00
    df['dir'] = 1
    
    for i in range(period, len(df)):
        if df.loc[i - 1, 'st'] == df.loc[i - 1, 'final_ub'] and df.loc[i, 'close'] <= df.loc[i, 'final_ub']:
            df.loc[i, 'st'] = df.loc[i, 'final_ub']
        elif df.loc[i - 1, 'st'] == df.loc[i - 1, 'final_ub'] and df.loc[i, 'close'] > df.loc[i, 'final_ub']:
            df.loc[i, 'st'] = df.loc[i, 'final_lb']
        elif df.loc[i - 1, 'st'] == df.loc[i - 1, 'final_lb'] and df.loc[i, 'close'] >= df.loc[i, 'final_lb']:
            df.loc[i, 'st'] = df.loc[i, 'final_lb']
        elif df.loc[i - 1, 'st'] == df.loc[i - 1, 'final_lb'] and df.loc[i, 'close'] < df.loc[i, 'final_lb']:
            df.loc[i, 'st'] = df.loc[i, 'final_ub']
            
        if df.loc[i, 'close'] > df.loc[i, 'st']:
            df.loc[i, 'dir'] = 1
        else:
            df.loc[i, 'dir'] = -1
            
    result = []
    for i in range(len(df)):
        result.append({
            "value": float(df.loc[i, 'st']),
            "dir": int(df.loc[i, 'dir'])
        })
    return result

def calculate_wma(data: list[float], period: int) -> list[float]:
    if len(data) < period:
        return [0.0] * len(data)
    s = pd.Series(data)
    weights = np.arange(1, period + 1)
    wma = s.rolling(period).apply(lambda prices: np.dot(prices, weights) / weights.sum(), raw=True)
    return wma.fillna(0.0).tolist()

def calculate_hull_ma(data: list[float], period: int) -> list[float]:
    if len(data) < period:
        return [0.0] * len(data)
    
    half_length = int(period / 2)
    sqrt_length = int(np.sqrt(period))
    
    wma_half = calculate_wma(data, half_length)
    wma_full = calculate_wma(data, period)
    
    # 2 * WMA(half) - WMA(full)
    raw_hull = [2 * h - f for h, f in zip(wma_half, wma_full)]
    
    # WMA of the raw hull over sqrt(period)
    hull_ma = calculate_wma(raw_hull, sqrt_length)
    return hull_ma

def calculate_macd(closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9):
    if len(closes) < slow:
        return [0.0]*len(closes), [0.0]*len(closes), [0.0]*len(closes)
    s = pd.Series(closes)
    ema_fast = s.ewm(span=fast, adjust=False).mean()
    ema_slow = s.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line.fillna(0.0).tolist(), signal_line.fillna(0.0).tolist(), hist.fillna(0.0).tolist()

def calculate_bollinger_bands(closes: list[float], period: int = 20, std_dev: float = 2.0):
    if len(closes) < period:
        return [0.0]*len(closes), [0.0]*len(closes), [0.0]*len(closes)
    s = pd.Series(closes)
    sma = s.rolling(window=period).mean()
    stdev = s.rolling(window=period).std()
    upper = sma + (stdev * std_dev)
    lower = sma - (stdev * std_dev)
    return sma.fillna(0.0).tolist(), upper.fillna(0.0).tolist(), lower.fillna(0.0).tolist()

def ta_rising(series: list[float], length: int) -> bool:
    if len(series) <= length:
        return False
    for i in range(1, length + 1):
        if series[-i] <= series[-(i + 1)]:
            return False
    return True

def ta_falling(series: list[float], length: int) -> bool:
    if len(series) <= length:
        return False
    for i in range(1, length + 1):
        if series[-i] >= series[-(i + 1)]:
            return False
    return True

def calculate_dmi(highs: list[float], lows: list[float], closes: list[float], period: int = 14):
    if len(closes) <= period:
        n = len(closes)
        return [0.0]*n, [0.0]*n, [0.0]*n
        
    df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
    df['prev_close'] = df['close'].shift(1)
    df['prev_high'] = df['high'].shift(1)
    df['prev_low'] = df['low'].shift(1)
    
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['prev_close']).abs()
    df['tr3'] = (df['low'] - df['prev_close']).abs()
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    
    df['up_move'] = df['high'] - df['prev_high']
    df['down_move'] = df['prev_low'] - df['low']
    
    df['+dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0.0)
    df['-dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0.0)
    
    tr_smoothed = df['tr'].ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * (df['+dm'].ewm(alpha=1/period, adjust=False).mean() / tr_smoothed)
    minus_di = 100 * (df['-dm'].ewm(alpha=1/period, adjust=False).mean() / tr_smoothed)
    
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    
    return plus_di.fillna(0.0).tolist(), minus_di.fillna(0.0).tolist(), adx.fillna(0.0).tolist()
