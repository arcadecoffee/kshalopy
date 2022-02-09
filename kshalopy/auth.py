from __future__ import annotations

import hmac

from base64 import b64decode, b64encode
from datetime import datetime
from os import urandom
from sys import byteorder
from typing import Tuple, Dict

from .config import (
    COGNITO_HASH_ALGO,
    COGNITO_AUTH_g,
    COGNITO_AUTH_N,
    COGNITO_INFO_BITS,
)


class SRPFactor:
    def __init__(self, int_value: int = 0, hex_value: str = "0") -> None:
        if int_value:
            self.int = int_value
            self.hex = "%x" % self.int
        else:
            self.hex = hex_value
            self.int = int(self.hex, 16)
        self.padded_hex = self.pad_hex(self.hex)
        self.bytes = bytes.fromhex(self.padded_hex)

    def __add__(self, other: SRPFactor) -> SRPFactor:
        return SRPFactor(int_value=self.int + other.int)

    def __sub__(self, other: SRPFactor) -> SRPFactor:
        return SRPFactor(int_value=self.int - other.int)

    def __mul__(self, other: SRPFactor) -> SRPFactor:
        return SRPFactor(int_value=self.int * other.int)

    def __repr__(self) -> int:
        return self.int

    @staticmethod
    def concat_and_hash(a: str, b: str) -> SRPFactor:
        r = hash_hex(bytearray.fromhex(a + b))
        return SRPFactor(hex_value=r)

    @staticmethod
    def pad_hex(value: str) -> str:
        if len(value) % 2 == 1:
            value = "0" + value
        elif int(value[0], 16) >= 8:
            value = "00" + value
        return value


def hash_hex(data: bytes) -> str:
    return COGNITO_HASH_ALGO(data).hexdigest()


def compute_hkdf(key_value: SRPFactor, msg_value: SRPFactor) -> bytes:
    prk = hmac.new(key_value.bytes, msg_value.bytes, COGNITO_HASH_ALGO).digest()
    hmac_hash = hmac.new(prk, COGNITO_INFO_BITS, COGNITO_HASH_ALGO).digest()
    return hmac_hash[:16]


class SRPHelper:
    PASSWORD_VERIFIER_CHALLENGE = "PASSWORD_VERIFIER"

    @staticmethod
    def generate_random_small_a() -> SRPFactor:
        return SRPFactor(int_value=int.from_bytes(urandom(128), byteorder))

    @staticmethod
    def get_secret_hash(username: str, client_id: str, client_secret: str) -> str:
        message = (username + client_id).encode()
        hmac_obj = hmac.new(client_secret.encode(), message, COGNITO_HASH_ALGO)
        return b64encode(hmac_obj.digest()).decode()

    def __init__(
        self,
        username,
        password,
        user_pool_id,
        client_id,
        device_key,
        client_secret=None,
    ):
        self._username = username
        self._password = password
        self._pool_id = user_pool_id.split("_")[1]
        self._client_id = client_id
        self._device_key = device_key
        self._client_secret = client_secret
        self._N = SRPFactor(hex_value=COGNITO_AUTH_N)
        self._g = SRPFactor(hex_value=COGNITO_AUTH_g)
        self._k = SRPFactor.concat_and_hash(self._N.padded_hex, self._g.padded_hex)
        self._small_a, self._large_a = self._calculate_a_values()

        self._auth_parameters = {
            "CHALLENGE_NAME": "SRP_A",
            "DEVICE_KEY": self._device_key,
            "USERNAME": self._username,
            "SRP_A": self._large_a.hex,
        }
        if self._client_secret is not None:
            self._auth_parameters["SECRET_HASH"] = self.get_secret_hash(
                self._username, self._client_id, self._client_secret
            )

    @property
    def auth_parameters(self) -> Dict[str, str]:
        return self._auth_parameters.copy()

    def _calculate_a_values(self) -> Tuple[SRPFactor, SRPFactor]:
        large_a = small_a = 0
        while large_a % self._N.int == 0:
            small_a = self.generate_random_small_a()
            large_a = pow(self._g.int, small_a.int, self._N.int)
        return small_a, SRPFactor(int_value=large_a)

    def _get_password_authentication_key(
        self, user_id: str, password: str, srp_b: SRPFactor, salt: SRPFactor
    ) -> bytes:
        u = SRPFactor.concat_and_hash(self._large_a.padded_hex, srp_b.padded_hex)
        id_hash = hash_hex(f"{self._pool_id}{user_id}:{password}".encode())
        x = SRPFactor.concat_and_hash(salt.padded_hex, id_hash)
        base = srp_b.int - self._k.int * pow(self._g.int, x.int, self._N.int)
        exponent = (self._small_a + u * x).int
        s = pow(base, exponent, self._N.int)
        hkdf = compute_hkdf(u, SRPFactor(int_value=s))
        return hkdf

    def process_challenge(self, challenge_parameters) -> Dict[str, str]:
        internal_username = challenge_parameters["USERNAME"]
        user_id_for_srp = challenge_parameters["USER_ID_FOR_SRP"]
        salt = SRPFactor(hex_value=challenge_parameters["SALT"])
        srp_b = SRPFactor(hex_value=challenge_parameters["SRP_B"])
        secret_block = challenge_parameters["SECRET_BLOCK"]
        timestamp = datetime.utcnow().strftime("%a %b %-d %H:%M:%S UTC %Y")

        hkdf = self._get_password_authentication_key(
            user_id_for_srp, self._password, srp_b, salt
        )
        msg = (
            self._pool_id.encode()
            + user_id_for_srp.encode()
            + b64decode(secret_block)
            + timestamp.encode()
        )
        hmac_obj = hmac.new(hkdf, msg, COGNITO_HASH_ALGO)
        signature_string = b64encode(hmac_obj.digest()).decode()

        response = {
            "TIMESTAMP": timestamp,
            "USERNAME": internal_username,
            "PASSWORD_CLAIM_SECRET_BLOCK": secret_block,
            "PASSWORD_CLAIM_SIGNATURE": signature_string,
        }
        if self._client_secret is not None:
            response["SECRET_HASH"] = self.get_secret_hash(
                internal_username, self._client_id, self._client_secret
            )
        return response
