"""
Test harness for logins
"""

import logging
import os
import signal
import threading

from datetime import datetime

from kshalopy import Config, Credentials
from kshalopy.login import LoginHandler, LoginParameters, VerificationMethods

logging.basicConfig(level=logging.INFO)

CREDENTIALS_FILE = 'credentials.secret.json'

config = Config.load_defaults()


def refresh_credentials(credentials: Credentials, exit_event, offset: int = 600):
    while True:
        if credentials.ttl < offset:
            logging.info("Getting fresh credentials")
            credentials.get_fresh_tokens()
            credentials.save_credentials(CREDENTIALS_FILE)
            logging.info("Got fresh credentials")
        if exit_event.wait(timeout=(credentials.ttl - offset)):
            break
    logging.info("Exiting")


def main():
    if os.path.exists(CREDENTIALS_FILE):
        credentials = Credentials.load_credentials(CREDENTIALS_FILE)
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

    exit_event = threading.Event()

    signal.signal(signal.SIGINT, lambda a, b: exit_event.set())

    worker = threading.Thread(
        target=refresh_credentials, args=[credentials, exit_event]
    )
    worker.start()

    while (not worker.join(1)) and worker.is_alive():
        print(
            f"\r{round(credentials.ttl)} : "
            f"{datetime.fromtimestamp(credentials.expiration).isoformat()}",
            end=""
        )


if __name__ == "__main__":
    main()
