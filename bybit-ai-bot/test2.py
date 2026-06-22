import asyncio, aiohttp, time, hmac, hashlib, os, json
from dotenv import load_dotenv
load_dotenv('.env')
api_key = os.getenv('BYBIT_API_KEY')
api_secret = os.getenv('BYBIT_API_SECRET')

async def get_orders():
    timestamp = str(int(time.time() * 1000))
    recv_window = '5000'
    params = 'category=linear&symbol=ETHUSDT&orderFilter=StopOrder'
    param_str = timestamp + api_key + recv_window + params
    signature = hmac.new(bytes(api_secret, 'utf-8'), param_str.encode('utf-8'), hashlib.sha256).hexdigest()
    headers = {'X-BAPI-API-KEY': api_key, 'X-BAPI-TIMESTAMP': timestamp, 'X-BAPI-SIGN': signature, 'X-BAPI-RECV-WINDOW': recv_window}
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.bybit.com/v5/order/realtime?{params}', headers=headers) as resp:
            print(json.dumps(await resp.json(), indent=2))

asyncio.run(get_orders())
