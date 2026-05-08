"""Main CLI entry point for sim command"""

import argparse
import sys
from .native import command as native_command
from .paths import WORKSPACE_DIR
from .output import die


def main() -> None:
    """Main entry point for sim command"""
    parser = argparse.ArgumentParser(
        prog="sim",
        description="TrickFire robot simulation launcher",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # native command
    native_parser = subparsers.add_parser(
        "native",
        help="Launch simulation natively (macOS/Linux/WSL)",
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

    # docker command
    docker_parser = subparsers.add_parser(
        "docker",
        help="Launch simulation in Docker",
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

    # clean command
    subparsers.add_parser(
        "clean",
        help="Delete build artifacts (build/, install/, log/)",
    )

    args = parser.parse_args()

    try:
        if args.command == "native":
            native_command.build_and_launch(
                args.robot,
                build_only=args.build_only,
                no_build=args.no_build,
            )
        elif args.command == "docker":
            die("Not yet implemented")
        elif args.command == "clean":
            import shutil
            from .output import info

            if (WORKSPACE_DIR / "build").exists():
                info("Removing build/...")
                shutil.rmtree(WORKSPACE_DIR / "build")
            if (WORKSPACE_DIR / "install").exists():
                info("Removing install/...")
                shutil.rmtree(WORKSPACE_DIR / "install")
            if (WORKSPACE_DIR / "log").exists():
                info("Removing log/...")
                shutil.rmtree(WORKSPACE_DIR / "log")
            info("Cleaned")
        else:
            parser.print_help()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:  # pylint: disable=broad-except
        die(str(e))


if __name__ == "__main__":
    main()
