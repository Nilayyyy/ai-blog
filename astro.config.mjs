import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import { unified } from '@astrojs/markdown-remark';
import remarkRadar from './src/lib/remark-radar.mjs';

// Set SITE_URL in Cloudflare (or edit here) once you have a domain.
// The unified (remark) processor is used so our diagram + STAR-heading plugin can run.
export default defineConfig({
  site: process.env.SITE_URL || 'https://example.com',
  integrations: [sitemap()],
  markdown: { processor: unified({ remarkPlugins: [remarkRadar] }) },
});
