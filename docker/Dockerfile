# --------------------------------------------------------------------------------------------
# Multi-stage build: Ubuntu 22.04 z(Jammy) + ROS 2 Humble + Gazebo Fortress
#
# Targets:
#   base    shared environment
#   dev     + VNC/headless display stack + dev tooling  (devcontainer, docker-compose)
# --------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------
# BASE

FROM ros:humble-ros-base AS base

ARG DEBIAN_FRONTEND=noninteractive
ARG TZ="America/Los_Angeles"

# --------------------------------------
# Locale + timezone

RUN apt-get update && \
    apt-get install --no-install-recommends -y locales && \
    locale-gen en_US en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8

RUN echo "${TZ}" > /etc/localtime && \
    echo "${TZ}" > /etc/timezone

# --------------------------------------
# Gazebo Fortress repo

RUN curl https://packages.osrfoundation.org/gazebo.gpg \
    --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] \
    https://packages.osrfoundation.org/gazebo/ubuntu-stable \
    $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/gazebo-stable.list

# --------------------------------------
# APT packages

RUN apt-get update && apt-get install -y --no-install-recommends \
    git python3-pip wget zstd \
    python3-rosdep \
    python3-colcon-common-extensions \
    ros-humble-ros-gz-sim \
    ros-humble-ros-ign-bridge \
    ros-humble-ros2-controllers \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    ignition-fortress \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository universe \
    && apt-get update && apt-get install -y --no-install-recommends \
    libgz-cmake3-dev \
    libgz-gui6 \
    libgz-plugin2-dev \
    libgz-common5-dev \
    libgz-sim7-dev \
    ros-humble-rviz2 \
    ros-humble-xacro \
    ros-humble-joint-state-publisher-gui \
    ros-humble-gz-ros2-control \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------
# Python packages

RUN pip3 install --upgrade pip setuptools

RUN rosdep init || true


# --------------------------------------------------------------------------------------------
# DEV — development environment for working on the codebase (devcontainer)

FROM base AS dev

#
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb novnc x11vnc websockify openbox xterm python3-xdg \
    mesa-utils libglx-mesa0 libgl1-mesa-glx libgl1-mesa-dri \
    xserver-xorg-core xserver-xorg-video-dummy \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------
# Dev tooling

RUN pip3 install ruff onshape-to-robot
RUN pip3 install open3d --ignore-installed blinker

EXPOSE 6080 5900
ENV VNC_PORT=5900
ENV NOVNC_PORT=6080

COPY docker/xorg.nvidia.conf /etc/X11/xorg.nvidia.conf
COPY docker/xorg.dummy.conf /etc/X11/xorg.dummy.conf

# The Jetson/Tegra libdrm.so.2 is missing drmCloseBufferHandle, which
# libdrm_nouveau.so.2 needs. Without it, swrast_dri.so fails to load and
# Mesa GLX has no FB configs. This stub provides the missing symbol so Mesa
# software rendering works inside the container.
# Sketchy solution idk what to do with this GG
# TODO: Remove this when graphics are fixed
RUN printf '#include <stdlib.h>\nint drmCloseBufferHandle(int fd, unsigned int handle){ return 0; }\n' \
    > /tmp/drm_stub.c && \
    gcc -shared -fPIC -o /usr/local/lib/libdrm_stub.so /tmp/drm_stub.c && \
    rm /tmp/drm_stub.c && \
    ldconfig

RUN curl -sSL "https://github.com/mvdan/sh/releases/latest/download/shfmt_$(curl -sSL https://api.github.com/repos/mvdan/sh/releases/latest | grep -oP '(?<="tag_name": ")v[^"]+')_linux_amd64" \
    -o /usr/local/bin/shfmt && \
    chmod +x /usr/local/bin/shfmt

RUN useradd trickfire --shell /bin/bash --create-home --no-log-init
COPY docker/shell/trickfire.bashrc /home/trickfire/.bashrc
COPY docker/shell/sim.aliases.sh /home/trickfire/.bash_aliases
RUN echo "trickfire ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user

RUN rosdep fix-permissions && \
    chown -R trickfire:trickfire /usr/local/lib/python3.10/dist-packages && \
    chmod -R a+rX /usr/local/lib/python3.10/dist-packages

USER trickfire
