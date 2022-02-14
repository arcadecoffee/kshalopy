"""
Test harness for logins
"""

from pprint import pprint

from kshalopy import Config
from kshalopy.login import LoginHandler, LoginParameters, VerificationMethods

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

pprint(authenticator.credentials)
