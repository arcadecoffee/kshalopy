"""
realtime/realtime.py
"""

import json
import logging

from base64 import urlsafe_b64encode
from threading import Timer
from typing import Dict
from uuid import uuid4

from websocket import WebSocketApp

from .. import AppCredentials, Config

logger = logging.getLogger(__name__)


class RealtimeClient:
    """
    Realtime GQL subscription client
    """

    def __init__(self, config: Config, credentials: AppCredentials, timeout: int = 10):
        self.config = config
        self.credentials = credentials
        self.timeout = timeout
        self.active = False
        self.ws_app = WebSocketApp(
            self._connection_url,
            subprotocols=["graphql-ws"],
            on_close=self._on_close,
            on_error=self._on_error,
            on_message=self._on_message,
            on_open=self._on_open,
        )
        self._subscription_ids = []
        self._timer = self._new_timer()

    @property
    def _connection_url(self) -> str:
        encoded_header = urlsafe_b64encode(json.dumps(self._header).encode()).decode()
        wss_url = f"wss{self.config.appsync_api_url[5:]}".replace(
            ".appsync-api.", ".appsync-realtime-api."
        )
        return f"{wss_url}?header={encoded_header}&payload=e30="

    @property
    def _header(self) -> Dict[str, str]:
        return {"host": self._host, "Authorization": self.credentials.id_token}

    @property
    def _host(self) -> str:
        return self.config.appsync_api_url[8:-8]

    @property
    def _device_subscription_query(self) -> str:
        return json.dumps(
            {
                "query": f"""
                    subscription onManageDevice {{
                    onManageDevice(email: "{self.credentials.username}")
                    {{ deviceid devicename devicestatus operationtype }} }}
                    """,
                "variables": {},
            }
        )

    def _build_start_message(self, subscription_id: str, query: str) -> str:
        return json.dumps(
            {
                "id": subscription_id,
                "payload": {
                    "data": query,
                    "extensions": {
                        "authorization": {
                            "host": self._host,
                            "Authorization": self.credentials.id_token,
                        }
                    },
                },
                "type": "start",
            }
        )

    @staticmethod
    def _build_stop_message(subscription_id: str) -> str:
        return json.dumps({"id": subscription_id, "type": "stop"})

    def _on_close(self, _ws_app: WebSocketApp, status_code: int, msg: str) -> None:
        logger.info("Connection closed : %s - %s", status_code, msg)
        self.active = False

    def _on_error(self, _ws_app: WebSocketApp, error: Exception) -> None:
        logger.error(error)
        self.active = False

    def _on_message(self, _ws_app: WebSocketApp, msg: str) -> None:
        logger.info("Message received : %s", msg)
        msg_content = json.loads(msg)

        if msg_content["type"] == "connection_ack":
            self.timeout = msg_content["payload"]["connectionTimeoutMs"] / 1000

            subscription_message = self._build_start_message(
                str(uuid4()), self._device_subscription_query
            )
            self.ws_app.send(subscription_message)

        elif msg_content["type"] == "start_ack":
            self._subscription_ids.append(msg_content["id"])

        elif msg_content["type"] == "complete":
            self._subscription_ids.remove(msg_content["id"])

        elif msg_content["type"] == "data":
            # {
            #   "id": "5a03c89b-8023-4194-ae81-50ee9cba1e86",
            #   "type": "data",
            #   "payload": {
            #       "data": {
            #           "onManageDevice": {
            #               "deviceid": "10ed83f37baa3f44c4",
            #               "devicename": "Workshop",
            #               "devicestatus": "Locked",
            #               "operationtype": "UpdateDeviceStatus"
            #               }
            #           }
            #       }
            #   }
            pass

        self._reset_timer()

        # There are other types: 'ka', 'complete', etc....
        # https://github.com/apollographql/apollo-ios/blob/main/Sources/ApolloWebSocket/OperationMessage.swift
        # https://docs.aws.amazon.com/appsync/latest/devguide/real-time-websocket-client.html

    def _on_open(self, _ws_app: WebSocketApp) -> None:
        logger.info("Opening connection")
        self.ws_app.send(json.dumps({"type": "connection_init"}))
        self.active = True

    def _new_timer(self) -> Timer:
        timer = Timer(self.timeout, self.close)
        timer.daemon = True
        return timer

    def _reset_timer(self) -> None:
        self._timer.cancel()
        self._timer = self._new_timer()
        self._timer.start()

    def start(self) -> None:
        """
        Start the WebApp...this should almost always be done in a thread
        :return: None
        """
        logger.info("Starting connection")
        self.ws_app.run_forever()

    def close(self, force: bool = False) -> None:
        """
        Close the connection, blocks until connections have been closed cleanly unless
        force is set
        :return:
        """
        logger.info("Closing connection")
        for subscription_id in self._subscription_ids:
            self.ws_app.send(self._build_stop_message(subscription_id))
        while self._subscription_ids and not force:
            pass
        self.ws_app.close()
