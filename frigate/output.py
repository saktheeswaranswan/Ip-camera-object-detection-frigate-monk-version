import cv2
import datetime
import math
import multiprocessing as mp
import queue
import signal
import subprocess as sp
import threading
from multiprocessing import shared_memory
from wsgiref.simple_server import make_server

import numpy as np
from setproctitle import setproctitle
from ws4py.server.wsgirefserver import (
    WebSocketWSGIHandler,
    WebSocketWSGIRequestHandler,
    WSGIServer,
)
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from ws4py.websocket import WebSocket

from frigate.config import FrigateConfig
from frigate.util import SharedMemoryFrameManager, get_yuv_crop, copy_yuv_to_position


class FFMpegConverter:
    def __init__(self, in_width, in_height, out_width, out_height, quality):
        ffmpeg_cmd = f"ffmpeg -f rawvideo -pix_fmt yuv420p -video_size {in_width}x{in_height} -i pipe: -f mpegts -s {out_width}x{out_height} -codec:v mpeg1video -q {quality} -bf 0 pipe:".split(
            " "
        )
        self.process = sp.Popen(
            ffmpeg_cmd,
            stdout=sp.PIPE,
            # TODO: logging
            stderr=sp.DEVNULL,
            stdin=sp.PIPE,
            start_new_session=True,
        )

    def write(self, b):
        self.process.stdin.write(b)

    def read(self, length):
        try:
            return self.process.stdout.read1(length)
        except ValueError:
            return False

    def exit(self):
        self.process.terminate()
        try:
            self.process.communicate(timeout=30)
        except sp.TimeoutExpired:
            self.process.kill()
            self.process.communicate()


class BroadcastThread(threading.Thread):
    def __init__(self, camera, converter, websocket_server):
        super(BroadcastThread, self).__init__()
        self.camera = camera
        self.converter = converter
        self.websocket_server = websocket_server

    def run(self):
        while True:
            buf = self.converter.read(65536)
            if buf:
                for ws in self.websocket_server.manager:
                    if ws.environ["PATH_INFO"].endswith(self.camera):
                        ws.send(buf, binary=True)
            elif self.converter.process.poll() is not None:
                break


class BirdsEyeFrameManager:
    def __init__(self, config, frame_manager: SharedMemoryFrameManager):
        self.config = config
        self.mode = config.birdseye.mode
        self.frame_manager = frame_manager
        width = config.birdseye.width
        height = config.birdseye.height
        self.frame_shape = (height, width)
        self.yuv_shape = (height * 3 // 2, width)
        self.frame = np.ndarray(self.yuv_shape, dtype=np.uint8)

        # initialize the frame as black and with the frigate logo
        self.blank_frame = np.zeros(self.yuv_shape, np.uint8)
        self.blank_frame[:] = 128
        self.blank_frame[0 : self.frame_shape[0], 0 : self.frame_shape[1]] = 16

        self.frame[:] = self.blank_frame

        self.cameras = {}
        for camera, settings in self.config.cameras.items():
            # precalculate the coordinates for all the channels
            y, u1, u2, v1, v2 = get_yuv_crop(
                settings.frame_shape_yuv,
                (
                    0,
                    0,
                    settings.frame_shape[1],
                    settings.frame_shape[0],
                ),
            )
            self.cameras[camera] = {
                "last_active_frame": 0.0,
                "layout_frame": 0.0,
                "channel_dims": {
                    "y": y,
                    "u1": u1,
                    "u2": u2,
                    "v1": v1,
                    "v2": v2,
                },
            }

        self.camera_layout = []
        self.active_cameras = set()
        self.layout_dim = 0
        self.last_output_time = 0.0

    def clear_frame(self):
        self.frame[:] = self.blank_frame

    def copy_to_position(self, position, camera=None, frame_time=None):
        if camera is None:
            frame = None
            channel_dims = None
        else:
            frame = self.frame_manager.get(
                f"{camera}{frame_time}", self.config.cameras[camera].frame_shape_yuv
            )
            channel_dims = self.cameras[camera]["channel_dims"]

        copy_yuv_to_position(position, self.frame, self.layout_dim, frame, channel_dims)

    def camera_active(self, object_box_count, motion_box_count):
        if self.mode == "continuous":
            return True

        if self.mode == "motion" and object_box_count + motion_box_count > 0:
            return True

        if self.mode == "objects" and object_box_count > 0:
            return True

    def update_frame(self):
        # determine how many cameras are tracking objects within the last 30 seconds
        now = datetime.datetime.now().timestamp()

        active_cameras = set(
            [
                cam
                for cam, cam_data in self.cameras.items()
                if now - cam_data["last_active_frame"] < 30
            ]
        )

        # if there are no active cameras
        if len(active_cameras) == 0:
            # if the layout is already cleared
            if len(self.camera_layout) == 0:
                return False
            # if the layout needs to be cleared
            else:
                self.camera_layout = []
                self.clear_frame()
                return True

        # calculate layout dimensions
        layout_dim = math.ceil(math.sqrt(len(active_cameras)))

        # reset the layout if it needs to be different
        if layout_dim != self.layout_dim:
            self.layout_dim = layout_dim

            self.camera_layout = [None] * layout_dim * layout_dim

            # calculate resolution of each position in the layout
            self.layout_frame_shape = (
                self.frame_shape[0] // layout_dim,  # height
                self.frame_shape[1] // layout_dim,  # width
            )

            self.clear_frame()

            for cam_data in self.cameras.values():
                cam_data["layout_frame"] = 0.0

            self.active_cameras = set()

        removed_cameras = self.active_cameras.difference(active_cameras)
        added_cameras = active_cameras.difference(self.active_cameras)

        self.active_cameras = active_cameras

        # update each position in the layout
        for position, camera in enumerate(self.camera_layout, start=0):

            # if this camera was removed, replace it or clear it
            if camera in removed_cameras:
                # if replacing this camera with a newly added one
                if len(added_cameras) > 0:
                    added_camera = added_cameras.pop()
                    self.camera_layout[position] = added_camera
                    self.copy_to_position(
                        position,
                        added_camera,
                        self.cameras[added_camera]["last_active_frame"],
                    )
                    self.cameras[added_camera]["layout_frame"] = self.cameras[
                        added_camera
                    ]["last_active_frame"]
                # if removing this camera with no replacement
                else:
                    self.camera_layout[position] = None
                    self.copy_to_position(position)
                removed_cameras.remove(camera)
            # if an empty spot and there are cameras to add
            elif camera is None and len(added_cameras) > 0:
                added_camera = added_cameras.pop()
                self.camera_layout[position] = added_camera
                self.copy_to_position(
                    position,
                    added_camera,
                    self.cameras[added_camera]["last_active_frame"],
                )
                self.cameras[added_camera]["layout_frame"] = self.cameras[added_camera][
                    "last_active_frame"
                ]
            # if not an empty spot and the camera has a newer frame, copy it
            elif (
                not camera is None
                and self.cameras[camera]["last_active_frame"]
                != self.cameras[camera]["layout_frame"]
            ):
                self.copy_to_position(
                    position, camera, self.cameras[camera]["last_active_frame"]
                )
                self.cameras[camera]["layout_frame"] = self.cameras[camera][
                    "last_active_frame"
                ]

        return True

    def update(self, camera, object_count, motion_count, frame_time, frame) -> bool:

        # update the last active frame for the camera
        if self.camera_active(object_count, motion_count):
            last_active_frame = self.cameras[camera]["last_active_frame"]
            # cleanup the old frame
            if last_active_frame != 0.0:
                frame_id = f"{camera}{last_active_frame}"
                self.frame_manager.delete(frame_id)
            self.cameras[camera]["last_active_frame"] = frame_time

        now = datetime.datetime.now().timestamp()

        # limit output to 10 fps
        if (now - self.last_output_time) < 1 / 10:
            return False

        self.last_output_time = now

        return self.update_frame()


def output_frames(config: FrigateConfig, video_output_queue):
    threading.current_thread().name = f"output"
    setproctitle(f"frigate.output")

    stop_event = mp.Event()

    def receiveSignal(signalNumber, frame):
        stop_event.set()

    signal.signal(signal.SIGTERM, receiveSignal)
    signal.signal(signal.SIGINT, receiveSignal)

    frame_manager = SharedMemoryFrameManager()
    previous_frames = {}

    # start a websocket server on 8082
    WebSocketWSGIHandler.http_version = "1.1"
    websocket_server = make_server(
        "127.0.0.1",
        8082,
        server_class=WSGIServer,
        handler_class=WebSocketWSGIRequestHandler,
        app=WebSocketWSGIApplication(handler_cls=WebSocket),
    )
    websocket_server.initialize_websockets_manager()
    websocket_thread = threading.Thread(target=websocket_server.serve_forever)

    converters = {}
    broadcasters = {}

    for camera, cam_config in config.cameras.items():
        converters[camera] = FFMpegConverter(
            cam_config.frame_shape[1], cam_config.frame_shape[0], 640, 320, 8
        )
        broadcasters[camera] = BroadcastThread(
            camera, converters[camera], websocket_server
        )

    if config.birdseye.enabled:
        converters["birdseye"] = FFMpegConverter(
            config.birdseye.width,
            config.birdseye.height,
            config.birdseye.width,
            config.birdseye.height,
            config.birdseye.quality,
        )
        broadcasters["birdseye"] = BroadcastThread(
            "birdseye", converters["birdseye"], websocket_server
        )

    websocket_thread.start()

    for t in broadcasters.values():
        t.start()

    birdseye_manager = BirdsEyeFrameManager(config, frame_manager)

    while not stop_event.is_set():
        try:
            (
                camera,
                frame_time,
                current_tracked_objects,
                motion_boxes,
                regions,
            ) = video_output_queue.get(True, 10)
        except queue.Empty:
            continue

        frame_id = f"{camera}{frame_time}"

        frame = frame_manager.get(frame_id, config.cameras[camera].frame_shape_yuv)

        # send camera frame to ffmpeg process if websockets are connected
        if any(
            ws.environ["PATH_INFO"].endswith(camera) for ws in websocket_server.manager
        ):
            # write to the converter for the camera if clients are listening to the specific camera
            converters[camera].write(frame.tobytes())

        # update birdseye if websockets are connected
        if config.birdseye.enabled and any(
            ws.environ["PATH_INFO"].endswith("birdseye")
            for ws in websocket_server.manager
        ):
            if birdseye_manager.update(
                camera,
                len(current_tracked_objects),
                len(motion_boxes),
                frame_time,
                frame,
            ):
                converters["birdseye"].write(birdseye_manager.frame.tobytes())

        if camera in previous_frames:
            # if the birdseye manager still needs this frame, don't delete it
            if (
                birdseye_manager.cameras[camera]["last_active_frame"]
                != previous_frames[camera]
            ):
                frame_manager.delete(f"{camera}{previous_frames[camera]}")

        previous_frames[camera] = frame_time

    while not video_output_queue.empty():
        (
            camera,
            frame_time,
            current_tracked_objects,
            motion_boxes,
            regions,
        ) = video_output_queue.get(True, 10)

        frame_id = f"{camera}{frame_time}"
        frame = frame_manager.get(frame_id, config.cameras[camera].frame_shape_yuv)
        frame_manager.delete(frame_id)

    for c in converters.values():
        c.exit()
    for b in broadcasters.values():
        b.join()
    websocket_server.manager.close_all()
    websocket_server.manager.stop()
    websocket_server.manager.join()
    websocket_server.shutdown()
    websocket_thread.join()
    # TODO: use actual logger
    print("exiting output process...")
