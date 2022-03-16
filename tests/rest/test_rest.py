import json

from pathlib import Path

from kshalopy.rest.rest import AppCredentials, Config, Device, Home, RestClient

config_path = str(Path.joinpath(Path(__file__).parent, "test_config.json"))
config = Config.from_app_json_file(config_path)

credentials_path = str(Path.joinpath(Path(__file__).parent, "test_credentials.json"))
credentials = AppCredentials.load_credentials(credentials_path, config)


def get_patched_client(monkeypatch):
    responses = {
        "https://fake.execute-api.us-east-1.amazonaws.fake/prod_v1/homes/fake_homeid/devices": {
            "data": [{"deviceid": "fake_deviceid1"}, {"deviceid": "fake_deviceid2"}]
        },
        "https://fake.execute-api.us-east-1.amazonaws.fake/prod_v1/users/me/homes": {
            "data": [{"homeid": "fake_homeid1"}, {"homeid": "fake_homeid2"}]
        },
        "https://fake.execute-api.us-east-1.amazonaws.fake/prod_v1/devices/fake_deviceid": {
            "data": [{"doorstatus": "Locked"}]
        },
        "https://fake.execute-api.us-east-1.amazonaws.fake/prod_v1/users/me": {
            "data": [{"email": "fake@fake.com"}]
        },
        "https://fake.execute-api.us-east-1.amazonaws.fake/prod_v1/homes/fake_homeid/sharedusers": {
            "data": [{"email": "fake1@fake.com"}, {"email": "fake2@fake.com"}]
        },
        "https://fake.execute-api.us-east-1.amazonaws.fake/prod_v1/devices/fake_deviceid_lock/status": {
            "data": "1"
        },
        "https://fake.execute-api.us-east-1.amazonaws.fake/prod_v1/devices/fake_deviceid_unlock/status": {
            "data": "1"
        },
    }

    class MockURLOpen:
        def __init__(self, request):
            self.request = request

        def read(self):
            assert self.request.headers["Authorization"] == "Bearer fake_id_token"

            if (
                self.request.full_url
                == "https://fake.execute-api.us-east-1.amazonaws.fake/prod_v1/devices/fake_deviceid_lock/status"
            ):
                assert self.request.method == "PATCH"
                assert json.loads(self.request.data) == {
                    "action": "Lock",
                    "source": '{"name": "fake_name", "device": "fake_device"}',
                }
            elif (
                self.request.full_url
                == "https://fake.execute-api.us-east-1.amazonaws.fake/prod_v1/devices/fake_deviceid_unlock/status"
            ):
                assert self.request.method == "PATCH"
                assert json.loads(self.request.data) == {
                    "action": "Unlock",
                    "source": '{"name": "fake_name", "device": "fake_device"}',
                }

            return json.dumps(responses[self.request.full_url]).encode()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("kshalopy.rest.rest.urllib.request.urlopen", MockURLOpen)
    return RestClient(config, credentials, "fake_name", "fake_device")


def test_get_devices_in_home(monkeypatch):
    client = get_patched_client(monkeypatch)
    devices = client.get_devices_in_home(Home(homeid="fake_homeid"))
    assert len(devices) == 2
    assert devices[0].deviceid == "fake_deviceid1"
    assert devices[1].deviceid == "fake_deviceid2"


def test_get_device_details(monkeypatch):
    client = get_patched_client(monkeypatch)
    device_details = client.get_device_details(Device(deviceid="fake_deviceid"))
    assert device_details.doorstatus == "Locked"


def test_get_my_homes(monkeypatch):
    client = get_patched_client(monkeypatch)
    homes = client.get_my_homes()
    assert len(homes) == 2
    assert homes[0].homeid == "fake_homeid1"
    assert homes[1].homeid == "fake_homeid2"


def test_get_my_user(monkeypatch):
    client = get_patched_client(monkeypatch)
    user = client.get_my_user()
    assert user.email == "fake@fake.com"


def test_get_shared_users_in_home(monkeypatch):
    client = get_patched_client(monkeypatch)
    users = client.get_shared_users_in_home(Home(homeid="fake_homeid"))
    assert len(users) == 2
    assert users[0].email == "fake1@fake.com"
    assert users[1].email == "fake2@fake.com"


def test_lock_device(monkeypatch):
    client = get_patched_client(monkeypatch)
    response = client.lock_device(Device(deviceid="fake_deviceid_lock"))
    assert response


def test_unlock_device(monkeypatch):
    client = get_patched_client(monkeypatch)
    response = client.unlock_device(Device(deviceid="fake_deviceid_unlock"))
    assert response
