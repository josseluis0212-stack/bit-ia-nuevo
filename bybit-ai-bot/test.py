import sys, os
sys.path.append('.')
import asyncio, json
from dotenv import load_dotenv
load_dotenv('.env')
from app.exchange.bybit_client import AsyncBybitClient
async def run():
    client = AsyncBybitClient(os.getenv('BYBIT_API_KEY'), os.getenv('BYBIT_API_SECRET'))
    orders = await client.get_open_orders('ETHUSDT')
    print(json.dumps(orders, indent=2))
asyncio.run(run())
