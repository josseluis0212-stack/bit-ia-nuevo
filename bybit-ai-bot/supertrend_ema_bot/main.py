import sys
print("!!! TEST BOOT SUPERTREND SCRIPT STARTED !!!", file=sys.stderr)
print("!!! TEST BOOT SUPERTREND SCRIPT STARTED !!!", flush=True)

import time
import logging
import pandas as pd
from datetime import datetime

import config
from execution import ExecutionManager
from indicators import calculate_indicators_15m, calculate_indicators_1h
from strategy import RegimeStrategy
from risk_management import RiskManager

import os

LOG_PATH = "/app/storage/bot.log"
if not os.path.exists("/app/storage"):
    LOG_PATH = "bot.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - SUPERTREND_BOT - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting SuperTrend EMA Regime MTF Pro Bot (Multi-Coin Scanner)...")
    
    execution = ExecutionManager(config)
    risk_manager = RiskManager(config)
    
    # State Dictionaries
    strategies = {}
    current_sls = {}
    
    while True:
        try:
            logger.info("SUPERTREND_BOT - [POLL] Obteniendo top 40 monedas por volumen...")
            symbols = execution.get_top_volume_symbols(40)
            
            for symbol in symbols:
                try:
                    if symbol not in strategies:
                        strategies[symbol] = RegimeStrategy()
                        current_sls[symbol] = None
                        
                    # 1. Fetch Data
                    data_15m = execution.fetch_ohlcv(symbol, config.TIMEFRAME_15M, limit=300)
                    time.sleep(0.1) # stagger
                    data_1h = execution.fetch_ohlcv(symbol, config.TIMEFRAME_1H, limit=300)
                    time.sleep(0.1) # stagger
                    
                    if not data_15m or not data_1h:
                        continue
                        
                    df_15m = pd.DataFrame(data_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df_1h = pd.DataFrame(data_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    df_15m['datetime'] = pd.to_datetime(df_15m['timestamp'], unit='ms')
                    df_1h['datetime'] = pd.to_datetime(df_1h['timestamp'], unit='ms')

                    # 2. Calculate Indicators
                    df_15m_calc = calculate_indicators_15m(df_15m, config)
                    df_1h_calc = calculate_indicators_1h(df_1h, config)
                    
                    # 3. Get Current Position
                    pos = execution.get_position(symbol)
                    if pos is None:
                        continue
                        
                    current_position = pos['side']
                    entry_price = pos['entry_price']
                    position_size = pos['size']
                    
                    latest_15m = df_15m_calc.iloc[-1]
                    current_price = latest_15m['close']
                    current_atr = latest_15m['atr']
                    ema_21 = latest_15m['ema_21']

                    # 4. Risk Management
                    if current_position is not None:
                        if current_sls[symbol] is None:
                            current_sls[symbol] = risk_manager.calculate_initial_sl(current_position, entry_price, current_atr)
                            execution.place_stop_loss(symbol, current_position, position_size, current_sls[symbol])
                        else:
                            new_sl = risk_manager.update_sl(
                                side=current_position, 
                                entry_price=entry_price, 
                                current_price=current_price, 
                                current_sl=current_sls[symbol], 
                                current_atr=current_atr, 
                                ema_21=ema_21
                            )
                            
                            if new_sl is not None and new_sl != current_sls[symbol]:
                                logger.info(f"[{symbol}] Updating SL to {new_sl} due to Trailing/Breakeven")
                                current_sls[symbol] = new_sl
                                execution.place_stop_loss(symbol, current_position, position_size, current_sls[symbol])

                        if current_position == 'long' and current_price <= current_sls[symbol]:
                            logger.info(f"[{symbol}] Local SL Hit for LONG at {current_price}")
                            execution.close_position(symbol, 'long', position_size)
                            current_position = None
                            current_sls[symbol] = None
                        elif current_position == 'short' and current_price >= current_sls[symbol]:
                            logger.info(f"[{symbol}] Local SL Hit for SHORT at {current_price}")
                            execution.close_position(symbol, 'short', position_size)
                            current_position = None
                            current_sls[symbol] = None
                    else:
                        current_sls[symbol] = None 

                    # 5. Evaluate Strategy
                    signal_data = strategies[symbol].evaluate(df_15m_calc, df_1h_calc, current_position)
                    signal = signal_data['signal']
                    reason = signal_data['reason']

                    if signal:
                        logger.info(f"[{symbol}] Signal Generated: {signal} - Reason: {reason}")
                        
                        if signal == 'close_long' and current_position == 'long':
                            execution.close_position(symbol, 'long', position_size)
                            
                        elif signal == 'close_short' and current_position == 'short':
                            execution.close_position(symbol, 'short', position_size)
                            
                        elif signal == 'long' and current_position is None:
                            success = execution.open_position(symbol, 'long', current_price)
                            if success:
                                current_sls[symbol] = risk_manager.calculate_initial_sl('long', current_price, current_atr)
                                pos = execution.get_position(symbol)
                                if pos and pos['size'] > 0:
                                    execution.place_stop_loss(symbol, 'long', pos['size'], current_sls[symbol])
                                    
                        elif signal == 'short' and current_position is None:
                            success = execution.open_position(symbol, 'short', current_price)
                            if success:
                                current_sls[symbol] = risk_manager.calculate_initial_sl('short', current_price, current_atr)
                                pos = execution.get_position(symbol)
                                if pos and pos['size'] > 0:
                                    execution.place_stop_loss(symbol, 'short', pos['size'], current_sls[symbol])
                except Exception as ex:
                    logger.error(f"[{symbol}] Error processing symbol: {ex}")

            logger.info("SUPERTREND_BOT - [POLL] Escaneo multi-moneda completado. Esperando 45s...")
            time.sleep(45)

        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            time.sleep(45)

if __name__ == '__main__':
    main()
