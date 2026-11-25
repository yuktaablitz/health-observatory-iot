"""AWS Lambda handlers for the API Gateway WebSocket API.

Routes: $connect -> connect, $disconnect -> disconnect, onMessage -> on_message,
$default -> default. Table names come from environment variables set in template.yaml.
"""
import json
import os
import time
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

from vitals import STATUS, classify, parse_reading

_dynamodb = None


def dynamodb():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.client("dynamodb")
    return _dynamodb


def management_api(event):
    """Build the callback client from the request itself instead of a hard-coded URL."""
    ctx = event["requestContext"]
    endpoint = "https://%s/%s" % (ctx["domainName"], ctx["stage"])
    return boto3.client("apigatewaymanagementapi", endpoint_url=endpoint)


def _response(code, body):
    return {"statusCode": code, "body": json.dumps(body)}


def connect(event, context):
    """Store the connection. Devices connect with ?role=device, screens default to dashboard."""
    params = event.get("queryStringParameters") or {}
    role = params.get("role", "dashboard")
    if role not in ("device", "dashboard"):
        return _response(400, {"error": "role must be device or dashboard"})
    dynamodb().put_item(
        TableName=os.environ["CONNECTIONS_TABLE"],
        Item={"connectionid": {"S": event["requestContext"]["connectionId"]}, "role": {"S": role}},
    )
    return _response(200, {"connected": role})


def disconnect(event, context):
    dynamodb().delete_item(
        TableName=os.environ["CONNECTIONS_TABLE"],
        Key={"connectionid": {"S": event["requestContext"]["connectionId"]}},
    )
    return _response(200, {"disconnected": True})


def default(event, context):
    return _response(400, {"error": 'unknown action; send {"action": "onMessage", ...}'})


def on_message(event, context):
    """Validate a reading, store it, and push the risk level to every dashboard."""
    try:
        reading = parse_reading(json.loads(event.get("body") or "{}"))
    except (ValueError, json.JSONDecodeError) as e:
        return _response(400, {"error": str(e)})

    level = classify(reading["temperature_c"])
    ts_ms = int(time.time() * 1000)

    item = {
        "patient_id": {"S": reading["patient_id"]},
        "ts": {"N": str(ts_ms)},
        "temperature_c": {"N": str(Decimal(str(reading["temperature_c"])))},
        "level": {"N": str(level)},
        "status": {"S": STATUS[level]},
    }
    for key in ("humidity", "seq", "pulse_ir", "pulse_red"):
        if key in reading:
            item[key] = {"N": str(reading[key])}
    dynamodb().put_item(TableName=os.environ["READINGS_TABLE"], Item=item)

    update = {
        "patient_id": reading["patient_id"],
        "level": level,                       # sent as a number so Unreal can read it directly
        "status": STATUS[level],
        "temperature_c": reading["temperature_c"],
        "ts": ts_ms,
    }
    sent = broadcast(event, update)
    return _response(200, {"level": level, "dashboards_notified": sent})


def broadcast(event, payload):
    """Send payload to every dashboard; delete connections that have gone away."""
    table = os.environ["CONNECTIONS_TABLE"]
    api = management_api(event)
    sender = event["requestContext"]["connectionId"]
    data = json.dumps(payload).encode("utf-8")
    sent = 0
    kwargs = {"TableName": table}
    while True:
        page = dynamodb().scan(**kwargs)
        for row in page.get("Items", []):
            conn_id = row["connectionid"]["S"]
            if conn_id == sender or row.get("role", {}).get("S", "dashboard") != "dashboard":
                continue
            try:
                api.post_to_connection(ConnectionId=conn_id, Data=data)
                sent += 1
            except ClientError as e:
                if e.response["Error"]["Code"] == "GoneException":
                    dynamodb().delete_item(TableName=table, Key={"connectionid": {"S": conn_id}})
                else:
                    raise
        if "LastEvaluatedKey" not in page:
            return sent
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]
