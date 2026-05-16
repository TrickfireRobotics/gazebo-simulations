"""Main CLI entry point for sim command"""

import argparse
import shutil
import sys
import threading

from .docker import build_and_launch, check_display
from .native import build_and_launch_native
from .create import create as robot_create, update as robot_update, PACKAGE_DIR, REPO_ROOT
from .create.commands import cmd_local, cmd_raw
from .auth import auth as cmd_auth
from .output import die, info
from .paths import WORKSPACE_DIR
from .drpc import rpc_start


def main() -> None:
    """Main method for sim CLI"""
    parser = argparse.ArgumentParser(
        prog="sim",
        description="TrickFire robot simulation launcher",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # --- docker ---
    docker_parser = subparsers.add_parser(
        "docker",
        help="Build and launch a robot simulation",
    )
    docker_parser.add_argument("robot", help="Robot name (e.g., arm, gripper)")
    docker_parser.add_argument(
        "--build-only",
        action="store_true",
        help="Build only, don't launch simulation",
    )
    docker_parser.add_argument(
        "--no-build",
        action="store_true",
        help="Skip build, use existing install/",
    )

    # --- native ---
    native_parser = subparsers.add_parser(
        "native",
        help="Build and launch a robot simulation using the native pixi environment",
    )
    native_parser.add_argument("robot", help="Robot name (e.g., arm, gripper)")
    native_parser.add_argument(
        "--build-only",
        action="store_true",
        help="Build only, don't launch simulation",
    )
    native_parser.add_argument(
        "--no-build",
        action="store_true",
        help="Skip build, use existing install/",
    )

    # --- clean ---
    subparsers.add_parser(
        "clean",
        help="Delete build artifacts (build/, install/, log/)",
    )

    # --- create ---
    create_parser = subparsers.add_parser(
        "create",
        help="Generate robot packages from an OnShape model",
    )
    create_parser.add_argument("robot", help="Robot name (e.g., arm, gripper)")
    create_parser.add_argument(
        "onshape_url",
        nargs="?",
        default=None,
        help="Full OnShape document URL (required unless --local is set)",
    )
    create_parser.add_argument(
        "--raw",
        action="store_true",
        help="Download raw OnShape files only, skip post-processing (for debugging)",
    )
    create_parser.add_argument(
        "--local",
        action="store_true",
        help="Generate packages from a local URDF instead of downloading from OnShape",
    )
    create_parser.add_argument(
        "--urdf", default=None, help="Path to local robot.urdf (used with --local)"
    )
    create_parser.add_argument(
        "--assets", default=None, help="Path to local assets/ directory (used with --local)"
    )
    create_parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for generated packages (default: robot-sim/)",
    )
    create_parser.add_argument(
        "--no-reduce",
        action="store_true",
        help="Skip STL mesh triangle-count reduction",
    )
    create_parser.add_argument(
        "--attach-to-world",
        dest="attach_to_world",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Fix robot to world frame (arm/fixed = yes, mobile = no; prompts if omitted)",
    )

    # --- auth ---
    subparsers.add_parser(
        "auth",
        help="Verify your SSH key can access Onshape credentials",
    )

    # --- update ---
    update_parser = subparsers.add_parser(
        "update",
        help="Update existing robot URDF and meshes from OnShape",
    )
    update_parser.add_argument("robot", help="Robot name to update (must exist in robots.json)")
    update_parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory containing packages (default: robot-sim/)",
    )
    update_parser.add_argument(
        "--no-reduce",
        action="store_true",
        help="Skip STL mesh triangle-count reduction",
    )

    args = parser.parse_args()

    try:
        if args.command == "docker":
            threading.Thread(
                target=rpc_start, kwargs={"is_docker": True, "robot_name": args.robot}, daemon=True
            ).start()
            check_display()
            build_and_launch(args.robot, build_only=args.build_only, no_build=args.no_build)
        elif args.command == "native":
            threading.Thread(
                target=rpc_start, kwargs={"is_docker": False, "robot_name": args.robot}, daemon=True
            ).start()
            build_and_launch_native(args.robot, build_only=args.build_only, no_build=args.no_build)
        elif args.command == "clean":
            for name in ("build", "install", "log"):
                path = WORKSPACE_DIR / name
                if path.exists():
                    info(f"Removing {name}/...")
                    shutil.rmtree(path)
            info("Cleaned")
        elif args.command == "create":
            if args.raw:
                cmd_raw(
                    argparse.Namespace(
                        robot_name=args.robot,
                        onshape_url=args.onshape_url,
                        output_dir=args.output_dir or str(PACKAGE_DIR / "tests"),
                    )
                )
            elif args.local:
                cmd_local(
                    argparse.Namespace(
                        robot_name=args.robot,
                        output_dir=args.output_dir or str(REPO_ROOT / "robot-sim"),
                        urdf=args.urdf,
                        assets=args.assets,
                        no_reduce=args.no_reduce,
                        attach_to_world=args.attach_to_world,
                    )
                )
            else:
                if not args.onshape_url:
                    create_parser.error("onshape_url is required unless --local or --raw is set")
                robot_create(
                    args.robot,
                    args.onshape_url,
                    output_dir=args.output_dir,
                    no_reduce=args.no_reduce,
                    attach_to_world=args.attach_to_world,
                )
        elif args.command == "auth":
            cmd_auth()
        elif args.command == "update":
            robot_update(
                args.robot,
                output_dir=args.output_dir,
                no_reduce=args.no_reduce,
            )
        else:
            parser.print_help()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:  # pylint: disable=broad-except
        die(str(e))


if __name__ == "__main__":
    main()
