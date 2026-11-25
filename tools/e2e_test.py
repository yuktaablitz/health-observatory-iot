"""End-to-end check: real device code on MicroPython -> local gateway -> real Lambda
handlers -> dashboard. Passes when the dashboard receives levels 0, 1, 2, 0 for the
fake DHT22 series (28.4, 30.6, 32.1, failed read, 29.0).

    MICROPYTHON=/path/to/micropython python tools/e2e_test.py
"""
import asyncio
import json
import os
import subprocess
import sys
import time

import websockets

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def collect(n):
    for _ in range(50):
        try:
            ws = await websockets.connect("ws://127.0.0.1:8765/dev?role=dashboard")
            break
        except OSError:
            await asyncio.sleep(0.2)
    async with ws:
        return [json.loads(await asyncio.wait_for(ws.recv(), 10)) for _ in range(n)]


def main():
    gateway = subprocess.Popen([sys.executable, "tools/local_gateway.py"], cwd=ROOT)
    device = None
    try:
        time.sleep(2)
        loop = asyncio.new_event_loop()
        task = loop.create_task(collect(4))
        loop.run_until_complete(asyncio.sleep(1))
        device = subprocess.Popen(["sh", "tools/run_device_on_laptop.sh"], cwd=ROOT)
        updates = loop.run_until_complete(task)
        levels = [u["level"] for u in updates]
        print("dashboard levels:", levels)
        assert levels == [0, 1, 2, 0], levels
        assert all(u["patient_id"] == "bed-01" for u in updates)
        print("E2E PASS")
    finally:
        for p in (device, gateway):
            if p:
                p.terminate()


if __name__ == "__main__":
    main()
