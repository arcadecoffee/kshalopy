"""
kshalopy/rest/rest.py
"""

import json
import urllib.request


from kshalopy.credentials import AppCredentials


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

    def get_homes(self):
        """
        :return:
        """
        self._request.selector = "/prod_v1/users/me/homes"
        response_body = urllib.request.urlopen(self._request).read()
        return json.loads(response_body.decode())
