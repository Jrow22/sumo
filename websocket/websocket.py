import asyncio
from aiohttp import web, WSMsgType
import redis.asyncio as aioredis
import gzip
import json

REDIS_URL = "redis://redis:6379"
#REDIS_URL = "redis://localhost:6379"
redis = aioredis.from_url(REDIS_URL, decode_responses=False)

clients = set()
redis_listener_task = None
def decompress_json_gzip(compressed_data):
    decompressed_bytes = gzip.decompress(compressed_data)
    json_string = decompressed_bytes.decode('utf-8')
    data = json.loads(json_string)
    return data

def compress_json_gzip(data):
    json_string = json.dumps(data)
    json_bytes = json_string.encode('utf-8')
    return gzip.compress(json_bytes, compresslevel=9)


async def health(request):
    return web.Response(text="OK")

async def broadcast(data):
    if clients:
        await asyncio.gather(*[client.send_bytes(data) for client in clients])

async def listen_to_redis():
    pubsub = redis.pubsub()
    await pubsub.subscribe("positions")

    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = message['data']
                await broadcast(data)
    except asyncio.CancelledError:
        print("Redis listener cancelled, unsubscribing...")
        await pubsub.unsubscribe("positions")
        await pubsub.close()
        raise

async def websocket_handler(request):
    global redis_listener_task
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    clients.add(ws)
    print("Client connected")

    if len(clients) == 1 and redis_listener_task is None:
        redis_listener_task = asyncio.create_task(listen_to_redis())
        print("Started Redis listener")

    await redis.set("sim_control", "start")

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                pass
            elif msg.type == WSMsgType.ERROR:
                print(f"WebSocket connection closed with exception {ws.exception()}")
    finally:
        clients.remove(ws)
        print("Client disconnected")

        if not clients:
            await redis.set("sim_control", "stop")
            if redis_listener_task:
                redis_listener_task.cancel()
                try:
                    await redis_listener_task
                except asyncio.CancelledError:
                    pass
                redis_listener_task = None
                print("Stopped Redis listener")

    return ws

async def main():
    app = web.Application()
    app.add_routes([
        web.get('/health', health),
        web.get('/', websocket_handler)
    ])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()

    print("Server started on port 8000")
    while True:
        await asyncio.sleep(3600)

asyncio.run(main())
