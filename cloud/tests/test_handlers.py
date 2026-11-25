import json

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

import handlers


class FakeManagementApi:
    """Records pushes; connection ids in `gone` raise GoneException like real API Gateway."""

    def __init__(self, gone=()):
        self.sent = []
        self.gone = set(gone)

    def post_to_connection(self, ConnectionId, Data):
        if ConnectionId in self.gone:
            raise ClientError({"Error": {"Code": "GoneException", "Message": "gone"}}, "PostToConnection")
        self.sent.append((ConnectionId, json.loads(Data)))


def event(conn_id, body=None, query=None):
    return {
        "requestContext": {"connectionId": conn_id, "domainName": "abc.execute-api.us-west-2.amazonaws.com", "stage": "dev"},
        "body": json.dumps(body) if body is not None else None,
        "queryStringParameters": query,
    }


@pytest.fixture
def aws(monkeypatch):
    with mock_aws():
        ddb = boto3.client("dynamodb", region_name="us-west-2")
        ddb.create_table(TableName="conns", BillingMode="PAY_PER_REQUEST",
                         AttributeDefinitions=[{"AttributeName": "connectionid", "AttributeType": "S"}],
                         KeySchema=[{"AttributeName": "connectionid", "KeyType": "HASH"}])
        ddb.create_table(TableName="readings", BillingMode="PAY_PER_REQUEST",
                         AttributeDefinitions=[{"AttributeName": "patient_id", "AttributeType": "S"},
                                               {"AttributeName": "ts", "AttributeType": "N"}],
                         KeySchema=[{"AttributeName": "patient_id", "KeyType": "HASH"},
                                    {"AttributeName": "ts", "KeyType": "RANGE"}])
        monkeypatch.setenv("CONNECTIONS_TABLE", "conns")
        monkeypatch.setenv("READINGS_TABLE", "readings")
        monkeypatch.setattr(handlers, "_dynamodb", ddb)
        yield ddb


def test_connect_and_disconnect(aws):
    assert handlers.connect(event("dev1", query={"role": "device"}), None)["statusCode"] == 200
    assert handlers.connect(event("screen1"), None)["statusCode"] == 200
    roles = {i["connectionid"]["S"]: i["role"]["S"] for i in aws.scan(TableName="conns")["Items"]}
    assert roles == {"dev1": "device", "screen1": "dashboard"}
    handlers.disconnect(event("dev1"), None)
    assert len(aws.scan(TableName="conns")["Items"]) == 1


def test_connect_rejects_unknown_role(aws):
    assert handlers.connect(event("x", query={"role": "admin"}), None)["statusCode"] == 400


def test_reading_is_stored_and_sent_only_to_dashboards(aws, monkeypatch):
    for cid, q in [("dev1", {"role": "device"}), ("dev2", {"role": "device"}), ("screen1", None), ("screen2", None)]:
        handlers.connect(event(cid, query=q), None)
    api = FakeManagementApi()
    monkeypatch.setattr(handlers, "management_api", lambda e: api)

    res = handlers.on_message(event("dev1", {"action": "onMessage", "patient_id": "bed-01",
                                              "temperature_c": 31.6, "humidity": 48.0, "seq": 3}), None)

    assert res["statusCode"] == 200
    assert json.loads(res["body"]) == {"level": 2, "dashboards_notified": 2}
    assert sorted(c for c, _ in api.sent) == ["screen1", "screen2"]
    payload = api.sent[0][1]
    assert payload["patient_id"] == "bed-01" and payload["level"] == 2 and isinstance(payload["level"], int)
    item = aws.query(TableName="readings", KeyConditionExpression="patient_id = :p",
                     ExpressionAttributeValues={":p": {"S": "bed-01"}})["Items"][0]
    assert item["temperature_c"]["N"] == "31.6" and item["level"]["N"] == "2" and item["seq"]["N"] == "3"


def test_stale_dashboard_is_removed(aws, monkeypatch):
    handlers.connect(event("dev1", query={"role": "device"}), None)
    handlers.connect(event("screen1"), None)
    handlers.connect(event("closed-tab"), None)
    api = FakeManagementApi(gone={"closed-tab"})
    monkeypatch.setattr(handlers, "management_api", lambda e: api)

    res = handlers.on_message(event("dev1", {"patient_id": "bed-02", "temperature_c": 25}), None)

    assert json.loads(res["body"])["dashboards_notified"] == 1
    left = {i["connectionid"]["S"] for i in aws.scan(TableName="conns")["Items"]}
    assert left == {"dev1", "screen1"}


def test_bad_message_returns_400_and_stores_nothing(aws, monkeypatch):
    monkeypatch.setattr(handlers, "management_api", lambda e: FakeManagementApi())
    for body in ("not json", json.dumps({"patient_id": "bed-01"})):
        ev = event("dev1")
        ev["body"] = body
        assert handlers.on_message(ev, None)["statusCode"] == 400
    assert aws.scan(TableName="readings")["Count"] == 0


def test_management_api_uses_request_endpoint():
    client = handlers.management_api(event("x"))
    assert client.meta.endpoint_url == "https://abc.execute-api.us-west-2.amazonaws.com/dev"


def test_default_route():
    assert handlers.default(event("x"), None)["statusCode"] == 400
