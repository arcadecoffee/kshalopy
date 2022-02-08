import base64
import datetime
import hashlib
import hmac
import os

from .constants import COGNITO_g_HEX, COGNITO_N_HEX, INFO_BITS


class ForceChangePasswordException(Exception):
    """Raised when the user is forced to change their password"""


def hash_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hex_hash(hex_string: str) -> str:
    return hash_sha256(bytearray.fromhex(hex_string))


def hex_to_int(hex_string: str) -> int:
    return int(hex_string, 16)


def int_to_hex(num: int) -> str:
    return "%x" % num


def pad_hex(value: str) -> str:
    if len(value) % 2 == 1:
        value = "0" + value
    elif hex_to_int(value[0]) >= 8:
        value = "00" + value
    return value


def compute_hkdf(ikm: bytes, salt: bytes) -> bytes:
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    hmac_hash = hmac.new(prk, INFO_BITS, hashlib.sha256).digest()
    return hmac_hash[:16]


def calculate_u(big_a: str, big_b: str) -> int:
    u_hex_hash = hex_hash(pad_hex(big_a) + pad_hex(big_b))
    return hex_to_int(u_hex_hash)


class AWSSRP:
    NEW_PASSWORD_REQUIRED_CHALLENGE = "NEW_PASSWORD_REQUIRED"
    PASSWORD_VERIFIER_CHALLENGE = "PASSWORD_VERIFIER"

    def __init__(
        self,
        username,
        password,
        user_pool_id,
        client_id,
        client_secret=None,
    ):
        self.username = username
        self.password = password
        self.pool_id = user_pool_id.split("_")[1]
        self.client_id = client_id
        self.client_secret = client_secret
        self.big_n = hex_to_int(COGNITO_N_HEX)
        self.val_g = hex_to_int(COGNITO_g_HEX)
        self.val_k = hex_to_int(
            hex_hash(pad_hex(COGNITO_N_HEX) + pad_hex(COGNITO_g_HEX))
        )
        self.small_a_value, self.large_a_value = self.calculate_a_values()

    @staticmethod
    def generate_random_small_a():
        return int.from_bytes(os.urandom(128), "big")

    def calculate_a_values(self):
        big_a = small_a = 0
        while big_a % self.big_n == 0:
            small_a = self.generate_random_small_a()
            big_a = pow(self.val_g, small_a, self.big_n)
        return small_a, int_to_hex(big_a)

    def get_password_authentication_key(self, username, password, server_b_value, salt):
        """
        Calculates the final hkdf based on computed S value, and computed U value and the key
        :param {String} username Username.
        :param {String} password Password.
        :param {Long integer} server_b_value Server B value.
        :param {Long integer} salt Generated salt.
        :return {Buffer} Computed HKDF value.
        """
        u_value = calculate_u(self.large_a_value, server_b_value)
        if u_value == 0:
            raise ValueError("U cannot be zero.")
        username_password = "%s%s:%s" % (self.pool_id, username, password)
        username_password_hash = hash_sha256(username_password.encode("utf-8"))

        x_value = hex_to_int(hex_hash(pad_hex(salt) + username_password_hash))
        g_mod_pow_xn = pow(self.val_g, x_value, self.big_n)
        int_value = hex_to_int(server_b_value) - self.val_k * g_mod_pow_xn
        s_value = pow(int_value, self.small_a_value + u_value * x_value, self.big_n)
        hkdf = compute_hkdf(
            bytearray.fromhex(pad_hex(int_to_hex(s_value))),
            bytearray.fromhex(pad_hex(int_to_hex(u_value))),
        )
        return hkdf

    def get_auth_params(self):
        auth_params = {
            "USERNAME": self.username,
            "SRP_A": self.large_a_value,
        }
        if self.client_secret is not None:
            auth_params.update(
                {
                    "SECRET_HASH": self.get_secret_hash(
                        self.username, self.client_id, self.client_secret
                    )
                }
            )
        return auth_params

    @staticmethod
    def get_secret_hash(username, client_id, client_secret):
        message = bytearray(username + client_id, "utf-8")
        hmac_obj = hmac.new(bytearray(client_secret, "utf-8"), message, hashlib.sha256)
        return base64.standard_b64encode(hmac_obj.digest()).decode("utf-8")

    def process_challenge(self, challenge_parameters):
        internal_username = challenge_parameters["USERNAME"]
        user_id_for_srp = challenge_parameters["USER_ID_FOR_SRP"]
        salt_hex = challenge_parameters["SALT"]
        srp_b_hex = challenge_parameters["SRP_B"]
        secret_block_b64 = challenge_parameters["SECRET_BLOCK"]

        timestamp = datetime.datetime.utcnow().strftime("%a %b %-d %H:%M:%S UTC %Y")

        hkdf = self.get_password_authentication_key(
            user_id_for_srp, self.password, srp_b_hex, salt_hex
        )

        msg = (
            self.pool_id.encode()
            + user_id_for_srp.encode()
            + base64.b64decode(secret_block_b64)
            + timestamp.encode()
        )

        hmac_obj = hmac.new(hkdf, msg, digestmod=hashlib.sha256)
        signature_string = base64.standard_b64encode(hmac_obj.digest())
        response = {
            "TIMESTAMP": timestamp,
            "USERNAME": internal_username,
            "PASSWORD_CLAIM_SECRET_BLOCK": secret_block_b64,
            "PASSWORD_CLAIM_SIGNATURE": signature_string.decode("utf-8"),
        }
        if self.client_secret is not None:
            response.update(
                {
                    "SECRET_HASH": self.get_secret_hash(
                        internal_username, self.client_id, self.client_secret
                    )
                }
            )
        return response
