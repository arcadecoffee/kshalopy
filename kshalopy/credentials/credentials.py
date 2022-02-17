"""
kshalopy.credentials.credentials
"""

# pylint: disable=R0902, R0913
# too-many-instance-attributes, too-many-arguments
# The credential set is as long as it wants to be and no longer

from __future__ import annotations

import json

from dataclasses import dataclass
from datetime import datetime

import boto3

from kshalopy.config import Config
from kshalopy.utils import calculate_expiration


@dataclass
class CredentialsBase:
    """
    Base class for credentials and generic methods
    """

    expiration: float = 0

    @property
    def expiration_dt(self) -> datetime:
        """
        Return expiration as datetime object
        :return: expiration datetime
        """
        return datetime.fromtimestamp(self.expiration)

    @property
    def ttl(self) -> float:
        """
        Return time, in seconds, until expiration of current access and ID token
        :return: time until expiration
        """
        ttl = self.expiration - datetime.now().timestamp()
        return 0 if ttl <= 0 else ttl

    def save_credentials(self, filename: str) -> None:
        """
        Save current credentials for future use to a JSON file
        :param filename: name and path for save file
        :return: None
        """
        with open(filename, "w", encoding="ascii") as outfile:
            outfile.write(json.dumps(self, default=lambda o: o.__dict__, indent=4))


@dataclass
class AWSCredentials(CredentialsBase):
    """
    Class for containing AWS credentials
    """

    identity_id: str = None
    access_key_id: str = None
    secret_key: str = None
    session_token: str = None

    @classmethod
    def get_credentials(
        cls, region: str, identity_pool_id: str, user_pool_id: str, id_token: str
    ) -> AWSCredentials:
        """
        Retrieve AWS identities and IAM access tokens for Cognito user
        :param region:
        :param identity_pool_id:
        :param user_pool_id:
        :param id_token:
        :return:
        """
        logins = {
            f"cognito-idp.{region}.amazonaws.com/{region}_{user_pool_id}": id_token
        }
        identity_client = boto3.client("cognito-identity", region_name=region)
        response = identity_client.get_id(
            IdentityPoolId=identity_pool_id, Logins=logins
        )
        response = identity_client.get_credentials_for_identity(
            IdentityId=response["IdentityId"], Logins=logins
        )
        return cls(
            identity_id=response["IdentityId"],
            access_key_id=response["Credentials"]["AccessKeyId"],
            secret_key=response["Credentials"]["SecretKey"],
            session_token=response["Credentials"]["SessionToken"],
            expiration=response["Credentials"]["Expiration"].timestamp(),
        )


@dataclass
class AppCredentials(CredentialsBase):
    """
    Class for storing, accessing, and refreshing credential tokens. Access and ID tokens
    will auto-refresh on use if they are expired or close to expiration
    """

    app_config: Config = None
    username: str = None
    access_token: str = None
    id_token: str = None
    refresh_token: str = None
    token_type: str = None
    lifespan: int = None
    aws_credentials: AWSCredentials = None

    def __post_init__(self):
        if not self.aws_credentials:
            self.aws_credentials = AWSCredentials.get_credentials(
                region=self.app_config.region,
                identity_pool_id=self.app_config.identity_pool_id,
                user_pool_id=self.app_config.user_pool_id,
                id_token=self.id_token,
            )

    def refresh(self, ttl_limit: int = 900, force: bool = False) -> None:
        """
        Use the refresh token to get new access and ID tokens
        :return: None
        """
        if (self.ttl < ttl_limit) or force:
            idp_client = boto3.client("cognito-idp", region_name=self.app_config.region)
            response = idp_client.initiate_auth(
                ClientId=self.app_config.client_id,
                AuthFlow="REFRESH_TOKEN",
                AuthParameters={
                    "CURRENT_USER": self.username,
                    "REFRESH_TOKEN": self.refresh_token,
                },
            )
            self.access_token = response["AuthenticationResult"]["AccessToken"]
            self.id_token = response["AuthenticationResult"]["IdToken"]
            self.lifespan = response["AuthenticationResult"]["ExpiresIn"]
            self.expiration = calculate_expiration(response)
            self.aws_credentials = AWSCredentials.get_credentials(
                region=self.app_config.region,
                identity_pool_id=self.app_config.identity_pool_id,
                user_pool_id=self.app_config.user_pool_id,
                id_token=self.id_token,
            )

    @classmethod
    def load_credentials(cls, filename: str) -> AppCredentials:
        """
        Load credentials from a JSON file like that created by the save method above
        :param filename: name and path for file to load
        :return: Credentials object
        """
        with open(filename, encoding="ascii") as infile:
            raw_data = json.load(infile)
        if isinstance(raw_data["app_config"], dict):
            raw_data["app_config"] = Config(**raw_data["app_config"])
        if isinstance(raw_data["aws_credentials"], dict):
            raw_data["aws_credentials"] = AWSCredentials(**raw_data["aws_credentials"])
        return cls(**raw_data)
