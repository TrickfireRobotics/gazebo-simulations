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
                    `,
                },
            ],
            logo: {
                src: './assets/nav-logo.png',
                alt: 'TrickFire Robotics Logo',
                replacesTitle: true,
            },
            favicon: '/favicon.ico',
            social: [
                {
                    icon: 'github',
                    label: 'GitHub',
                    href: 'https://github.com/TrickfireRobotics/gazebo-simulations',
                },
                {
                    icon: 'external',
                    label: 'Notion',
                    href: 'https://www.notion.so/trickfire/invite/7f153eec8ed8ebe4608dc95892fce859540f8640',
                },
                {
                    icon: 'external',
                    label: 'TrickFire Robotics',
                    href: 'https://trickfirerobotics.github.io',
                },
            ],
            sidebar: [
                {
                    label: 'Guides',
                    items: [
                        { label: 'Getting Started', slug: 'guides/getting-started' },
                        { label: 'Jetson Quick Start', slug: 'guides/jetson-quickstart' },
                        { label: 'Running on a Jetson', slug: 'guides/jetson-setup' },
                        { label: 'Running Simulations', slug: 'guides/running-simulations' },
                        { label: 'Moving Joints', slug: 'guides/moving-joints' },
                        { label: 'Adding a New Robot', slug: 'guides/adding-robots' },
                    ],
                },
                {
                    label: 'Reference',
                    items: [
                        { label: 'ROS Workspace', slug: 'reference/ros-workspace' },
                        { label: 'Scripts', slug: 'reference/scripts' },
                        { label: 'Genbot', slug: 'reference/genbot' },
                        { label: 'Joint GUI', slug: 'reference/joint-gui' },
                        { label: 'Launch System', slug: 'reference/launch-system' },
                        { label: 'Docker Environment', slug: 'reference/docker-environment' },
                    ],
                },
                { label: 'Dev Notes', autogenerate: { directory: 'dev' } },
            ],
            components: {
                SocialIcons: './components/SocialIcons.astro',
            },
            customCss: ['./styles/custom.css'],
        }),
    ],
});
