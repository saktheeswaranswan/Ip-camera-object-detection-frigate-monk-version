"""Handle sending notifications for Frigate via Firebase."""

import datetime
import json
import logging
import os
from typing import Any, Callable

from py_vapid import Vapid01
from pywebpush import WebPusher

from frigate.comms.dispatcher import Communicator
from frigate.config import FrigateConfig
from frigate.const import CONFIG_DIR
from frigate.models import User

logger = logging.getLogger(__name__)


class WebPushClient(Communicator):  # type: ignore[misc]
    """Frigate wrapper for firebase client."""

    def __init__(self, config: FrigateConfig) -> None:
        self.config = config
        self.claim_headers: dict[str, dict[str, str]] = {}
        self.refresh = 0
        self.web_pushers: list[WebPusher] = []

        if not self.config.notifications.email:
            logger.warning("Email must be provided for push notifications to be sent.")

        # Pull keys from PEM or generate if they do not exist
        self.vapid = Vapid01.from_file(os.path.join(CONFIG_DIR, "notifications.pem"))

        users: list[User] = User.select(User.notification_tokens).dicts().iterator()
        for user in users:
            for sub in user["notification_tokens"]:
                self.web_pushers.append(WebPusher(sub))

    def subscribe(self, receiver: Callable) -> None:
        """Wrapper for allowing dispatcher to subscribe."""
        pass

    def check_registrations(self) -> None:
        # check for valid claim or create new one
        now = datetime.datetime.now().timestamp()
        if len(self.claim_headers) == 0 or self.refresh < now:
            self.refresh = (
                datetime.datetime.now() + datetime.timedelta(hours=1)
            ).timestamp()
            endpoints: set[str] = set()

            # get a unique set of push endpoints
            for push in self.web_pushers:
                endpoint: str = push.subscription_info["endpoint"]
                endpoints.add(endpoint[0 : endpoint.index("/", 10)])

            # create new claim
            for endpoint in endpoints:
                claim = {
                    "sub": f"mailto:{self.config.notifications.email}",
                    "aud": endpoint,
                    "exp": self.refresh,
                }
                self.claim_headers[endpoint] = self.vapid.sign(claim)

    def publish(self, topic: str, payload: Any, retain: bool = False) -> None:
        """Wrapper for publishing when client is in valid state."""
        if topic == "reviews":
            self.send_alert(json.loads(payload))

    def send_alert(self, payload: dict[str, any]) -> None:
        if not self.config.notifications.email:
            return

        self.check_registrations()

        # Only notify for alerts
        if payload["after"]["severity"] != "alert":
            return

        state = payload["type"]

        # Don't notify if message is an update and important fields don't have an update
        if (
            state == "update"
            and len(payload["before"]["data"]["objects"])
            == len(payload["after"]["data"]["objects"])
            and len(payload["before"]["data"]["zones"])
            == len(payload["after"]["data"]["zones"])
        ):
            return

        reviewId = payload["after"]["id"]
        sorted_objects: set[str] = set()

        for obj in payload["after"]["data"]["objects"]:
            if "-verified" not in obj:
                sorted_objects.add(obj)

        sorted_objects.update(payload["after"]["data"]["sub_labels"])

        camera: str = payload["after"]["camera"]
        title = f"{', '.join(sorted_objects).replace('_', ' ').title()}{' was' if state == 'end' else ''} detected in {', '.join(payload['after']['data']['zones']).replace('_', ' ').title()}"
        message = f"Detected on {camera.replace('_', ' ').title()}"
        image = f'{payload["after"]["thumb_path"].replace("/media/frigate", "")}'

        # if event is ongoing open to live view otherwise open to recordings view
        direct_url = f"/review?id={reviewId}" if state == "end" else f"/#{camera}"

        for pusher in self.web_pushers:
            endpoint = pusher.subscription_info["endpoint"]

            # set headers for notification behavior
            headers = self.claim_headers[endpoint[0 : endpoint.index("/", 10)]].copy()
            headers["urgency"] = "high"

            # send message
            pusher.send(
                headers=headers,
                ttl=3600,
                data=json.dumps(
                    {
                        "title": title,
                        "message": message,
                        "direct_url": direct_url,
                        "image": image,
                        "id": reviewId,
                    }
                ),
            )

    def stop(self) -> None:
        pass
