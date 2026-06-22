from app.config import Config
from app.logger import logger

class RiskManager:
    def __init__(self):
        self.risk_per_trade = Config.RISK_PER_TRADE
        self.max_open_trades = Config.MAX_OPEN_TRADES

    async def can_open_trade(self, current_open_trades: int) -> bool:
        if current_open_trades >= self.max_open_trades:
            logger.info(f"[RISK] Max open trades reached ({self.max_open_trades}). Skipping.")
            return False
        return True

    def calculate_trade_parameters(self, entry_price: float, atr: float, side: str, balance: float = 0.0) -> dict:
        """
        Calculates position size and all target levels based on Entry, ATR and Side.
        SL = 2.5 ATR
        TP_FINAL = 5 ATR
        TP1 = 30% del recorrido (Entry a TP_FINAL)
        LOCK = 40% del recorrido
        TP2 = 60% del recorrido
        """
        sl_distance = atr * 2.5
        tp_final_distance = atr * 5.0
        
        if side.upper() == 'LONG':
            stop_loss = entry_price - sl_distance
            tp_final_price = entry_price + tp_final_distance
            
            tp1_price = entry_price + (tp_final_distance * 0.30)
            profit_lock_price = entry_price + (tp_final_distance * 0.40)
            tp2_price = entry_price + (tp_final_distance * 0.60)
        else: # SHORT
            stop_loss = entry_price + sl_distance
            tp_final_price = entry_price - tp_final_distance
            
            tp1_price = entry_price - (tp_final_distance * 0.30)
            profit_lock_price = entry_price - (tp_final_distance * 0.40)
            tp2_price = entry_price - (tp_final_distance * 0.60)
            
        if sl_distance <= 0:
            position_size = 0.0
        else:
            position_size = self.risk_per_trade / sl_distance
            
        logger.info(f"[RISK] Calculated for {side}: Entry={entry_price}, Size={position_size:.6f}, SL={stop_loss:.4f}, TP1={tp1_price:.4f}, LOCK={profit_lock_price:.4f}, TP2={tp2_price:.4f}")
            
        return {
            "stop_loss": stop_loss,
            "tp1_price": tp1_price,
            "profit_lock_price": profit_lock_price,
            "tp2_price": tp2_price,
            "position_size": position_size
        }