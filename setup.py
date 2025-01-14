from src import globals as g
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": [
        "PyQt6",
        "requests",
        "os",
        "sys",
        "subprocess",
        "json",
        "platform",
        "pathlib",
        "threading",
    ],
    "excludes": ["tkinter"],
    "optimize": 2,
    "include_files": [("res", "res")],
}

# No base is required for Linux
base = None

executables = [
    Executable(
        "main.py",
        base=base,
        target_name=f"cheezos_video_compressor_v{g.VERSION}",
        icon="res/icon.png",  # Remove icon or use a .png compatible with Linux, if required
    )
]

setup(
    name="CheezosVideoCompressor",
    version=g.VERSION,
    description="Compress videos to any file size.",
    options={"build_exe": build_exe_options},
    executables=executables,
)
