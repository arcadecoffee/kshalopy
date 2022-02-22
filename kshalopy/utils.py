"""
kshalopy.utils
"""

from typing import Dict

from dateutil import parser


def date_string_to_timestamp(dt_string: str) -> float:
    """
    Convert timestamp string from Cognito client to timestamp value.
    Expected format: Tue, 22 Feb 2022 18:59:01 GMT
    :param dt_string: date string
    :return: timestamp value
    """
    return parser.parse(dt_string).timestamp()


def calculate_expiration(response: Dict[str, Dict]) -> float:
    """
    Calculate timestamp of expiration from a Response body
    :param response: response body
    :return: float timestamp of expiration
    """
    expiration = (
        date_string_to_timestamp(response["ResponseMetadata"]["HTTPHeaders"]["date"])
        + response["AuthenticationResult"]["ExpiresIn"]
    )
    return expiration
