"""
kshalopy/rest/rest.py
"""

import json
import urllib.request

from typing import List

from kshalopy.credentials import AppCredentials
from kshalopy.models import Device, DeviceDetails, Generic, Home, User


class RestClient:
    """
    REST Client for Kwikset Halo 'public' API
    """

    def __init__(
        self, credentials: AppCredentials, source_name: str, source_device: str
    ):
        self.credentials = credentials
        self._source_body = json.dumps({"name": source_name, "device": source_device})

    def _actuate_device(self, device: Device, action: str):
        """

        :param device:
        :param action:
        :return:
        """
        selector = f"/prod_v1/devices/{device.deviceid}/status"
        request = self._build_request(selector)
        request.data = json.dumps(
            {"action": action, "source": self._source_body}
        ).encode()
        request.method = "PATCH"
        with urllib.request.urlopen(request) as request:
            return request.read()

    def _build_request(self, selector):
        """

        :param selector:
        :return:
        """
        request = urllib.request.Request(
            f"https://{self.credentials.app_config.host}{selector}"
        )
        request.add_header(
            "Authorization",
            f"{self.credentials.token_type} {self.credentials.id_token}",
        )
        return request

    def _response_to_objects(self, selector, model):
        """
        Execute request at specified selector and convert response body into a list of
        provided type
        :param selector:
        :param model:
        :return:
        """
        request = self._build_request(selector)

        with urllib.request.urlopen(request) as request:
            response_body = request.read()
            response_dict = json.loads(response_body.decode())
            objects = [model(**item) for item in response_dict["data"]]
            return objects

    def get_devices_in_home(self, home: Home) -> List[Device]:
        """

        :param home:
        :return:
        """
        selector = f"/prod_v1/homes/{home.homeid}/devices"
        return self._response_to_objects(selector, Device)

    def get_device_details(self, device: Device) -> List[DeviceDetails]:
        """

        :param device:
        :return:
        """
        selector = f"/prod_v1/devices/{device.deviceid}"
        return self._response_to_objects(selector, DeviceDetails)[0]

    def get_my_homes(self) -> List[Home]:
        """

        :return:
        """
        selector = "/prod_v1/users/me/homes"
        return self._response_to_objects(selector, Home)

    def get_my_user(self) -> User:
        """

        :return:
        """
        selector = "/prod_v1/users/me"
        return self._response_to_objects(selector, User)[0]

    def get_users_in_home(self, home: Home) -> List[Generic]:
        """

        :param home:
        :return:
        """
        selector = f"/prod_v1/homes/{home.homeid}/sharedusers"
        return self._response_to_objects(selector, Generic)

    def lock_device(self, device: Device):
        """

        :param device:
        :return:
        """
        return self._actuate_device(device, "Lock")

    def unlock_device(self, device: Device):
        """

        :param device:
        :return:
        """
        return self._actuate_device(device, "Unlock")
