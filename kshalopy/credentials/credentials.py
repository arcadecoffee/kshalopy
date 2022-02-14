"""
kshalopy.credentials.credentials
"""

from datetime import datetime


class Credentials:
    """
    Class for storing, accessing, and refreshing credential tokens. Access and ID tokens
    will auto-refresh on use if they are expired or close to expiration
    """

    def __init__(
        self,
        *,
        access_token: str,
        id_token: str,
        refresh_token: str,
        token_type: str,
        lifespan: int,
        expiration: float
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
        self.expiration = datetime.utcnow().timestamp()

    @property
    def is_fresh(self) -> bool:
        """
        A credential set is 'fresh' if it is less that 90% through its lifespan
        :return: freshness status
        """
        now = datetime.utcnow().timestamp()
        return now > (self.expiration - (self.lifespan * 0.1))

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
