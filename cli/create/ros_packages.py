"""ROS 2 package generation and updating"""

import shutil
from pathlib import Path

from . import TEMPLATES
from ..output import die as err, info
from .template import write_template


def generate_robot_pkg(
    robot: str,
    geometry_urdf: str,
    meshes_src: Path,
    links: list,
    out_dir: Path,
) -> None:
    """Generate a single robot package containing urdf/, meshes/, and config/."""
    pkg_dir = out_dir / robot
    urdf_dir = pkg_dir / "urdf"
    meshes_dir = pkg_dir / "meshes"
    config_dir = pkg_dir / "config"

    urdf_dir.mkdir(parents=True, exist_ok=True)
    meshes_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    (urdf_dir / f"{robot}.urdf").write_text(geometry_urdf)

    if meshes_src.exists():
        for item in meshes_src.iterdir():
            dest = meshes_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    tmpl = TEMPLATES / "robot"
    write_template(tmpl / "CMakeLists.txt", pkg_dir / "CMakeLists.txt", robot)
    write_template(tmpl / "package.xml", pkg_dir / "package.xml", robot)

    links_yaml = ""
    for name in sorted(links):
        links_yaml += f"        {name}:\n"
        links_yaml += "          Alpha: 1\n"
        links_yaml += "          Show Axes: false\n"
        links_yaml += "          Show Trail: false\n"
        if name != "base_link":
            links_yaml += "          Value: true\n"

    write_template(
        tmpl / "__ROBOT__.rviz",
        config_dir / f"{robot}.rviz",
        robot,
        LINKS=links_yaml,
    )

    info(f"Created {pkg_dir.relative_to(out_dir.parent)}/")


def update_robot_pkg(
    robot: str, geometry_urdf: str, generated_meshes_src: Path, out_dir: Path
) -> None:
    pkg_dir = out_dir / robot
    urdf_dir = pkg_dir / "urdf"
    meshes_dir = pkg_dir / "meshes"

    if not pkg_dir.exists():
        err(f"Package {pkg_dir} does not exist. Use 'sim create' first.")

    (urdf_dir / f"{robot}.urdf").write_text(geometry_urdf)

    if generated_meshes_src.exists():
        if meshes_dir.exists():
            shutil.rmtree(meshes_dir)
        meshes_dir.mkdir(parents=True, exist_ok=True)
        for item in generated_meshes_src.iterdir():
            dest = meshes_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    info(f"Updated {pkg_dir.relative_to(out_dir.parent)}/urdf and meshes")
