from enum import Enum

import boto3

from .helper import LoginHelper


class VerificationMethod(Enum):
    EMAIL = 'email'
    PHONE = 'phone'

    def __str__(self) -> str:
        return self.value


class LoginHandler:
    def __init__(
        self,
        username: str,
        password: str,
        user_pool_id: str,
        client_id: str,
        client_secret: str,
        device_key: str,
        verification_method: VerificationMethod,
    ):
        self.username = username
        self.password = password
        self.client_id = client_id
        self.device_key = device_key
        self.client_secret = client_secret
        self.verification_method = verification_method
        self.region, self.pool_id = user_pool_id.split("_")

        self.cognito_client = boto3.client("cognito-idp", region_name=self.region)
        self.tokens = {}
        self.last_session = None

    def start_login(self):
        auth_helper = LoginHelper(
            username=self.username,
            password=self.password,
            pool_id=self.pool_id,
            client_id=self.client_id,
            device_key=self.device_key,
            client_secret=self.client_secret,
        )

        response_1 = self.cognito_client.initiate_auth(
            AuthFlow="CUSTOM_AUTH",
            AuthParameters=auth_helper.auth_parameters,
            ClientId=self.client_id,
        )

        response_2 = self.cognito_client.respond_to_auth_challenge(
            ChallengeName="PASSWORD_VERIFIER",
            ChallengeResponses=auth_helper.process_challenge(
                response_1["ChallengeParameters"]
            ),
            ClientId=self.client_id,
            Session=response_1["Session"],
        )

        answer = ",".join(
            [
                "answerType:generateCode",
                f"medium:{self.verification_method}",
                "codeType:login",
            ]
        )
        response_3 = self.cognito_client.respond_to_auth_challenge(
            ChallengeName="CUSTOM_CHALLENGE",
            ChallengeResponses={"ANSWER": answer, "USERNAME": self.username},
            ClientId=self.client_id,
            Session=response_2["Session"],
        )
        self.last_session = response_3["Session"]

    def submit_verification_code(self, code: str):
        answer = ",".join(
            [
                "answerType:verifyCode",
                f"medium:{self.verification_method}",
                "codeType:login",
                f"code:{code}",
            ]
        )

        response = self.cognito_client.respond_to_auth_challenge(
            ChallengeName="CUSTOM_CHALLENGE",
            ChallengeResponses={"ANSWER": answer, "USERNAME": self.username},
            ClientId=self.client_id,
            Session=self.last_session,
        )

        self.tokens = response["AuthenticationResult"]
