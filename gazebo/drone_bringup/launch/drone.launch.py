"""
Launch script for the ArduPilot SITL + Gazebo drone simulation.

Unlike the URDF/ros2_control robots (arm, chassis), the quadcopter is an SDF
model embedded directly in the world file (see drone_description) and is
flown by ArduCopter SITL, not ROS 2 controllers - there's no robot_state_publisher,
controller spawners, or RViz here.
"""

import os
import socket
import struct

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from sim_common.launch_utils import err, gazebo_launch_actions, get_asset

# UW campus, arbitrary - override by editing --home below for a real flying field.
SITL_HOME = "47.6521,-122.3037,0.0,0"


def _default_gateway() -> str:
    """The default gateway of *this* container's actual network namespace.

    Docker's `extra_hosts: host.docker.internal:host-gateway` isn't reliably
    scoped to whichever network a compose-created container lands on - it
    can resolve to a different bridge's gateway than the one this container
    is actually attached to. Reading /proc/net/route is the ground truth.
    """
    with open("/proc/net/route") as f:
        for line in f.readlines()[1:]:
            fields = line.split()
            if fields[1] == "00000000":  # destination 0.0.0.0 = default route
                return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
    err("Could not determine default gateway from /proc/net/route")


def generate_launch_description():
    """ROS launch method, must have this name"""

    world_file = get_asset("drone_description", "worlds", "drone.world.sdf")
    gz_gui_config = get_asset("sim_worlds", "gui", "gui.config")

    arducopter_bin = os.environ.get("ARDUCOPTER_BIN")
    if not arducopter_bin or not os.path.isfile(arducopter_bin):
        err(
            "ARDUCOPTER_BIN not set or missing - ArduPilot SITL is not built.\n"
            "        Run: sim gazebo setup-drone"
        )

    # ------------------------------------------------
    # ArduCopter SITL
    # ------------------------------------------------
    # --model JSON talks to the ardupilot_gazebo plugin's JSON backend on the
    # model's configured fdm ports. ArduPilot's serial-device parser has no
    # listening/server UDP mode - only udpclient: (see AP_HAL_SITL/UARTDriver.cpp) -
    # so SITL sends telemetry out to the GCS's address instead of waiting for
    # one. That parser also uses the legacy inet_addr() to turn the address
    # into a sockaddr, which cannot resolve hostnames, so a plain IP is
    # required - QGroundControl runs on the host, reachable at this
    # container's default gateway.
    gcs_host = _default_gateway()
    sitl = ExecuteProcess(
        cmd=[
            arducopter_bin,
            "--model", "JSON",
            "--home", SITL_HOME,
            "--speedup", "1",
            "-I0",
            f"--serial0=udpclient:{gcs_host}:14550",
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            *gazebo_launch_actions(world_file, gz_gui_config, combined_gui=True),
            DeclareLaunchArgument("gui", default_value="true", description="Open Gazebo GUI."),
            # SITL's JSON backend retries aggressively (and noisily) until the Gazebo
            # plugin is up, which competes for CPU with the GUI's mesh import right
            # when it needs it most. Give Gazebo (server + GUI + meshes) a real head
            # start before SITL starts hammering it.
            TimerAction(period=15.0, actions=[sitl]),
        ]
    )
