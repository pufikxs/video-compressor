import json
import subprocess
import os
import src.globals as g
from math import ceil, floor
from PyQt6.QtCore import QThread, pyqtSignal


def get_video_length(file_path):
    cmd = [
        g.ffprobe_path,
        "-v",
        "quiet",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        file_path,
    ]

    output = subprocess.check_output(cmd)
    data = json.loads(output)

    if "format" in data:
        duration = data["format"].get("duration")
        return float(duration) if duration else 0

    return 0


def get_audio_bitrate(video_path):
    cmd = [
        g.ffprobe_path,
        "-v",
        "quiet",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=bit_rate",
        "-of",
        "json",
        video_path,
    ]

    output = subprocess.check_output(cmd)
    data = json.loads(output)

    if "streams" in data and len(data["streams"]) > 0:
        bitrate = data["streams"][0].get("bit_rate")
        return round(float(bitrate) / 1000) if bitrate else 0

    return 0


def calculate_video_bitrate(file_path, target_size_mb):
    v_len = get_video_length(file_path)
    print(f"Video duration: {v_len} seconds")
    a_rate = get_audio_bitrate(file_path)
    print(f"Audio Bitrate: {a_rate}k")
    total_bitrate = (target_size_mb * 8192.0 * 0.98) / (1.048576 * v_len) - a_rate
    return max(1, round(total_bitrate))


class CompressionThread(QThread):
    update_log = pyqtSignal(str)
    update_progress = pyqtSignal(int)
    completed = pyqtSignal()

    def __init__(self, target_size_mb, use_gpu, parent=None):
        super().__init__(parent)
        self.target_size_mb = target_size_mb
        self.use_gpu = use_gpu
        self.process = None

    def detect_gpu_encoder(self):
        try:
            cmd = [g.ffmpeg_path, "-hide_banner", "-encoders"]
            output = subprocess.check_output(cmd, universal_newlines=True)
            print(output)

            if "h264_nvenc" in output:
                return "h264_nvenc"
            elif "h264_qsv" in output:  # Intel QuickSync
                return "h264_qsv"
            elif "h264_vaapi" in output:  # AMD/Intel VAAPI
                return "h264_vaapi"
            else:
                return None

        except subprocess.CalledProcessError:
            return None

    def run_pass(self, file_path):
        video_rate = calculate_video_bitrate(file_path, self.target_size_mb)
        gpu_encoder = self.detect_gpu_encoder() if self.use_gpu else None
        file_name = os.path.basename(file_path)

        for i in range(2):
            total_steps = len(g.queue) * 2
            current_step = (len(g.completed) * 2) + i
            progress_percentage = (current_step / total_steps) * 100
            self.update_progress.emit(int(progress_percentage))
            encoder_type = (
                f"GPU ({gpu_encoder})" if self.use_gpu and gpu_encoder else "CPU"
            )
            status_msg = f"""
[Compression Status]
File: {file_name}
Queue: {len(g.completed) + 1}/{len(g.queue)}
Pass: {i + 1}/2
Target Size: {self.target_size_mb}MB
Bitrate: {video_rate}k
Encoder: {encoder_type}
"""

            bitrate_str = f"{video_rate}k"
            file_name_without_ext, original_ext = os.path.basename(file_path).rsplit(
                ".", 1
            )
            output_path = os.path.join(
                g.output_dir, f"{file_name_without_ext}-compressed.{original_ext}"
            )
            print(f"New bitrate: {bitrate_str}")
            print(status_msg)

            cmd_args = [
                g.ffmpeg_path,
                "-i", file_path,
                "-y",
                "-b:v", bitrate_str,
            ]

            if self.use_gpu and gpu_encoder:
                print("Using GPU")
                cmd_args.extend(["-c:v", gpu_encoder])
                if gpu_encoder == "h264_vaapi":
                    cmd_args.extend(["-vaapi_device", "/dev/dri/renderD128", "-vf", "format=nv12,hwupload"])
            else:
                print("Using CPU")
                cmd_args.extend(["-c:v", "libx264"])

            if i == 0:
                cmd_args.extend(["-an", "-pass", "1", "-f", "mp4", "TEMP"])
            else:
                cmd_args.extend(["-pass", "2", output_path])

            print(f"Running command: {' '.join(cmd_args)}")
            self.update_log.emit(status_msg)
            subprocess.check_call(cmd_args)

    def run(self):
        g.completed = []

        for file_path in g.queue:
            if not g.compressing:
                break

            self.run_pass(file_path)
            g.completed.append(file_path)

        msg = (
            f"Compressed {len(g.completed)} video(s)!" if g.compressing else "Aborted!"
        )

        print(msg)
        self.update_log.emit(msg)
        self.completed.emit()
