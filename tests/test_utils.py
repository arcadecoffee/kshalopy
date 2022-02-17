from kshalopy.utils import calculate_expiration, date_string_to_timestamp


def test_date_string_to_timestamp():
    assert date_string_to_timestamp("Sat, 3 Oct 2020 11:18:20 GMT") == 1601723900.0


def test_calculate_expiration():
    response = {
        "ResponseMetadata": {"HTTPHeaders": {"date": "Sat, 3 Oct 2020 11:18:20 GMT"}},
        "AuthenticationResult": {"ExpiresIn": 3600},
    }
    assert calculate_expiration(response) == 1601723900.0 + 3600
