"""
kshalopy/rest/rest.py
"""

import json
import urllib.request

from typing import List

from kshalopy.credentials import AppCredentials
from kshalopy.models import Home, User


class RestClient:
    """
    REST Client for Kwikset Halo 'public' API
    """

    def __init__(self, credentials: AppCredentials):
        self.credentials = credentials
        self._request = urllib.request.Request(
            f"https://{self.credentials.app_config.host}"
        )
        self._request.add_header(
            "Authorization", f"{credentials.token_type} {credentials.id_token}"
        )

    def get_my_user(self) -> User:
        """
        :return:
        """
        return self.response_to_objects("/prod_v1/users/me", User)[0]

    def get_my_homes(self) -> List[Home]:
        """
        :return:
        """
        return self.response_to_objects("/prod_v1/users/me/homes", Home)

    def response_to_objects(self, selector, class_type):
        """
        Execute request at specified selector and convert response body into a list of
        provided type
        :param selector:
        :param class_type:
        :return:
        """
        self._request.selector = selector
        with urllib.request.urlopen(self._request) as request:
            response_body = request.read()
            response_dict = json.loads(response_body.decode())
            objects = [class_type(**item) for item in response_dict["data"]]
            return objects
