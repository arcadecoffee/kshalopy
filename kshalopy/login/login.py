"""
kshalopy.login.login
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import boto3

from kshalopy.config import Config
from kshalopy.credentials import Credentials
from kshalopy.utils import calculate_expiration

from kshalopy.login.helper import LoginHelper


@dataclass
class LoginParameters:
    """
    Class containing credentials and preferences for login
    """

    username: str
    password: str
    verification_method: VerificationMethods
    device_key: str


class VerificationMethods(Enum):
    """
    Enumeration of available verification methods
    """

    EMAIL = "email"
    PHONE = "phone"

    def __str__(self) -> str:
        return self.value


class LoginHandler:
    """
    Class for execution of the login process from initial username and password input,
    response with verification method, response with verification code, and receipt of
    credential tokens at the end.
    """

    def __init__(self, login_params: LoginParameters, app_config: Config):
        self.login_params = login_params
        self.app_config = app_config

        self.cognito_client = boto3.client("cognito-idp", region_name=app_config.region)
        self.credentials = None
        self.last_session = None

    def start_login(self) -> None:
        """
        Perform the first steps of the login process; sending username and initial auth
        parameters to the server, response to the first challenge, and response with
        verification method.

        Exceptions will be raised by the Cognito client if the username and password
        are invalid.
        :return: None
        """
        auth_helper = LoginHelper(
            login_params=self.login_params, app_config=self.app_config
        )

        response_1 = self.cognito_client.initiate_auth(
            AuthFlow="CUSTOM_AUTH",
            AuthParameters=auth_helper.auth_parameters,
            ClientId=self.app_config.client_id,
        )

        response_2 = self.cognito_client.respond_to_auth_challenge(
            ChallengeName="PASSWORD_VERIFIER",
            ChallengeResponses=auth_helper.process_challenge(
                response_1["ChallengeParameters"]
            ),
            ClientId=self.app_config.client_id,
            Session=response_1["Session"],
        )

        answer = ",".join(
            [
                "answerType:generateCode",
                f"medium:{self.login_params.verification_method}",
                "codeType:login",
            ]
        )
        response_3 = self.cognito_client.respond_to_auth_challenge(
            ChallengeName="CUSTOM_CHALLENGE",
            ChallengeResponses={
                "ANSWER": answer,
                "USERNAME": self.login_params.username,
            },
            ClientId=self.app_config.client_id,
            Session=response_2["Session"],
        )
        self.last_session = response_3["Session"]

    def submit_verification_code(self, code: str) -> None:
        """
        Supply the verification code to the server and receive credential tokens in
        response.

        An exception will be raised by the Cognito client if the verification code is
        invalid.
        :param code: code received via specified verification method
        :return: None
        """
        answer = ",".join(
            [
                "answerType:verifyCode",
                f"medium:{self.login_params.verification_method}",
                "codeType:login",
                f"code:{code}",
            ]
        )

        response = self.cognito_client.respond_to_auth_challenge(
            ChallengeName="CUSTOM_CHALLENGE",
            ChallengeResponses={
                "ANSWER": answer,
                "USERNAME": self.login_params.username,
            },
            ClientId=self.app_config.client_id,
            Session=self.last_session,
        )

        self.credentials = Credentials(
            region=self.app_config.region,
            client_id=self.app_config.client_id,
            username=self.login_params.username,
            access_token=response["AuthenticationResult"]["AccessToken"],
            id_token=response["AuthenticationResult"]["IdToken"],
            refresh_token=response["AuthenticationResult"]["RefreshToken"],
            token_type=response["AuthenticationResult"]["TokenType"],
            lifespan=response["AuthenticationResult"]["ExpiresIn"],
            expiration=calculate_expiration(response),
        )
