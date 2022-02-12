from __future__ import annotations

import hmac

from base64 import b64decode, b64encode
from datetime import datetime
from os import urandom
from sys import byteorder
from typing import Tuple, Dict

from .config import COGNITO_HASH_ALGO, COGNITO_AUTH_g, COGNITO_AUTH_N
from .factor import Factor
from .utils import concat_and_hash, compute_hkdf, hash_hex


class LoginHelper:
    @staticmethod
    def generate_random_small_a() -> Factor:
        return Factor(int_value=int.from_bytes(urandom(128), byteorder))

    @staticmethod
    def get_secret_hash(username: str, client_id: str, client_secret: str) -> str:
        message = (username + client_id).encode()
        hmac_obj = hmac.new(client_secret.encode(), message, COGNITO_HASH_ALGO)
        return b64encode(hmac_obj.digest()).decode()

    def __init__(
        self,
        username,
        password,
        pool_id,
        client_id,
        device_key,
        client_secret=None,
    ):
        self._username = username
        self._password = password
        self._pool_id = pool_id
        self._client_id = client_id
        self._device_key = device_key
        self._client_secret = client_secret
        self._N = Factor(hex_value=COGNITO_AUTH_N)
        self._g = Factor(hex_value=COGNITO_AUTH_g)
        self._k = concat_and_hash(self._N.padded_hex, self._g.padded_hex)
        self._small_a, self._large_a = self._calculate_a_values()

        self._auth_parameters = {
            "CHALLENGE_NAME": "SRP_A",
            "DEVICE_KEY": self._device_key,
            "USERNAME": self._username,
            "SRP_A": self._large_a.hex,
        }
        if self._client_secret:
            self._auth_parameters["SECRET_HASH"] = self.get_secret_hash(
                self._username, self._client_id, self._client_secret
            )

    @property
    def auth_parameters(self) -> Dict[str, str]:
        return self._auth_parameters.copy()

    def _calculate_a_values(self) -> Tuple[Factor, Factor]:
        large_a = small_a = 0
        while large_a % self._N.int == 0:
            small_a = self.generate_random_small_a()
            large_a = pow(self._g.int, small_a.int, self._N.int)
        return small_a, Factor(int_value=large_a)

    def _get_password_authentication_key(
        self, user_id: str, password: str, srp_b: Factor, salt: Factor
    ) -> bytes:
        u = concat_and_hash(self._large_a.padded_hex, srp_b.padded_hex)
        id_hash = hash_hex(f"{self._pool_id}{user_id}:{password}".encode())
        x = concat_and_hash(salt.padded_hex, id_hash)
        base = srp_b.int - self._k.int * pow(self._g.int, x.int, self._N.int)
        exponent = (self._small_a + u * x).int
        s = pow(base, exponent, self._N.int)
        hkdf = compute_hkdf(u, Factor(int_value=s))
        return hkdf

    def process_challenge(self, challenge_parameters) -> Dict[str, str]:
        internal_username = challenge_parameters["USERNAME"]
        user_id_for_srp = challenge_parameters["USER_ID_FOR_SRP"]
        salt = Factor(hex_value=challenge_parameters["SALT"])
        srp_b = Factor(hex_value=challenge_parameters["SRP_B"])
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
        if self._client_secret:
            response["SECRET_HASH"] = self.get_secret_hash(
                internal_username, self._client_id, self._client_secret
            )
        return response
