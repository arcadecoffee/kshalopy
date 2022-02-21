"""
kshalopy/models/models.py
"""

# pylint: disable=R0902,R0903
# too-many-instance-attributes, too-few-public-methods
# The models are as big as they are and no smaller; these are all dataclasses unless
# there is a function or mutation to perform

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Home:
    """
    Data-only class for Homes
    """

    isshared: bool = None
    useraccesslevelstatus: str = None
    createddate: str = None
    createddate_dt: datetime = field(init=False)
    sharedwithname: str = None
    ownername: str = None
    homeid: str = None
    homename: str = None
    useraccesslevel: str = None
    sharedbyname: str = None
    email: str = None

    def __post_init__(self):
        self.createddate_dt = datetime.utcfromtimestamp(int(self.createddate))


class User:
    """
    Data-only class for Users
    """

    def __init__(self, **kwargs):
        self.first_name: str = kwargs.get("firstname")
        self.last_name: str = kwargs.get("lastname")
        self.account_enables: bool = kwargs.get("accountenabled")
        self.email: str = kwargs.get("email")
        self.phone_active: bool = kwargs.get("phoneactive")
        self.phone_number: str = kwargs.get("phonenumber")
        self.brand_name: str = kwargs.get("brandname")
        self.email_notification: bool = kwargs.get("emailnotification")
        self.sms_notification: bool = kwargs.get("smsnotification")
        self.push_notification: bool = kwargs.get("pushnotification")
        self.country_code: str = kwargs.get("countrycode")
