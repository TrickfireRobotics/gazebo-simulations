# --------------------------------------------------------------------------------------------
# Base image
# --------------------------------------------------------------------------------------------
# Start from the official ROS 2 Humble base image
# This gives us:
#   - Ubuntu Jammy (22.04)
#   - ROS 2 Humble
FROM ros:humble-ros-base


# --------------------------------------------------------------------------------------------
# APT / DEBIAN CONFIGURATION
# --------------------------------------------------------------------------------------------
# Prevent apt from asking interactive questions during installs
# (for automated Docker builds)
ARG DEBIAN_FRONTEND=noninteractive


# --------------------------------------------------------------------------------------------
# SYSTEM LOCALE + TIMEZONE SETUP
# --------------------------------------------------------------------------------------------

# Install locale tools and configure UTF-8 support
# This avoids weird issues with Python, ROS, and CLI tools that expect UTF-8
RUN apt-get update && \
    apt-get install --no-install-recommends -y locales && \
    locale-gen en_US en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && \
    export LANG=en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

# Configure the system timezone
# For logs, timestamps and tools to use correct local time
ARG TZ="America/Los_Angeles"
RUN echo "${TZ}" > /etc/localtime && \
    echo "${TZ}" > /etc/timezone

# Configure keyboard layout
RUN apt-get update && \
    echo "keyboard-configuration keyboard-configuration/layoutcode string us" | debconf-set-selections && \
    echo "keyboard-configuration keyboard-configuration/modelcode string pc105" | debconf-set-selections && \
    echo "keyboard-configuration keyboard-configuration/xkb-keymap select us" | debconf-set-selections && \
    apt-get install -y --no-install-recommends keyboard-configuration console-setup && \
    rm -rf /var/lib/apt/lists/*


# --------------------------------------------------------------------------------------------
# SYSTEM / APT DEPENDENCIES
# --------------------------------------------------------------------------------------------
# Install all system-level packages needed for:
#   - Graphics (X11, OpenGL, VNC)
#   - ROS tooling
#   - Computer vision
#   - USB / CAN devices
#   - Development utilities
RUN apt-get update && apt-get install -y \
    \
    # ---------------- DISPLAY / GUI STACK ----------------
    # Virtual X server
    xvfb \
    # VNC + browser-based remote desktop support
    novnc \
    x11vnc \
    websockify \
    # Simple window manager and terminal
    openbox \
    xterm \
    # Helpers
    python3-xdg \
    \
    # ---------------- OPENGL / GRAPHICS ----------------
    # Mesa OpenGL utilities and drivers
    mesa-utils \
    libglx-mesa0 \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    # Dummy X11 server so graphical apps run without real GPU/display
    xserver-xorg-core \
    xserver-xorg-video-dummy \
    \
    # ---------------- DEVELOPMENT TOOLS ----------------
    # Git for version control
    git \
    # Python package manager
    python3-pip \
    # SSH client for GitHub / remote access
    ssh-client \
    \
    # ---------------- ROS 2 TOOLS ----------------
    # ROS bridge for websocket communication
    ros-humble-rosbridge-server \
    # rosdep installs system dependencies for ROS packages
    python3-rosdep \
    # colcon build tools for ROS workspaces
    python3-colcon-common-extensions \
    \
    # ---------------- HARDWARE / NETWORK ----------------
    # USB utilities
    usbutils \
    # CAN bus utilities
    can-utils \
    # Networking utilities
    iproute2 \
    # Kernel module tools
    kmod \
    \
    # ---------------- PYTHON ----------------
    python3-numpy \
    libboost-python-dev \
    libopencv-dev \
    python3-opencv \
    \
    # ---------------- MISC / UTILITIES ----------------
    lsb-release \
    gnupg \
    wget \
    zstd \
    && rm -rf /var/lib/apt/lists/*


# --------------------------------------------------------------------------------------------
# PYTHON DEPENDENCIES
# --------------------------------------------------------------------------------------------

# Install the moteus Python library (motor controller interface)
# https://github.com/mjbots/moteus
RUN pip3 install moteus

# Install additional Python libraries used by the project
#   - pyusb: USB device communication
#   - opencv-python: Python OpenCV bindings
RUN pip3 install pyusb opencv-python

# Update pydocstyle to avoid deprecation warnings during testing
RUN pip3 install --upgrade pydocstyle


# --------------------------------------------------------------------------------------------
# GAZEBO / SIMULATION SETUP
# --------------------------------------------------------------------------------------------

# Add the OSRF Gazebo package signing key
RUN curl https://packages.osrfoundation.org/gazebo.gpg \
    --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg

# Add the Gazebo stable repository
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] \
    https://packages.osrfoundation.org/gazebo/ubuntu-stable \
    $(lsb_release -cs) main" \
    | tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

# Install Gazebo Ignition Fortress (simulation environment)
RUN apt-get update && apt-get install -y ignition-fortress


# --------------------------------------------------------------------------------------------
# DISPLAY / VNC CONFIGURATION
# --------------------------------------------------------------------------------------------

# Expose ports for:
#   - noVNC (browser-based desktop)
#   - VNC client connections
EXPOSE 6080 5900

# Environment variables used by X11, VNC, and helper scripts
ENV DISPLAY=:1
ENV VNC_PORT=5900
ENV NOVNC_PORT=6080
ENV SCREEN_WIDTH=1280
ENV SCREEN_HEIGHT=720
ENV SCREEN_DEPTH=24

# Custom Xorg configuration for the dummy display
COPY xorg.conf /etc/X11/xorg.conf


# --------------------------------------------------------------------------------------------
# USER SETUP + SHELL CUSTOMIZATION
# --------------------------------------------------------------------------------------------

# Create a non-root user for daily development.
# Running as non-root is safer and matches real dev environments.
RUN useradd trickfire \
    --shell /bin/bash \
    --create-home \
    --no-log-init

# Copy custom bash configuration for the user
COPY .devcontainer/trickfire.bashrc /home/trickfire/.bashrc

# Allow the user to run sudo commands without a password
# (useful inside devcontainers)
RUN echo "trickfire ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user

# Fix permissions for ROS + Python tooling
#   - rosdep requires correct permissions
#   - ensure Python packages are readable
RUN rosdep fix-permissions && \
    chown -R trickfire:trickfire /usr/local/lib/python3.10/dist-packages && \
    chmod -R a+rX /usr/local/lib/python3.10/dist-packages

# Switch to the non-root user by default
USER trickfire
