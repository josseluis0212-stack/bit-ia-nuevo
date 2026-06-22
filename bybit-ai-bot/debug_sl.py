import asyncio
import json
from dotenv import load_dotenv
load_dotenv()
from app.exchange.bybit_client import AsyncBybitClient

async def main():
    client = AsyncBybitClient()
    orders = await client.get_open_orders('FARTCOINUSDT')
    print(json.dumps(orders, indent=2))
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
