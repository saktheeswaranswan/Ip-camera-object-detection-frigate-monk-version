import functools
import threading
import unittest
import multiprocessing as mp
from unittest.mock import MagicMock, Mock, patch
from multiprocessing.shared_memory import SharedMemory
import numpy as np
from pydantic import parse_obj_as

from frigate.config import FrigateConfig, DetectorConfig, InputTensorEnum, ModelConfig
from frigate.detectors import (
    DetectorTypeEnum,
    ObjectDetectionClient,
    ObjectDetectionWorker,
)
from frigate.majortomo import Broker
from frigate.util import deep_merge
import frigate.detectors.detector_types as detectors


test_tensor_input = np.random.randint(
    np.iinfo(np.uint8).min,
    np.iinfo(np.uint8).max,
    (1, 320, 320, 3),
    dtype=np.uint8,
)

test_detection_output = np.random.rand(20, 6).astype("f")


def create_detector(det_type):
    api = Mock()
    api.return_value.detect_raw = Mock(return_value=test_detection_output)
    return api


def start_broker(ipc_address, tcp_address, camera_names):
    detection_shms: dict[str, SharedMemory] = {}

    def detect_no_shm(worker, service_name, body):
        in_shm = detection_shms[str(service_name, "ascii")]
        tensor_input = in_shm.buf
        body = body[0:2] + [tensor_input]
        return body

    queue_broker = Broker(bind=[ipc_address, tcp_address])
    queue_broker.register_request_handler("DETECT_NO_SHM", detect_no_shm)
    queue_broker.start()

    for camera_name in camera_names:
        shm_name = camera_name
        out_shm_name = f"out-{camera_name}"
        try:
            shm = SharedMemory(name=shm_name, size=512 * 512 * 3, create=True)
        except FileExistsError:
            shm = SharedMemory(name=shm_name, create=False)
        detection_shms[shm_name] = shm
        try:
            out_shm = SharedMemory(name=out_shm_name, size=20 * 6 * 4, create=True)
        except FileExistsError:
            out_shm = SharedMemory(name=out_shm_name, create=False)
        detection_shms[out_shm_name] = out_shm

    return queue_broker, detection_shms


class WorkerTestThread(threading.Thread):
    def __init__(self, detector_name, detector_config, stop_event):
        super().__init__()
        self.detector_name = detector_name
        self.detector_config = detector_config
        self.stop_event = stop_event

    def run(self):
        worker = ObjectDetectionWorker(
            self.detector_name,
            self.detector_config,
            mp.Value("d", 0.01),
            mp.Value("d", 0.0),
            None,
            self.stop_event,
        )
        worker.connect()
        if not self.stop_event.is_set():
            client_id, request = worker.wait_for_request()
            reply = worker.handle_request(client_id, request)
            worker.send_reply_final(client_id, reply)
        worker.close()


class TestLocalObjectDetector(unittest.TestCase):
    @patch.dict(
        "frigate.detectors.detector_types.api_types",
        {det_type: create_detector(det_type) for det_type in DetectorTypeEnum},
    )
    def test_socket_client_broker_worker(self):
        detector_name = "cpu"
        ipc_address = "ipc://queue_broker.ipc"
        tcp_address = "tcp://127.0.0.1:5555"

        detector = {"type": "cpu"}
        test_cases = {
            "ipc_shm": {"cameras": ["ipc_shm"]},
            "ipc_no_shm": {"shared_memory": False, "cameras": ["ipc_no_shm"]},
            "tcp_shm": {
                "address": tcp_address,
                "shared_memory": True,
                "cameras": ["tcp_shm"],
            },
            "tcp_no_shm": {"address": tcp_address, "cameras": ["tcp_no_shm"]},
        }

        try:
            queue_broker, detection_shms = None, None
            queue_broker, detection_shms = start_broker(
                ipc_address, tcp_address, test_cases.keys()
            )

            for test_case in test_cases.keys():
                with self.subTest(test_case=test_case):
                    camera_name = test_case
                    shm_name = camera_name
                    shm = detection_shms[shm_name]
                    out_shm_name = f"out-{camera_name}"
                    out_shm = detection_shms[out_shm_name]

                    test_cfg = FrigateConfig.parse_obj(
                        {
                            "server": {
                                "mode": "detection_only",
                                "ipc": ipc_address,
                                "addresses": [tcp_address],
                            },
                            "detectors": {
                                detector_name: deep_merge(
                                    detector, test_cases[test_case]
                                )
                            },
                        }
                    )
                    config = test_cfg.runtime_config
                    detector_config = config.detectors[detector_name]
                    model_config = detector_config.model
                    stop_event = mp.Event()

                    tensor_input = np.ndarray(
                        (1, config.model.height, config.model.width, 3),
                        dtype=np.uint8,
                        buffer=shm.buf,
                    )
                    tensor_input[:] = test_tensor_input[:]
                    out_np = np.ndarray((20, 6), dtype=np.float32, buffer=out_shm.buf)

                    try:
                        client = None
                        worker = WorkerTestThread(
                            detector_name, detector_config, stop_event
                        )
                        worker.start()

                        client = ObjectDetectionClient(
                            camera_name,
                            test_cfg.model.merged_labelmap,
                            model_config,
                            config.server.ipc,
                            timeout=10,
                        )
                        client.detect(tensor_input)
                    finally:
                        stop_event.set()
                        if client is not None:
                            client.cleanup()
                        if worker is not None:
                            worker.join()

                    self.assertIsNone(
                        np.testing.assert_array_almost_equal(
                            out_np, test_detection_output
                        )
                    )
        finally:
            if queue_broker is not None:
                queue_broker.stop()
                for shm in detection_shms.values():
                    shm.close()
                    shm.unlink()

    def test_localdetectorprocess_should_only_create_specified_detector_type(self):
        for det_type in detectors.api_types:
            with self.subTest(det_type=det_type):
                with patch.dict(
                    "frigate.detectors.detector_types.api_types",
                    {
                        det_type: create_detector(det_type)
                        for det_type in DetectorTypeEnum
                    },
                ):
                    test_cfg = parse_obj_as(
                        DetectorConfig,
                        ({"type": det_type, "model": {}, "cameras": ["test"]}),
                    )
                    test_cfg.model.path = "/test/modelpath"
                    test_obj = ObjectDetectionWorker(
                        detector_name="test", detector_config=test_cfg
                    )

                    assert test_obj is not None
                    for api_key, mock_detector in detectors.api_types.items():
                        if test_cfg.type == api_key:
                            mock_detector.assert_called_once_with(test_cfg)
                        else:
                            mock_detector.assert_not_called()

    @patch.dict(
        "frigate.detectors.detector_types.api_types",
        {det_type: Mock() for det_type in DetectorTypeEnum},
    )
    def test_detect_raw_given_tensor_input_should_return_api_detect_raw_result(self):
        mock_cputfl = detectors.api_types[DetectorTypeEnum.cpu]

        TEST_DATA = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        TEST_DETECT_RESULT = np.ndarray([1, 2, 4, 8, 16, 32])
        test_obj_detect = ObjectDetectionWorker(
            detector_name="test",
            detector_config=parse_obj_as(
                DetectorConfig, {"type": "cpu", "model": {}, "cameras": ["test"]}
            ),
        )

        mock_det_api = mock_cputfl.return_value
        mock_det_api.detect_raw.return_value = TEST_DETECT_RESULT

        test_result = test_obj_detect.detect_raw(TEST_DATA)

        mock_det_api.detect_raw.assert_called_once_with(tensor_input=TEST_DATA)
        assert test_result is mock_det_api.detect_raw.return_value

    @patch.dict(
        "frigate.detectors.detector_types.api_types",
        {det_type: Mock() for det_type in DetectorTypeEnum},
    )
    def test_detect_raw_given_tensor_input_should_call_api_detect_raw_with_transposed_tensor(
        self,
    ):
        mock_cputfl = detectors.api_types[DetectorTypeEnum.cpu]

        TEST_DATA = np.zeros((1, 32, 32, 3), np.uint8)
        TEST_DETECT_RESULT = np.ndarray([1, 2, 4, 8, 16, 32])

        test_cfg = parse_obj_as(
            DetectorConfig, {"type": "cpu", "model": {}, "cameras": ["test"]}
        )
        test_cfg.model.input_tensor = InputTensorEnum.nchw

        test_obj_detect = ObjectDetectionWorker(
            detector_name="test", detector_config=test_cfg
        )

        mock_det_api = mock_cputfl.return_value
        mock_det_api.detect_raw.return_value = TEST_DETECT_RESULT

        test_result = test_obj_detect.detect_raw(TEST_DATA)

        mock_det_api.detect_raw.assert_called_once()
        assert (
            mock_det_api.detect_raw.call_args.kwargs["tensor_input"].shape
            == np.zeros((1, 3, 32, 32)).shape
        )

        assert test_result is mock_det_api.detect_raw.return_value

    @patch.dict(
        "frigate.detectors.detector_types.api_types",
        {det_type: Mock() for det_type in DetectorTypeEnum},
    )
    @patch("frigate.detectors.detection_worker.load_labels")
    def test_detect_given_tensor_input_should_return_lfiltered_detections(
        self, mock_load_labels
    ):
        mock_cputfl = detectors.api_types[DetectorTypeEnum.cpu]

        TEST_DATA = np.zeros((1, 32, 32, 3), np.uint8)
        TEST_DETECT_RAW = [
            [2, 0.9, 5, 4, 3, 2],
            [1, 0.5, 8, 7, 6, 5],
            [0, 0.4, 2, 4, 8, 16],
        ]
        TEST_DETECT_RESULT = [
            ("label-3", 0.9, (5, 4, 3, 2)),
            ("label-2", 0.5, (8, 7, 6, 5)),
        ]
        TEST_LABEL_FILE = "/test_labels.txt"
        mock_load_labels.return_value = [
            "label-1",
            "label-2",
            "label-3",
            "label-4",
            "label-5",
        ]

        test_cfg = parse_obj_as(
            DetectorConfig, {"type": "cpu", "model": {}, "cameras": ["test"]}
        )
        test_cfg.model = ModelConfig()
        test_obj_detect = ObjectDetectionWorker(
            detector_name="test",
            detector_config=test_cfg,
            labels=TEST_LABEL_FILE,
        )

        mock_load_labels.assert_called_once_with(TEST_LABEL_FILE)

        mock_det_api = mock_cputfl.return_value
        mock_det_api.detect_raw.return_value = TEST_DETECT_RAW

        test_result = test_obj_detect.detect(tensor_input=TEST_DATA, threshold=0.5)

        mock_det_api.detect_raw.assert_called_once()
        assert (
            mock_det_api.detect_raw.call_args.kwargs["tensor_input"].shape
            == np.zeros((1, 32, 32, 3)).shape
        )
        assert test_result == TEST_DETECT_RESULT
