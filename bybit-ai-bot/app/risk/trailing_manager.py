from app.logger import logger

class TrailingManager:
    @staticmethod
    def calculate_new_sl(mark_price: float, best_price: float, current_sl: float, atr: float, side: str) -> float:
        """
        Calcula la nueva posición del Trailing Stop a exactamente 1.2 ATR del mejor precio alcanzado.
        Asegura que el Trailing Stop NUNCA retroceda.
        """
        atr_distance = atr * 1.2  # 1.2 ATR de distancia (40% del runner)
        
        if side.upper() == "LONG":
            new_sl = best_price - atr_distance
            if new_sl > current_sl:
                logger.info(f"[TRAILING] LONG - Ajustando Trailing Stop de {current_sl:.4f} a {new_sl:.4f}")
                return new_sl
            return current_sl
            
        else: # SHORT
            new_sl = best_price + atr_distance
            if new_sl < current_sl:
                logger.info(f"[TRAILING] SHORT - Ajustando Trailing Stop de {current_sl:.4f} a {new_sl:.4f}")
                return new_sl
            return current_sl
