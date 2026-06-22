import asyncio
import os
import shutil
from dotenv import load_dotenv
load_dotenv()
from app.exchange.bybit_client import AsyncBybitClient
from app.logger import logger

async def close_all_trades():
    client = AsyncBybitClient()
    logger.info("Fetching open positions to close...")
    positions = await client.get_positions()
    for pos in positions:
        symbol = pos.get("symbol")
        amt = float(pos.get("positionAmt", 0))
        side = "LONG" if pos.get("positionSide") == "LONG" else "SHORT"
        
        if abs(amt) > 0:
            logger.info(f"Closing {symbol} {side} position...")
            # Cancel orders first
            await client.cancel_all_orders(symbol)
            # Close position via MARKET order
            close_side = "SELL" if side == "LONG" else "BUY"
            pos_side = "LONG" if side == "LONG" else "SHORT"
            await client.place_order(
                symbol=symbol, side=close_side, position_side=pos_side,
                order_type="MARKET", quantity=abs(amt), reduce_only=True
            )
            logger.info(f"Closed {symbol}.")
    await client.close()
    logger.info("All exchange positions closed and orders cancelled.")

def delete_dbs():
    db_paths = [
        "trades.db", "bybit_trades.db", "bot_history.json",
        "../bot_history.json", "../trades.db", "../operaciones_cerradas"
    ]
    for p in db_paths:
        if os.path.exists(p):
            if os.path.isdir(p):
                shutil.rmtree(p)
                logger.info(f"Deleted directory: {p}")
            else:
                os.remove(p)
                logger.info(f"Deleted file: {p}")
                
if __name__ == "__main__":
    asyncio.run(close_all_trades())
    delete_dbs()
    print("RESET COMPLETADO")
