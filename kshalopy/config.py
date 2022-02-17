"""
kshalopy.config.config
"""

# pylint: disable=R0902
# too-many-instance-attributes
# The configuration is what it is

from __future__ import annotations

import json
import os

from dataclasses import dataclass

DEFAULT_CONFIG_JSON = os.path.join(os.path.dirname(__file__), "default_config.json")


@dataclass
class Config:
    """
    Class for loading and carrying the base configuration of the 'Kwikset' app.

    The base configuration can be found at:
        '/Applications/Kwikset.app/Wrapper/Spectrum.app/spectrum.environments.json'

    The 'Prod' environment is the only one that is likely to work / be accessible
    publicly.
    """

    host: str
    port: int
    use_ssl: bool
    region: str
    user_pool_id: str
    client_id: str
    identity_pool_id: str
    client_secret: str

    @classmethod
    def from_app_json(cls, json_string: str) -> Config:
        """
        Create a Config object from a JSON string
        :param json_string: JSON string to parse
        :return: Config object
        """
        settings = json.loads(json_string)
        return cls(
            host=settings["host"],
            port=settings["port"],
            use_ssl=settings["useSSL"],
            region=settings["userpoolid"].split("_")[0],
            user_pool_id=settings["userpoolid"].split("_")[1],
            client_id=settings["userappclientid"],
            identity_pool_id=settings["identitypoolid"],
            client_secret=settings["identityappclientsecret"],
        )

    @classmethod
    def from_app_json_file(cls, json_file: str) -> Config:
        """
        Create a Config object from a JSON file
        :param json_file: file name
        :return: Config object
        """
        with open(json_file, encoding="ascii") as json_fh:
            return cls.from_app_json(json_fh.read())

    @classmethod
    def load_defaults(cls):
        """
        Load the default configuration file included with this module
        :return: Config object
        """
        return cls.from_app_json_file(DEFAULT_CONFIG_JSON)
