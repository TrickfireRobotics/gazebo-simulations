# ---------------------------------------------------------------------------- #
#                                     BASE                                     #
# ---------------------------------------------------------------------------- #

FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG TZ="America/Los_Angeles"

RUN echo "------------------- BASE -------------------"

# Locale + timezone
RUN apt-get update && \
    apt-get install --no-install-recommends -y locales curl gcc libc6-dev sudo && \
    locale-gen en_US en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8

RUN ln -snf "/usr/share/zoneinfo/${TZ}" /etc/localtime && \
    echo "${TZ}" > /etc/timezone

# VNC / headless display stack
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb novnc x11vnc websockify openbox xterm python3-xdg x11-utils \
    mesa-utils libglx-mesa0 libgl1-mesa-dri \
    xserver-xorg-core xserver-xorg-video-dummy \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 6080 5900
ENV VNC_PORT=5900
ENV NOVNC_PORT=6080

COPY docker/xorg.nvidia.conf /etc/X11/xorg.nvidia.conf
COPY docker/xorg.dummy.conf /etc/X11/xorg.dummy.conf

# The Jetson/Tegra libdrm.so.2 is missing drmCloseBufferHandle, which
# libdrm_nouveau.so.2 needs. Without it, swrast_dri.so fails to load and
# Mesa GLX has no FB configs. This stub provides the missing symbol so Mesa
# software rendering works inside the container.
# Sketchy solution idk what to do with this...
# TODO: Remove this when graphics are fixed
RUN printf 'int drmCloseBufferHandle(int fd, unsigned int handle){ return 0; }\n' \
    > /tmp/drm_stub.c && \
    gcc -shared -fPIC -o /usr/local/lib/libdrm_stub.so /tmp/drm_stub.c && \
    rm /tmp/drm_stub.c && \
    ldconfig

# User
RUN userdel ubuntu 2>/dev/null || true && \
    useradd trickfire --uid 1000 --shell /bin/bash --create-home --no-log-init && \
    usermod -aG video trickfire
RUN echo "trickfire ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user

COPY docker/bashrc.sh /home/trickfire/.bashrc

# ---------------------------------------------------------------------------- #
#                                    GAZEBO                                    #
# ---------------------------------------------------------------------------- #

RUN echo "------------------ GAZEBO ------------------"

# ROS 2 Jazzy apt source
RUN apt-get update && apt-get install -q -y --no-install-recommends \
    ca-certificates dirmngr gnupg2 \
    && rm -rf /var/lib/apt/lists/*
RUN curl -L -s -f -o /tmp/ros2-apt-source.deb \
    https://github.com/ros-infrastructure/ros-apt-source/releases/download/1.2.0/ros2-apt-source_1.2.0.noble_all.deb && \
    echo "0804d9b13db770eb87019be414cd78378835228ad5fa801fc88758596dd8f7e5 */tmp/ros2-apt-source.deb" | sha256sum --strict --check && \
    apt-get update && apt-get install /tmp/ros2-apt-source.deb && \
    rm -f /tmp/ros2-apt-source.deb && \
    rm -rf /var/lib/apt/lists/*

# Gazebo Harmonic apt source
RUN curl https://packages.osrfoundation.org/gazebo.gpg \
    --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable noble main" \
    > /etc/apt/sources.list.d/gazebo-stable.list

# apt packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake \
    git python3-pip python3.12-venv wget zstd \
    python3-rosdep \
    python3-colcon-common-extensions \
    ros-jazzy-ros-base \
    ros-jazzy-ros-gz \
    ros-jazzy-ros2-controllers \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    gz-harmonic \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository universe \
    && apt-get update && apt-get install -y --no-install-recommends \
    libgz-cmake4-dev \
    libgz-gui8 \
    libgz-plugin3-dev \
    libgz-common6-dev \
    libgz-sim8-dev \
    ros-jazzy-rviz2 \
    ros-jazzy-xacro \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-gz-ros2-control \
    && rm -rf /var/lib/apt/lists/*

# python packages
RUN pip3 install --break-system-packages pypresence
RUN rosdep init || true

RUN rosdep fix-permissions && \
    chown -R trickfire:trickfire /usr/local/lib/python3.12/dist-packages /usr/local/bin && \
    chmod -R a+rX /usr/local/lib/python3.12/dist-packages

# ---------------------------------------------------------------------------- #
#                                    CHRONO                                    #
# ---------------------------------------------------------------------------- #

RUN echo "------------------ CHRONO ------------------"
RUN echo "todo - implement"

# ---------------------------------------------------------------------------- #
#                                 DEVCONTAINER                                 #
# ---------------------------------------------------------------------------- #

RUN echo "--------------- DEVCONTAINER ---------------"

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server

RUN pip3 install ruff --break-system-packages

RUN curl -sSL "https://github.com/mvdan/sh/releases/latest/download/shfmt_$(curl -sSL https://api.github.com/repos/mvdan/sh/releases/latest | grep -oP '(?<="tag_name": ")v[^"]+')_linux_amd64" \
    -o /usr/local/bin/shfmt && \
    chmod +x /usr/local/bin/shfmt

USER trickfire
