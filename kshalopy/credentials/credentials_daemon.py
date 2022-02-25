"""
credentials/credentials_daemon.py
"""

import logging
import threading

from . import AppCredentials

logger = logging.getLogger(__name__)


class CredentialsDaemon:
    """
    Daemon for keeping credentials fresh
    """

    def __init__(
        self,
        credentials: AppCredentials,
        expiration_offset: int = 600,
        credentials_file: str = None,
        start: bool = False
    ):
        self.credentials = credentials
        self.expiration_offset = expiration_offset
        self.credentials_file = credentials_file
        self._exit_event = threading.Event()
        self._worker = threading.Thread(target=self._refresh_credentials, daemon=True)

        if start:
            self.start()

    def _refresh_credentials(self):
        logger.info("Daemon started")
        while True:
            if self.credentials.ttl < self.expiration_offset:
                logger.info("Getting fresh credentials")
                self.credentials.refresh()
                if self.credentials_file:
                    self.credentials.save_credentials(self.credentials_file)
                logger.info(
                    "Got fresh credentials - exp: %s",
                    self.credentials.expiration_dt.isoformat(),
                )
            if self._exit_event.wait(
                timeout=(self.credentials.ttl - self.expiration_offset)
            ):
                break
        logger.info("Daemon stopped")

    def start(self) -> bool:
        """
        Start the daemon thread
        :return: Daemon state
        """
        logger.info("Starting daemon")
        self._worker.start()
        return self._worker.is_alive()

    def stop(self) -> bool:
        """
        Stop the daemon thread
        :return: Daemon state
        """
        logger.info("Stopping daemon")
        self._exit_event.set()
        logger.info("Waiting for daemon to stop")
        self._worker.join()
        return self._worker.is_alive()

    @property
    def is_running(self) -> bool:
        """
        Return state of daemon
        :return:
        """
        return self._worker.is_alive()
