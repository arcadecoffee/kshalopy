from dataclasses import dataclass


@dataclass
class HaloCredentials:
    access_token: str
    id_token: str
    refresh_token: str
    token_type: str
