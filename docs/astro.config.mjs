import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
    site: 'https://docs.trickfirerobotics.com',
    base: '/gazebo-simulations',
    srcDir: './',
    integrations: [
        starlight({
            title: 'TrickFire Gazebo Simulations',
            head: [
                {
                    tag: 'script',
                    content: `
                        if (!localStorage.getItem('starlight-theme')) {
                            localStorage.setItem('starlight-theme', 'dark');
                        }
                    `
                }
            ],
            logo: {
                src: './assets/nav-logo.png',
                alt: 'TrickFire Robotics Logo',
                replacesTitle: true
            },
            favicon: '/favicon.ico',
            social: [
                {
                    icon: 'github',
                    label: 'GitHub',
                    href: 'https://github.com/TrickfireRobotics/gazebo-simulations'
                },
                {
                    icon: 'external',
                    label: 'Notion',
                    href: 'https://www.notion.so/trickfire/invite/7f153eec8ed8ebe4608dc95892fce859540f8640'
                },
                {
                    icon: 'external',
                    label: 'TrickFire Robotics',
                    href: 'https://docs.trickfirerobotics.com'
                }
            ],
            sidebar: [
                {
                    label: 'Setup',
                    items: [
                        { label: 'Getting Started', slug: 'setup/getting-started' },
                        { label: 'Native', slug: 'setup/macos' },
                        { label: 'Dev Container', slug: 'setup/devcontainer' },
                        { label: 'Nvidia Container', slug: 'setup/nvidia' }
                    ]
                },
                {
                    label: 'Simulation',
                    items: [
                        { label: 'Running Simulations', slug: 'guides/running-simulations' },
                        { label: 'Moving Joints', slug: 'guides/moving-joints' },
                        { label: 'Adding a New Robot', slug: 'guides/adding-robots' }
                    ]
                },
                {
                    label: 'Deep Dives',
                    items: [
                        { label: 'Dev Notes', slug: 'reference/dev-notes' },
                        { label: 'ROS Workspace', slug: 'reference/ros-workspace' },
                        { label: 'Docker Environment', slug: 'reference/docker-environment' },
                        { label: 'Launch System', slug: 'reference/launch-system' },
                        { label: 'Robot Packages', slug: 'reference/robot-packages' },
                        { label: 'Joint GUI', slug: 'reference/joint-gui' }
                    ]
                }
            ],
            components: {
                SocialIcons: './components/SocialIcons.astro'
            },
            customCss: ['./styles/custom.css']
        })
    ]
});
