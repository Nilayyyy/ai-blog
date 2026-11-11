# AI Dev Radar

A static Astro site plus a daily GitHub Actions job. Every morning the job looks at what is new in AI, picks the most interesting story, reads the real article, writes a short post in **STAR** form (Situation, Task, Action, Result) with a **diagram**, and opens a pull request. You edit it, merge it, and it goes live. On **Thursdays** it writes **Tricks & Tips Thursday** instead.

## What a day looks like

1. **Discover (no topic list).** Fresh items from official lab and startup blogs, AI press, Hacker News and fast-rising new GitHub repos (see `scripts/radar.yaml`). The same story on several sources ranks higher. Anything already published, or waiting in an open draft PR, is skipped.
2. **Pick.** The model chooses the story most likely to make a developer curious.
3. **Read.** The script fetches the article text, so the post is written from the source, not from model memory.
4. **Write.** Hook, Situation, Task, Action, Result, then your take and sources. A small JSON spec becomes a diagram (flow, before/after, or layer stack) drawn in plain HTML/CSS.
5. **Check.** Figures not found in the source get a `VERIFY` note, raw HTML is stripped, and the post stays hidden until you clear the markers.
6. **Open a PR** at about 07:47 IST. Pushes and PR creation retry on GitHub errors; if it still fails, the draft is saved as a downloadable artifact.

Thursday (IST) switches to tips mode: 4 to 6 niche tricks from fresh developer sources, every snippet flagged for you to run before you publish.

## Reviewing a draft (about 5 minutes)

- Replace the `TODO(nilay)` line under "My take" with your own words.
- Check each `<!-- VERIFY: ... -->` note, fix the sentence, delete the note. Typical ones: a figure the source didn't contain, a shaky claim, a snippet to run.
- Check the diagram says what the post says. Edit the JSON in the `diagram` block if not.
- Merge. Cloudflare rebuilds and the post is live in about a minute.

## Upgrading the existing project

1. Unzip over your project folder. Your posts in `src/content/posts` are untouched.
2. Delete `scripts/topics.yaml` and, if present, `body.json` (no longer used).
3. `npm install` (adds `@astrojs/markdown-remark`; `package-lock.json` is included so the Cloudflare build stays in sync).
4. `pip install -r scripts/requirements.txt` in your venv (adds `feedparser` and `trafilatura`).
5. Commit and push. Add secret `CLAUDE_CODE_OAUTH_TOKEN` (see "Which model writes the posts"). `GEMINI_API_KEY` and the "allow Actions to create pull requests" setting stay as they are.
6. First run: Actions tab, "Daily post draft", Run workflow, mode `news`. Open the log and look at the line `Sources: X/Y reachable`.

## Which model writes the posts

Claude writes the posts through **Claude Code on your Claude subscription** (Pro or Max), so there is no separate API bill. Gemini is the automatic backup: if the Claude token is missing, or your subscription limit is used up that morning, the run switches to Gemini and the PR says so under "Written by".

Setup, once:

1. Run `claude setup-token` in a terminal (install the CLI first with `npm install -g @anthropic-ai/claude-code`). It opens a browser login and prints a token valid for about a year.
2. Repo Settings > Secrets and variables > Actions > New repository secret: name `CLAUDE_CODE_OAUTH_TOKEN`, paste the token.
3. Actions tab > "Daily post draft" > Run workflow, tick **"Only test the model login"**. The log should end with `Answered by Claude Code (sonnet): OK`.

Good to know: the daily run draws on the same usage limit as your own Claude chats (a post is a handful of calls). The token is tied to your personal account; never commit it. When it expires, repeat steps 1-2.

## First-time setup

1. Push this folder to a GitHub repo.
2. Repo Settings > Secrets and variables > Actions: add secret `CLAUDE_CODE_OAUTH_TOKEN` (see above) and `GEMINI_API_KEY` (the backup).
3. Settings > Actions > General > Workflow permissions: tick "Allow GitHub Actions to create and approve pull requests".
4. Deploy on Cloudflare (Workers & Pages, connect the repo). Build command `npm run build`, deploy command `npx wrangler deploy`. Variables: `NODE_VERSION=22`, `SITE_URL=<your address>`. `wrangler.jsonc` is included.

## Run it on your own machine (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r scripts\requirements.txt

python scripts\generate.py --check-sources          # which sources work from here, no key needed
$env:PROVIDER = "mock"; $env:RADAR_OFFLINE = "1"
python scripts\generate.py --mode news --dry-run     # full pipeline on test data, no key, no network

$env:RADAR_OFFLINE = ""; $env:PROVIDER = ""          # default chain: Claude Code, then Gemini
python scripts\generate.py --check-model             # one tiny call: which model answers?
python scripts\generate.py --mode news --dry-run     # real run, prints the post, writes nothing
python scripts\generate.py --mode tips               # writes the file into src\content\posts

python -m unittest discover -s scripts\tests         # 27 tests
npm install; npm run dev                             # preview the site
```

## Tuning

- **Sources, keywords, freshness window:** `scripts/radar.yaml`. A source that fails is skipped. If every source fails, the run fails loudly instead of quietly skipping.
- **Model:** repo variable `PROVIDER` is the chain to try, default `claude-code,gemini`. Other options: `claude-api` (separately billed API key in secret `ANTHROPIC_API_KEY`), `gemini` alone. `CLAUDE_CODE_MODEL` picks the Claude model (default `sonnet`; `opus` writes better but uses your limit faster), `CLAUDE_CODE_EFFORT` sets thinking effort (`low` to `max`), `GEMINI_MODEL` the Gemini one.
- **Schedule:** the cron line in `.github/workflows/daily-post.yml`. GitHub can start scheduled runs 15 to 60 minutes late.
- **Site name and tagline:** `src/config.ts`.

## Good to know

- The Anthropic feed in `radar.yaml` is community-maintained (Anthropic has no official RSS), so it can lag or disappear. The other sources are official feeds.
- The read-aloud button uses your browser's built-in speech. Voice quality depends on the device; it is hidden where unsupported. It skips code and the sources list, and reads the diagram as steps.
- Free-tier model limits and model names change. If the job fails with a model error, check `GEMINI_MODEL`.
- v2, parked: cross-posting to dev.to with the canonical URL pointing at this site. Each post already has an empty `canonical` field for it.
