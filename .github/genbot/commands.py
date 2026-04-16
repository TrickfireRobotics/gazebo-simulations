"""Subcommands main logic"""

import shutil
import tempfile
from pathlib import Path

from genbot import REPO_ROOT
from genbot.log import err, info, warn
from genbot.onshape import download, parse_onshape_url
from genbot.reduce_stl import batch_process_directory
from genbot.registry import load_robots_json, save_robots_json
from genbot.ros_packages import (
    generate_bringup_pkg,
    generate_description_pkg,
    update_description_pkg,
)
from genbot.urdf import postprocess

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reduce_meshes(meshes_dir: Path, no_reduce: bool) -> None:
    """Reduce STL triangle counts in-place unless --no-reduce was passed"""
    if no_reduce:
        info("Skipping STL reduction")
        return
    if not meshes_dir.exists() or not any(meshes_dir.iterdir()):
        return
    info("Reducing STL triangle counts...")
    batch_process_directory(str(meshes_dir), str(meshes_dir))


def _scaffold_packages(robot: str, urdf_path: Path, meshes_src: Path, out_dir: Path) -> None:
    """Post-process URDF and write _description + _bringup packages"""
    if not meshes_src.exists():
        warn(f"Meshes directory {meshes_src} was not created")
    elif not any(meshes_src.iterdir()):
        warn(f"Meshes directory {meshes_src} is empty")

    info("Post-processing URDF...")
    geometry_urdf, control_xacro, joints, links = postprocess(urdf_path, robot)

    if joints:
        joint_names = [name for name, _, _ in joints]
        info(f"Found {len(joints)} revolute joint(s): {', '.join(joint_names)}")
    else:
        info("No revolute joints found")

    info("Generating description package...")
    generate_description_pkg(robot, geometry_urdf, control_xacro, meshes_src, out_dir)

    info("Generating bringup package...")
    generate_bringup_pkg(robot, joints, links, out_dir)

    info("Done!")
    info(f"Packages written to: {out_dir}")
    info(f" ├─ {robot}_description/")
    info(f" └─ {robot}_bringup/")


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_create(args) -> None:
    """Create subcommand"""
    robot = args.robot_name
    out_dir = Path(args.output_dir)

    info(f"Creating packages for robot: {robot}")

    api_url, doc_id, ws_id, el_id = parse_onshape_url(args.onshape_url)
    info(f"documentId={doc_id}  workspaceId={ws_id}  elementId={el_id}")

    workdir = download(robot, doc_id, ws_id, el_id, api_url)

    urdf_path = workdir / "robot.urdf"
    if not urdf_path.exists():
        err(
            f"Expected {urdf_path} but it was not found.\n"
            "  Check onshape-to-robot output above for errors."
        )

    _reduce_meshes(workdir / "assets", args.no_reduce)
    _scaffold_packages(robot, urdf_path, workdir / "assets", out_dir)

    # Register in robots.json
    registry = load_robots_json()
    registry = [e for e in registry if e["name"] != robot]
    registry.append({"name": robot, "url": args.onshape_url})
    save_robots_json(registry)
    info(f"Registered '{robot}' in robots.json")


def cmd_local(args) -> None:
    """Local subcommand"""
    robot = args.robot_name
    out_dir = Path(args.output_dir)
    raw_default = REPO_ROOT / ".github" / "genbot" / "tests" / robot
    urdf_path = Path(args.urdf) if args.urdf else raw_default / "robot.urdf"
    meshes_src = Path(args.assets) if args.assets else urdf_path.parent / "assets"

    if not urdf_path.exists():
        err(f"URDF file not found: {urdf_path}")

    info(f"Creating packages for robot: {robot} (local mode)")

    if not args.no_reduce and meshes_src.exists() and any(meshes_src.iterdir()):
        with tempfile.TemporaryDirectory() as tmp:
            reduced = Path(tmp) / "assets"
            shutil.copytree(meshes_src, reduced)
            _reduce_meshes(reduced, no_reduce=False)
            _scaffold_packages(robot, urdf_path, reduced, out_dir)
    else:
        if args.no_reduce:
            info("Skipping STL reduction (--no-reduce)")
        _scaffold_packages(robot, urdf_path, meshes_src, out_dir)


def cmd_raw(args) -> None:
    """Raw subcommand"""
    robot = args.robot_name
    out_dir = Path(args.output_dir)

    if args.onshape_url:
        url = args.onshape_url
    else:
        registry = load_robots_json()
        entry = next((e for e in registry if e["name"] == robot), None)
        if entry is None:
            names = ", ".join(e["name"] for e in registry) or "(none)"
            err(
                f"Robot '{robot}' not found in robots.json.\n"
                f"  Available robots: {names}\n"
                "  Pass an OnShape URL as the second argument to use it directly."
            )
        url = entry["url"]

    api_url, doc_id, ws_id, el_id = parse_onshape_url(url)
    info(f"documentId={doc_id}  workspaceId={ws_id}  elementId={el_id}")

    workdir = download(robot, doc_id, ws_id, el_id, api_url)

    dest = out_dir / robot
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(workdir, dest)

    info(f"Saved raw URDF and assets to: {dest}")
    info(f"  {dest}/robot.urdf")
    info(f"  {dest}/assets/")
    info("")
    info("Use with genbot local:")
    info(f"  python3 -m genbot local {robot} {dest}/robot.urdf --assets {dest}/assets/")


def cmd_update(args) -> None:
    """Update mode: replace only URDF and meshes in existing _description package"""
    robot = args.robot_name
    out_dir = Path(args.output_dir)

    info(f"Updating packages for robot: {robot}")

    registry = load_robots_json()
    entry = next((e for e in registry if e["name"] == robot), None)
    if entry is None:
        names = ", ".join(e["name"] for e in registry) or "(none)"
        err(
            f"Robot '{robot}' not found in robots.json.\n"
            f"  Available robots: {names}\n"
            "  Use 'create' mode to add a new robot."
        )

    api_url, doc_id, ws_id, el_id = parse_onshape_url(entry["url"])
    info(f"documentId={doc_id}  workspaceId={ws_id}  elementId={el_id}")

    workdir = download(robot, doc_id, ws_id, el_id, api_url)

    exported_urdf_path = workdir / "robot.urdf"
    exported_meshes_src = workdir / "assets"

    if not exported_urdf_path.exists():
        err(
            f"Expected {exported_urdf_path} but it was not found.\n"
            "  Check onshape-to-robot output above for errors."
        )

    if not exported_meshes_src.exists():
        warn(f"Meshes directory {exported_meshes_src} was not created")
    elif not any(exported_meshes_src.iterdir()):
        warn(f"Meshes directory {exported_meshes_src} is empty")

    _reduce_meshes(exported_meshes_src, args.no_reduce)

    info("Post-processing URDF...")
    geometry_urdf, _, _, _ = postprocess(exported_urdf_path, robot)

    info("Updating description package...")
    update_description_pkg(robot, geometry_urdf, exported_meshes_src, out_dir)

    info("Done!")
    info(f"Updated {robot}_description/urdf and meshes only.")
    info("Bringup package and control xacro were NOT modified.")
