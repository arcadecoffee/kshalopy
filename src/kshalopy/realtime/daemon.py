"""
realtime/daemon.py
"""


import logging
import threading

from ..realtime.realtime import RealtimeClient

logger = logging.getLogger(__name__)


class RealtimeDaemon:
    """
    Daemon for running the realtime sync interface in a background thread
    """

    def __init__(
        self,
        client: RealtimeClient,
        start: bool = False
    ):
        self._client = client
        self._worker = threading.Thread(target=self._client.start, daemon=True)

        if start:
            self.start()

    def start(self) -> bool:
        """
        Start the daemon thread
        :return: Daemon state
        """
        logger.info("Starting daemon")
        self._worker = threading.Thread(target=self._client.start, daemon=True)
        self._worker.start()
        return self._worker.is_alive()

    def stop(self) -> bool:
        """
        Stop the daemon thread
        :return: Daemon state
        """
        logger.info("Stopping daemon")
        if self._client.active:
            self._client.close()
            logger.info("Waiting for daemon to stop")
            self._worker.join()
        return not self._worker.is_alive()

    @property
    def is_running(self) -> bool:
        """
        Return state of daemon
        :return:
        """
        return self._worker.is_alive()
