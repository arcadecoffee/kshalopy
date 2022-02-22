import json

from datetime import datetime, timezone
from io import TextIOBase
from pathlib import Path

from kshalopy.credentials.credentials import AppCredentials

test_path = str(Path.joinpath(Path(__file__).parent, "test_credentials.json"))
test_path_partial = str(
    Path.joinpath(Path(__file__).parent, "test_partial_credentials.json")
)


def test_loaded_credentials():
    credentials = AppCredentials.load_credentials(test_path)
    assert credentials.aws_credentials.secret_key == "fake_secret_key"
    assert credentials.id_token == "fake_id_token"
    assert credentials.expiration_dt.astimezone(timezone.utc) == datetime(
        2022, 2, 18, 17, 46, 17, tzinfo=timezone.utc
    )
    assert credentials.ttl == 0

    credentials.expiration = datetime.now().timestamp() + 3600
    assert 3600 > credentials.ttl > 3599


def test_partial_loaded_credentials():
    credentials = AppCredentials.load_credentials(test_path_partial)
    assert not credentials.aws_credentials
    assert not credentials.app_config
    assert credentials.id_token == "fake_id_token"


def test_save_credentials(monkeypatch):
    class FakeFile(TextIOBase):
        with open(test_path) as infile:
            expected = infile.read()

        def write(self, content):
            assert json.loads(content) == json.loads(self.expected)

    credentials = AppCredentials.load_credentials(test_path)
    monkeypatch.setattr("builtins.open", FakeFile)
    credentials.save_credentials("foo.123.json")


class MockClient:
    call_count = -1

    arg_sets = [
        {
            "AuthFlow": "REFRESH_TOKEN",
            "AuthParameters": {
                "CURRENT_USER": "fake_username",
                "REFRESH_TOKEN": "fake_refresh_token",
            },
            "ClientId": "fake_client_id",
        },
        {
            "IdentityPoolId": "fake_identity_pool_id",
            "Logins": {
                "cognito-idp.us-east-1.amazonaws.com/us-east-1_fake_user_pool_id": (
                    "fake_id_token"
                )
            },
        },
        {
            "IdentityId": "fake_identity_id",
            "Logins": {
                "cognito-idp.us-east-1.amazonaws.com/us-east-1_fake_user_pool_id": (
                    "fake_id_token"
                )
            },
        },
    ]

    return_sets = [
        {
            "AuthenticationResult": {
                "AccessToken": "fake_access_token",
                "ExpiresIn": 3600,
                "IdToken": "fake_id_token",
                "RefreshToken": "fake_refresh_token",
                "TokenType": "Bearer",
            },
            "ResponseMetadata": {
                "HTTPHeaders": {"date": "Fri, Feb 18 2022 16:57:52 GMT"}
            },
            "Session": "fake_session",
        },
        {
            "IdentityId": "fake_identity_id",
        },
        {
            "IdentityId": "fake_identity_id",
            "Credentials": {
                "AccessKeyId": "fake_access_key_id",
                "SecretKey": "fake_secret_key",
                "SessionToken": "fake_session_token",
                "Expiration": datetime(2022, 2, 18, 12, 47, 56, 201585),
            },
        },
    ]

    def __init__(self, client_type, region_name):
        assert client_type in ("cognito-idp", "cognito-identity")
        assert region_name

        for func in (
            "initiate_auth",
            "respond_to_auth_challenge",
            "get_id",
            "get_credentials_for_identity",
        ):
            self.__dict__[func] = self.handle_call

    def handle_call(self, **kwargs):
        self.__class__.call_count += 1
        assert kwargs == self.arg_sets[self.__class__.call_count]
        return self.return_sets[self.__class__.call_count]


def test_refresh(monkeypatch):
    class MyMockClient(MockClient):
        pass

    monkeypatch.setattr("kshalopy.login.login.boto3.client", MyMockClient)
    credentials = AppCredentials.load_credentials(test_path)
    credentials.refresh()


def test_early_refresh(monkeypatch):
    class MyMockClient(MockClient):
        pass

    monkeypatch.setattr("kshalopy.login.login.boto3.client", MyMockClient)
    credentials = AppCredentials.load_credentials(test_path)
    credentials.expiration = datetime.now().timestamp() + 1000
    credentials.refresh()
    assert MyMockClient.call_count == -1


def test_forced_refresh(monkeypatch):
    class MyMockClient(MockClient):
        pass

    monkeypatch.setattr("kshalopy.login.login.boto3.client", MyMockClient)
    credentials = AppCredentials.load_credentials(test_path)
    credentials.expiration = datetime.now().timestamp() + 1000
    credentials.refresh(force=True)
    assert MyMockClient.call_count > -1
