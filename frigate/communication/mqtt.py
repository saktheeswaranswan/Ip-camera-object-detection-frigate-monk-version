import logging
import threading

import paho.mqtt.client as mqtt

from frigate.communication.dispatcher import Communicator
from frigate.config import FrigateConfig
from frigate.types import CameraMetricsTypes


logger = logging.getLogger(__name__)


class MqttClient(Communicator):
    """Frigate wrapper for mqtt client."""

    def __init__(self, config: FrigateConfig) -> None:
        self.config = config
        self.mqtt_config = config.mqtt
        self.connected: bool = False
        self._start()

    def subscribe(self, receiver) -> None:
        """Wrapper for allowing dispatcher to subscribe."""
        self._dispatcher = receiver

        # register callbacks
        for name in self.config.cameras.keys():
            self.client.message_callback_add(
                f"{self.mqtt_config.topic_prefix}/{name}/recordings/set",
                self.on_mqtt_command,
            )
            self.client.message_callback_add(
                f"{self.mqtt_config.topic_prefix}/{name}/snapshots/set",
                self.on_mqtt_command,
            )
            self.client.message_callback_add(
                f"{self.mqtt_config.topic_prefix}/{name}/detect/set",
                self.on_mqtt_command,
            )
            self.client.message_callback_add(
                f"{self.mqtt_config.topic_prefix}/{name}/motion/set",
                self.on_mqtt_command,
            )
            self.client.message_callback_add(
                f"{self.mqtt_config.topic_prefix}/{name}/improve_contrast/set",
                self.on_mqtt_command,
            )
            self.client.message_callback_add(
                f"{self.mqtt_config.topic_prefix}/{name}/motion_threshold/set",
                self.on_mqtt_command,
            )
            self.client.message_callback_add(
                f"{self.mqtt_config.topic_prefix}/{name}/motion_contour_area/set",
                self.on_mqtt_command,
            )

        self.client.message_callback_add(
            f"{self.mqtt_config.topic_prefix}/restart", self.on_mqtt_command
        )

    def publish(self, topic: str, payload, retain: bool = False) -> None:
        """Wrapper for publishing when client is in valid state."""
        if not self.connected:
            logger.error(f"Unable to publish to {topic}: client is not connected")
            return

        self.client.publish(
            f"{self.mqtt_config.topic_prefix}/{topic}", payload, retain=retain
        )

    def _set_initial_topics(self) -> None:
        """Set initial state topics."""
        for camera_name, camera in self.config.cameras.items():
            self.publish(
                f"{self.mqtt_config.topic_prefix}/{camera_name}/recordings/state",
                "ON" if camera.record.enabled else "OFF",
                retain=True,
            )
            self.publish(
                f"{self.mqtt_config.topic_prefix}/{camera_name}/snapshots/state",
                "ON" if camera.snapshots.enabled else "OFF",
                retain=True,
            )
            self.publish(
                f"{self.mqtt_config.topic_prefix}/{camera_name}/detect/state",
                "ON" if camera.detect.enabled else "OFF",
                retain=True,
            )
            self.publish(
                f"{self.mqtt_config.topic_prefix}/{camera_name}/motion/state",
                "ON",
                retain=True,
            )
            self.publish(
                f"{self.mqtt_config.topic_prefix}/{camera_name}/improve_contrast/state",
                "ON" if camera.motion.improve_contrast else "OFF",
                retain=True,
            )
            self.publish(
                f"{self.mqtt_config.topic_prefix}/{camera_name}/motion_threshold/state",
                camera.motion.threshold,
                retain=True,
            )
            self.publish(
                f"{self.mqtt_config.topic_prefix}/{camera_name}/motion_contour_area/state",
                camera.motion.contour_area,
                retain=True,
            )
            self.publish(
                f"{self.mqtt_config.topic_prefix}/{camera_name}/motion",
                "OFF",
                retain=False,
            )

        self.publish(
            self.mqtt_config.topic_prefix + "/available", "online", retain=True
        )

    def on_mqtt_command(
        self, client: mqtt.Client, userdata, message: mqtt.MQTTMessage
    ) -> None:
        self._dispatcher(
            message.topic.replace(f"{self.mqtt_config.topic_prefix}/", ""),
            message.payload.decode(),
        )

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc) -> None:
        """Mqtt connection callback."""
        threading.current_thread().name = "mqtt"
        if rc != 0:
            if rc == 3:
                logger.error(
                    "Unable to connect to MQTT server: MQTT Server unavailable"
                )
            elif rc == 4:
                logger.error(
                    "Unable to connect to MQTT server: MQTT Bad username or password"
                )
            elif rc == 5:
                logger.error("Unable to connect to MQTT server: MQTT Not authorized")
            else:
                logger.error(
                    "Unable to connect to MQTT server: Connection refused. Error code: "
                    + str(rc)
                )

        self.connected = True
        logger.debug("MQTT connected")
        client.subscribe(f"{self.mqtt_config.topic_prefix}/#")
        self._set_initial_topics()

    def _on_disconnect(self, client: mqtt.Client, userdata, flags, rc) -> None:
        """Mqtt disconnection callback."""
        self.connected = False
        logger.error("MQTT disconnected")

    def _start(self) -> None:
        """Start mqtt client."""
        self.client = mqtt.Client(client_id=self.mqtt_config.client_id)
        self.client.on_connect = self._on_connect
        self.client.will_set(
            self.mqtt_config.topic_prefix + "/available",
            payload="offline",
            qos=1,
            retain=True,
        )

        if not self.mqtt_config.tls_ca_certs is None:
            if (
                not self.mqtt_config.tls_client_cert is None
                and not self.mqtt_config.tls_client_key is None
            ):
                self.client.tls_set(
                    self.mqtt_config.tls_ca_certs,
                    self.mqtt_config.tls_client_cert,
                    self.mqtt_config.tls_client_key,
                )
            else:
                self.client.tls_set(self.mqtt_config.tls_ca_certs)
        if not self.mqtt_config.tls_insecure is None:
            self.client.tls_insecure_set(self.mqtt_config.tls_insecure)
        if not self.mqtt_config.user is None:
            self.client.username_pw_set(
                self.mqtt_config.user, password=self.mqtt_config.password
            )
        try:
            # https://stackoverflow.com/a/55390477
            # with connect_async, retries are handled automatically
            self.client.connect_async(self.mqtt_config.host, self.mqtt_config.port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Unable to connect to MQTT server: {e}")
            return

    def add_topic_callback(self, topic: str, callback) -> None:
        self.client.message_callback_add(topic, callback)
