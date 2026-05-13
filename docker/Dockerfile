FROM ros:humble-ros-base AS runtime

ARG DEBIAN_FRONTEND=noninteractive
ARG TZ="America/Los_Angeles"

# Locale + timezone
RUN apt-get update && \
    apt-get install --no-install-recommends -y locales && \
    locale-gen en_US en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8

RUN ln -snf "/usr/share/zoneinfo/${TZ}" /etc/localtime && \
    echo "${TZ}" > /etc/timezone

# APT packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git openssh-client python3-pip python3.10-venv wget zstd \
    python3-rosdep \
    python3-colcon-common-extensions \
    ros-humble-ros2-controllers \
    ros-humble-robot-state-publisher \
    ros-humble-xacro \
    ros-humble-rosbridge-suite \
    ros-humble-joint-state-publisher \
    ros-humble-rviz2 \
    python3-tk \
    age \
    && rm -rf /var/lib/apt/lists/*

# VNC / headless display stack
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb novnc x11vnc websockify openbox xterm python3-xdg x11-utils \
    mesa-utils libglx-mesa0 libgl1-mesa-glx libgl1-mesa-dri \
    xserver-xorg-core xserver-xorg-video-dummy \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 6080 5900
ENV VNC_PORT=5900
ENV NOVNC_PORT=6080

COPY docker/xorg.nvidia.conf /etc/X11/xorg.nvidia.conf
COPY docker/xorg.dummy.conf /etc/X11/xorg.dummy.conf

# Python packages
RUN pip3 install --no-cache-dir --upgrade pip "setuptools<66.0.0"
RUN pip3 install --no-cache-dir genesis-world
RUN rosdep init || true

# User
RUN useradd trickfire --shell /bin/bash --create-home --no-log-init && \
    usermod -aG video trickfire

COPY docker/container.bashrc /home/trickfire/.bashrc

RUN echo "trickfire ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user
RUN rosdep fix-permissions && \
    chown -R trickfire:trickfire /usr/local/lib/python3.10/dist-packages && \
    chmod -R a+rX /usr/local/lib/python3.10/dist-packages
RUN mkdir -p /home/trickfire/gazebo-simulations && \
    chown trickfire:trickfire /home/trickfire/gazebo-simulations

USER trickfire
WORKDIR /home/trickfire/gazebo-simulations


# Dev image

FROM runtime AS dev
USER root

RUN pip3 install --no-cache-dir ruff
RUN curl -sSL "https://github.com/mvdan/sh/releases/latest/download/shfmt_$(curl -sSL https://api.github.com/repos/mvdan/sh/releases/latest | grep -oP '(?<="tag_name": ")v[^"]+')_linux_amd64" \
    -o /usr/local/bin/shfmt && \
    chmod +x /usr/local/bin/shfmt

USER trickfire
