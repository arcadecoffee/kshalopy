from pprint import pprint

from kshalopy import AuthInitiator, VerificationMethod

## from /Applications/Kwikset.app/Wrapper/Spectrum.app/spectrum.environments.json
config = {
    "host": "ynk95r1v52.execute-api.us-east-1.amazonaws.com",
    "port": 443,
    "useSSL": True,
    "webapp": "prod",
    "userpoolid": "us-east-1_6B3uo6uKN",
    "userappclientid": "5eu1cdkjp1itd1fi7b91m6g79s",
    "identitypoolid": "us-east-1:3e3c1b84-4a85-4ad1-8785-1ba943b85075",
    "identityappclientsecret": "",
    "pinpointAppName": "hhi-prod-pinpoint",
    "pinpointAppId": "983d13e8ade444269c968f6f7359c0fc",
}

username = input("Username: ")
password = input("Password: ")

authenticator = AuthInitiator(
    username=username,
    password=password,
    user_pool_id=config["userpoolid"],
    client_id=config["userappclientid"],
    device_key="foo42",
    verification_method=VerificationMethod.EMAIL,
    client_secret="",
)
authenticator.start_login()

verification_code = input("Verification Code: ")
authenticator.submit_verification_code(verification_code)

pprint(authenticator.tokens)
