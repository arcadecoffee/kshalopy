"""
Test harness for logins
"""
import logging
import os
import signal

import kshalopy

logging.basicConfig(level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)

CREDENTIALS_FILE = "test-user.credentials.secret.json"

config = kshalopy.Config.load_defaults()


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

    credential_daemon = kshalopy.CredentialsDaemon(
        credentials=credentials,
        credentials_file=CREDENTIALS_FILE,
        start=True
    )

    def stop_daemons(_signal, _handler):
        credential_daemon.stop()

    signal.signal(signal.SIGINT, stop_daemons)

    # while not credentials.ttl:
    #     time.sleep(1)
    #
    # rest_client = kshalopy.RestClient(credentials, "kshalopy_test", "kshalopy")
    #
    # devices = {}
    # for home in rest_client.get_my_homes():
    #     for device in rest_client.get_devices_in_home(home):
    #         devices[device.deviceid] = device
    #
    # print(json.dumps([ob.__dict__ for ob in devices.values()], indent=4))
    pass


if __name__ == "__main__":
    main()
