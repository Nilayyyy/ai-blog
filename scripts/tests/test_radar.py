"""Run from the project root:  python -m unittest discover -s scripts/tests -v"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from radar import article, llm, rank, sources, writer  # noqa: E402
from radar.sources import Item  # noqa: E402

NOW = datetime(2026, 11, 5, 3, 0, tzinfo=timezone.utc)


def item(title, url, source="S", hours=5, weight=0.5, points=0, origin="feed", summary=""):
    return Item(title=title, url=url, source=source, published=NOW - timedelta(hours=hours),
                weight=weight, points=points, origin=origin, summary=summary, ai_only=True)


class RankTests(unittest.TestCase):
    def test_normalize_url_strips_tracking_and_www(self):
        a = rank.normalize_url("https://www.Example.com/post/?utm_source=x&id=3#frag")
        b = rank.normalize_url("https://example.com/post?id=3")
        self.assertEqual(a, b)

    def test_same_story_clusters_across_sources(self):
        items = [
            item("ExampleLab launches Atlas code review agent", "https://a.test/1", "Lab", weight=1.0),
            item("ExampleLab launches Atlas code review agent for pull requests", "https://b.test/2", "News"),
            item("Totally different robotics story about humanoids", "https://c.test/3", "News"),
        ]
        stories = rank.cluster(items)
        self.assertEqual(len(stories), 2)
        big = max(stories, key=lambda s: len(s.members))
        self.assertEqual(big.rep.source, "Lab")  # most trusted source becomes the primary

    def test_buzz_and_recency_rank_higher(self):
        items = [
            item("Atlas code review agent launches today", "https://a.test/1", "Lab", weight=1.0),
            item("Atlas code review agent launches today for teams", "https://b.test/2", "News"),
            item("Quiet single source story about embeddings", "https://c.test/3", "Blog", hours=60),
        ]
        ranked = rank.rank_stories(items, NOW, 72, {})
        self.assertIn("Atlas", ranked[0].rep.title)

    def test_seen_urls_and_titles_are_excluded(self):
        items = [
            item("Atlas code review agent launches today", "https://a.test/1?utm_source=x"),
            item("Something else entirely about vector databases", "https://c.test/3"),
        ]
        by_url = rank.rank_stories(items, NOW, 72, {}, seen_urls={rank.normalize_url("https://a.test/1")})
        self.assertEqual(len(by_url), 1)
        by_title = rank.rank_stories(items, NOW, 72, {}, seen_titles=["Atlas code review agent launches"])
        self.assertEqual(len(by_title), 1)
        self.assertIn("vector", by_title[0].rep.title)


class SourceTests(unittest.TestCase):
    def test_parse_feed_rss(self):
        xml = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
        <item><title>Model X released</title><link>https://x.test/a</link>
        <pubDate>Wed, 04 Nov 2026 10:00:00 GMT</pubDate><description>&lt;p&gt;Hello  world&lt;/p&gt;</description></item>
        <item><title>No link</title></item></channel></rss>"""
        items = sources.parse_feed(xml, {"name": "T", "weight": 0.9, "ai": True})
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].summary, "Hello world")
        self.assertEqual(items[0].published, datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc))
        self.assertTrue(items[0].ai_only)

    def test_filter_drops_old_undated_and_non_ai(self):
        section = {"require_ai": True}
        fresh = Item("Claude gets a new feature", "https://a.test", "S", NOW - timedelta(hours=2))
        old = Item("Claude gets a new feature", "https://b.test", "S", NOW - timedelta(hours=200))
        undated = Item("Claude gets a new feature", "https://c.test", "S", None)
        offtopic = Item("Local bakery wins award", "https://d.test", "S", NOW - timedelta(hours=2))
        out = sources.filter_items([fresh, old, undated, offtopic], section, NOW, 72)
        self.assertEqual(out, [fresh])


class SafetyTests(unittest.TestCase):
    def test_safe_get_blocks_private_and_bad_schemes(self):
        for bad in ("http://127.0.0.1/", "http://localhost:8000/x", "http://169.254.169.254/latest/meta-data", "file:///etc/passwd", "ftp://example.com"):
            with self.assertRaises(ValueError, msg=bad):
                article.safe_get(bad)

    def test_sanitize_strips_html_but_keeps_code_and_comments(self):
        raw = "Hi <script>alert(1)</script> there <!-- VERIFY: x --> and `List<String>`\n\n```java\nList<String> a;\n```\n![px](http://t.test/p.png) [x](javascript:alert(1)) <https://ok.test>"
        out = writer.sanitize_markdown(raw)
        self.assertNotIn("<script>", out)
        self.assertIn("<!-- VERIFY: x -->", out)
        self.assertIn("`List<String>`", out)
        self.assertIn("List<String> a;", out)
        self.assertNotIn("![", out)
        self.assertIn("](#)", out)
        self.assertIn("https://ok.test", out)
        self.assertNotIn("<https", out)

    def test_extract_text_fallback_without_trafilatura(self):
        html = "<html><head><title>T</title><script>var a=1</script></head><body><nav>menu</nav><p>" + ("Real paragraph text here. " * 10) + "</p></body></html>"
        title, text = article.extract_text(html)
        self.assertIn("Real paragraph text", text)
        self.assertNotIn("var a=1", text)


class WriterTests(unittest.TestCase):
    def test_unsourced_numbers_are_flagged(self):
        src = "The trial covered 40 repositories and a median of 12 minutes."
        body = "## Result\nIt cut review time by 37% across 40 repositories in 2026.\nTwo teams tried it, 12 minutes each.\n```\nx = 99\n```"
        out = writer.flag_unsourced_numbers(body, src)
        lines = out.splitlines()
        self.assertIn("VERIFY: figure 37%", lines[1])
        self.assertNotIn("VERIFY", lines[2])   # 12 is in the source; 2 is small
        self.assertNotIn("VERIFY", out.split("```")[1])  # code untouched

    def test_snippets_marked_in_tips(self):
        out = writer.mark_snippets("a\n```bash\ngit diff\n```\nafter")
        self.assertIn("<!-- VERIFY: run this snippet", out)
        again = writer.mark_snippets(out)
        self.assertEqual(again.count("VERIFY"), 1)

    def test_parse_and_validate_mock_news(self):
        post = writer.parse_write_output(llm._MOCK_NEWS)
        self.assertTrue(post["title"].startswith("Atlas"))
        self.assertEqual(post["tags"], ["agents", "code-review", "developer-tools"])
        self.assertEqual(writer.validate_post(post, "news"), [])

    def test_validate_catches_missing_star_and_h1(self):
        bad = {"title": "T", "body": "# Big\n\nIntro " * 20 + "\n\n## Situation\nx\n\n## Action\ny"}
        errors = " ".join(writer.validate_post(bad, "news"))
        self.assertIn("exactly Situation", errors)
        self.assertIn("H1", errors)

    def test_validate_diagram_shapes(self):
        good = writer.validate_diagram(json.loads(llm._MOCK_DIAGRAM))
        self.assertEqual(good["type"], "flow")
        self.assertIsNone(writer.validate_diagram({"type": "flow", "steps": [{"label": "only one"}]}))
        self.assertIsNone(writer.validate_diagram({"type": "unknown"}))
        cmp_ok = writer.validate_diagram({"type": "compare", "before": {"points": ["a", "b"]}, "after": {"points": ["c", "d"]}})
        self.assertEqual(cmp_ok["before"]["heading"], "Before")
        clean = writer.validate_diagram({"type": "stack", "layers": [{"label": "<b>x</b>"}, {"label": "y"}, {"label": "z"}]})
        self.assertNotIn("<", clean["layers"][0]["label"])

    def test_extract_json_handles_fences(self):
        self.assertEqual(llm.extract_json('```json\n{"a": 1}\n```'), {"a": 1})
        with self.assertRaises(ValueError):
            llm.extract_json("no json here")

    def test_front_matter_round_trips(self):
        post = writer.parse_write_output(llm._MOCK_NEWS)
        post["errors"] = []
        srcs = [{"title": "A [post]", "url": "https://x.test/a", "publisher": "X", "text": "12 minutes"}]
        diagram = writer.validate_diagram(json.loads(llm._MOCK_DIAGRAM))
        title, md = writer.finalize(post, "news", today_iso="2026-11-05", srcs=srcs, diagram=diagram)
        fm = writer.read_front_matter(md)
        self.assertEqual(fm["title"], title)
        self.assertEqual(fm["kind"], "radar")
        self.assertEqual(fm["sources"], ["https://x.test/a"])
        self.assertIn("ai-radar", fm["tags"])
        self.assertIn("```diagram", md)
        self.assertIn("TODO(nilay)", md)
        self.assertIn("VERIFY: figure 37%", md)  # not in the source text
        self.assertLess(md.index("```diagram"), md.index("## Situation"))


class ModeTests(unittest.TestCase):
    def test_thursday_ist_is_tips(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import generate

        thu = datetime(2026, 11, 5, 2, 17, tzinfo=timezone.utc)   # Thu 07:47 IST
        wed = datetime(2026, 11, 4, 2, 17, tzinfo=timezone.utc)
        late_wed_utc = datetime(2026, 11, 4, 20, 0, tzinfo=timezone.utc)  # Thu 01:30 IST
        os.environ.pop("MODE", None)
        self.assertEqual(generate.resolve_mode("auto", thu), "tips")
        self.assertEqual(generate.resolve_mode("auto", wed), "news")
        self.assertEqual(generate.resolve_mode(None, late_wed_utc), "tips")
        self.assertEqual(generate.resolve_mode("news", thu), "news")

    def test_load_seen_reads_posts_and_open_prs(self):
        import generate

        with tempfile.TemporaryDirectory() as d:
            posts = Path(d)
            (posts / "2026-11-01-a.md").write_text('---\ntitle: "Old post"\nsources: ["https://old.test/a"]\n---\nbody', encoding="utf-8")
            prs = Path(d) / "prs.json"
            prs.write_text(json.dumps([
                {"title": "Draft: Open story", "body": "Sources:\n- https://open.test/x", "headRefName": "draft/123"},
                {"title": "Unrelated", "body": "https://other.test", "headRefName": "feature/x"},
            ]), encoding="utf-8")
            urls, titles = generate.load_seen(posts, str(prs))
        self.assertIn("old.test/a", urls)
        self.assertIn("open.test/x", urls)
        self.assertNotIn("other.test", urls)
        self.assertIn("Open story", titles)


class AllSourcesDown(unittest.TestCase):
    def test_exits_nonzero_when_every_source_fails(self):
        from unittest import mock

        import generate

        failed = ([], [("OpenAI", False, 0, "ProxyError"), ("HN: AI", False, 0, "ProxyError")])
        with mock.patch.object(generate.sources, "gather", return_value=failed), \
             mock.patch.object(sys, "argv", ["generate.py", "--mode", "news", "--dry-run"]), \
             mock.patch.dict(os.environ, {"RADAR_OFFLINE": "0", "PROVIDER": "mock"}):
            self.assertEqual(generate.main(), 1)

    def test_quiet_day_is_not_an_error(self):
        from unittest import mock

        import generate

        quiet = ([], [("OpenAI", True, 0, ""), ("HN: AI", False, 0, "x")])
        with mock.patch.object(generate.sources, "gather", return_value=quiet), \
             mock.patch.object(sys, "argv", ["generate.py", "--mode", "news", "--dry-run"]), \
             mock.patch.dict(os.environ, {"RADAR_OFFLINE": "0", "PROVIDER": "mock"}):
            self.assertEqual(generate.main(), 0)


class ProviderChain(unittest.TestCase):
    """The Claude Code provider and the fallback chain, with the CLI faked out."""

    def setUp(self):
        from unittest import mock
        llm.reset()
        self.env = mock.patch.dict(os.environ, {
            "CLAUDE_CODE_BIN": "claude-fake", "RETRY_BASE_SECONDS": "0", "CALL_GAP_SECONDS": "0",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(llm.reset)

    def fake_run(self, payload, returncode=0):
        calls = []

        def run(cmd, **kw):
            calls.append((cmd, kw))
            out = payload if isinstance(payload, str) else json.dumps(payload)
            return subprocess.CompletedProcess(cmd, returncode, stdout=out, stderr="")
        return run, calls

    def test_provider_parsing(self):
        from unittest import mock
        with mock.patch.dict(os.environ, {"PROVIDER": "Claude-Code, claude ,gemini,gemini"}):
            self.assertEqual(llm.providers(), ["claude-code", "claude-api", "gemini"])
        with mock.patch.dict(os.environ, {"PROVIDER": ""}):
            self.assertEqual(llm.providers(), ["claude-code", "gemini"])
        with mock.patch.dict(os.environ, {"PROVIDER": "gpt"}):
            with self.assertRaises(llm.LLMError):
                llm.providers()

    def test_claude_code_call_shape(self):
        from unittest import mock
        run, calls = self.fake_run({"type": "result", "subtype": "success", "is_error": False, "result": " Hello ",
                                    "usage": {"input_tokens": 10, "output_tokens": 2}})
        with mock.patch.dict(os.environ, {"PROVIDER": "claude-code", "CLAUDE_CODE_OAUTH_TOKEN": "tok",
                                          "ANTHROPIC_API_KEY": "sk-should-not-leak"}), \
             mock.patch.object(llm.subprocess, "run", run):
            self.assertEqual(llm.complete("sys", "the long prompt", stage="write:news"), "Hello")
        cmd, kw = calls[0]
        self.assertEqual(cmd[:2], ["claude-fake", "-p"])
        self.assertIn("--system-prompt-file", cmd)
        self.assertEqual(cmd[cmd.index("--tools") + 1], "")          # no tools at all
        self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        self.assertEqual(kw["input"], "the long prompt")            # prompt on stdin, not argv
        self.assertNotIn("ANTHROPIC_API_KEY", kw["env"])             # subscription, not API billing
        self.assertEqual(llm.used_summary(), "Claude Code (sonnet)")

    def test_usage_limit_falls_back_once_and_stays_down(self):
        from unittest import mock
        run, calls = self.fake_run({"type": "result", "subtype": "success", "is_error": True,
                                    "result": "Claude usage limit reached. Your limit will reset at 5pm"})
        with mock.patch.dict(os.environ, {"PROVIDER": "claude-code,mock"}), \
             mock.patch.object(llm.subprocess, "run", run):
            first = llm.complete("s", "p", stage="write:news")
            llm.complete_json("s", "p", stage="diagram:news")
        self.assertIn("TITLE:", first)
        self.assertEqual(len(calls), 1)   # no retry on a limit, and skipped for later stages
        self.assertEqual(llm.used_summary(), "mock")

    def test_garbage_output_is_an_error(self):
        from unittest import mock
        run, _ = self.fake_run("not json", returncode=1)
        with mock.patch.dict(os.environ, {"PROVIDER": "claude-code"}), \
             mock.patch.object(llm.subprocess, "run", run):
            with self.assertRaises(llm.LLMError):
                llm.complete("s", "p", stage="select:news")

    def test_pr_body_names_the_model(self):
        body = writer.pr_body("news", [{"url": "https://x.test/a"}], model="Claude Code (sonnet)")
        self.assertIn("Written by: Claude Code (sonnet)", body)
        self.assertIn("https://x.test/a", body)


class EndToEndOffline(unittest.TestCase):
    def run_gen(self, mode):
        env = dict(os.environ, PROVIDER="mock", RADAR_OFFLINE="1", RETRY_BASE_SECONDS="0", CALL_GAP_SECONDS="0")
        env.pop("OPEN_PRS_FILE", None)
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--mode", mode, "--dry-run"],
                           capture_output=True, text=True, env=env, cwd=ROOT, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return r.stdout

    def test_news_post_has_star_diagram_and_markers(self):
        out = self.run_gen("news")
        for h in ("## Situation", "## Task", "## Action", "## Result", "## My take", "## Sources"):
            self.assertIn(h, out)
        self.assertIn("```diagram", out)
        self.assertIn("TODO(nilay)", out)
        self.assertIn("kind: radar", out)
        self.assertIn("examplelab.test/blog/atlas", out)   # the official source was picked as primary

    def test_tips_post_marks_snippets_and_title(self):
        out = self.run_gen("tips")
        self.assertIn("kind: tips", out)
        self.assertIn("Tricks & Tips Thursday", out)
        self.assertIn("VERIFY: run this snippet", out)


if __name__ == "__main__":
    unittest.main()
