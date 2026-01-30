#!/usr/bin/env python3
# pylint: skip-file

# --------------------------------------------------------------------------------------------
# fix_urdf.py
# --------------------------------------------------------------------------------------------
# Utility script to rewrite URDF asset paths for Gazebo compatibility
#
# This script:
#   - Reads an URDF fule
#   - Rewrites mesh/asset paths to match ROS package or Gazebo model URI formats
#   - Outputs a corrected URDF alongside the original
#   - The script does NOT modify the original file, it writes a new *_fixed.urdf file
#
# Supports:
#   - ROS package paths (package://...)
#   - Gazebo model paths (model://...) via the --use-gz-model-path flag
# --------------------------------------------------------------------------------------------

import argparse
from pathlib import Path

# Helpers ------------------------------------------------------------------------------------


def ensure_exists(path):
    if not Path(path).exists():
        print(f"File does not exist: {path}")
        raise SystemExit(1)


def line():
    print("--------------------------------------")


# Argument parsing ----------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description="Fix URDF asset paths to point into a ROS model package"
)

parser.add_argument("input_file", help="Path to the URDF file")
parser.add_argument("model_name", help="Model name inside the ROS package")

parser.add_argument(
    "-gz",
    "--use-gz-model-path",
    action="store_true",
    help="Use Gazebo-style asset paths",
)

args = parser.parse_args()

# Parameters ---------------------------------------------------------------------------------

USE_GZ_PATH = args.use_gz_model_path
ROS_MODEL_PACKAGE = "models_and_worlds"
INPUT_FILE = args.input_file
MODEL_NAME = args.model_name

OUTPUT_FILE = Path(INPUT_FILE).with_suffix("").as_posix() + "_fixed.urdf"

ensure_exists(INPUT_FILE)

line()
print("ROS model package:", ROS_MODEL_PACKAGE)
print("Model Name:", MODEL_NAME)
print("Input URDF file:", INPUT_FILE)
print("Output URDF file:", OUTPUT_FILE)
print("Use Gazebo paths:", USE_GZ_PATH)
line()

# Replace ------------------------------------------------------------------------------------

prefix = f"package://{ROS_MODEL_PACKAGE}/models/{MODEL_NAME}/"

print("Reading URDF file...")
content = Path(INPUT_FILE).read_text(encoding="UTF-8")

print("Replacing asset paths...")

if USE_GZ_PATH:
    print("Using model path...")
    prefix = f"model://{MODEL_NAME}/"
else:
    print("Using package path...")
    prefix = f"package://{ROS_MODEL_PACKAGE}/models/{MODEL_NAME}/"

new_content = content.replace('filename="assets/', f'filename="{prefix}assets/')
new_content = new_content.replace("filename='assets/", f"filename='{prefix}assets/")

print("Writing new URDF file...")
Path(OUTPUT_FILE).write_text(new_content, encoding="UTF-8")

print("Done!")
