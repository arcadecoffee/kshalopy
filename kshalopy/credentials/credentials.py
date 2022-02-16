"""
kshalopy.credentials.credentials
"""

# pylint: disable=R0902, R0913
# too-many-instance-attributes, too-many-arguments
# The credential set is as long as it wants to be and no longer

from __future__ import annotations

import json
import logging

from datetime import datetime

import boto3

from kshalopy.utils import calculate_expiration


class Credentials:
    """
    Class for storing, accessing, and refreshing credential tokens. Access and ID tokens
    will auto-refresh on use if they are expired or close to expiration
    """

    def __init__(
        self,
        *,
        region: str,
        client_id: str,
        username: str,
        access_token: str,
        id_token: str,
        refresh_token: str,
        token_type: str,
        lifespan: int,
        expiration: float,
    ):
        self.region = region
        self.client_id = client_id
        self.username = username
        self.access_token = access_token
        self.id_token = id_token
        self.refresh_token = refresh_token
        self.token_type = token_type
        self.lifespan = lifespan
        self.expiration = expiration

    def get_fresh_tokens(self) -> None:
        """
        Use the refresh token to get new access and ID tokens
        :return: None
        """
        client = boto3.client("cognito-idp", region_name=self.region)
        response = client.initiate_auth(
            ClientId=self.client_id,
            AuthFlow="REFRESH_TOKEN",
            AuthParameters={
                "CURRENT_USER": self.username,
                "REFRESH_TOKEN": self.refresh_token,
            },
        )
        logging.info(response)
        self.access_token = response["AuthenticationResult"]["AccessToken"]
        self.id_token = response["AuthenticationResult"]["IdToken"]
        self.lifespan = response["AuthenticationResult"]["ExpiresIn"]
        self.expiration = calculate_expiration(response)

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
            json.dump(self.__dict__, outfile, indent=4)

    @classmethod
    def load_credentials(cls, filename: str) -> Credentials:
        """
        Load credentials from a JSON file like that created by the save method above
        :param filename: name and path for file to load
        :return: Credentials object
        """
        with open(filename, encoding="ascii") as infile:
            return Credentials(**json.load(infile))
