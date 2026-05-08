import argparse
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

SCRIPTS = Path(__file__).parent.parent / "scripts"

COMMANDS = {
    "launch":    ("sim",       "launch.sh",  "Launch the simulator"),
    "container": ("container", "launch.sh",  "Start the dev container"),
    "attach":    ("container", "attach.sh",  "Attach to running container"),
    "sync":      ("remote",    "sync.sh",    "Sync files to remote machine"),
    "health":    ("remote",    "health.sh",  "Run health check on remote"),
}

def show_help():
    table = Table(title="sim", show_header=True, header_style="bold magenta")
    table.add_column("command", style="green", no_wrap=True)
    table.add_column("description")

    for cmd, (_, _, desc) in COMMANDS.items():
        table.add_row(cmd, desc)

    console.print(table)

def main():
    parser = argparse.ArgumentParser(prog="sim", add_help=False)
    parser.add_argument("command", nargs="?")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if not args.command:
        show_help()
        return

    if args.command not in COMMANDS:
        console.print(f"[red]Unknown command:[/red] {args.command}")
        show_help()
        return

    group, script, _ = COMMANDS[args.command]
    path = SCRIPTS / group / script
    subprocess.run([path, *args.args])
