from dataclasses import dataclass

from kshalopy.realtime.daemon import RealtimeDaemon


class MockRealtimeClient:
    def __init__(self):
        self.call_count = {}
        self._started = False

    def start(self):
        self.call_count["start"] = self.call_count.get("start", 0) + 1
        self._started = True
        while self._started:
            pass

    def close(self):
        self.call_count["close"] = self.call_count.get("close", 0) + 1
        self._started = False

    @property
    def active(self):
        return self._started


def test_auto_start():
    client = MockRealtimeClient()
    daemon = RealtimeDaemon(client, start=True)
    assert daemon.is_running
    assert client.call_count.get("start", 0) == 1
    assert client.call_count.get("close", 0) == 0
    daemon.stop()


def test_start():
    client = MockRealtimeClient()
    daemon = RealtimeDaemon(client)
    assert daemon.start()
    assert daemon.is_running
    assert client.call_count.get("start", 0) == 1
    assert client.call_count.get("close", 0) == 0
    daemon.stop()

def test_start_stop():
    client = MockRealtimeClient()
    daemon = RealtimeDaemon(client)
    assert daemon.start()
    assert daemon.is_running
    assert client.call_count.get("start", 0) == 1
    assert client.call_count.get("close", 0) == 0
    assert daemon.stop()
    assert not daemon.is_running
    assert client.call_count.get("start", 0) == 1
    assert client.call_count.get("close", 0) == 1


def test_stop():
    client = MockRealtimeClient()
    daemon = RealtimeDaemon(client)
    assert not daemon.is_running
    assert client.call_count.get("start", 0) == 0
    assert client.call_count.get("close", 0) == 0
    assert daemon.stop()
    assert not daemon.is_running
    assert client.call_count.get("start", 0) == 0
    assert client.call_count.get("close", 0) == 0
