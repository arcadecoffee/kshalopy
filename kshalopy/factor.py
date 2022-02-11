from __future__ import annotations


class Factor:
    def __init__(self, int_value: int = 0, hex_value: str = "0") -> None:
        if int_value:
            self.int = int_value
            self.hex = "%x" % self.int
        else:
            self.hex = hex_value
            self.int = int(self.hex, 16)
        self.padded_hex = self.pad_hex(self.hex)
        self.bytes = bytes.fromhex(self.padded_hex)

    def __add__(self, other: Factor) -> Factor:
        return Factor(int_value=self.int + other.int)

    def __sub__(self, other: Factor) -> Factor:
        return Factor(int_value=self.int - other.int)

    def __mul__(self, other: Factor) -> Factor:
        return Factor(int_value=self.int * other.int)

    def __repr__(self) -> int:
        return self.int

    @staticmethod
    def pad_hex(value: str) -> str:
        if len(value) % 2 == 1:
            value = "0" + value
        elif int(value[0], 16) >= 8:
            value = "00" + value
        return value
