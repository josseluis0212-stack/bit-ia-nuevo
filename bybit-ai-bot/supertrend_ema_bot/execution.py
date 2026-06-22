import ccxt
import time
import logging

class ExecutionManager:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        exchange_class = getattr(ccxt, self.config.EXCHANGE_ID)
        
        demo_mode = getattr(self.config, 'DEMO_MODE', False)
        testnet_mode = getattr(self.config, 'TESTNET', False)
        
        exchange_params = {
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
            }
        }
        
        # Bybit Demo: public market data is NOT available on api-demo.bybit.com
        # Only authenticated endpoints (orders, positions) use api-demo.bybit.com
        # OHLCV/market data must come from api.bybit.com (public)
        if demo_mode:
            exchange_params['urls'] = {
                'api': {
                    'spot':    'https://api-demo.bybit.com',
                    'public':  'https://api-demo.bybit.com',
                    'private': 'https://api-demo.bybit.com',
                    'v2':      'https://api-demo.bybit.com',
                    'futures': 'https://api-demo.bybit.com',
                }
            }
            self.logger.info("SuperTrend: All CCXT routes -> api-demo.bybit.com (OHLCV uses api.bybit.com directly)")
        elif testnet_mode:
            self.logger.info("SuperTrend running in TESTNET mode")
        else:
            self.logger.info("SuperTrend running in LIVE mode")
        
        # Instantiate WITHOUT keys first to prevent authenticated calls during load_markets
        self.exchange = exchange_class(exchange_params)
        
        if testnet_mode and not demo_mode:
            self.exchange.set_sandbox_mode(True)
            
        # Load markets
        try:
            self.exchange.load_markets()
            self.logger.info("Markets loaded successfully without auth.")
        except Exception as e:
            self.logger.error(f"Failed to load markets: {e}")

        # Set keys AFTER loading markets
        self.exchange.apiKey = self.config.API_KEY
        self.exchange.secret = self.config.API_SECRET



    def get_top_volume_symbols(self, limit=40):
        import urllib.request
        import json
        url = "https://api.bybit.com/v5/market/tickers?category=linear"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            if data.get('retCode') != 0:
                self.logger.error("Error fetching top symbols")
                return ["BTC/USDT:USDT"]
            
            tickers = data['result']['list']
            tickers.sort(key=lambda x: float(x.get('turnover24h', 0)), reverse=True)
            symbols = []
            for t in tickers:
                sym = t['symbol']
                if sym.endswith('USDT'):
                    symbols.append(f"{sym[:-4]}/USDT:USDT")
                if len(symbols) >= limit:
                    break
            return symbols if symbols else ["BTC/USDT:USDT"]
        except Exception as e:
            self.logger.error(f"Error fetching top volume symbols: {e}")
            return ["BTC/USDT:USDT"]

    def fetch_ohlcv(self, symbol, timeframe, limit=300):
        """Fetch OHLCV directly from Bybit public API - bypasses CCXT URL routing.
        This ensures market data always comes from api.bybit.com regardless of demo/live mode."""
        import urllib.request
        import json
        
        # Map ccxt timeframe to Bybit interval
        tf_map = {'1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30',
                  '1h': '60', '2h': '120', '4h': '240', '6h': '360', '12h': '720',
                  '1d': 'D', '1w': 'W', '1M': 'M'}
        interval = tf_map.get(timeframe, '60')
        
        # Convert symbol from ccxt format (BTC/USDT:USDT) to Bybit format (BTCUSDT)
        symbol_bybit = symbol.split('/')[0] + symbol.split('/')[1].split(':')[0]
        
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol_bybit}&interval={interval}&limit={limit}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            if data.get('retCode') != 0:
                self.logger.error(f"Bybit OHLCV error {timeframe}: {data.get('retMsg')}")
                return []
            # Bybit returns [startTime, open, high, low, close, volume, turnover]
            # Convert to ccxt format: [timestamp, open, high, low, close, volume]
            candles = []
            for row in reversed(data['result']['list']):
                candles.append([int(row[0]), float(row[1]), float(row[2]),
                                 float(row[3]), float(row[4]), float(row[5])])
            return candles
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV for {timeframe}: {e}")
            return []

    def get_position(self, symbol):
        """
        Retrieves current position for the symbol.
        Returns a dict with 'side' ('long', 'short', None), 'size', 'entry_price'.
        """
        try:
            # Different exchanges handle positions differently. CCXT standardize it mostly.
            positions = self.exchange.fetch_positions([symbol])
            for pos in positions:
                if pos['symbol'] == symbol:
                    size = float(pos.get('contracts', pos.get('info', {}).get('size', 0)))
                    side = pos['side']
                    
                    if size > 0:
                        return {
                            'side': side, # 'long' or 'short'
                            'size': size,
                            'entry_price': float(pos['entryPrice'])
                        }
            return {'side': None, 'size': 0, 'entry_price': 0}
        except Exception as e:
            self.logger.error(f"Error fetching position: {e}")
            # If we can't confirm position, assume None to avoid errors, or raise
            return None

    def cancel_all_orders(self, symbol):
        """Cancels all open orders for the symbol (useful before opening new pos or updating SL)"""
        try:
            self.exchange.cancel_all_orders(symbol)
            self.logger.info("All open orders cancelled.")
        except Exception as e:
            self.logger.error(f"Error cancelling orders: {e}")

    def open_position(self, symbol, side, price):
        """
        Opens a position using TRADE_CAPITAL.
        """
        try:
            self.cancel_all_orders(symbol)
            
            # Calculate quantity based on capital and current price
            # Assuming no leverage defined in script, or leverage is 1x. If leverage is used, adjust quantity.
            # Usually USDT-M futures capital is margin. Qty = Capital * Leverage / Price
            # Here we just use Capital / Price as a basic assumption (1x leverage).
            # To use 15 USDT margin at 10x leverage, qty would be (15 * 10) / price.
            # Defaulting to 1x leverage for safety if not specified.
            quantity = self.config.TRADE_CAPITAL / price
            
            # Adjust to lot size
            market = self.exchange.market(symbol)
            quantity = float(self.exchange.amount_to_precision(symbol, quantity))
            
            if quantity <= 0:
                self.logger.error("Calculated quantity is <= 0")
                return False

            order_side = 'buy' if side == 'long' else 'sell'
            
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=order_side,
                amount=quantity
            )
            self.logger.info(f"Opened {side} position: {order}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening position: {e}")
            return False

    def close_position(self, symbol, side, size):
        """
        Closes the current position.
        """
        try:
            self.cancel_all_orders(symbol)
            
            order_side = 'sell' if side == 'long' else 'buy'
            
            # Note: Many exchanges support 'reduceOnly'
            params = {'reduceOnly': True}
            
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=order_side,
                amount=size,
                params=params
            )
            self.logger.info(f"Closed {side} position: {order}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return False

    def place_stop_loss(self, symbol, side, size, stop_price):
        """
        Places a stop loss order.
        """
        try:
            self.cancel_all_orders(symbol)
            
            order_side = 'sell' if side == 'long' else 'buy'
            
            # This is specific to how the exchange handles stop market orders.
            # Using basic CCXT unified parameters.
            params = {
                'stopPrice': stop_price,
                'reduceOnly': True
            }
            
            # Some exchanges require 'stop_market' or 'stop' type, ccxt tries to unify but it can be tricky.
            # Assuming Binance/Bybit standard here.
            order = self.exchange.create_order(
                symbol=symbol,
                type='market', # Some need 'stop_market'
                side=order_side,
                amount=size,
                params=params
            )
            self.logger.info(f"Placed Stop Loss at {stop_price}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error placing stop loss: {e}")
            return False
