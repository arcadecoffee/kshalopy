import time
import tempfile
import os

from datetime import datetime
from pathlib import Path

from kshalopy.config import Config
from kshalopy.credentials import AppCredentials, CredentialsDaemon


TEST_CYCLE_TIME = 3


class MockAppCredentials(AppCredentials):
    def refresh(self, ttl_limit: int = 900, force: bool = False) -> None:
        self.expiration = int(datetime.now().timestamp()) + TEST_CYCLE_TIME


test_config = Config.from_app_json_file(
    str(Path.joinpath(Path(__file__).parent, "test_config.json"))
)

test_credentials = MockAppCredentials.load_credentials(
    str(Path.joinpath(Path(__file__).parent, "test_credentials.json")), test_config
)


def test_manual_start_stop(monkeypatch):
    daemon = CredentialsDaemon(credentials=test_credentials)
    assert test_credentials.ttl == 0
    daemon.start()
    assert TEST_CYCLE_TIME > test_credentials.ttl > 0
    assert daemon.is_running
    time.sleep(TEST_CYCLE_TIME)
    assert TEST_CYCLE_TIME > test_credentials.ttl > 0
    daemon.stop()
    assert not daemon.is_running


def test_auto_start_stop():
    daemon = CredentialsDaemon(credentials=test_credentials, start=True)
    assert TEST_CYCLE_TIME > test_credentials.ttl > 0
    time.sleep(TEST_CYCLE_TIME)
    assert TEST_CYCLE_TIME > test_credentials.ttl > 0
    daemon.stop()


def test_credential_file_write():
    test_file = tempfile.NamedTemporaryFile().name
    daemon = CredentialsDaemon(
        credentials=test_credentials, credentials_file=test_file, start=True
    )
    daemon.start()
    time.sleep(1)
    daemon.stop()
    new_credentials = AppCredentials.load_credentials(test_file)
    assert TEST_CYCLE_TIME > test_credentials.ttl > 0
    assert new_credentials.expiration == test_credentials.expiration
