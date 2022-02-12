import hmac

from datetime import datetime

from .config import COGNITO_HASH_ALGO, COGNITO_INFO_BITS, DATETIME_FORMAT
from .factor import Factor


def compute_hkdf(key_value: Factor, msg_value: Factor) -> bytes:
    prk = hmac.new(key_value.bytes, msg_value.bytes, COGNITO_HASH_ALGO).digest()
    hmac_hash = hmac.new(prk, COGNITO_INFO_BITS, COGNITO_HASH_ALGO).digest()
    return hmac_hash[:16]


def concat_and_hash(a: str, b: str) -> Factor:
    r = hash_hex(bytearray.fromhex(a + b))
    return Factor(hex_value=r)


def hash_hex(data: bytes) -> str:
    return COGNITO_HASH_ALGO(data).hexdigest()


def date_string_to_timestamp(dt: str) -> float:
    return datetime.strptime(dt, '%a, %d %b %Y %H:%M:%S %Z').timestamp()
