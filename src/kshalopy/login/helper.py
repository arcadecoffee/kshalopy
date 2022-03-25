"""
login/helper.py
"""

# pylint: disable=C0103, R0902
# invalid-name, too-many-instance-attributes
# This is a very complicated algorithm.
# A lotta ins, a lotta outs, a lotta what-have-yous.

from __future__ import annotations

import hmac

from base64 import b64decode, b64encode
from datetime import datetime
from os import urandom
from sys import byteorder
from typing import Tuple, Dict

from ..login.config import CognitoHashAlgo, COGNITO_AUTH_G, COGNITO_AUTH_N
from ..login.factor import Factor
from ..login.utils import concat_and_hash, get_hmac_hash, hash_bytes


class LoginHelper:
    """
    Helper class for performing the Authentication Dance with the Kwikset Cognito pool's
    SRP implementation
    """

    @staticmethod
    def generate_random(size: int) -> Factor:
        """
        Generate random bytes of specified size
        
        :param size: length of random value in bytes
        :return: random value as a Factor
        """
        return Factor(int_value=int.from_bytes(urandom(size), byteorder))

    @staticmethod
    def get_secret_hash(username: str, client_id: str, client_secret: str) -> str:
        """
        Calculate secret hash as required by Cognito SRP
        
        :param username: username
        :param client id: client id
        :param client_secret: client secret
        :return: hash string
        """
        message = (username + client_id).encode()
        hmac_obj = hmac.new(client_secret.encode(), message, CognitoHashAlgo)
        return b64encode(hmac_obj.digest()).decode()

    def __init__(self, login_params, app_config):
        self.login_params = login_params
        self.app_config = app_config
        self.N = Factor(hex_value=COGNITO_AUTH_N)
        self.g = Factor(hex_value=COGNITO_AUTH_G)
        self.k = concat_and_hash(self.N.padded_hex, self.g.padded_hex)
        self.a, self.A = self._calculate_a_values()

        self.auth_parameters = {
            "CHALLENGE_NAME": "SRP_A",
            "DEVICE_KEY": self.login_params.device_key,
            "USERNAME": self.login_params.username,
            "SRP_A": self.A.hex,
        }
        if self.app_config.client_secret:
            self.auth_parameters["SECRET_HASH"] = self.get_secret_hash(
                self.login_params.username,
                self.app_config.client_id,
                self.app_config.client_secret,
            )

    def _calculate_a_values(self) -> Tuple[Factor, Factor]:
        """
        Calculate 'a' values for Cognito SRP protocol
        
        :return: (small 'a', big 'a')
        """
        A = a = 0
        while A % self.N.int == 0:
            a = self.generate_random(128)
            A = pow(self.g.int, a.int, self.N.int)
        return a, Factor(int_value=A)

    def _get_password_authentication_key(
        self, user_id: str, password: str, srp_b: Factor, salt: Factor
    ) -> bytes:
        u = concat_and_hash(self.A.padded_hex, srp_b.padded_hex)
        id_hash = hash_bytes(
            f"{self.app_config.user_pool_id}{user_id}:{password}".encode()
        )
        x = concat_and_hash(salt.padded_hex, id_hash)
        base = srp_b.int - self.k.int * pow(self.g.int, x.int, self.N.int)
        exponent = (self.a + u * x).int
        s = Factor(int_value=pow(base, exponent, self.N.int))
        return get_hmac_hash(key_value=u, msg_value=s)

    def process_challenge(self, challenge_parameters) -> Dict[str, str]:
        """
        Produces the correct response to the challenge received from the server during
        the authentication / login process.
        
        :param challenge_parameters: from the authentication server
        :return: response to challenge
        """
        internal_username = challenge_parameters["USERNAME"]
        user_id_for_srp = challenge_parameters["USER_ID_FOR_SRP"]
        salt = Factor(hex_value=challenge_parameters["SALT"])
        srp_b = Factor(hex_value=challenge_parameters["SRP_B"])
        secret_block = challenge_parameters["SECRET_BLOCK"]
        timestamp = datetime.utcnow().strftime("%a %b %-d %H:%M:%S UTC %Y")

        hkdf = self._get_password_authentication_key(
            user_id_for_srp, self.login_params.password, srp_b, salt
        )
        msg = (
            self.app_config.user_pool_id.encode()
            + user_id_for_srp.encode()
            + b64decode(secret_block)
            + timestamp.encode()
        )
        hmac_obj = hmac.new(hkdf, msg, CognitoHashAlgo)
        signature_string = b64encode(hmac_obj.digest()).decode()

        response = {
            "TIMESTAMP": timestamp,
            "USERNAME": internal_username,
            "PASSWORD_CLAIM_SECRET_BLOCK": secret_block,
            "PASSWORD_CLAIM_SIGNATURE": signature_string,
        }
        if self.app_config.client_secret:
            response["SECRET_HASH"] = self.get_secret_hash(
                internal_username,
                self.app_config.client_id,
                self.app_config.client_secret,
            )
        return response
