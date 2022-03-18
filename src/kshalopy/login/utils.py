"""
login/utils.py
"""

import hmac

from src.kshalopy.login.config import CognitoHashAlgo, COGNITO_INFO_BITS
from src.kshalopy.login.factor import Factor


def get_hmac_hash(key_value: Factor, msg_value: Factor) -> bytes:
    """
    Get HMAC hask for given key and message as per Cognito SRP protocol
    :param key_value: key value
    :param msg_value: message value
    :return: first 16 bytes of HMAC hash as per Cognito SRP spec
    """
    prk = hmac.new(key_value.bytes, msg_value.bytes, CognitoHashAlgo).digest()
    hmac_hash = hmac.new(prk, COGNITO_INFO_BITS, CognitoHashAlgo).digest()
    return hmac_hash[:16]


def concat_and_hash(left: str, right: str) -> Factor:
    """
    Create a Factor value by concatentating two hex strings together
    :param left: hexadecimal string value
    :param right: hexadecimal string value
    :return: value
    """
    result = hash_bytes(bytearray.fromhex(left + right))
    return Factor(hex_value=result)


def hash_bytes(data: bytes) -> str:
    """
    Hash a given byte set using the algorithm specified in the config
    :param data: bytes to hash
    :return: hexadecimal digest of the resulting hash value
    """
    return CognitoHashAlgo(data).hexdigest()
