"""Handles inserting and maintaining ffmpeg presets."""

import logging
import os

from typing import Any

from frigate.version import VERSION
from frigate.const import BTBN_PATH
from frigate.util import vainfo_hwaccel


logger = logging.getLogger(__name__)


class LibvaGpuSelector:
    "Automatically selects the correct libva GPU."

    _selected_gpu = None

    def get_selected_gpu(self) -> str:
        """Get selected libva GPU."""
        if not os.path.exists("/dev/dri"):
            return ""

        if self._selected_gpu:
            return self._selected_gpu

        devices = list(filter(lambda d: d.startswith("render"), os.listdir("/dev/dri")))

        if len(devices) < 2:
            self._selected_gpu = "/dev/dri/renderD128"
            return self._selected_gpu

        for device in devices:
            check = vainfo_hwaccel(device_name=device)

            logger.debug(f"{device} return vainfo status code: {check.returncode}")

            if check.returncode == 0:
                self._selected_gpu = f"/dev/dri/{device}"
                return self._selected_gpu

        return ""


TIMEOUT_PARAM = "-timeout" if os.path.exists(BTBN_PATH) else "-stimeout"

_gpu_selector = LibvaGpuSelector()
_user_agent_args = [
    "-user_agent",
    f"FFmpeg Frigate/{VERSION}",
]

PRESETS_FFMPEG_HW_ACCEL = {
    "preset-rpi-32-h264": "h264_v4l2m2m",
    "preset-rpi-64-h264": "h264_v4l2m2m",
    "preset-vaapi": "h264_vaapi",
    "preset-intel-qsv-h264": "h264_qsv",  # From Sandy Bridge (gen 6)
    "preset-intel-qsv-h265": "h264_qsv",  # From Sandy Bridge (gen 6)
    "preset-nvidia-h264": "h264_nvenc",
    "preset-nvidia-h265": "h264_nvenc",
    "default": "libx264",  # SW codecs
}

PRESETS_HW_ACCEL_DECODE = {
    "preset-rpi-32-h264": ["-c:v", "h264_v4l2m2m"],
    "preset-rpi-64-h264": ["-c:v", "h264_v4l2m2m"],
    "preset-vaapi": [
        "-hwaccel_flags",
        "allow_profile_mismatch",
        "-hwaccel",
        "vaapi",
        "-hwaccel_device",
        _gpu_selector.get_selected_gpu(),
        "-hwaccel_output_format",
        "vaapi",
    ],
    "preset-intel-qsv-h264": [
        "-hwaccel",
        "qsv",
        "-qsv_device",
        _gpu_selector.get_selected_gpu(),
        "-hwaccel_output_format",
        "qsv",
        "-c:v",
        "h264_qsv",
    ],
    "preset-intel-qsv-h265": [
        "-load_plugin",
        "hevc_hw",
        "-hwaccel",
        "qsv",
        "-qsv_device",
        _gpu_selector.get_selected_gpu(),
        "-hwaccel_output_format",
        "qsv",
        "-c:v",
        "hevc_qsv",
    ],
    "preset-nvidia-h264": [
        "-hwaccel",
        "cuda",
        "-hwaccel_output_format",
        "cuda",
    ],
    "preset-nvidia-h265": [
        "-hwaccel",
        "cuda",
        "-hwaccel_output_format",
        "cuda",
    ],
    "preset-nvidia-mjpeg": [
        "-hwaccel",
        "cuda",
        "-hwaccel_output_format",
        "cuda",
    ],
}

PRESETS_HW_ACCEL_SCALE = {
    "preset-rpi-32-h264": "-r {0}{3} -s {1}x{2}",
    "preset-rpi-64-h264": "-r {0}{3} -s {1}x{2}",
    "preset-vaapi": "-r {0} -vf fps={0},{3}scale_vaapi=w={1}:h={2},hwdownload,format=yuv420p",
    "preset-intel-qsv-h264": "-r {0} -vf vpp_qsv=framerate={0}:{3}w={1}:h={2}:format=nv12,hwdownload,format=nv12,format=yuv420p",
    "preset-intel-qsv-h265": "-r {0} -vf vpp_qsv=framerate={0}:{3}w={1}:h={2}:format=nv12,hwdownload,format=nv12,format=yuv420p",
    "preset-nvidia-h264": "-r {0} -vf fps={0},{3}scale_cuda=w={1}:h={2}:format=nv12,hwdownload,format=nv12,format=yuv420p",
    "preset-nvidia-h265": "-r {0} -vf fps={0},{3}scale_cuda=w={1}:h={2}:format=nv12,hwdownload,format=nv12,format=yuv420p",
    "default": "-r {0}{3} -s {1}x{2}",
}

PRESETS_HW_ACCEL_SCALE_ROTATION = {
    "preset-rpi-32-h264": {
        "detect": " -vf transpose={0}",
        "record": " -vf transpose={0}",
    },
    "preset-rpi-64-h264": {
        "detect": " -vf transpose={0}",
        "record": " -vf transpose={0}",
    },
    "preset-vaapi": {
        "detect": "transpose_vaapi={0},",
        "record": " -vf transpose_vaapi={0}",
    },
    "preset-intel-qsv-h264": {
        "detect": "transpose={0}:",
        "record": " -vf vpp_qsv=transpose={0}",
    },
    "preset-intel-qsv-h265": {
        "detect": "transpose={0}:",
        "record": " -vf vpp_qsv=transpose={0}",
    },
    "preset-nvidia-h264": {
        "detect": "transpose={0},",
        "record": " -vf transpose={0}",
    },
    "preset-nvidia-h265": {
        "detect": "transpose={0},",
        "record": " -vf transpose={0}",
    },
    "default": {
        "detect": " -vf transpose={0}",
        "record": " -vf transpose={0}",
    },
}

PRESETS_HW_ACCEL_ENCODE = {
    "preset-rpi-32-h264": "ffmpeg -hide_banner {0} -c:v h264_v4l2m2m {1}",
    "preset-rpi-64-h264": "ffmpeg -hide_banner {0} -c:v h264_v4l2m2m {1}",
    "preset-vaapi": "ffmpeg -hide_banner -hwaccel vaapi -hwaccel_output_format vaapi -hwaccel_device {2} {0} -c:v h264_vaapi -g 50 -bf 0 -profile:v high -level:v 4.1 -sei:v 0 -an -vf format=vaapi|nv12,hwupload {1}",
    "preset-intel-qsv-h264": "ffmpeg -hide_banner {0} -c:v h264_qsv -g 50 -bf 0 -profile:v high -level:v 4.1 -async_depth:v 1 {1}",
    "preset-intel-qsv-h265": "ffmpeg -hide_banner {0} -c:v h264_qsv -g 50 -bf 0 -profile:v high -level:v 4.1 -async_depth:v 1 {1}",
    "preset-nvidia-h264": "ffmpeg -hide_banner {0} -c:v h264_nvenc -g 50 -profile:v high -level:v auto -preset:v p2 -tune:v ll {1}",
    "preset-nvidia-h265": "ffmpeg -hide_banner {0} -c:v h264_nvenc -g 50 -profile:v high -level:v auto -preset:v p2 -tune:v ll {1}",
    "default": "ffmpeg -hide_banner {0} -c:v libx264 -g 50 -profile:v high -level:v 4.1 -preset:v superfast -tune:v zerolatency {1}",
}


def parse_preset_hardware_acceleration_decode(arg: Any) -> list[str]:
    """Return the correct preset if in preset format otherwise return None."""
    if not isinstance(arg, str):
        return None

    return PRESETS_HW_ACCEL_DECODE.get(arg, None)


def _parse_rotation_scale(
    arg: Any,
    mode: str,
    rotate: int,
) -> str:
    """Return the correct rotation scale or "" if preset none is set."""
    if not isinstance(arg, str) or " " in arg:
        return ""

    if rotate == 90:
        transpose = "clock"
    elif rotate == 180:
        if arg.startswith("preset-vaapi") or arg.startswith("preset-intel-qsv"):
            transpose = "reverse"
        else:  # No 'reverse' option suported, then 2 'clocks' rotations
            transpose = "clock,transpose=clock"
    elif rotate == 270:
        transpose = "cclock"
    else:  # Rotation not need or not supported
        return ""

    return PRESETS_HW_ACCEL_SCALE_ROTATION.get(arg, "").get(mode, "").format(transpose)


def parse_preset_hardware_acceleration_scale(
    arg: Any,
    detect_args: list[str],
    fps: int,
    width: int,
    height: int,
    rotate: int,
) -> list[str]:
    """Return the correct scaling preset or default preset if none is set."""
    if not isinstance(arg, str) or " " in arg:
        scale = (
            PRESETS_HW_ACCEL_SCALE["default"].format(fps, width, height, "").split(" ")
        )
        scale.extend(detect_args)
        return scale

    transpose = _parse_rotation_scale(arg, "detect", rotate)

    scale = PRESETS_HW_ACCEL_SCALE.get(arg, "")

    if scale:
        scale = scale.format(fps, width, height, transpose).split(" ")
        scale.extend(detect_args)
        return scale
    else:
        scale = scale.format(fps, width, height, transpose).split(" ")
        scale.extend(detect_args)
        return scale


def parse_preset_hardware_acceleration_encode(arg: Any, input: str, output: str) -> str:
    """Return the correct scaling preset or default preset if none is set."""
    if not isinstance(arg, str):
        return PRESETS_HW_ACCEL_ENCODE["default"].format(input, output)

    return PRESETS_HW_ACCEL_ENCODE.get(arg, PRESETS_HW_ACCEL_ENCODE["default"]).format(
        input,
        output,
        _gpu_selector.get_selected_gpu(),
    )


PRESETS_INPUT = {
    "preset-http-jpeg-generic": _user_agent_args
    + [
        "-r",
        "{}",
        "-stream_loop",
        "-1",
        "-f",
        "image2",
        "-avoid_negative_ts",
        "make_zero",
        "-fflags",
        "nobuffer",
        "-flags",
        "low_delay",
        "-strict",
        "experimental",
        "-fflags",
        "+genpts+discardcorrupt",
        "-use_wallclock_as_timestamps",
        "1",
    ],
    "preset-http-mjpeg-generic": _user_agent_args
    + [
        "-avoid_negative_ts",
        "make_zero",
        "-fflags",
        "nobuffer",
        "-flags",
        "low_delay",
        "-strict",
        "experimental",
        "-fflags",
        "+genpts+discardcorrupt",
        "-use_wallclock_as_timestamps",
        "1",
    ],
    "preset-http-reolink": _user_agent_args
    + [
        "-avoid_negative_ts",
        "make_zero",
        "-fflags",
        "+genpts+discardcorrupt",
        "-flags",
        "low_delay",
        "-strict",
        "experimental",
        "-analyzeduration",
        "1000M",
        "-probesize",
        "1000M",
        "-rw_timeout",
        "5000000",
    ],
    "preset-rtmp-generic": [
        "-avoid_negative_ts",
        "make_zero",
        "-fflags",
        "nobuffer",
        "-flags",
        "low_delay",
        "-strict",
        "experimental",
        "-fflags",
        "+genpts+discardcorrupt",
        "-rw_timeout",
        "5000000",
        "-use_wallclock_as_timestamps",
        "1",
        "-f",
        "live_flv",
    ],
    "preset-rtsp-generic": _user_agent_args
    + [
        "-avoid_negative_ts",
        "make_zero",
        "-fflags",
        "+genpts+discardcorrupt",
        "-rtsp_transport",
        "tcp",
        TIMEOUT_PARAM,
        "5000000",
        "-use_wallclock_as_timestamps",
        "1",
    ],
    "preset-rtsp-restream": _user_agent_args
    + [
        "-rtsp_transport",
        "tcp",
        TIMEOUT_PARAM,
        "5000000",
    ],
    "preset-rtsp-restream-low-latency": _user_agent_args
    + [
        "-rtsp_transport",
        "tcp",
        TIMEOUT_PARAM,
        "5000000",
        "-fflags",
        "nobuffer",
        "-flags",
        "low_delay",
    ],
    "preset-rtsp-udp": _user_agent_args
    + [
        "-avoid_negative_ts",
        "make_zero",
        "-fflags",
        "+genpts+discardcorrupt",
        "-rtsp_transport",
        "udp",
        TIMEOUT_PARAM,
        "5000000",
        "-use_wallclock_as_timestamps",
        "1",
    ],
    "preset-rtsp-blue-iris": _user_agent_args
    + [
        "-user_agent",
        f"FFmpeg Frigate/{VERSION}",
        "-avoid_negative_ts",
        "make_zero",
        "-flags",
        "low_delay",
        "-strict",
        "experimental",
        "-fflags",
        "+genpts+discardcorrupt",
        "-rtsp_transport",
        "tcp",
        TIMEOUT_PARAM,
        "5000000",
        "-use_wallclock_as_timestamps",
        "1",
    ],
}


def parse_preset_input(arg: Any, detect_fps: int) -> list[str]:
    """Return the correct preset if in preset format otherwise return None."""
    if not isinstance(arg, str):
        return None

    if arg == "preset-http-jpeg-generic":
        input = PRESETS_INPUT[arg].copy()
        input[1] = str(detect_fps)
        return input

    return PRESETS_INPUT.get(arg, None)


PRESETS_RECORD_OUTPUT = "-f segment -segment_time 10 -segment_format mp4 -reset_timestamps 1 -strftime 1 {0} {1}"
PRESETS_RECORD_VIDEO_AUDIO = {
    "preset-record-generic": {
        "video": "-c:v copy",
        "audio": "-an",
    },
    "preset-record-generic-audio-aac": {
        "video": "-c:v copy",
        "audio": "-c:a aac",
    },
    "preset-record-generic-audio-copy": {
        "video": "-c:v copy",
        "audio": "-c:a copy",
    },
    "preset-record-mjpeg": {
        "video": "-c:v libx264",
        "audio": "-an",
    },
    "preset-record-jpeg": {
        "video": "-c:v libx264",
        "audio": "-an",
    },
    "preset-record-ubiquiti": {
        "video": "-c:v copy",
        "audio": "-ar 44100 -c:a aac",
    },
}


def parse_preset_output_record(arg: Any, hw_acc: Any, rotate: int) -> list[str]:
    """Return the correct preset if in preset format otherwise return None."""
    if not isinstance(arg, str):
        return None
    if not isinstance(hw_acc, str):
        hw_acc = "default"

    preset_record_video_audio = PRESETS_RECORD_VIDEO_AUDIO.get(arg, None)
    if not preset_record_video_audio:
        return None

    audio = preset_record_video_audio["audio"]

    video = preset_record_video_audio["video"]
    transpose = _parse_rotation_scale(hw_acc, "record", rotate)
    if transpose != "" or not "copy" in video:
        encode = PRESETS_FFMPEG_HW_ACCEL.get(hw_acc, "libx264")
        video = transpose + " -c:v " + encode

    return PRESETS_RECORD_OUTPUT.format(video, audio).split(" ")


PRESETS_RTMP_OUTPUT = {
    "preset-rtmp-generic": ["-c", "copy", "-f", "flv"],
    "preset-rtmp-mjpeg": ["-c:v", "libx264", "-an", "-f", "flv"],
    "preset-rtmp-jpeg": ["-c:v", "libx264", "-an", "-f", "flv"],
    "preset-rtmp-ubiquiti": [
        "-c:v",
        "copy",
        "-f",
        "flv",
        "-ar",
        "44100",
        "-c:a",
        "aac",
    ],
}


def parse_preset_output_rtmp(arg: Any) -> list[str]:
    """Return the correct preset if in preset format otherwise return None."""
    if not isinstance(arg, str):
        return None

    return PRESETS_RTMP_OUTPUT.get(arg, None)
