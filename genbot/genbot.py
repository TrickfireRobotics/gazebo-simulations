#!/usr/bin/env python3

"""genbot - generate and update ROS2 packages from an OnShape URDF"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NoReturn

TEMPLATES = Path(__file__).parent / "templates"
REPO_ROOT = Path(__file__).parent.parent
ROBOTS_JSON = REPO_ROOT / "robots.json"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def info(msg: str) -> None:
    """Info log"""
    print(f"[genbot] {msg}")


def err(msg: str) -> NoReturn:
    """Error log, sys exits with 1"""
    print(f"[genbot] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------


def render(template_path: Path, robot: str, **extras) -> str:
    """Read a template and substitute __ROBOT__ (and any extras) into it"""
    text = template_path.read_text()
    text = text.replace("__ROBOT__", robot)
    for key, value in extras.items():
        text = text.replace(f"__{key}__", value)
    return text


def write_template(src: Path, dest: Path, robot: str, **extras) -> None:
    """Writes a template file"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(src, robot, **extras))


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


def get_credentials() -> dict:
    """Read ONSHAPE_API_KEY / ONSHAPE_API_SECRET from environment variables"""
    key = os.environ.get("ONSHAPE_API_KEY")
    secret = os.environ.get("ONSHAPE_API_SECRET")

    if not key or not secret:
        err(
            "OnShape credentials not found.\n"
            "  Set ONSHAPE_API_KEY and ONSHAPE_API_SECRET environment variables."
        )

    return {"key": key, "secret": secret}


# ---------------------------------------------------------------------------
# URL parsing
# ---------------------------------------------------------------------------

_ONSHAPE_URL_RE = re.compile(
    r"documents/([0-9a-f]+)/[wv]/([0-9a-f]+)/e/([0-9a-f]+)",
    re.IGNORECASE,
)


def parse_onshape_url(url: str) -> tuple:
    """Return (documentId, workspaceId, elementId) from an OnShape URL"""
    m = _ONSHAPE_URL_RE.search(url)
    if not m:
        err(
            f"Could not parse OnShape URL: {url}\n"
            "  Expected format: https://cad.onshape.com/documents/<docId>/w/<wsId>/e/<elId>"
        )
    return m.group(1), m.group(2), m.group(3)


# ---------------------------------------------------------------------------
# robots.json registry
# ---------------------------------------------------------------------------


def load_robots_json() -> dict:
    """Load the robot registry"""
    if not ROBOTS_JSON.exists():
        return {}
    return json.loads(ROBOTS_JSON.read_text())


def save_robots_json(data: dict) -> None:
    """Write the robot registry"""
    ROBOTS_JSON.write_text(json.dumps(data, indent=2) + "\n")


# ---------------------------------------------------------------------------
# onshape-to-robot runner
# ---------------------------------------------------------------------------


def run_onshape_to_robot(doc_id: str, ws_id: str, el_id: str, creds: dict, workdir: Path) -> None:
    """Write config.json and invoke onshape-to-robot in workdir"""
    config = {
        "documentId": doc_id,
        "workspaceId": ws_id,
        "elementId": el_id,
    }
    (workdir / "config.json").write_text(json.dumps(config, indent=2))

    env = os.environ.copy()
    env["ONSHAPE_API_KEY"] = creds["key"]
    env["ONSHAPE_API_SECRET"] = creds["secret"]

    result = subprocess.run(
        ["onshape-to-robot", "."],
        cwd=workdir,
        env=env,
        check=True,
    )
    if result.returncode != 0:
        err(f"onshape-to-robot exited with code {result.returncode}")


# ---------------------------------------------------------------------------
# URDF post-processing
# ---------------------------------------------------------------------------


def _ensure_xacro_ns(urdf_text: str) -> str:
    """Add xmlns:xacro to <robot> tag if missing"""
    if "xmlns:xacro" in urdf_text:
        return urdf_text
    return urdf_text.replace("<robot ", '<robot xmlns:xacro="http://www.ros.org/wiki/xacro" ', 1)


def _inject_xacro_properties(urdf_text: str, robot_name: str) -> str:
    """Insert xacro property and arg declarations after the <robot> opening tag"""
    props = (
        "\n"
        "    <!-- XACRO -->\n"
        f'   <xacro:property name="mesh_path" value="package://{robot_name}_description/meshes"/>\n'
        '    <xacro:arg name="controller_config" default=""/>\n'
    )
    pattern = re.compile(r"(<robot\b[^>]*>)")
    return pattern.sub(r"\1" + props, urdf_text, count=1)


def _rewrite_mesh_paths(urdf_text: str) -> str:
    """Replace filename="meshes/foo.stl" with filename="${mesh_path}/foo.stl" """
    return re.sub(
        r'filename="meshes/([^"]+)"',
        r'filename="${mesh_path}/\1"',
        urdf_text,
    )


def _extract_revolute_joints(urdf_text: str) -> list:
    """
    Parse and return list of (name, lower_limit, upper_limit) for all revolute joints.
    Uses ElementTree on a cleaned copy (xacro tags stripped).
    """
    cleaned = re.sub(r"<xacro:[^>]*/?>", "", urdf_text)
    cleaned = re.sub(r"</xacro:[^>]*>", "", cleaned)
    cleaned = re.sub(r'xmlns:xacro="[^"]*"', "", cleaned)
    cleaned = re.sub(r"\$\{[^}]*\}", "", cleaned)

    root = ET.fromstring(cleaned)
    joints = []
    for j in root.findall("joint"):
        if j.get("type") == "revolute" and j.get("name"):
            limit = j.find("limit")
            lower = float(limit.get("lower", "0")) if limit is not None else 0.0
            upper = float(limit.get("upper", "0")) if limit is not None else 0.0
            joints.append((j.get("name"), lower, upper))
    return joints


def _generate_control_xacro(robot_name: str, joints: list) -> str:
    """Return a complete xacro string with ros2_control block + gazebo plugin block"""
    lines = [
        '<?xml version="1.0" ?>',
        f'<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="{robot_name}_control">',
        "",
        "    <!-- ros2_control hardware interface -->",
        '    <ros2_control name="GazeboSimSystem" type="system">',
        "        <hardware>",
        "            <plugin>gz_ros2_control/GazeboSimSystem</plugin>",
        "        </hardware>",
    ]

    for name, lower, upper in joints:
        lines += [
            "",
            f'        <joint name="{name}">',
            '            <command_interface name="position">',
            f'                <param name="min">{lower:.2f}</param>',
            f'                <param name="max">{upper:.2f}</param>',
            "            </command_interface>",
            "",
            '            <state_interface name="position">',
            '                <param name="initial_value">1.0</param>',
            "            </state_interface>",
            '            <state_interface name="velocity"/>',
            '            <state_interface name="effort"/>',
            "        </joint>",
        ]

    lines += [
        "    </ros2_control>",
        "",
        "    <gazebo>",
        "        <!-- JOINT CONTROLLER -->",
        '        <plugin filename="libgz_ros2_control-system.so" name="gz_ros2_control::GazeboSimROS2ControlPlugin">',
        "            <robot_param>robot_description</robot_param>",
        "            <robot_param_node>robot_state_publisher</robot_param_node>",
        "            <parameters>$(arg controller_config)</parameters>",
        "            <update_rate>60</update_rate>",
        "        </plugin>",
        "    </gazebo>",
        "</robot>",
        "",
    ]

    return "\n".join(lines)


def _inject_control_include(urdf_text: str, robot_name: str) -> str:
    """Append xacro:include for control xacro before </robot>"""
    include = (
        f'    <xacro:include filename="$(find {robot_name}_description)'
        f'/urdf/{robot_name}_control.urdf.xacro"/>\n'
    )
    return urdf_text.replace("</robot>", include + "</robot>")


def postprocess(raw_urdf_path: str | Path, robot_name: str) -> tuple:
    """Read raw URDF, apply all transforms.

    Returns (geometry_urdf_string, control_xacro_string, joint_list).
    joint_list items are (name, lower_limit, upper_limit).
    """
    text = Path(raw_urdf_path).read_text(encoding="utf-8")
    text = _ensure_xacro_ns(text)
    text = _inject_xacro_properties(text, robot_name)
    text = _rewrite_mesh_paths(text)
    joints = _extract_revolute_joints(text)
    control_xacro = _generate_control_xacro(robot_name, joints)
    text = _inject_control_include(text, robot_name)
    return text, control_xacro, joints


# ---------------------------------------------------------------------------
# Package generators
# ---------------------------------------------------------------------------


def generate_description_pkg(
    robot: str,
    geometry_urdf: str,
    control_xacro: str,
    meshes_src: Path,
    out_dir: Path,
) -> None:
    """Create <robot>_description package"""
    pkg_dir = out_dir / f"{robot}_description"
    urdf_dir = pkg_dir / "urdf"
    meshes_dir = pkg_dir / "meshes"

    urdf_dir.mkdir(parents=True, exist_ok=True)
    meshes_dir.mkdir(parents=True, exist_ok=True)

    # Write processed URDF
    (urdf_dir / f"{robot}.urdf").write_text(geometry_urdf)

    # Write control xacro
    (urdf_dir / f"{robot}_control.urdf.xacro").write_text(control_xacro)

    # Copy meshes
    if meshes_src.exists():
        for item in meshes_src.iterdir():
            dest = meshes_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    tmpl = TEMPLATES / "description"
    write_template(tmpl / "CMakeLists.txt", pkg_dir / "CMakeLists.txt", robot)
    write_template(tmpl / "package.xml", pkg_dir / "package.xml", robot)

    info(f"Created {pkg_dir.relative_to(out_dir.parent)}")


def generate_bringup_pkg(robot: str, joints: list, out_dir: Path) -> None:
    """Create <robot>_bringup package"""
    pkg_dir = out_dir / f"{robot}_bringup"

    tmpl = TEMPLATES / "bringup"

    write_template(tmpl / "CMakeLists.txt", pkg_dir / "CMakeLists.txt", robot)
    write_template(tmpl / "package.xml", pkg_dir / "package.xml", robot)

    if joints:
        joints_yaml = "".join(f"      - {name}\n" for name, _, _ in joints)
    else:
        joints_yaml = "      # no revolute joints found — fill in manually\n"

    write_template(
        tmpl / "config" / "controller.yaml",
        pkg_dir / "config" / f"{robot}.controller.yaml",
        robot,
        JOINTS=joints_yaml,
    )

    write_template(tmpl / "launch" / "sim.launch.py", pkg_dir / "launch" / "sim.launch.py", robot)

    info(f"Created {pkg_dir.relative_to(out_dir.parent)}")


def update_description_pkg(robot: str, geometry_urdf: str, meshes_src: Path, out_dir: Path) -> None:
    """Update only the URDF and meshes in an existing <robot>_description package"""
    pkg_dir = out_dir / f"{robot}_description"
    urdf_dir = pkg_dir / "urdf"
    meshes_dir = pkg_dir / "meshes"

    if not pkg_dir.exists():
        err(f"Package {pkg_dir} does not exist. Use 'create' mode first.")

    # Replace URDF (but NOT the control xacro)
    (urdf_dir / f"{robot}.urdf").write_text(geometry_urdf)

    # Replace meshes
    if meshes_src.exists():
        if meshes_dir.exists():
            shutil.rmtree(meshes_dir)
        meshes_dir.mkdir(parents=True, exist_ok=True)
        for item in meshes_src.iterdir():
            dest = meshes_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    info(f"Updated {pkg_dir.relative_to(out_dir.parent)}/urdf and meshes")


# ---------------------------------------------------------------------------
# Download helper
# ---------------------------------------------------------------------------


def download(doc_id: str, ws_id: str, el_id: str) -> Path:
    """Run onshape-to-robot and return the working directory"""
    creds = get_credentials()
    workdir = Path(tempfile.mkdtemp(prefix="genbot_"))
    info("Running onshape-to-robot (this may take a while)...")
    run_onshape_to_robot(doc_id, ws_id, el_id, creds, workdir)
    return workdir


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_create(args) -> None:
    """Create mode: full scaffold of _description + _bringup packages"""
    robot = args.robot_name
    out_dir = Path(args.output_dir)

    info(f"Creating packages for robot: {robot}")

    if not args.onshape_url:
        err("OnShape URL is required for 'create' mode.")

    doc_id, ws_id, el_id = parse_onshape_url(args.onshape_url)
    info(f"documentId={doc_id}  workspaceId={ws_id}  elementId={el_id}")

    workdir = download(doc_id, ws_id, el_id)

    urdf_path = workdir / "robot.urdf"
    meshes_src = workdir / "meshes"

    if not urdf_path.exists():
        err(
            f"Expected {urdf_path} but it was not found.\n"
            "  Check onshape-to-robot output above for errors."
        )

    info("Post-processing URDF...")
    geometry_urdf, control_xacro, joints = postprocess(urdf_path, robot)

    if joints:
        joint_names = [name for name, _, _ in joints]
        info(f"Found {len(joints)} revolute joint(s): {', '.join(joint_names)}")
    else:
        info("No revolute joints found — controller YAML will have a placeholder.")

    info("Generating description package...")
    generate_description_pkg(robot, geometry_urdf, control_xacro, meshes_src, out_dir)

    info("Generating bringup package...")
    generate_bringup_pkg(robot, joints, out_dir)

    # Register in robots.json
    registry = load_robots_json()
    registry[robot] = {
        "documentId": doc_id,
        "workspaceId": ws_id,
        "elementId": el_id,
        "onshapeUrl": args.onshape_url,
    }
    save_robots_json(registry)
    info(f"Registered '{robot}' in robots.json")

    info("Done!")
    info(f"Packages written to: {out_dir}")
    info(f"  {robot}_description/")
    info(f"  {robot}_bringup/")


def cmd_update(args) -> None:
    """Update mode: replace only URDF and meshes in existing _description package"""
    robot = args.robot_name
    out_dir = Path(args.output_dir)

    info(f"Updating packages for robot: {robot}")

    registry = load_robots_json()
    if robot not in registry:
        err(
            f"Robot '{robot}' not found in robots.json.\n"
            f"  Available robots: {', '.join(registry.keys()) or '(none)'}\n"
            "  Use 'create' mode to add a new robot."
        )

    entry = registry[robot]
    doc_id = entry["documentId"]
    ws_id = entry["workspaceId"]
    el_id = entry["elementId"]
    info(f"documentId={doc_id}  workspaceId={ws_id}  elementId={el_id}")

    workdir = download(doc_id, ws_id, el_id)

    urdf_path = workdir / "robot.urdf"
    meshes_src = workdir / "meshes"

    if not urdf_path.exists():
        err(
            f"Expected {urdf_path} but it was not found.\n"
            "  Check onshape-to-robot output above for errors."
        )

    info("Post-processing URDF...")
    geometry_urdf, _, _ = postprocess(urdf_path, robot)

    info("Updating description package...")
    update_description_pkg(robot, geometry_urdf, meshes_src, out_dir)

    info("Done!")
    info(f"Updated {robot}_description/urdf and meshes only.")
    info("Bringup package and control xacro were NOT modified.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


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

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args)
    elif args.command == "update":
        cmd_update(args)


if __name__ == "__main__":
    main()
