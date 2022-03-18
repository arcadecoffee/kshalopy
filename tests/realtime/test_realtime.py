import json
import re
import threading

from src.kshalopy import AppCredentials, Config, RealtimeClient
from models.models import Device

config = Config(
    host="fake.execute-api.us-east-1.amazonaws.fake",
    port=443,
    use_ssl=True,
    region="us-east-1",
    user_pool_id="fake_user_pool_id",
    client_id="fake_client_id",
    identity_pool_id="fake_identity_pool_id",
    client_secret="",
    appsync_api_url="https://fake.appsync-api.us-east-1.amazonaws.fake/graphql",
)

credentials = AppCredentials()


def normalize(data: str) -> str:
    return re.sub(" +", " ", data.replace("\n", " "))


def test_realtime_client_url():
    realtime_client = RealtimeClient(
        config=config, credentials=credentials, devices={}
    )
    assert (
        realtime_client.ws_app.url
        == "wss://fake.appsync-realtime-api.us-east-1.amazonaws.fake/graphql?header=eyJob3N0IjogImZha2UuYXBwc3luYy1hcGkudXMtZWFzdC0xLmFtYXpvbmF3cy5mYWtlIiwgIkF1dGhvcml6YXRpb24iOiBudWxsfQ==&payload=e30="
    )


def test_realtime_subscription_flow(monkeypatch):
    class MockWebsocketApp:
        query = json.dumps(
            {
                "query": f"""
                        subscription onManageDevice {{
                        onManageDevice(email: "None")
                    {{ deviceid devicename devicestatus operationtype }} }}
                    """,
                "variables": {},
            }
        )
        messages_sent = [
            {"type": "connection_init"},
            {
                "id": "42",
                "payload": {
                    "data": query,
                    "extensions": {
                        "authorization": {
                            "host": "fake.appsync-api.us-east-1.amazonaws.fake",
                            "Authorization": None,
                        }
                    },
                },
                "type": "start",
            },
            {"id": "42", "type": "stop"}
        ]

        messages_received = [
            {"type": "connection_ack", "payload": {"connectionTimeoutMs": 1000}},
            {"type": "start_ack", "id": "42"},
            {"type": "complete", "id": "42"},
        ]

        def __init__(self, url, *args, **kwargs):
            self.url = url
            self.on_close = kwargs["on_close"]
            self.on_message = kwargs["on_message"]
            self.on_open = kwargs["on_open"]
            self.keep_running = False

        def run_forever(self):
            self.keep_running = True
            self.on_open(self)

        def send(self, msg: str):
            actual = normalize(msg)
            expected = normalize(json.dumps(self.messages_sent.pop(0)))
            assert actual == expected
            if self.messages_received:
                self.on_message(self, json.dumps(self.messages_received.pop(0)))

        def close(self):
            self.on_close(self, 42, "42")

    monkeypatch.setattr("src.kshalopy.realtime.realtime.WebSocketApp", MockWebsocketApp)
    monkeypatch.setattr("src.kshalopy.realtime.realtime.uuid4", lambda: "42")
    realtime_client = RealtimeClient(
        config=config, credentials=credentials, devices={}
    )
    realtime_client.start()
    assert realtime_client.active
    realtime_client.close()


def test_realtime_data_message():
    devices = {
        "fake_device_id": Device("fake_device_id")
    }
    realtime_client = RealtimeClient(
        config=config, credentials=credentials, devices=devices
    )
    realtime_client._subscription_ids.append("42")
    msg = {
        "type": "data",
        "id": "42",
        "payload": {
            "data": {
                "onManageDevice": {
                    "deviceid": "fake_device_id",
                    "devicestatus": "Locked"
                }
            }
        }
    }
    realtime_client._on_message(realtime_client.ws_app, json.dumps(msg))
    assert devices["fake_device_id"].lockstatus == "Locked"


def test_unknown_message_type():
    devices = {
        "fake_device_id": Device("fake_device_id")
    }
    realtime_client = RealtimeClient(
        config=config, credentials=credentials, devices=devices
    )
    realtime_client._subscription_ids.append("42")
    msg = {
        "type": "FOO",
        "id": "42",
        "payload": {
            "data": {
                "onManageDevice": {
                    "deviceid": "fake_device_id",
                    "devicestatus": "Locked"
                }
            }
        }
    }
    realtime_client._on_message(realtime_client.ws_app, json.dumps(msg))
    assert not devices["fake_device_id"].lockstatus


def test_unknown_device():
    devices = {
        "fake_device_id": Device("fake_device_id")
    }
    realtime_client = RealtimeClient(
        config=config, credentials=credentials, devices=devices
    )
    realtime_client._subscription_ids.append("42")
    msg = {
        "type": "data",
        "id": "42",
        "payload": {
            "data": {
                "onManageDevice": {
                    "deviceid": "other_fake_device_id",
                    "devicestatus": "Locked"
                }
            }
        }
    }
    realtime_client._on_message(realtime_client.ws_app, json.dumps(msg))
    assert not devices["fake_device_id"].lockstatus


def test_close(monkeypatch):
    class MockWebsocketApp:
        def __init__(self, *args, **kwargs):
            pass

        def close(self):
            pass

        def send(self, msg):
            pass

    monkeypatch.setattr("src.kshalopy.realtime.realtime.WebSocketApp", MockWebsocketApp)
    realtime_client = RealtimeClient(
        config=config, credentials=credentials, devices={}
    )
    realtime_client._subscription_ids.append("42")
    t = threading.Thread(target=realtime_client.close)
    t.start()
    realtime_client._subscription_ids.pop()
    t.join()


def test_error():
    realtime_client = RealtimeClient(
        config=config, credentials=credentials, devices={}
    )
    realtime_client._on_error(realtime_client.ws_app, Exception("FOO"))
