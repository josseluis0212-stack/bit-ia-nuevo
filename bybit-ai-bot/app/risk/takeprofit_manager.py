class TakeProfitManager:
    @staticmethod
    def calculate_tp_quantities(total_size: float) -> tuple:
        """
        Returns exactly 30% of total size for TP1, and 30% for TP2.
        Remaining 40% is kept for the trailing stop.
        """
        tp_qty = round(total_size * 0.30, 4)
        return tp_qty, tp_qty