"""
kshalopy/models/models.py
"""

# pylint: disable=R0902,R0903
# too-many-instance-attributes, too-few-public-methods
# The models are as big as they are and no smaller; these are all dataclasses unless
# there is a function or mutation to perform

from dataclasses import dataclass
from typing import Union


class Generic:
    """
    Generic data class
    """

    def __init__(self, **kwargs):
        self.data = kwargs


@dataclass
class Device:
    """
    Data-only class for Devices
    """

    deviceid: str
    devicename: str = None
    activationstate: bool = None
    firmwareversion: str = None
    lockstatus: str = None
    batterypercentage: int = None
    modelnumber: str = None
    lastupdatestatus: int = None
    batterystatus: str = None
    devicetimezone: str = None
    firmwareupdateavailable: bool = None
    forcefirmwareupdate: bool = None
    bleadvertisement: str = None
    activationdate: int = None
    owneremail: str = None
    clearedeventhistorytimestamp: int = None


@dataclass
class DeviceDetails:
    """
    Data-only class for Device Details
    """
    audiostatus: str = None
    ledstatus: str = None
    securescreenstatus: str = None
    autolockstate: str = None
    autolockdelay: int = None
    lastupdatestatus: int = None
    batterystatus: str = None
    batterypercentage: int = None
    doorstatus: str = None
    locktamperstate: str = None
    securemodeenabled: str = None
    securemodeactive: str = None
    alexasetup: bool = None
    alexahomelockstatus: str = None
    googlehomesetup: bool = None
    googleunlockpinsetup: bool = None
    googlehomelockstatus: str = None
    clearedeventhistorytimestamp: int = None
    bleadvertisement: str = None
    modelnumber: str = None
    productfamily: str = None
    sku: str = None
    serialnumber: str = None
    firmwarebundleversion: str = None
    firmwareupdateavailable: bool = None
    forcefirmwareupdate: bool = None
    devicetimezone: str = None
    hardwarevariant: str = None


@dataclass
class Home:
    """
    Data-only class for Homes
    """

    homeid: str
    isshared: bool = None
    useraccesslevelstatus: str = None
    createddate: Union[str, int] = None
    sharedwithname: str = None
    ownername: str = None
    homename: str = None
    useraccesslevel: str = None
    sharedbyname: str = None
    email: str = None

    def __post_init__(self):
        if isinstance(self.createddate, str):
            self.createddate = int(self.createddate)


@dataclass
class User:
    """
    Data-only class for Users
    """

    email: str
    operationtype: str = None
    firstname: str = None
    lastname: str = None
    phonenumber: str = None
    accountenabled: bool = None
    phoneactive: bool = None
    brandname: str = None
    emailnotification: bool = None
    smsnotification: bool = None
    pushnotification: bool = None
    countrycode: str = None
