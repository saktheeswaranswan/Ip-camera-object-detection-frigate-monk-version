import unittest
import numpy as np
from pydantic import ValidationError
from frigate.config import (
    FrigateConfig,
    DetectorTypeEnum,
)


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.minimal = {
            "mqtt": {"host": "mqtt"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }

    def test_config_class(self):
        frigate_config = FrigateConfig(**self.minimal)
        assert self.minimal == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert "cpu" in runtime_config.detectors.keys()
        assert runtime_config.detectors["cpu"].type == DetectorTypeEnum.cpu

    def test_invalid_mqtt_config(self):
        config = {
            "mqtt": {"host": "mqtt", "user": "test"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }
        self.assertRaises(ValidationError, lambda: FrigateConfig(**config))

    def test_inherit_tracked_objects(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "objects": {"track": ["person", "dog"]},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert "dog" in runtime_config.cameras["back"].objects.track

    def test_override_tracked_objects(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "objects": {"track": ["person", "dog"]},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                    "objects": {"track": ["cat"]},
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert "cat" in runtime_config.cameras["back"].objects.track

    def test_default_object_filters(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "objects": {"track": ["person", "dog"]},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert "dog" in runtime_config.cameras["back"].objects.filters

    def test_inherit_object_filters(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "objects": {
                "track": ["person", "dog"],
                "filters": {"dog": {"threshold": 0.7}},
            },
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert "dog" in runtime_config.cameras["back"].objects.filters
        assert runtime_config.cameras["back"].objects.filters["dog"].threshold == 0.7

    def test_override_object_filters(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                    "objects": {
                        "track": ["person", "dog"],
                        "filters": {"dog": {"threshold": 0.7}},
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert "dog" in runtime_config.cameras["back"].objects.filters
        assert runtime_config.cameras["back"].objects.filters["dog"].threshold == 0.7

    def test_global_object_mask(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "objects": {"track": ["person", "dog"]},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                    "objects": {
                        "mask": "0,0,1,1,0,1",
                        "filters": {"dog": {"mask": "1,1,1,1,1,1"}},
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        back_camera = runtime_config.cameras["back"]
        assert "dog" in back_camera.objects.filters
        assert len(back_camera.objects.filters["dog"].raw_mask) == 2
        assert len(back_camera.objects.filters["person"].raw_mask) == 1

    def test_default_input_args(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }

        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert "-rtsp_transport" in runtime_config.cameras["back"].ffmpeg_cmds[0]["cmd"]

    def test_ffmpeg_params_global(self):
        config = {
            "ffmpeg": {"input_args": "-re"},
            "mqtt": {"host": "mqtt"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                    "objects": {
                        "track": ["person", "dog"],
                        "filters": {"dog": {"threshold": 0.7}},
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert "-re" in runtime_config.cameras["back"].ffmpeg_cmds[0]["cmd"]

    def test_ffmpeg_params_camera(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "ffmpeg": {"input_args": ["test"]},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ],
                        "input_args": ["-re"],
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                    "objects": {
                        "track": ["person", "dog"],
                        "filters": {"dog": {"threshold": 0.7}},
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert "-re" in runtime_config.cameras["back"].ffmpeg_cmds[0]["cmd"]
        assert "test" not in runtime_config.cameras["back"].ffmpeg_cmds[0]["cmd"]

    def test_ffmpeg_params_input(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "ffmpeg": {"input_args": ["test2"]},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                                "input_args": "-re test",
                            }
                        ],
                        "input_args": "test3",
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                    "objects": {
                        "track": ["person", "dog"],
                        "filters": {"dog": {"threshold": 0.7}},
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert "-re" in runtime_config.cameras["back"].ffmpeg_cmds[0]["cmd"]
        assert "test" in runtime_config.cameras["back"].ffmpeg_cmds[0]["cmd"]
        assert "test2" not in runtime_config.cameras["back"].ffmpeg_cmds[0]["cmd"]
        assert "test3" not in runtime_config.cameras["back"].ffmpeg_cmds[0]["cmd"]

    def test_inherit_clips_retention(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "record": {
                "events": {"retain": {"default": 20, "objects": {"person": 30}}}
            },
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert (
            runtime_config.cameras["back"].record.events.retain.objects["person"] == 30
        )

    def test_roles_listed_twice_throws_error(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "record": {
                "events": {"retain": {"default": 20, "objects": {"person": 30}}}
            },
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]},
                            {"path": "rtsp://10.0.0.1:554/video2", "roles": ["detect"]},
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }
        self.assertRaises(ValidationError, lambda: FrigateConfig(**config))

    def test_zone_matching_camera_name_throws_error(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "record": {
                "events": {"retain": {"default": 20, "objects": {"person": 30}}}
            },
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                    "zones": {"back": {"coordinates": "1,1,1,1,1,1"}},
                }
            },
        }
        self.assertRaises(ValidationError, lambda: FrigateConfig(**config))

    def test_zone_assigns_color_and_contour(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "record": {
                "events": {"retain": {"default": 20, "objects": {"person": 30}}}
            },
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                    "zones": {"test": {"coordinates": "1,1,1,1,1,1"}},
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert isinstance(
            runtime_config.cameras["back"].zones["test"].contour, np.ndarray
        )
        assert runtime_config.cameras["back"].zones["test"].color != (0, 0, 0)

    def test_clips_should_default_to_global_objects(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "record": {
                "events": {"retain": {"default": 20, "objects": {"person": 30}}}
            },
            "objects": {"track": ["person", "dog"]},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {"path": "rtsp://10.0.0.1:554/video", "roles": ["detect"]}
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                    "record": {"events": {"enabled": True}},
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        back_camera = runtime_config.cameras["back"]
        assert back_camera.record.events.objects is None
        assert back_camera.record.events.retain.objects["person"] == 30

    def test_role_assigned_but_not_enabled(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect", "rtmp"],
                            },
                            {"path": "rtsp://10.0.0.1:554/record", "roles": ["record"]},
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }

        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        ffmpeg_cmds = runtime_config.cameras["back"].ffmpeg_cmds
        assert len(ffmpeg_cmds) == 1
        assert not "clips" in ffmpeg_cmds[0]["roles"]

    def test_max_disappeared_default(self):
        config = {
            "mqtt": {"host": "mqtt"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    },
                    "detect": {
                        "enabled": True,
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }

        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.cameras["back"].detect.max_disappeared == 5 * 5

    def test_motion_frame_height_wont_go_below_120(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }

        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.cameras["back"].motion.frame_height >= 120

    def test_motion_contour_area_dynamic(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }

        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert round(runtime_config.cameras["back"].motion.contour_area) == 99

    def test_merge_labelmap(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "model": {"labelmap": {7: "truck"}},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }

        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.model.merged_labelmap[7] == "truck"

    def test_default_labelmap_empty(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }

        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.model.merged_labelmap[0] == "person"

    def test_default_labelmap(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "model": {"width": 320, "height": 320},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }

        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.model.merged_labelmap[0] == "person"

    def test_fails_on_invalid_role(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect", "clips"],
                            },
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }

        self.assertRaises(ValidationError, lambda: FrigateConfig(**config))

    def test_global_detect(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "detect": {"max_disappeared": 1},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.cameras["back"].detect.max_disappeared == 1
        assert runtime_config.cameras["back"].detect.height == 1080

    def test_default_detect(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    }
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.cameras["back"].detect.max_disappeared == 25
        assert runtime_config.cameras["back"].detect.height == 720

    def test_global_detect_merge(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "detect": {"max_disappeared": 1, "height": 720},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    },
                    "detect": {
                        "height": 1080,
                        "width": 1920,
                        "fps": 5,
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.cameras["back"].detect.max_disappeared == 1
        assert runtime_config.cameras["back"].detect.height == 1080
        assert runtime_config.cameras["back"].detect.width == 1920

    def test_global_snapshots(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "snapshots": {"enabled": True},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    },
                    "snapshots": {
                        "height": 100,
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.cameras["back"].snapshots.enabled
        assert runtime_config.cameras["back"].snapshots.height == 100

    def test_default_snapshots(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    }
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.cameras["back"].snapshots.bounding_box
        assert runtime_config.cameras["back"].snapshots.quality == 70

    def test_global_snapshots_merge(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "snapshots": {"bounding_box": False, "height": 300},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    },
                    "snapshots": {
                        "height": 150,
                        "enabled": True,
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.cameras["back"].snapshots.bounding_box == False
        assert runtime_config.cameras["back"].snapshots.height == 150
        assert runtime_config.cameras["back"].snapshots.enabled
    
    def test_global_rtmp(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "rtmp": {"enabled": True},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.cameras["back"].rtmp.enabled

    def test_default_snapshots(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    }
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.cameras["back"].rtmp.enabled

    def test_global_snapshots_merge(self):

        config = {
            "mqtt": {"host": "mqtt"},
            "rtmp": {"enabled": False},
            "cameras": {
                "back": {
                    "ffmpeg": {
                        "inputs": [
                            {
                                "path": "rtsp://10.0.0.1:554/video",
                                "roles": ["detect"],
                            },
                        ]
                    },
                    "rtmp": {
                        "enabled": True,
                    },
                }
            },
        }
        frigate_config = FrigateConfig(**config)
        assert config == frigate_config.dict(exclude_unset=True)

        runtime_config = frigate_config.runtime_config
        assert runtime_config.cameras["back"].rtmp.enabled


if __name__ == "__main__":
    unittest.main(verbosity=2)
