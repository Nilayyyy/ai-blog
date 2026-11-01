import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Set SITE_URL in Cloudflare Pages (or edit here) once you have a domain.
export default defineConfig({
  site: process.env.SITE_URL || 'https://example.com',
  integrations: [sitemap()],
});
