import kshalopy


config = kshalopy.Config(
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

credentials = kshalopy.AppCredentials()
devices = {}


class MockWebsocketApp:
    def __init__(self, url, *args, **kwargs):
        self.url = url


def test_realtime_client_url(monkeypatch):
    monkeypatch.setattr("kshalopy.realtime.realtime.WebSocketApp", MockWebsocketApp)
    realtime_client = kshalopy.RealtimeClient(
        config=config, credentials=credentials, devices=devices
    )
    assert (
        realtime_client.ws_app.url
        == "wss://fake.appsync-realtime-api.us-east-1.amazonaws.fake/graphql?header=eyJob3N0IjogImZha2UuYXBwc3luYy1hcGkudXMtZWFzdC0xLmFtYXpvbmF3cy5mYWtlIiwgIkF1dGhvcml6YXRpb24iOiBudWxsfQ==&payload=e30="
    )

