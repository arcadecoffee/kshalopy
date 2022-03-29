"""
Test harness for logins
"""

import logging
import os
import signal
import time

import src.kshalopy as kshalopy

logging.basicConfig(level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)
logger = logging.getLogger(__name__)

CREDENTIALS_FILE = "test-user.credentials.secret.json"

config = kshalopy.Config.load_defaults()


def main():
    """
    :return:
    """
    if os.path.exists(CREDENTIALS_FILE):
        credentials = kshalopy.AppCredentials.load_credentials(CREDENTIALS_FILE, config)
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

    credential_daemon = kshalopy.CredentialsDaemon(
        credentials=credentials, credentials_file=CREDENTIALS_FILE, start=True
    )

    while not credentials.ttl:
        logger.info("Waiting for fresh credentials")
        time.sleep(1)

    rest_client = kshalopy.RestClient(
        config=config,
        credentials=credentials,
        source_name="kshalopy_test",
        source_device="kshalopy",
    )

    devices = {}
    for home in rest_client.get_my_homes():
        for device in rest_client.get_devices_in_home(home):
            devices[device.deviceid] = device

    realtime_daemon = kshalopy.RealtimeDaemon(
        kshalopy.RealtimeClient(
            config=config, credentials=credentials, devices=devices
        ),
        start=True,
    )

    def stop_daemons(_signal=None, _handler=None):
        credential_daemon.stop()
        realtime_daemon.stop()

    signal.signal(signal.SIGINT, stop_daemons)

    while credential_daemon.is_running or realtime_daemon.is_running:
        # You could make a whole interactive app and call things like:
        # rest_client.lock_device(devices["SOME_DEVICE_ID"])
        # or
        # rest_client.unlock_device(devices["SOME_DEVICE_ID"])
        # but as it is, this example just kind of watches the state of the lock
        pass


if __name__ == "__main__":
    pass
    main()
