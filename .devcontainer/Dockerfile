# Force amd64 image so macOS (ARM) doesn’t pull the ARM variant
# Required because ZED SDK and other x86_64-only tools fail on ARM images
FROM ros:humble-ros-base

# Enable non-interactive mode.
ARG DEBIAN_FRONTEND=noninteractive

# ------------------------ SYSTEM SETUP  ------------------------

# Set locale.
RUN apt-get update && \
    apt-get install --no-install-recommends -y locales && \
    locale-gen en_US en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && \
    export LANG=en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

# Set the timezone and keyboard layout.
ARG TZ="America/Los_Angeles"
RUN echo "${TZ}" > /etc/localtime && \
    echo "${TZ}" > /etc/timezone

RUN apt-get update && \
    echo "keyboard-configuration keyboard-configuration/layoutcode string us" | debconf-set-selections && \
    echo "keyboard-configuration keyboard-configuration/modelcode string pc105" | debconf-set-selections && \
    echo "keyboard-configuration keyboard-configuration/xkb-keymap select us" | debconf-set-selections && \
    apt-get install -y --no-install-recommends keyboard-configuration console-setup && \
    rm -rf /var/lib/apt/lists/*

# ------------------------ APT DEPENDENCIES ------------------------

RUN apt-get update && apt-get install -y \
    zstd \
    # To use git in the container
    git \
    # pip is a package manager for Python
    python3-pip \
    # To let us sync with GitHub over SSH
    ssh-client \
    ros-humble-rosbridge-server \
    # To use rosdep for installing system dependencies
    python3-rosdep \
    python3-colcon-common-extensions \
    # Install usb utilities
    usbutils \
    can-utils \
    iproute2 \
    kmod \
    # Used for cv_bridge
    python3-numpy \
    libboost-python-dev \
    # OpenCV
    libopencv-dev \
    python3-opencv \
    # Clean out the apt lists after `apt-get update`
    lsb-release gnupg \
    wget \
    # Tools like xeyes
    x11-apps \
    # LibGL libraries
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*

# ------------------------ PYTHON SETUP ------------------------

# Install moteus python library.
# https://github.com/mjbots/moteus/tree/main/lib/python
RUN pip3 install moteus

# Install additional Python dependencies.
RUN pip3 install pyusb opencv-python

# Update pydocstyle to remove a deprecation warning when testing for PEP257.
RUN pip3 install --upgrade pydocstyle

# ------------------------ GAZEBO INSTALL------------------------

# Install Gazebo Ignition Fortress
RUN sudo curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
RUN sudo apt-get update && sudo apt-get install -y ignition-fortress

# ------------------------ USER + BASH CUSTOMIZATION ------------------------

# Add a user so we can remote into this container with a non-root user
RUN useradd trickfire \
    # Bash will be its default shell
    --shell /bin/bash \
    # Give it a directory in /home
    --create-home \
    # Don't make a giant log file for login data, we don't care about it
    --no-log-init

# Copy all the bash customizations over to the user.
COPY .devcontainer/trickfire.bashrc /home/trickfire/.bashrc

# Give sudo access.
RUN echo "trickfire ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user

# Fix permissions.
RUN rosdep fix-permissions && \
    chown -R trickfire:trickfire /usr/local/lib/python3.10/dist-packages && \
    chmod -R a+rX /usr/local/lib/python3.10/dist-packages

# Change to the non-root user.
USER trickfire
