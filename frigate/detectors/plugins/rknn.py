import logging
import os.path
import re
import urllib.request
from typing import Literal

from pydantic import Field

from frigate.detectors.detection_api import DetectionApi
from frigate.detectors.detector_config import BaseDetectorConfig

logger = logging.getLogger(__name__)

DETECTOR_KEY = "rknn"

supported_socs = ["rk3562", "rk3566", "rk3568", "rk3588"]

supported_models = ["^default-fp16-yolonas_[sml]$"]

default_model = "default-fp16-yolonas_s"

model_chache_dir = "/config/model_cache/rknn_cache/"


class RknnDetectorConfig(BaseDetectorConfig):
    type: Literal[DETECTOR_KEY]
    num_cores: int = Field(default=0, ge=0, le=3, title="Number of NPU cores to use.")
    purge_model_cache: bool = Field(default=True)


class Rknn(DetectionApi):
    type_key = DETECTOR_KEY

    def __init__(self, config: RknnDetectorConfig):
        self.height = config.model.height
        self.width = config.model.width
        core_mask = 2**config.num_cores - 1
        soc = self.get_soc()

        if config.purge_model_cache:
            self.purge_model_cache()
        else:
            logger.warning(
                "Purging model chache is disabled. Remember to manually delete unused models from "
                + str(model_chache_dir[1:])
            )

        model_props = self.parse_model_input(config.model.path, soc)

        from rknnlite.api import RKNNLite

        self.rknn = RKNNLite(verbose=False)
        if self.rknn.load_rknn(model_props["path"]) != 0:
            logger.error("Error initializing rknn model.")
        if self.rknn.init_runtime(core_mask=core_mask) != 0:
            logger.error(
                "Error initializing rknn runtime. Do you run docker in privileged mode?"
            )

    def __del__(self):
        self.rknn.release()

    def purge_model_cache(self):
        if os.path.isdir(model_chache_dir):
            for file in os.listdir(model_chache_dir):
                if os.path.isfile(file):
                    if file.endswith("-v2.0.0-1.rknn"):
                        continue
                    else:
                        os.remove(file)

    def get_soc(self):
        try:
            with open("/proc/device-tree/compatible") as file:
                soc = file.read().split(",")[-1].strip("\x00")
        except FileNotFoundError:
            raise Exception("Make sure to run docker in privileged mode.")

        if soc not in supported_socs:
            raise Exception(
                f"Your SoC is not supported. Your SoC is: {soc}. Currently these SoCs are supported: {supported_socs}."
            )

        return soc

    def parse_model_input(self, model_path, soc):
        model_props = {}

        # find out if user provides his own model
        # user provided models should be a path and contain a "/"
        if "/" in model_path:
            model_props["preset"] = False
            model_props["path"] = model_path
        else:
            model_props["preset"] = True

            """
            Filenames follow this pattern:
            origin-quant-basename-soc-tk_version-rev.rknn
            origin: From where comes the model? default: upstream repo; rknn: modifications from airockchip
            quant: i8 or fp16
            basename: e.g. yolonas_s
            soc: e.g. rk3588
            tk_version: e.g. v2.0.0
            rev: e.g. 1

            Full name could be: default-fp16-yolonas_s-rk3588-v2.0.0-1.rknn
            """

            if any(re.match(pattern, model_path) for pattern in supported_models):
                model_props["filename"] = model_path + f"-{soc}-v2.0.0-1.rknn"

                if model_path == default_model:
                    model_path["path"] = "/models/" + model_props["filename"]
                else:
                    model_props["path"] = model_chache_dir + model_props["filename"]

                    if not os.path.isfile(model_props["path"]):
                        self.download_model(model_props["filename"])
            else:
                supported_models_str = ", ".join(
                    model[1:-1] for model in supported_models
                )
                raise Exception(
                    f"Model {model_path} is unsupported. Provide your own model or choose one of the following: {supported_models_str}"
                )

    def download_model(self, filename):
        if not os.path.isdir(model_chache_dir):
            os.mkdir(model_chache_dir)

        urllib.request.urlretrieve(
            f"https://github.com/MarcA711/rknn-models/releases/tag/v2.0.0/{filename}",
            model_chache_dir + filename,
        )

    def check_config(self, config):
        if (config.model.width != 320) or (config.model.height != 320):
            raise Exception(
                "Make sure to set the model width and height to 320 in your config.yml."
            )

        if config.model.input_pixel_format != "bgr":
            raise Exception(
                'Make sure to set the model input_pixel_format to "bgr" in your config.yml.'
            )

        if config.model.input_tensor != "nhwc":
            raise Exception(
                'Make sure to set the model input_tensor to "nhwc" in your config.yml.'
            )

    def post_process(self, output):
        pass

    def detect_raw(self, tensor_input):
        output = self.rknn.inference(
            [
                tensor_input,
            ]
        )
        return self.postprocess(output[0])
