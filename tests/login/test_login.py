from copy import deepcopy
from datetime import datetime

from kshalopy import Config
from kshalopy.login import LoginHandler, LoginParameters, VerificationMethods


class MockClient:
    call_count = -1

    arg_sets = [
        {
            "AuthFlow": "CUSTOM_AUTH",
            "AuthParameters": {
                "CHALLENGE_NAME": "SRP_A",
                "DEVICE_KEY": "fake_device",
                "SECRET_HASH": "6WklTTP6NIz2Em94M0ZqlDgoitf1aK+4NiKRJ1mU5iM=",
                "SRP_A": "29772b3d9e02c39d051aad22060afa7ffd56f689cfb6b4dbeb35822a8079f0fd1d9d4556bb59e0e5106a50307f78d5017fce6f61f872c6e1a2def7a425e0740ccda3cc5e13694bfba22e52a38f844295d5736706471228522a97c834f8df833ff9cde2cad88d311988705a1917f08d789df85aaa96ce69f0f432b597a097098078031d840c25c9613ae62cfe1a9a4ed0e854e75fdf80337dd534db4f6c01cd42e085482720d23d47cb8f5689661980fe058b2592c54d1c22ad0658efe0a0a342e8e344f74422ad3665f35d7ea185375b85ff27d2efaac8e72a856fa5f8ba069dfe6528a31e0fa889ab96f4b017305001a03f7ca7bc27e5454dd9096f51e225ca5b2a88d193ea2104bbc626680907dabb21cfc737427fde9cbe65b9b46f6ece6921a4e7185b6016250524db7e70227fec9ca0120b546ab687265a4191941b0ce3a8d1988c90abdc1c30c94426603e0d3da952efd65672815c4a6b850f716046608b9993fcb875479bfd058ce3be6733a9137c88abb8a3041e9b7fe7098fdc340f",
                "USERNAME": "fake_name",
            },
            "ClientId": "fake_client_id",
        },
        {
            "ChallengeName": "PASSWORD_VERIFIER",
            "ChallengeResponses": {
                "PASSWORD_CLAIM_SECRET_BLOCK": "fake_secret_block=",
                "PASSWORD_CLAIM_SIGNATURE": "tN7tn9cO42beu3Qp9ANX3Oy0GOfvke07tLHUFM8ioug=",
                "SECRET_HASH": "6WklTTP6NIz2Em94M0ZqlDgoitf1aK+4NiKRJ1mU5iM=",
                "TIMESTAMP": "Fri Feb 18 16:57:48 UTC 2022",
                "USERNAME": "fake_name",
            },
            "ClientId": "fake_client_id",
            "Session": "fake_session",
        },
        {
            "ChallengeName": "CUSTOM_CHALLENGE",
            "ChallengeResponses": {
                "ANSWER": "answerType:generateCode,medium:email,codeType:login",
                "USERNAME": "fake_name",
            },
            "ClientId": "fake_client_id",
            "Session": "fake_session",
        },
        {
            "ChallengeName": "CUSTOM_CHALLENGE",
            "ChallengeResponses": {
                "ANSWER": "answerType:verifyCode,medium:email,codeType:login,code:12345",
                "USERNAME": "fake_name",
            },
            "ClientId": "fake_client_id",
            "Session": "fake_session",
        },
        {
            "IdentityPoolId": "fake_identity_pool",
            "Logins": {
                "cognito-idp.us-east-1.amazonaws.com/us-east-1_fake_user_pool": "fake_id_token"
            },
        },
        {
            "IdentityId": "fake_identity_id",
            "Logins": {
                "cognito-idp.us-east-1.amazonaws.com/us-east-1_fake_user_pool": "fake_id_token"
            },
        },
    ]

    return_sets = [
        {
            "ChallengeParameters": {
                "USERNAME": "fake_name",
                "USER_ID_FOR_SRP": "fake_user_id",
                "SALT": "42",
                "SECRET_BLOCK": "fake_secret_block=",
                "SRP_B": "0420",
            },
            "Session": "fake_session",
        },
        {
            "ChallengeParameters": {
                "USERNAME": "fake_name",
                "USER_ID_FOR_SRP": "fake_user_id",
                "SALT": "42",
                "SECRET_BLOCK": "fake_secret_block=",
                "SRP_B": "0420",
            },
            "Session": "fake_session",
        },
        {
            "Session": "fake_session",
        },
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
                "Expiration": datetime(2022, 2, 18, 12, 47, 56, 201585)
            }
        }
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


class FakeDatetime:
    @staticmethod
    def utcnow():
        return datetime.utcfromtimestamp(1645203468)


def fake_login_flow(monkeypatch, client_secret, mock_client):
    monkeypatch.setattr("kshalopy.login.helper.urandom", lambda n: b"0" * n)
    monkeypatch.setattr("kshalopy.login.login.boto3.client", mock_client)
    monkeypatch.setattr("kshalopy.login.helper.datetime", FakeDatetime)

    config = Config.load_defaults()
    config.__dict__.update(
        {
            "host": "fake.execute-api.us-east-1.amazonaws.fake",
            "user_pool_id": "fake_user_pool",
            "client_id": "fake_client_id",
            "identity_pool_id": "fake_identity_pool",
            "client_secret": "fake_secret" if client_secret else "",
        }
    )

    login_params = LoginParameters(
        username="fake_name",
        password="fake_password",
        verification_method=VerificationMethods.EMAIL,
        device_key="fake_device",
    )

    authenticator = LoginHandler(login_params=login_params, app_config=config)
    authenticator.start_login()
    authenticator.submit_verification_code("12345")
    return authenticator.credentials


def test_login_flow_with_secret(monkeypatch):
    class MyMockClient(MockClient):
        pass
    with_secret = fake_login_flow(monkeypatch, True, MyMockClient)
    assert with_secret.access_token == "fake_access_token"


def test_login_flow_without_secret(monkeypatch):
    class MyMockClient(MockClient):
        pass
    del MyMockClient.arg_sets[0]["AuthParameters"]["SECRET_HASH"]
    del MyMockClient.arg_sets[1]["ChallengeResponses"]["SECRET_HASH"]
    without_secret = fake_login_flow(monkeypatch, False, MyMockClient)
    assert without_secret.access_token == "fake_access_token"
