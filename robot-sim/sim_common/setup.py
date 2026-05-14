"""Setup file for the sim_common package"""

from setuptools import setup  # type: ignore[import-untyped]

PACKAGE_NAME = "sim_common"

setup(
    name=PACKAGE_NAME,
    version="0.0.0",
    packages=[PACKAGE_NAME],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + PACKAGE_NAME]),
        ("share/" + PACKAGE_NAME, ["package.xml"]),
        ("share/" + PACKAGE_NAME + "/launch", ["launch/sim.launch.py"]),
    ],
    entry_points={
        "console_scripts": [
            "move_joints = sim_common.move_joints:main",
            "joint_gui = sim_common.joint_gui:main",
            "genesis_sim = sim_common.genesis_sim:main",
            "web_bridge = sim_common.webbridge:main"
        ],
    },
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Trickfire Robotics",
    maintainer_email="tfrbtcs@uw.edu",
    description="Shared utilities for simulation launch files",
    license="TODO",
)
