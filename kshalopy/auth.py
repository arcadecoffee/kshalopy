import base64
import datetime
import hashlib
import hmac
import os
from typing import Tuple

from .constants import COGNITO_g_HEX, COGNITO_N_HEX, INFO_BITS


class ForceChangePasswordException(Exception):
    """Raised when the user is forced to change their password"""


class SRPFactor:
    def __init__(self, int_value: int = None, hex_value: str = None):
        self.int = 0
        self.hex = "0"
        if int_value:
            self.int = int_value
            self.hex = "%x" % self.int
        elif hex_value:
            self.hex = hex_value
            self.int = int(self.hex, 16)
        self.padded_hex = self.pad_hex(self.hex)

    @staticmethod
    def pad_hex(value: str) -> str:
        if len(value) % 2 == 1:
            value = "0" + value
        elif int(value[0], 16) >= 8:
            value = "00" + value
        return value


def hash_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hex_hash(hex_string: str) -> str:
    return hash_sha256(bytearray.fromhex(hex_string))


def int_to_bytes(value: SRPFactor) -> bytes:
    return bytes.fromhex(value.padded_hex)


def compute_hkdf(key_value: SRPFactor, msg_value: SRPFactor) -> bytes:
    prk = hmac.new(
        int_to_bytes(key_value), int_to_bytes(msg_value), hashlib.sha256
    ).digest()
    hmac_hash = hmac.new(prk, INFO_BITS, hashlib.sha256).digest()
    return hmac_hash[:16]


def calculate_u(big_a: SRPFactor, big_b: SRPFactor) -> SRPFactor:
    u_hex_hash = hex_hash(big_a.padded_hex + big_b.padded_hex)
    return SRPFactor(hex_value=u_hex_hash)


class AWSSRP:
    NEW_PASSWORD_REQUIRED_CHALLENGE = "NEW_PASSWORD_REQUIRED"
    PASSWORD_VERIFIER_CHALLENGE = "PASSWORD_VERIFIER"

    def __init__(
        self,
        username,
        password,
        user_pool_id,
        client_id,
        device_key,
        client_secret=None,
    ):
        self.username = username
        self.password = password
        self.pool_id = user_pool_id.split("_")[1]
        self.client_id = client_id
        self.device_key = device_key
        self.client_secret = client_secret
        self.big_n = SRPFactor(hex_value=COGNITO_N_HEX)
        self.val_g = SRPFactor(hex_value=COGNITO_g_HEX)
        self.val_k = SRPFactor(
            hex_value=hex_hash(self.big_n.padded_hex + self.val_g.padded_hex)
        )
        self.small_a_value, self.large_a_value = self.calculate_a_values()

    @staticmethod
    def generate_random_small_a() -> SRPFactor:
        return SRPFactor(int_value=int.from_bytes(os.urandom(128), "big"))

    def calculate_a_values(self) -> Tuple[SRPFactor, SRPFactor]:
        big_a = small_a = 0
        while big_a % self.big_n.int == 0:
            small_a = self.generate_random_small_a()
            big_a = pow(self.val_g.int, small_a.int, self.big_n.int)
        return small_a, SRPFactor(int_value=big_a)

    def get_password_authentication_key(
        self, user_id: str, password: str, srp_b: SRPFactor, salt: SRPFactor
    ) -> bytes:
        u_value = calculate_u(self.large_a_value, srp_b)
        username_password_hash = hash_sha256(
            f"{self.pool_id}{user_id}:{password}".encode()
        )
        x_value = SRPFactor(
            hex_value=hex_hash(salt.padded_hex + username_password_hash)
        )
        g_mod_pow_xn = pow(self.val_g.int, x_value.int, self.big_n.int)
        base = srp_b.int - self.val_k.int * g_mod_pow_xn
        s_value = SRPFactor(
            int_value=pow(
                base, self.small_a_value.int + u_value.int * x_value.int, self.big_n.int
            )
        )
        hkdf = compute_hkdf(u_value, s_value)
        return hkdf

    def get_auth_params(self) -> dict:
        auth_params = {
            "CHALLENGE_NAME": "SRP_A",
            "DEVICE_KEY": self.device_key,
            "USERNAME": self.username,
            "SRP_A": self.large_a_value.hex,
        }
        if self.client_secret is not None:
            auth_params["SECRET_HASH"] = self.get_secret_hash(
                self.username, self.client_id, self.client_secret
            )
        return auth_params

    @staticmethod
    def get_secret_hash(username: str, client_id: str, client_secret: str) -> str:
        message = (username + client_id).encode()
        hmac_obj = hmac.new(client_secret.encode(), message, hashlib.sha256)
        return base64.b64encode(hmac_obj.digest()).decode()

    def process_challenge(self, challenge_parameters):
        internal_username = challenge_parameters["USERNAME"]
        user_id_for_srp = challenge_parameters["USER_ID_FOR_SRP"]
        salt = SRPFactor(hex_value=challenge_parameters["SALT"])
        srp_b = SRPFactor(hex_value=challenge_parameters["SRP_B"])
        secret_block = challenge_parameters["SECRET_BLOCK"]
        timestamp = datetime.datetime.utcnow().strftime("%a %b %-d %H:%M:%S UTC %Y")

        hkdf = self.get_password_authentication_key(
            user_id_for_srp, self.password, srp_b, salt
        )
        msg = (
            self.pool_id.encode()
            + user_id_for_srp.encode()
            + base64.b64decode(secret_block)
            + timestamp.encode()
        )
        hmac_obj = hmac.new(hkdf, msg, hashlib.sha256)
        signature_string = base64.b64encode(hmac_obj.digest()).decode()

        response = {
            "TIMESTAMP": timestamp,
            "USERNAME": internal_username,
            "PASSWORD_CLAIM_SECRET_BLOCK": secret_block,
            "PASSWORD_CLAIM_SIGNATURE": signature_string,
        }
        if self.client_secret is not None:
            response["SECRET_HASH"] = self.get_secret_hash(
                internal_username, self.client_id, self.client_secret
            )

        return response
