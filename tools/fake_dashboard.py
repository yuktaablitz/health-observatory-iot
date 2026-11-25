"""Prints what the Unreal client would receive. Usage: python tools/fake_dashboard.py [url] [count]"""
import asyncio
import sys

import websockets


async def main(url, count):
    async with websockets.connect(url) as ws:
        print("dashboard connected")
        for _ in range(count):
            print("update:", await ws.recv())


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8765/dev?role=dashboard"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10**9
    asyncio.run(main(url, count))
