"""
rest/rest.py
"""

import json
import urllib.request

from enum import Enum
from typing import Any, List

from src.kshalopy.models.models import Device, DeviceDetails, Home, SharedUser, User
from src.kshalopy.credentials.credentials import AppCredentials
from src.kshalopy.config import Config


class DeviceAction(Enum):
    """
    Enumeration of available device actions
    """

    LOCK = "Lock"
    UNLOCK = "Unlock"


class RestClient:
    """
    REST Client for Kwikset Halo 'public' API
    """

    def __init__(
        self,
        config: Config,
        credentials: AppCredentials,
        source_name: str,
        source_device: str,
    ):
        self.config = config
        self.credentials = credentials
        self._source_body = json.dumps({"name": source_name, "device": source_device})

    def _actuate_device(self, device: Device, action: DeviceAction) -> str:
        """
        Internal method for lock/unlock calls with required data objects
        :param device: device object to interact with
        :param action: action to take on the device
        :return: response body
        """
        selector = f"/prod_v1/devices/{device.deviceid}/status"
        request = self._build_request(selector)
        request.data = json.dumps(
            {"action": action.value, "source": self._source_body}
        ).encode()
        request.method = "PATCH"
        with urllib.request.urlopen(request) as request:
            return request.read().decode()

    def _build_request(self, selector: str) -> urllib.request.Request:
        """
        Construct a urllib request with required headers, etc.
        :param selector: path / endpoint for the request
        :return: Request object
        """
        request = urllib.request.Request(f"https://{self.config.host}{selector}")
        request.add_header(
            "Authorization",
            f"{self.credentials.token_type} {self.credentials.id_token}",
        )
        return request

    def _response_to_objects(self, selector: str, model: Any) -> Any:
        """
        Execute request at specified selector and convert response body into a list of
        provided type
        :param selector: API route to call
        :param model: Class type to convert for response
        :return: Object of type model
        """
        with urllib.request.urlopen(self._build_request(selector)) as request:
            response_body = request.read()
            response_dict = json.loads(response_body.decode())
            objects = [model(**item) for item in response_dict["data"]]
            return objects

    def get_devices_in_home(self, home: Home) -> List[Device]:
        """
        Get list of devices in a given Home
        :param home: Home to query
        :return: List of Devices
        """
        selector = f"/prod_v1/homes/{home.homeid}/devices"
        return self._response_to_objects(selector, Device)

    def get_device_details(self, device: Device) -> DeviceDetails:
        """
        Get details of a specific device
        :param device: Device to query
        :return: Device details
        """
        selector = f"/prod_v1/devices/{device.deviceid}"
        return self._response_to_objects(selector, DeviceDetails)[0]

    def get_my_homes(self) -> List[Home]:
        """
        Get list of Homes to which the current user is "attached"
        :return: List of Homes
        """
        selector = "/prod_v1/users/me/homes"
        return self._response_to_objects(selector, Home)

    def get_my_user(self) -> User:
        """
        Get information about the current user
        :return: User details
        """
        selector = "/prod_v1/users/me"
        return self._response_to_objects(selector, User)[0]

    def get_shared_users_in_home(self, home: Home) -> List[SharedUser]:
        """
        Get users with shared access to the specified home, assuming the current user
        is the "owner".
        :param home: Home to query
        :return: List of users with shared access
        """
        selector = f"/prod_v1/homes/{home.homeid}/sharedusers"
        return self._response_to_objects(selector, SharedUser)

    def lock_device(self, device: Device) -> str:
        """
        Set a device's state to "locked"
        :param device: Device to lock
        :return: Response body as a string (contains a count of affected devices)
        """
        return self._actuate_device(device, DeviceAction.LOCK)

    def unlock_device(self, device: Device) -> str:
        """
        Set a device's state to "unlocked"
        :param device: Device to lock
        :return: Response body as a string (contains a count of affected devices)
        """
        return self._actuate_device(device, DeviceAction.UNLOCK)
