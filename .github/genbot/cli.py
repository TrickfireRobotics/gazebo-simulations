"""Main file for genbot, holds entrypoint and argument parsing"""

import argparse

from genbot import REPO_ROOT
from genbot.commands import cmd_create, cmd_local, cmd_raw, cmd_update


def main() -> None:
    """Main method"""
    parser = argparse.ArgumentParser(
        description="Generate or update ROS2 packages from an OnShape model via onshape-to-robot."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- create ---
    create_parser = subparsers.add_parser("create", help="Create new robot packages")
    create_parser.add_argument("robot_name", help="Name for the robot (e.g. arm, rover)")
    create_parser.add_argument("onshape_url", help="Full OnShape document URL")
    create_parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "robot-sim"),
        help="Directory to write packages into (default: robot-sim/)",
    )
    create_parser.add_argument(
        "--no-reduce",
        action="store_true",
        help="Skip STL triangle-count reduction",
    )
    create_parser.add_argument(
        "--attach-to-world",
        dest="attach_to_world",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Fix robot to world (arm/fixed base = yes, mobile chassis = no). "
        "If omitted, prompts interactively.",
    )

    # --- local ---
    local_parser = subparsers.add_parser(
        "local", help="Create packages from a local URDF (no API calls)"
    )
    local_parser.add_argument("robot_name", help="Name for the robot (e.g. arm, rover)")
    local_parser.add_argument(
        "urdf",
        nargs="?",
        default=None,
        help="Path to a local URDF file (default: .github/genbot/tests/<robot_name>/robot.urdf)",
    )
    local_parser.add_argument(
        "--assets",
        default=None,
        help="Path to meshes/assets directory (default: <urdf_dir>/assets/)",
    )
    local_parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "robot-sim"),
        help="Directory to write packages into (default: robot-sim/)",
    )
    local_parser.add_argument(
        "--no-reduce",
        action="store_true",
        help="Skip STL triangle-count reduction",
    )
    local_parser.add_argument(
        "--attach-to-world",
        dest="attach_to_world",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Fix robot to world (arm/fixed base = yes, mobile chassis = no). "
        "If omitted, prompts interactively.",
    )

    # --- raw ---
    raw_parser = subparsers.add_parser(
        "raw", help="Download raw URDF and assets from onshape into a local directory"
    )
    raw_parser.add_argument("robot_name", help="Name for the robot (e.g. arm, rover)")
    raw_parser.add_argument(
        "onshape_url",
        nargs="?",
        default=None,
        help="OnShape URL (optional, looks for robot in robot.json if not passed)",
    )
    raw_parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / ".github" / "genbot" / "tests"),
        help="Directory to save raw files into (default: .github/genbot/tests/)",
    )

    # --- update ---
    update_parser = subparsers.add_parser("update", help="Update existing robot URDF and meshes")
    update_parser.add_argument(
        "robot_name", help="Name of the robot to update (must exist in robots.json)"
    )
    update_parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "robot-sim"),
        help="Directory containing packages (default: robot-sim/)",
    )
    update_parser.add_argument(
        "--no-reduce",
        action="store_true",
        help="Skip STL triangle-count reduction",
    )

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args)
    elif args.command == "local":
        cmd_local(args)
    elif args.command == "raw":
        cmd_raw(args)
    elif args.command == "update":
        cmd_update(args)
