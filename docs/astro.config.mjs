import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
    site: 'https://trickfirerobotics.github.io',
    base: '/gazebo-simulations',
    integrations: [
        starlight({
            title: 'Trickfire Gazebo Simulations',
            social: [
                {
                    icon: 'github',
                    label: 'GitHub',
                    href: 'https://github.com/TrickfireRobotics/gazebo-simulations',
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
