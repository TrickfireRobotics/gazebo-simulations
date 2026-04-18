import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
    site: 'https://trickfirerobotics.github.io',
    base: '/gazebo-simulations',
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
                src: './src/assets/logo.png',
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
                { label: 'Guides', autogenerate: { directory: 'guides' } },
                { label: 'Reference', autogenerate: { directory: 'reference' } },
                { label: 'Dev Notes', autogenerate: { directory: 'dev' } },
            ],
            customCss: ['./src/styles/custom.css'],
        }),
    ],
});
