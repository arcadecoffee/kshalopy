from kshalopy.login.factor import Factor


def test_int_declaration():
    a = Factor(int_value=93159224)
    assert a.int == 93159224
    assert a.hex == "58d7f38"
    assert a.padded_hex == "058d7f38"


def test_hex_declaration():
    a = Factor(hex_value="8d7f38")
    assert a.int == 9273144
    assert a.hex == "8d7f38"
    assert a.padded_hex == "008d7f38"


def test_no_padding():
    a = Factor(hex_value="7d7f38")
    assert a.int == 8224568

def test_operators():
    a = Factor(int_value=93159224)
    b = Factor(hex_value="7d7f38")
    assert (a + b).int == 93159224 + 8224568
    assert (a - b).int == 93159224 - 8224568
    assert (a * b).int == 93159224 * 8224568
    assert f"{a}, {b}" == "93159224, 8224568"
