import asyncio
import os
import shutil
from app.exchange.bybit_client import AsyncBybitClient
from app.logger import logger
from app.database import crud

async def reset_all():
    logger.info("Iniciando reseteo total...")
    
    # 1. Limpiar base de datos
    logger.info("Borrando base de datos y archivos de estado...")
    if os.path.exists("trades.db"):
        os.remove("trades.db")
    if os.path.exists("app/data"):
        shutil.rmtree("app/data")
        os.makedirs("app/data")
    if os.path.exists("btc_block.json"):
        os.remove("btc_block.json")
        
    await crud.init_db()
    
    # 2. Cerrar todo en el exchange
    logger.info("Conectando al exchange para cancelar órdenes y posiciones...")
    client = AsyncBybitClient()
    
    # Cerrar posiciones
    positions = await client.get_positions()
    if positions:
        for pos in positions:
            sym = pos.get("symbol")
            amt = float(pos.get("positionAmt", 0))
            if abs(amt) > 0:
                side = "SELL" if pos.get("positionSide") == "LONG" else "BUY"
                logger.info(f"Cerrando posición en {sym} ({amt})...")
                await client.place_order(
                    symbol=sym,
                    side=side,
                    position_side=pos.get("positionSide"),
                    order_type="MARKET",
                    quantity=abs(amt),
                    reduce_only=True
                )
    
    # Cancelar órdenes
    open_orders = await client.get_open_orders()
    if open_orders:
        symbols_with_orders = set(o.get("symbol") for o in open_orders)
        for sym in symbols_with_orders:
            logger.info(f"Cancelando todas las órdenes para {sym}...")
            await client.cancel_all_orders(sym)

    logger.info("Reseteo completado. Listo para arrancar desde cero.")

if __name__ == "__main__":
    asyncio.run(reset_all())
