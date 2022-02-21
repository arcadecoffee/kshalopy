"""
Test harness for logins
"""

import logging
import os
import signal
import threading

import kshalopy

logging.basicConfig(level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)

CREDENTIALS_FILE = "test-user.credentials.secret.json"

config = kshalopy.Config.load_defaults()


def refresh_credentials(
    credentials: kshalopy.AppCredentials, exit_event, offset: int = 600
):
    """
    :param credentials:
    :param exit_event:
    :param offset:
    :return:
    """
    while True:
        if credentials.ttl < offset:
            logging.info("Getting fresh credentials")
            credentials.refresh()
            credentials.save_credentials(CREDENTIALS_FILE)
            logging.info(
                "Got fresh credentials - exp: %s", credentials.expiration_dt.isoformat()
            )
        if exit_event.wait(timeout=(credentials.ttl - offset)):
            break
    logging.info("Exiting")


def main():
    """
    :return:
    """
    if os.path.exists(CREDENTIALS_FILE):
        credentials = kshalopy.AppCredentials.load_credentials(CREDENTIALS_FILE)
    else:
        login_params = kshalopy.LoginParameters(
            username=input("Username: "),
            password=input("Password: "),
            verification_method=kshalopy.VerificationMethods.PHONE,
            device_key="foo42",
        )

        authenticator = kshalopy.LoginHandler(
            login_params=login_params, app_config=config
        )
        authenticator.start_login()

        verification_code = input("Verification Code: ")
        authenticator.submit_verification_code(verification_code)

        credentials = authenticator.credentials
        credentials.save_credentials(CREDENTIALS_FILE)

    exit_event = threading.Event()

    signal.signal(signal.SIGINT, lambda a, b: exit_event.set())

    credential_worker = threading.Thread(
        target=refresh_credentials, args=[credentials, exit_event]
    )
    credential_worker.start()

    rest_client = kshalopy.RestClient(credentials, "kshalopy_test", "kshalopy")
    homes = rest_client.get_my_homes()
    devices = {}
    for home in homes:
        for device in rest_client.get_devices_in_home(home):
            devices[device.deviceid] = device
    # pass


if __name__ == "__main__":
    main()
