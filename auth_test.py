"""
Test harness for logins
"""

import os

from kshalopy import Config, Credentials
from kshalopy.login import LoginHandler, LoginParameters, VerificationMethods

CREDENTIALS_FILE = 'credentials.secret.json'

if os.path.exists(CREDENTIALS_FILE):
    credentials = Credentials.load_credentials(CREDENTIALS_FILE)
else:
    config = Config.load_defaults()

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
