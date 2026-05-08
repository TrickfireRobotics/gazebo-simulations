import argparse
import sys


def main():
    p = argparse.ArgumentParser(prog="sim")
    p.add_argument("cmd", nargs="?", help="Command to execute")
    args = p.parse_args()

    try:
        if args.cmd == "command1":
            # Call main from another script
            print("todo")
        elif args.cmd == "command2":
            # Call main from another script
            print("todo")
        else:
            p.print_help()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
