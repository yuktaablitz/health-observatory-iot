"""Run the whole cloud side on your laptop - no AWS account needed.

Stands in for API Gateway: accepts WebSocket connections on ws://localhost:8765,
routes them to the real Lambda handlers in cloud/functions, and keeps DynamoDB
in memory with moto. Point the ESP32 (or tools/fake_device.py) and the Unreal
client at ws://<your-laptop-ip>:8765/dev?role=device / ?role=dashboard.

    pip install -r cloud/requirements-dev.txt websockets
    python tools/local_gateway.py
"""
import asyncio
import json
import os
import sys
import uuid
from urllib.parse import parse_qs, urlparse

import boto3
import websockets
from moto import mock_aws

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cloud", "functions"))
os.environ.setdefault("AWS_DEFAULT_REGION", "us-west-2")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "local")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "local")
os.environ.setdefault("CONNECTIONS_TABLE", "connections")
os.environ.setdefault("READINGS_TABLE", "readings")

import handlers  # noqa: E402

SOCKETS = {}
LOOP = None


class LocalManagementApi:
    """Same call the Lambda makes on API Gateway, delivered to local sockets."""

    def post_to_connection(self, ConnectionId, Data):
        ws = SOCKETS.get(ConnectionId)
        if ws is None:
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "GoneException", "Message": "gone"}}, "PostToConnection")
        LOOP.create_task(ws.send(Data.decode() if isinstance(Data, bytes) else Data))


def make_event(conn_id, path, body=None):
    query = {k: v[0] for k, v in parse_qs(urlparse(path).query).items()} or None
    return {"requestContext": {"connectionId": conn_id, "domainName": "localhost", "stage": "dev"},
            "queryStringParameters": query, "body": body}


async def serve(ws):
    conn_id = uuid.uuid4().hex[:12]
    path = ws.request.path
    res = handlers.connect(make_event(conn_id, path), None)
    if res["statusCode"] != 200:
        await ws.close(1008, res["body"])
        return
    SOCKETS[conn_id] = ws
    print("connected", conn_id, path)
    try:
        async for raw in ws:
            try:
                action = json.loads(raw).get("action")
            except (ValueError, AttributeError):
                action = None
            handler = handlers.on_message if action == "onMessage" else handlers.default
            res = handler(make_event(conn_id, path, raw), None)
            print(conn_id, action, res["statusCode"], res["body"])
    finally:
        SOCKETS.pop(conn_id, None)
        handlers.disconnect(make_event(conn_id, path), None)
        print("disconnected", conn_id)


def create_tables():
    ddb = boto3.client("dynamodb")
    ddb.create_table(TableName=os.environ["CONNECTIONS_TABLE"], BillingMode="PAY_PER_REQUEST",
                     AttributeDefinitions=[{"AttributeName": "connectionid", "AttributeType": "S"}],
                     KeySchema=[{"AttributeName": "connectionid", "KeyType": "HASH"}])
    ddb.create_table(TableName=os.environ["READINGS_TABLE"], BillingMode="PAY_PER_REQUEST",
                     AttributeDefinitions=[{"AttributeName": "patient_id", "AttributeType": "S"},
                                           {"AttributeName": "ts", "AttributeType": "N"}],
                     KeySchema=[{"AttributeName": "patient_id", "KeyType": "HASH"},
                                {"AttributeName": "ts", "KeyType": "RANGE"}])


async def main(port):
    global LOOP
    LOOP = asyncio.get_running_loop()
    handlers.management_api = lambda event: LocalManagementApi()
    async with websockets.serve(serve, "0.0.0.0", port):
        print("local gateway on ws://0.0.0.0:%d" % port)
        await asyncio.Future()


if __name__ == "__main__":
    with mock_aws():
        create_tables()
        asyncio.run(main(int(os.environ.get("PORT", "8765"))))
