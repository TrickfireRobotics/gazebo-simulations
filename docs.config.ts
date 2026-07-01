    import { defineConfig } from "trickfire-docs";

    export default defineConfig({
        name: "TrickFire Gazebo Simulations",
        description: "Simulation system guide for TrickFire Robotics systems in Gazebo with ROS 2, inside a fully containerized environment, with an OnShape to simulation pipeline.",
        landing: [
    {
        title: "Getting Started",
        description: "Clone the repo and pick your environment - Docker, macOS native, or Jetson.",
        link: "/setup/getting-started/",
    },
    {
        title: "Running Simulations",
        description: "Launch any robot with a single command. Build, source, and run Gazebo + RViz + Joint GUI automatically.",
        link: "/guides/running-simulations/",
    },
    {
        title: "Adding Robots",
        description: "Pull a CAD model from OnShape and generate ready-to-build ROS 2 packages with one command.",
        link: "/guides/adding-robots/",
    },
    {
        title: "Deep Dives",
        description: "Architecture deep dives into the launch system, Docker environment, ROS workspace, and robot package generation.",
        link: "/reference/ros-workspace/",
    },
],
        sidebar: [
            {
                label: "Setup",
                items: [
                    { label: "Getting Started", slug: "setup/getting-started" },
                    { label: "Native", slug: "setup/macos" },
                    { label: "Dev Container", slug: "setup/devcontainer" },
                    { label: "Nvidia Container", slug: "setup/nvidia" }
                ]
            },
            {
                label: "Simulation",
                items: [
                    { label: "Running Simulations", slug: "guides/running-simulations" },
                    { label: "Moving Joints", slug: "guides/moving-joints" },
                    { label: "Adding a New Robot", slug: "guides/adding-robots" }
                ]
            },
            {
                label: "Deep Dives",
                items: [
                    { label: "Dev Notes", slug: "reference/dev-notes" },
                    { label: "ROS Workspace", slug: "reference/ros-workspace" },
                    { label: "Docker Environment", slug: "reference/docker-environment" },
                    { label: "Launch System", slug: "reference/launch-system" },
                    { label: "Robot Packages", slug: "reference/robot-packages" },
                    { label: "Joint GUI", slug: "reference/joint-gui" }
                ]
            }
        ],
    });
