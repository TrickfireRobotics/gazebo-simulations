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
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Trickfire Robotics",
    maintainer_email="tfrbtcs@uw.edu",
    description="Shared utilities for simulation launch files",
    license="TODO",
)
