# AI-assisted blog

A static Astro site plus a daily GitHub Actions job that drafts one post and opens a pull request. You review, add your own take, and merge. Merging publishes.

## How it works

1. `scripts/topics.yaml` holds the topic queue. When it runs out, the model suggests more.
2. `scripts/generate.py` runs outline, draft and edit passes, then writes `src/content/posts/YYYY-MM-DD-slug.md`.
3. The workflow opens a PR with that file.
4. A post stays hidden from the site while it contains `TODO(nilay)` (your personal take) or `<!-- VERIFY: ... -->` (claims to check). Remove them in the PR, merge, and it goes live.

## Setup (about 20 minutes)

1. **Push this folder to a new GitHub repo.**
2. **Get a free Gemini API key** from Google AI Studio. In the repo: Settings > Secrets and variables > Actions > New repository secret, name `GEMINI_API_KEY`.
3. **Allow PRs from Actions:** Settings > Actions > General > Workflow permissions > tick "Allow GitHub Actions to create and approve pull requests".
4. **Deploy on Cloudflare Pages:** connect the repo, framework preset Astro, build command `npm run build`, output directory `dist`. Add an environment variable `SITE_URL` with your final URL.
5. **Domain (when ready):** buy one (Cloudflare Registrar sells at cost), then attach it under Pages > Custom domains and update `SITE_URL`.
6. **Test:** Actions tab > "Daily post draft" > Run workflow. A PR should appear within a minute or two.

The cron runs daily at 08:00 IST. Change it in `.github/workflows/daily-post.yml`.

## Switching to Claude later

Add a repo secret `ANTHROPIC_API_KEY` and a repo variable `PROVIDER` set to `claude`. Optional variable `CLAUDE_MODEL` overrides the model. No code changes.

## Local use

```bash
npm install && npm run dev            # site
pip install -r scripts/requirements.txt
PROVIDER=mock python scripts/generate.py --dry-run   # test without any key
GEMINI_API_KEY=... python scripts/generate.py        # real draft
```

## v2: cross-posting to dev.to

Already prepared: every post has a `canonical` front matter field (empty on your own site). The plan is a separate `scripts/crosspost.py` that, after a post is merged and live, publishes it to dev.to with `canonical_url` set to your site's URL, so search credit goes to your domain. It would need a `DEVTO_API_KEY` secret and a second workflow triggered on merge.

## Notes

- Free-tier model names and limits change. If the Gemini call fails with a 404, set the `GEMINI_MODEL` variable to a current model name.
- The prompt forbids invented experiences and numbers, but always read drafts before merging. You are the editor.
