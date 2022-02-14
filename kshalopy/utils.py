"""
kshalopy.utils
"""

from datetime import datetime
from typing import Dict


def date_string_to_timestamp(dt_string: str) -> float:
    """
    Convert timestamp string from Cognito client to timestamp value
    :param dt_string: date string
    :return: timestamp value
    """
    return datetime.strptime(dt_string, '%a, %d %b %Y %H:%M:%S %Z').timestamp()


def calculate_expiration(response: Dict[str, Dict]) -> float:
    """
    Calculate timestamp of expiration from a Response body
    :param response: response body
    :return: float timestamp of expiration
    """
    expiration = (
            date_string_to_timestamp(
                response["ResponseMetadata"]["HTTPHeaders"]["date"]
            )
            + response["AuthenticationResult"]["ExpiresIn"]
    )
    return expiration
