from setuptools import setup

package_name = "sim_common"

setup(
    name=package_name,
    version="0.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Trickfire Robotics",
    maintainer_email="tfrbtcs@uw.edu",
    description="Shared utilities for simulation launch files",
    license="TODO",
)
