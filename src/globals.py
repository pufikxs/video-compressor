VERSION = "3.2.0"
TITLE = f"Video Compressor"
READY_TEXT = f"Drag and Drop Videos here."
DEFAULT_SETTINGS = {"target_size": 20.0, "use_gpu": False}

ffmpeg_path = "ffmpeg"
ffprobe_path = "ffprobe"
queue = []
completed = []
root_dir = ""
bin_dir = ""
output_dir = ""
res_dir = ""
ffmpeg_installed = False
compressing = False
