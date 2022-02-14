"""
kshalopy.credentials.credentials
"""

# pylint: disable=R0913
# too-many-arguments
# The credential set is as long as it wants to be and no longer

from __future__ import annotations

import json

from datetime import datetime


class Credentials:
    """
    Class for storing, accessing, and refreshing credential tokens. Access and ID tokens
    will auto-refresh on use if they are expired or close to expiration
    """

    def __init__(
        self,
        access_token: str = None,
        id_token: str = None,
        refresh_token: str = None,
        token_type: str = None,
        lifespan: int = None,
        expiration: float = None
    ):
        self._access_token = access_token
        self._id_token = id_token
        self.refresh_token = refresh_token
        self.token_type = token_type
        self.lifespan = lifespan
        self.expiration = expiration

    def get_fresh_tokens(self) -> None:
        """
        Use the refresh token to get new access and ID tokens
        :return: None
        """
        print(f'Expired @ {self.expiration}')

    @property
    def is_fresh(self) -> bool:
        """
        A credential set is 'fresh' if it is less that 90% through its lifespan
        :return: freshness status
        """
        now = datetime.utcnow().timestamp()
        return now < (self.expiration - (self.lifespan * 0.1))

    @property
    def access_token(self) -> str:
        """
        Get a 'good' access token
        :return: access token string
        """
        if not self.is_fresh:
            self.get_fresh_tokens()
        return self._access_token

    @property
    def id_token(self) -> str:
        """
        Get a 'good' ID token
        :return: access token string
        """
        if not self.is_fresh:
            self.get_fresh_tokens()
        return self._id_token

    def save_credentials(self, filename: str) -> None:
        """
        Save current credentials for future use to a JSON file
        :param filename: name and path for save file
        :return: None
        """
        with open(filename, 'w', encoding='ascii') as outfile:
            outfile.write(json.dumps(self.__dict__))

    @classmethod
    def load_credentials(cls, filename: str) -> Credentials:
        """
        Load credentials from a JSON file like that created by the save method above
        :param filename: name and path for file to load
        :return: Credentials object
        """
        credentials = cls()
        with open(filename, encoding="ascii") as infile:
            credentials.__dict__.update(json.loads(infile.read()))
        return credentials
