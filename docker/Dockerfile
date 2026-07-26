FROM ubuntu:24.04 AS sim

ARG DEBIAN_FRONTEND=noninteractive
ARG TZ="America/Los_Angeles"
ARG BUILD_JOBS

# ---------------------------------------------------------------------------- #
#                                     BASE                                     #
# ---------------------------------------------------------------------------- #

RUN echo "------------------- BASE -------------------"

# Locale + timezone
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install --no-install-recommends -y locales curl gcc libc6-dev sudo ca-certificates && \
    locale-gen en_US en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

ENV LANG=en_US.UTF-8

RUN ln -snf "/usr/share/zoneinfo/${TZ}" /etc/localtime && \
    echo "${TZ}" > /etc/timezone

# User
RUN userdel ubuntu 2>/dev/null || true && \
    useradd trickfire --uid 1000 --shell /bin/bash --create-home --no-log-init && \
    usermod -aG video trickfire
RUN echo "trickfire ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user

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

# ---------------------------------------------------------------------------- #
#                                      VSG                                     #
# ---------------------------------------------------------------------------- #

RUN echo "-------------------- VSG -------------------"

# Build tools + Vulkan/Eigen deps — shared by VSG and Chrono
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    git build-essential cmake \
    libeigen3-dev \
    libvulkan-dev \
    libxcb1-dev \
    mesa-vulkan-drivers \
    ninja-build \
    pkg-config \
    vulkan-tools

ENV VSG_INSTALL_DIR=/opt/vsg

RUN git clone -c advice.detachedHead=false --depth 1 --branch 16.1.0 \
    https://github.com/KhronosGroup/glslang.git /tmp/glslang && \
    cmake -GNinja -B /tmp/build_glslang -S /tmp/glslang \
    -DBUILD_SHARED_LIBS=ON -DENABLE_OPT=0 && \
    cmake --build /tmp/build_glslang --parallel ${BUILD_JOBS:-$(nproc)} && \
    cmake --install /tmp/build_glslang --prefix ${VSG_INSTALL_DIR} && \
    rm -rf /tmp/glslang /tmp/build_glslang

RUN git clone -c advice.detachedHead=false --depth 1 --branch v4.4.2 \
    https://github.com/KhronosGroup/KTX-Software.git /tmp/ktx && \
    cmake -GNinja -B /tmp/build_ktx -S /tmp/ktx \
    -DBUILD_SHARED_LIBS=ON \
    -DKTX_FEATURE_TESTS=OFF \
    -DKTX_FEATURE_TOOLS=OFF \
    -DKTX_FEATURE_DOC=OFF && \
    cmake --build /tmp/build_ktx --parallel ${BUILD_JOBS:-$(nproc)} && \
    cmake --install /tmp/build_ktx --prefix ${VSG_INSTALL_DIR} && \
    rm -rf /tmp/ktx /tmp/build_ktx

RUN git clone -c advice.detachedHead=false --depth 1 --branch 1.5.7 \
    https://github.com/google/draco.git /tmp/draco && \
    cmake -GNinja -B /tmp/build_draco -S /tmp/draco \
    -DBUILD_SHARED_LIBS=ON \
    -DDRACO_TESTS=OFF && \
    cmake --build /tmp/build_draco --parallel ${BUILD_JOBS:-$(nproc)} && \
    cmake --install /tmp/build_draco --prefix ${VSG_INSTALL_DIR} && \
    rm -rf /tmp/draco /tmp/build_draco

RUN git clone -c advice.detachedHead=false --depth 1 --branch v6.0.5 \
    https://github.com/assimp/assimp /tmp/assimp && \
    cmake -GNinja -B /tmp/build_assimp -S /tmp/assimp \
    -DBUILD_SHARED_LIBS=OFF \
    -DASSIMP_BUILD_TESTS=OFF \
    -DASSIMP_BUILD_ASSIMP_TOOLS=OFF \
    -DASSIMP_BUILD_ZLIB=ON && \
    cmake --build /tmp/build_assimp --parallel ${BUILD_JOBS:-$(nproc)} && \
    cmake --install /tmp/build_assimp --prefix ${VSG_INSTALL_DIR} && \
    rm -rf /tmp/assimp /tmp/build_assimp

RUN git clone -c advice.detachedHead=false --depth 1 --branch v1.1.15 \
    https://github.com/vsg-dev/VulkanSceneGraph.git /tmp/vsg && \
    cmake -GNinja -B /tmp/build_vsg -S /tmp/vsg \
    -DCMAKE_PREFIX_PATH=${VSG_INSTALL_DIR} \
    -DBUILD_SHARED_LIBS=ON && \
    cmake --build /tmp/build_vsg --parallel ${BUILD_JOBS:-$(nproc)} && \
    cmake --install /tmp/build_vsg --prefix ${VSG_INSTALL_DIR} && \
    rm -rf /tmp/vsg /tmp/build_vsg

RUN git clone -c advice.detachedHead=false --depth 1 --branch v1.1.12 \
    https://github.com/vsg-dev/vsgXchange.git /tmp/vsgXchange && \
    ASSIMP_CMAKE=$(find ${VSG_INSTALL_DIR}/lib/cmake -maxdepth 1 -name "assimp-*" -type d | head -1) && \
    cmake -GNinja -B /tmp/build_vsgXchange -S /tmp/vsgXchange \
    -DCMAKE_PREFIX_PATH=${VSG_INSTALL_DIR} \
    -DBUILD_SHARED_LIBS=ON \
    -Dvsg_DIR=${VSG_INSTALL_DIR}/lib/cmake/vsg \
    -Dassimp_DIR=${ASSIMP_CMAKE} && \
    cmake --build /tmp/build_vsgXchange --parallel ${BUILD_JOBS:-$(nproc)} && \
    cmake --install /tmp/build_vsgXchange --prefix ${VSG_INSTALL_DIR} && \
    rm -rf /tmp/vsgXchange /tmp/build_vsgXchange

RUN git clone -c advice.detachedHead=false --depth 1 --branch v0.7.0 \
    https://github.com/vsg-dev/vsgImGui.git /tmp/vsgImGui && \
    cmake -GNinja -B /tmp/build_vsgImGui -S /tmp/vsgImGui \
    -DCMAKE_PREFIX_PATH=${VSG_INSTALL_DIR} \
    -DBUILD_SHARED_LIBS=ON \
    -Dvsg_DIR=${VSG_INSTALL_DIR}/lib/cmake/vsg && \
    cmake --build /tmp/build_vsgImGui --parallel ${BUILD_JOBS:-$(nproc)} && \
    cmake --install /tmp/build_vsgImGui --prefix ${VSG_INSTALL_DIR} && \
    rm -rf /tmp/vsgImGui /tmp/build_vsgImGui

ENV LD_LIBRARY_PATH=/opt/vsg/lib

# ---------------------------------------------------------------------------- #
#                                    CHRONO                                    #
# ---------------------------------------------------------------------------- #

RUN echo "------------------ CHRONO ------------------"

RUN git clone --depth 1 https://github.com/projectchrono/chrono.git /home/trickfire/chrono

# Fix upstream bug: AddActiveDomain appends without clearing the null-body default domain
# added by SetupInitial, causing a crash when OnBindAssets iterates all domains.
RUN sed -i \
    's|    m_loader->m_active_domains.push_back(ad);|    if (!m_loader->m_user_domains)\n        m_loader->m_active_domains.clear();\n    m_loader->m_active_domains.push_back(ad);|' \
    /home/trickfire/chrono/src/chrono_vehicle/terrain/SCMTerrain.cpp

RUN cmake -S /home/trickfire/chrono -B /home/trickfire/chrono/build \
    -GNinja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH=${VSG_INSTALL_DIR} \
    -DCH_ENABLE_MODULE_VEHICLE=ON \
    -DCH_ENABLE_MODULE_VSG=ON \
    -Dvsg_DIR=${VSG_INSTALL_DIR}/lib/cmake/vsg \
    -DvsgXchange_DIR=${VSG_INSTALL_DIR}/lib/cmake/vsgXchange \
    -DvsgImGui_DIR=${VSG_INSTALL_DIR}/lib/cmake/vsgImGui

RUN cmake --build /home/trickfire/chrono/build \
    --target demo_VEH_SCMTerrain_RigidTire \
    --parallel ${BUILD_JOBS:-$(nproc)}

RUN chown -R trickfire:trickfire /home/trickfire/chrono

# ---------------------------------------------------------------------------- #
#                                    GAZEBO                                    #
# ---------------------------------------------------------------------------- #

RUN echo "------------------ GAZEBO ------------------"

# ROS 2 Jazzy apt source
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -q -y --no-install-recommends \
    dirmngr gnupg2

RUN curl -L -s -f -o /tmp/ros2-apt-source.deb \
    https://github.com/ros-infrastructure/ros-apt-source/releases/download/1.2.0/ros2-apt-source_1.2.0.noble_all.deb && \
    echo "0804d9b13db770eb87019be414cd78378835228ad5fa801fc88758596dd8f7e5 */tmp/ros2-apt-source.deb" | sha256sum --strict --check && \
    apt-get update && apt-get install /tmp/ros2-apt-source.deb && \
    rm -f /tmp/ros2-apt-source.deb

# Gazebo Harmonic apt source
RUN curl https://packages.osrfoundation.org/gazebo.gpg \
    --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable noble main" \
    > /etc/apt/sources.list.d/gazebo-stable.list

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-rosdep \
    python3-colcon-common-extensions \
    ros-jazzy-ros-base \
    ros-jazzy-ros-gz \
    ros-jazzy-ros2-controllers \
    python3-tk

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gz-harmonic

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common && \
    add-apt-repository universe && \
    apt-get update && apt-get install -y --no-install-recommends \
    libgz-cmake4-dev \
    libgz-gui8 \
    libgz-plugin3-dev \
    libgz-common6-dev \
    libgz-sim8-dev \
    ros-jazzy-rviz2 \
    ros-jazzy-xacro \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-gz-ros2-control

RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --break-system-packages pypresence trimesh pyfqmr

RUN rosdep init || true

# ---------------------------------------------------------------------------- #
#                                 VNC / DISPLAY                                #
# ---------------------------------------------------------------------------- #

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    xvfb novnc x11vnc websockify openbox xterm python3-xdg x11-utils \
    mesa-utils libglx-mesa0 libgl1-mesa-dri x11-apps \
    xserver-xorg-core xserver-xorg-video-dummy kmod

EXPOSE 6080 5900
ENV VNC_PORT=5900
ENV NOVNC_PORT=6080

# ---------------------------------------------------------------------------- #
#                                  DEV TOOLING                                 #
# ---------------------------------------------------------------------------- #

RUN echo "--------------- DEV TOOLING ----------------"

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    openssh-server python3.12-venv wget zstd

RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install ruff pre-commit --break-system-packages --ignore-installed

RUN curl -sSL "https://github.com/mvdan/sh/releases/latest/download/shfmt_$(curl -sSL https://api.github.com/repos/mvdan/sh/releases/latest | grep -oP '(?<="tag_name": ")v[^"]+')_linux_amd64" \
    -o /usr/local/bin/shfmt && \
    chmod +x /usr/local/bin/shfmt

RUN rosdep fix-permissions && \
    chown -R trickfire:trickfire /usr/local/lib/python3.12/dist-packages /usr/local/bin && \
    chmod -R a+rX /usr/local/lib/python3.12/dist-packages

COPY docker/xorg.nvidia.conf /etc/X11/xorg.nvidia.conf
COPY docker/xorg.dummy.conf /etc/X11/xorg.dummy.conf
COPY docker/bashrc.sh /home/trickfire/.bashrc

USER trickfire
