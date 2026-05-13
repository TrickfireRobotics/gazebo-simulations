"""URDF post-processing: xacro injection, mesh path rewriting, control generation."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path


def _ensure_xacro_ns(urdf_text: str) -> str:
    if "xmlns:xacro" in urdf_text:
        return urdf_text
    return urdf_text.replace("<robot ", '<robot xmlns:xacro="http://www.ros.org/wiki/xacro" ', 1)


def _inject_xacro_properties(urdf_text: str, robot_name: str) -> str:
    props = (
        "\n"
        "  <!-- XACRO -->\n"
        f'  <xacro:property name="mesh_path" value="package://{robot_name}/meshes"/>\n'
    )
    pattern = re.compile(r"(<robot\b[^>]*>)")
    return pattern.sub(r"\1" + props, urdf_text, count=1)

def _rewrite_mesh_paths(urdf_text: str, robot_name: str) -> str:
    # Emit package:// URIs so consumers (ROS, Genesis loader) can resolve
    # meshes via ament_index regardless of where the URDF lives on disk.
    target = f"package://{robot_name}/meshes"
    # Raw onshape-to-robot form
    urdf_text = re.sub(
        r'filename="package://assets/([^"]+)"',
        rf'filename="{target}/\1"',
        urdf_text,
    )
    # Old xacro form: ${mesh_path}/...
    urdf_text = re.sub(
        r'filename="\$\{mesh_path\}/([^"]+)"',
        rf'filename="{target}/\1"',
        urdf_text,
    )
    # Old relative form: ../meshes/...
    urdf_text = re.sub(
        r'filename="\.\./meshes/([^"]+)"',
        rf'filename="{target}/\1"',
        urdf_text,
    )
    return urdf_text


def _strip_xacro_for_parsing(urdf_text: str) -> str:
    cleaned = re.sub(r"<xacro:[^>]*/?>", "", urdf_text)
    cleaned = re.sub(r"</xacro:[^>]*>", "", cleaned)
    cleaned = re.sub(r'xmlns:xacro="[^"]*"', "", cleaned)
    cleaned = re.sub(r"\$\{[^}]*\}", "", cleaned)
    return cleaned


def _extract_links(urdf_text: str) -> list:
    root = ET.fromstring(_strip_xacro_for_parsing(urdf_text))
    return [link.get("name") for link in root.findall("link") if link.get("name")]


def _extract_revolute_joints(urdf_text: str) -> list:
    root = ET.fromstring(_strip_xacro_for_parsing(urdf_text))
    joints = []
    for j in root.findall("joint"):
        if j.get("type") == "revolute" and j.get("name"):
            limit = j.find("limit")
            lower = float(limit.get("lower", "0")) if limit is not None else 0.0
            upper = float(limit.get("upper", "0")) if limit is not None else 0.0
            joints.append((j.get("name"), lower, upper))
    return joints


def _inject_world_base_link(urdf_text: str) -> str:
    snippet = (
        "\n"
        "  <!-- World base link -->\n"
        '  <link name="world"/>\n'
        "\n"
        '  <joint name="world_to_base_link" type="fixed">\n'
        '    <parent link="world"/>\n'
        '    <child link="base_link"/>\n'
        '    <origin xyz="0 0 0" rpy="0 0 0"/>\n'
        "  </joint>\n"
        "\n"
    )
    match = re.search(r"<link\b", urdf_text)
    if match:
        pos = match.start()
        return urdf_text[:pos] + snippet + urdf_text[pos:]
    return urdf_text.replace("</robot>", snippet + "</robot>", 1)


def _reindent(text: str, from_spaces: int = 2, to_spaces: int = 4) -> str:
    result = []
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip(" ")
        n = len(line) - len(stripped)
        level = round(n / from_spaces)
        result.append(" " * (level * to_spaces) + stripped)
    return "".join(result)


def postprocess(raw_urdf_path: str | Path, robot_name: str, world_base_link: bool = False) -> tuple:
    """Read raw URDF and apply all transforms.

    Returns (geometry_urdf_string, joint_list, link_list).
    joint_list items are (name, lower_limit, upper_limit).
    """
    text = Path(raw_urdf_path).read_text(encoding="utf-8")
    text = _rewrite_mesh_paths(text, robot_name)
    if world_base_link:
        text = _inject_world_base_link(text)
    links = _extract_links(text)
    joints = _extract_revolute_joints(text)
    text = _reindent(text)
    return text, joints, links
