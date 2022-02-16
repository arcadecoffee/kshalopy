"""
Test harness for logins
"""

import logging
import os
import threading
import time

from kshalopy import Config, Credentials
from kshalopy.login import LoginHandler, LoginParameters, VerificationMethods

logging.basicConfig(level=logging.INFO)

CREDENTIALS_FILE = 'credentials.secret.json'

config = Config.load_defaults()


def main():
    if os.path.exists(CREDENTIALS_FILE):
        credentials = Credentials.load_credentials(CREDENTIALS_FILE)
        if credentials.ttl < 300:
            credentials.get_fresh_tokens()
            credentials.save_credentials(CREDENTIALS_FILE)
    else:
        login_params = LoginParameters(
            username=input("Username: "),
            password=input("Password: "),
            verification_method=VerificationMethods.EMAIL,
            device_key="foo42"
        )

        authenticator = LoginHandler(
            login_params=login_params,
            app_config=config
        )
        authenticator.start_login()

        verification_code = input("Verification Code: ")
        authenticator.submit_verification_code(verification_code)

        credentials = authenticator.credentials
        credentials.save_credentials(CREDENTIALS_FILE)


if __name__ == "__main__":
    main()
