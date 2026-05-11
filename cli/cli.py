"""Main CLI entry point for sim command"""

import argparse
import sys
from .paths import WORKSPACE_DIR
from .output import die


def main() -> None:
    """Main entry point for sim command"""
    parser = argparse.ArgumentParser(
        prog="sim",
        description="TrickFire robot simulation launcher",
    )
    parser.add_argument("robot", nargs="?", help="Robot name (e.g., arm, gripper)")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    subparsers.add_parser(
        "clean",
        help="Delete build artifacts (build/, install/, log/)",
    )

    args = parser.parse_args()

    try:
        if args.command == "clean":
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
        elif args.robot:
            die("Not yet implemented")
        else:
            parser.print_help()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:  # pylint: disable=broad-except
        die(str(e))


if __name__ == "__main__":
    main()
