import { getCollection } from 'astro:content';

// A post is held back from the site while it still contains an unresolved marker.
// The generator adds TODO(nilay) (your personal take) and VERIFY: (claims to check).
// Remove them while reviewing the PR and the post goes live when you merge.
const UNRESOLVED = /TODO\(nilay\)|VERIFY:/;

export async function getPublishedPosts() {
  const all = await getCollection('posts');
  return all
    .filter((p) => !UNRESOLVED.test(p.body ?? ''))
    .sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf());
}
