import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const posts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/posts' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    tags: z.array(z.string()).default([]),
    // radar = a news post, tips = Tricks & Tips Thursday. Older posts have neither.
    kind: z.enum(['radar', 'tips']).nullish(),
    // The pages the post was written from (also how the generator avoids repeating a story).
    sources: z.array(z.string()).default([]),
    // v2: used for dev.to cross-posting. Leave empty on your own site.
    canonical: z.string().url().nullish(),
  }),
});

export const collections = { posts };
