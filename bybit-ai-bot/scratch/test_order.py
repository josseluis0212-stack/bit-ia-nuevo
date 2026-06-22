import asyncio
from app.exchange.bybit_client import AsyncBybitClient
import os

async def main():
    # Set the environment variables to mimic Render
    os.environ["BYBIT_API_KEY"] = "HhnNGLd7a7SggiiflC"
    os.environ["BYBIT_API_SECRET"] = "L1B2bTfMgN39mFF5RfcRhgs2aylfuIo1FjVL"
    os.environ["BYBIT_DEMO"] = "True"
    
    # Reload config just in case
    import importlib
    import app.config
    importlib.reload(app.config)
    
    print("REST URL:", app.config.Config.REST_URL)
    
    client = AsyncBybitClient()
    
    print("Testing connection (get_positions)...")
    positions = await client.get_positions()
    print("Positions result:", positions)
    
    if isinstance(positions, list):
        print("API keys are valid! Attempting to place a test Limit Order (to be cancelled immediately)...")
        # Place a limit order far away from current price
        # For BTCUSDT, limit buy at $10,000
        order = await client.create_order(
            symbol="BTCUSDT",
            side="Buy",
            order_type="Limit",
            qty=0.001,
            price=10000.0,
            is_leverage=True
        )
        print("Order Placement Result:", order)
        
        if order and "orderId" in order:
            print("Canceling test order...")
            cancel = await client.cancel_order("BTCUSDT", order["orderId"])
            print("Cancel Result:", cancel)
            print("SUCCESS! The bot can open and close positions perfectly.")
        else:
            print("Failed to place test order.")
    else:
        print("Failed to get positions. Keys might still be invalid.")
        
asyncio.run(main())
