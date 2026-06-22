import asyncio
from app.exchange.bybit_client import AsyncBybitClient

async def main():
    client = AsyncBybitClient()
    print("Cancelling ALL linear orders for USDT settled contracts...")
    params_stop = {"category": "linear", "settleCoin": "USDT", "orderFilter": "StopOrder"}
    res_stop = await client._request("POST", "/v5/order/cancel-all", params=params_stop, signed=True)
    print("StopOrder Cancel Res:", res_stop)

    params_normal = {"category": "linear", "settleCoin": "USDT", "orderFilter": "Order"}
    res_normal = await client._request("POST", "/v5/order/cancel-all", params=params_normal, signed=True)
    print("Normal Order Cancel Res:", res_normal)

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
