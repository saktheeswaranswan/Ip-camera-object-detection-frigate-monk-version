"""Handle communication between frigate and other applications."""

import logging

from abc import ABC, abstractmethod

from frigate.config import FrigateConfig
from frigate.types import CameraMetricsTypes
from frigate.util import restart_frigate


logger = logging.getLogger(__name__)


class Communicator(ABC):
    """pub/sub model via specific protocol."""

    @abstractmethod
    def publish(self, topic: str, payload, retain: bool = False):
        """Send data via specific protocol."""
        pass

    @abstractmethod
    def subscribe(self, receiver):
        pass


class Dispatcher:
    """Handle communication between frigate and communicators."""

    def __init__(
        self,
        config: FrigateConfig,
        camera_metrics: dict[str, CameraMetricsTypes],
        communicators: list[Communicator],
    ) -> None:
        self.config = config
        self.camera_metrics = camera_metrics
        self.comms = communicators

        for comm in self.comms:
            comm.subscribe(self._receive)

    def _receive(self, topic: str, payload: str) -> None:
        """Handle receiving of payload from communicators."""
        if "detect/set" in topic:
            camera_name = topic.split("/")[-3]
            self._on_detect_command(camera_name, payload)
        elif "improve_contrast/set" in topic:
            camera_name = topic.split("/")[-3]
            self._on_motion_improve_contrast_command(camera_name, payload)
        elif "motion/set" in topic:
            camera_name = topic.split("/")[-3]
            self._on_motion_command(camera_name, payload)
        elif "motion_contour_area/set":
            camera_name = topic.split("/")[-3]

            try:
                value = int(payload)
            except ValueError:
                f"Received unsupported value at {topic}: {payload}"
                return

            self._on_motion_contour_area_command(camera_name, value)
        elif "motion_threshold/set":
            camera_name = topic.split("/")[-3]

            try:
                value = int(payload)
            except ValueError:
                f"Received unsupported value at {topic}: {payload}"
                return

            self._on_motion_threshold_command(camera_name, value)
        elif "recordings/set" in topic:
            camera_name = topic.split("/")[-3]
            self._on_recordings_command(camera_name, payload)
        elif "snapshots/set" in topic:
            camera_name = topic.split("/")[-3]
            self._on_snapshots_command(camera_name, payload)
        elif topic == "restart":
            restart_frigate()

    def publish(self, topic: str, payload, retain: bool = False) -> None:
        """Handle publishing to communicators."""
        for comm in self.comms:
            comm.publish(topic, payload, retain)

    def _on_detect_command(self, camera_name: str, payload: str) -> None:
        """Callback for detect topic."""
        detect_settings = self.config.cameras[camera_name].detect

        if payload == "ON":
            if not self.camera_metrics[camera_name]["detection_enabled"].value:
                logger.info(f"Turning on detection for {camera_name}")
                self.camera_metrics[camera_name]["detection_enabled"].value = True
                detect_settings.enabled = True

                if not self.camera_metrics[camera_name]["motion_enabled"].value:
                    logger.info(
                        f"Turning on motion for {camera_name} due to detection being enabled."
                    )
                    self.camera_metrics[camera_name]["motion_enabled"].value = True
                    self.publish(f"{camera_name}/motion/state", payload, retain=True)
        elif payload == "OFF":
            if self.camera_metrics[camera_name]["detection_enabled"].value:
                logger.info(f"Turning off detection for {camera_name}")
                self.camera_metrics[camera_name]["detection_enabled"].value = False
                detect_settings.enabled = False

        self.publish(f"{camera_name}/detect/state", payload, retain=True)

    def _on_motion_command(self, camera_name: str, payload: str) -> None:
        """Callback for motion topic."""
        if payload == "ON":
            if not self.camera_metrics[camera_name]["motion_enabled"].value:
                logger.info(f"Turning on motion for {camera_name}")
                self.camera_metrics[camera_name]["motion_enabled"].value = True
        elif payload == "OFF":
            if self.camera_metrics[camera_name]["detection_enabled"].value:
                logger.error(
                    f"Turning off motion is not allowed when detection is enabled."
                )
                return

            if self.camera_metrics[camera_name]["motion_enabled"].value:
                logger.info(f"Turning off motion for {camera_name}")
                self.camera_metrics[camera_name]["motion_enabled"].value = False

        self.publish(f"{camera_name}/motion/state", payload, retain=True)

    def _on_motion_improve_contrast_command(
        self, camera_name: str, payload: str
    ) -> None:
        """Callback for improve_contrast topic."""
        motion_settings = self.config.cameras[camera_name].motion

        if payload == "ON":
            if not self.camera_metrics[camera_name]["improve_contrast_enabled"].value:
                logger.info(f"Turning on improve contrast for {camera_name}")
                self.camera_metrics[camera_name][
                    "improve_contrast_enabled"
                ].value = True
                motion_settings.improve_contrast = True
        elif payload == "OFF":
            if self.camera_metrics[camera_name]["improve_contrast_enabled"].value:
                logger.info(f"Turning off improve contrast for {camera_name}")
                self.camera_metrics[camera_name][
                    "improve_contrast_enabled"
                ].value = False
                motion_settings.improve_contrast = False

        self.publish(f"{camera_name}/improve_contrast/state", payload, retain=True)

    def _on_motion_contour_area_command(self, camera_name: str, payload: int) -> None:
        """Callback for motion contour topic."""
        motion_settings = self.config.cameras[camera_name].motion
        logger.info(f"Setting motion contour area for {camera_name}: {payload}")
        self.camera_metrics[camera_name]["motion_contour_area"].value = payload
        motion_settings.contour_area = payload
        self.publish(f"{camera_name}/motion_contour_area/state", payload, retain=True)

    def _on_motion_threshold_command(self, camera_name: str, payload: int) -> None:
        """Callback for motion threshold topic."""
        motion_settings = self.config.cameras[camera_name].motion
        logger.info(f"Setting motion threshold for {camera_name}: {payload}")
        self.camera_metrics[camera_name]["motion_threshold"].value = payload
        motion_settings.threshold = payload
        self.publish(f"{camera_name}/motion_threshold/state", payload, retain=True)

    def _on_recordings_command(self, camera_name: str, payload: str) -> None:
        """Callback for recordings topic."""
        record_settings = self.config.cameras[camera_name].record

        if payload == "ON":
            if not record_settings.enabled:
                logger.info(f"Turning on recordings for {camera_name}")
                record_settings.enabled = True
        elif payload == "OFF":
            if record_settings.enabled:
                logger.info(f"Turning off recordings for {camera_name}")
                record_settings.enabled = False

        self.publish(f"{camera_name}/recordings/state", payload, retain=True)

    def _on_snapshots_command(self, camera_name: str, payload: str) -> None:
        """Callback for snapshots topic."""
        snapshots_settings = self.config.cameras[camera_name].snapshots

        if payload == "ON":
            if not snapshots_settings.enabled:
                logger.info(f"Turning on snapshots for {camera_name}")
                snapshots_settings.enabled = True
        elif payload == "OFF":
            if snapshots_settings.enabled:
                logger.info(f"Turning off snapshots for {camera_name}")
                snapshots_settings.enabled = False

        self.publish(f"{camera_name}/snapshots/state", payload, retain=True)
