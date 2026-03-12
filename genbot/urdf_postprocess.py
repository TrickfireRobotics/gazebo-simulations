"""
URDF post-processing for onshape-to-robot output.

Handles all transformations on raw URDF: namespace injection, mesh path
rewriting, ros2_control xacro generation, and control include injection.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path


def ensure_xacro_ns(urdf_text: str) -> str:
    """Add xmlns:xacro to <robot> tag if missing."""
    if "xmlns:xacro" in urdf_text:
        return urdf_text
    return urdf_text.replace("<robot ", '<robot xmlns:xacro="http://www.ros.org/wiki/xacro" ', 1)


def inject_xacro_properties(urdf_text: str, robot_name: str) -> str:
    """Insert xacro property and arg declarations after the <robot> opening tag"""
    props = (
        "\n"
        "    <!-- XACRO -->\n"
        f'   <xacro:property name="mesh_path" value="package://{robot_name}_description/meshes"/>\n'
        '    <xacro:arg name="controller_config" default=""/>\n'
    )
    # Insert after the closing > of the <robot ...> tag
    pattern = re.compile(r"(<robot\b[^>]*>)")
    return pattern.sub(r"\1" + props, urdf_text, count=1)


def rewrite_mesh_paths(urdf_text: str) -> str:
    """Replace filename="meshes/foo.stl" with filename="${mesh_path}/foo.stl"."""
    return re.sub(
        r'filename="meshes/([^"]+)"',
        r'filename="${mesh_path}/\1"',
        urdf_text,
    )


def extract_revolute_joints(urdf_text: str) -> list:
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


def generate_control_xacro(robot_name: str, joints: list) -> str:
    """Return a complete xacro string with ros2_control block + gazebo plugin block."""
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


def inject_control_include(urdf_text: str, robot_name: str) -> str:
    """Append xacro:include for control xacro before </robot>."""
    include = (
        f'    <xacro:include filename="$(find {robot_name}_description)'
        f'/urdf/{robot_name}_control.urdf.xacro"/>\n'
    )
    return urdf_text.replace("</robot>", include + "</robot>")


def postprocess(raw_urdf_path: str | Path, robot_name: str) -> tuple:
    """Orchestrator: read raw URDF, apply all transforms.

    Returns (geometry_urdf_string, control_xacro_string, joint_list).
    joint_list items are (name, lower_limit, upper_limit).
    """
    text = Path(raw_urdf_path).read_text(encoding="utf-8")

    # Ensure xacro namespace
    text = ensure_xacro_ns(text)

    # Inject xacro properties
    text = inject_xacro_properties(text, robot_name)

    # Rewrite mesh paths
    text = rewrite_mesh_paths(text)

    # Extract joints (before any control injection)
    joints = extract_revolute_joints(text)

    # Generate control xacro
    control_xacro = generate_control_xacro(robot_name, joints)

    # Inject control include
    text = inject_control_include(text, robot_name)

    return text, control_xacro, joints
