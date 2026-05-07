import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
    site: 'https://trickfirerobotics.github.io',
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
                    href: 'https://trickfirerobotics.github.io'
                }
            ],
            sidebar: [
                {
                    label: 'Getting Started',
                    items: [{ label: 'Prerequisites & Cloning', slug: 'simulate/getting-started' }]
                },
                {
                    label: 'Running the Simulation',
                    items: [
                        { label: 'Dev Container', slug: 'simulate/devcontainer' },
                        { label: 'Nvidia Container', slug: 'simulate/nvidia' },
                        { label: 'MacOS Native', slug: 'simulate/macos' }
                    ]
                },
                {
                    label: 'Using the Simulation',
                    items: [
                        { label: 'Running Simulations', slug: 'simulate/running-simulations' },
                        { label: 'Moving Joints', slug: 'simulate/moving-joints' },
                        { label: 'Adding a New Robot', slug: 'simulate/adding-robots' }
                    ]
                },
                {
                    label: 'Development',
                    items: [
                        { label: 'Dev Guide', slug: 'dev/development' },
                        { label: 'Dev Notes', slug: 'dev/dev-notes' }
                    ]
                },
                {
                    label: 'Deep Dives',
                    items: [
                        { label: 'ROS Workspace', slug: 'reference/ros-workspace' },
                        { label: 'Docker Environment', slug: 'reference/docker-environment' },
                        { label: 'Launch System', slug: 'reference/launch-system' },
                        { label: 'Genbot', slug: 'reference/genbot' },
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
