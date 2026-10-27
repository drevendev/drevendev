"""Offline contract tests. Fixtures are synthetic; live acceptance is separate."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock, MagicMock
from urllib.error import HTTPError, URLError
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import refresh_profile as r
import build_static
import publish_refresh

FIXTURE = Path(__file__).parent / "fixtures/releases.json"


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.config = r.load_config()
        self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.readme = b"manual intro\r\n" + r.START + b"\r\nold\r\n" + r.END + b"\r\nmanual tail\r\n"

    def latest(self, data=None):
        return r.select_releases(self.config, self.data if data is None else data)[0]

    def config_error(self, mutate):
        config = copy.deepcopy(self.config)
        mutate(config)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaises(r.ProfileError):
                r.load_config(path)

    def test_initial_curated_composition(self):
        self.assertEqual([p["slug"] for p in self.config["projects"] if p["featured"]],
                         ["HungryCrab", "Devostasis", "BeautifulRepo", "trade_simulation"])
        self.assertEqual([p["slug"] for p in self.config["projects"] if p["secondary"]],
                         ["Dayflare", "Scriptorium", "Quillgrain", "PatchPitch", "CompostClub",
                          "Playmancer", "EndlessZenFramework"])

    def test_config_rejects_duplicate_slug(self):
        self.config_error(lambda c: c["projects"][1].update(slug="hungrycrab"))

    def test_config_rejects_unsafe_slug(self):
        self.config_error(lambda c: c["projects"][0].update(slug="<img>"))

    def test_config_rejects_wrong_owner(self):
        self.config_error(lambda c: c["projects"][0].update(url="https://github.com/other/HungryCrab"))

    def test_config_rejects_tier_overlap(self):
        self.config_error(lambda c: c["projects"][0].update(secondary=True))

    def test_config_rejects_featured_count(self):
        self.config_error(lambda c: c["projects"][0].update(featured=False, secondary=True))

    def test_config_rejects_nonboolean_flag(self):
        self.config_error(lambda c: c["projects"][0].update(collect_releases=1))

    def test_config_rejects_unverified_cta(self):
        self.config_error(lambda c: c["projects"][0]["ctas"].append(
            {"label": "Open", "url": "https://evil.example/"}))

    def test_config_rejects_unsafe_icon_path(self):
        self.config_error(lambda c: c["projects"][0].update(icon="../heart"))

    def test_release_icons_have_uniform_slots_and_a_fallback(self):
        self.config["projects"][0].pop("icon")
        output = r.render_releases(self.latest())
        self.assertEqual(output.count('width="20" height="20"'), 4)
        self.assertIn('assets/icons/package.svg', output)
        self.assertIn('assets/icons/pulse.svg', output)
        self.assertNotIn('heart.svg', output)

    def test_config_rejects_social_redirect_host(self):
        self.config_error(lambda c: c["links"].update(spotify="https://redirect.example/spotify"))

    def test_four_distinct_sources_and_stable_tie(self):
        chosen = self.latest()
        self.assertEqual([x["project"]["slug"] for x in chosen],
                         ["HungryCrab", "Devostasis", "BeautifulRepo", "trade_simulation"])

    def test_latest_is_by_published_date_not_input_order(self):
        older = copy.deepcopy(self.data["HungryCrab"][0])
        older["published_at"] = "2026-01-01T00:00:00Z"
        self.data["HungryCrab"].insert(0, older)
        self.assertEqual(self.latest()[0]["date"].month, 9)

    def test_latest_same_project_tie_is_deterministic(self):
        other = copy.deepcopy(self.data["HungryCrab"][0])
        other.update(tag_name="v1.3.0", html_url="https://github.com/drevendev/HungryCrab/releases/tag/v1.3.0")
        self.data["HungryCrab"].append(other)
        first = r.render_releases(self.latest())
        self.data["HungryCrab"].reverse()
        self.assertEqual(first, r.render_releases(self.latest()))

    def test_drafts_and_prereleases_are_excluded_before_field_validation(self):
        self.data["HungryCrab"] = [{"draft": True, "prerelease": False},
                                  {"draft": False, "prerelease": True}]
        self.assertNotIn("HungryCrab", [x["project"]["slug"] for x in self.latest()])

    def test_duplicate_release_is_not_repeated(self):
        self.data["HungryCrab"] *= 2
        chosen, _, skipped = r.select_releases(self.config, self.data)
        self.assertEqual(skipped["duplicate"], 1)
        self.assertEqual(len([x for x in chosen if x["project"]["slug"] == "HungryCrab"]), 1)

    def test_real_empty_collection_is_valid(self):
        empty = {p["slug"]: [] for p in r.sources(self.config)}
        self.assertIn("No stable public releases", r.render_releases(self.latest(empty)))

    def test_missing_source_is_failure(self):
        del self.data["CompostClub"]
        with self.assertRaises(r.ProfileError):
            self.latest()

    def test_wrong_collection_and_record_shapes_fail(self):
        for value in ({}, None, [None], ["bad"], [{}]):
            with self.subTest(value=value), self.assertRaises(r.ProfileError):
                data = copy.deepcopy(self.data)
                data["HungryCrab"] = value
                self.latest(data)

    def test_invalid_dates_fail(self):
        for value in ("2026-02-30T01:00:00Z", "tomorrow", "", "2026-10-27", None):
            with self.subTest(value=value), self.assertRaises(r.ProfileError):
                data = copy.deepcopy(self.data)
                data["HungryCrab"][0]["published_at"] = value
                self.latest(data)

    def test_missing_or_empty_tag_fails(self):
        self.data["HungryCrab"][0]["tag_name"] = ""
        with self.assertRaises(r.ProfileError):
            self.latest()

    def test_unsafe_urls_fail(self):
        for url in ("https://evil.example/x", "http://github.com/drevendev/HungryCrab/releases/tag/v1.2.0",
                    "https://github.com/other/HungryCrab/releases/tag/v1.2.0",
                    "https://github.com/drevendev/HungryCrab-other/releases/tag/v1.2.0",
                    "https://github.com@evil.example/x",
                    "https://github.com/drevendev/HungryCrab/releases/tag/v1.2.0?redirect=evil"):
            with self.subTest(url=url), self.assertRaises(r.ProfileError):
                data = copy.deepcopy(self.data)
                data["HungryCrab"][0]["html_url"] = url
                self.latest(data)

    def test_html_markdown_quotes_are_literal_text(self):
        tag = '<img src=x onerror="alert(1)">[]' + chr(96)
        entry = self.data["HungryCrab"][0]
        entry.update(tag_name=tag, html_url="https://github.com/drevendev/HungryCrab/releases/tag/" + quote(tag, safe=""),
                     name="<script>do not publish</script>", body="PRIVATE_BODY_SENTINEL")
        output = r.render_releases(self.latest())
        self.assertIn("&lt;img", output)
        self.assertNotIn("<img src=x", output)
        self.assertNotIn(' onerror="', output)
        self.assertEqual(output.count("<img "), 4)
        self.assertNotIn("<script", output)
        self.assertNotIn("PRIVATE_BODY_SENTINEL", output)

    def test_marker_errors_fail(self):
        for content in (b"none", r.START + r.START + r.END, r.START, r.END + r.START, r.START + r.END + r.END):
            with self.subTest(content=content), self.assertRaises(r.ProfileError):
                r.replace_block(content, "new")

    def test_preserves_manual_bytes_and_crlf(self):
        updated = r.replace_block(self.readme, r.render_releases(self.latest()))
        r.assert_only_block(self.readme, updated)
        self.assertTrue(updated.startswith(b"manual intro\r\n"))
        self.assertTrue(updated.endswith(b"\r\nmanual tail\r\n"))
        self.assertNotIn(b"\n", updated.replace(b"\r\n", b""))

    def test_refresh_is_byte_idempotent(self):
        block = r.render_releases(self.latest())
        first = r.replace_block(self.readme, block)
        self.assertEqual(first, r.replace_block(first, block))

    def test_rejects_manual_area_mutation(self):
        with self.assertRaises(r.ProfileError):
            r.assert_only_block(self.readme, self.readme.replace(b"intro", b"edited"))

    def test_atomic_write_detects_stale_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "README.md"
            path.write_bytes(b"human edit")
            with self.assertRaises(r.ProfileError):
                r.atomic_write(path, self.readme, b"new")
            self.assertEqual(path.read_bytes(), b"human edit")

    def test_fixture_mode_has_no_network_and_check_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(r, "fetch_sources") as network:
            path = Path(directory) / "README.md"
            path.write_bytes(self.readme)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(r.main(["--fixture", str(FIXTURE), "--readme", str(path), "--check"]), 1)
                self.assertEqual(r.main(["--fixture", str(FIXTURE), "--readme", str(path), "--dry-run"]), 0)
            network.assert_not_called()
            self.assertEqual(path.read_bytes(), self.readme)

    def test_no_implicit_live_mode(self):
        with contextlib.redirect_stdout(io.StringIO()), patch.object(r, "fetch_sources") as network:
            self.assertEqual(r.main([]), 2)
        network.assert_not_called()

    def test_cli_failure_preserves_readme_and_writes_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            path, fixture, summary = [Path(directory) / p for p in ("README.md", "bad.json", "summary.md")]
            path.write_bytes(self.readme)
            fixture.write_text("{bad", encoding="utf-8")
            with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(r.main(["--fixture", str(fixture), "--readme", str(path)]), 2)
            self.assertEqual(path.read_bytes(), self.readme)
            self.assertIn("sources_checked", summary.read_text())

    def test_http_errors_timeout_and_malformed_json_fail_closed(self):
        url = "https://api.github.com/repos/drevendev/HungryCrab/releases"
        for status in (403, 404, 429, 500):
            with self.subTest(status=status):
                opener = Mock()
                opener.open.side_effect = HTTPError(url, status, "SECRET_SENTINEL", {}, None)
                with self.assertRaises(r.ProfileError) as raised:
                    r.request_json(url, opener, lambda _: None)
                self.assertNotIn("SECRET_SENTINEL", str(raised.exception))
        opener = Mock()
        opener.open.side_effect = URLError("network")
        with self.assertRaises(r.ProfileError):
            r.request_json(url, opener, lambda _: None)
        response = Mock(status=200)
        response.geturl.return_value = url
        response.read.return_value = b"{bad"
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value = response
        with self.assertRaises(r.ProfileError):
            r.request_json(url, opener, lambda _: None)

    def test_redirect_refused_before_target_request(self):
        with self.assertRaises(r.ProfileError):
            r.NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.example/")

    def test_pagination_is_complete_or_failure(self):
        calls = []
        def requester(url):
            calls.append(url)
            return [self.data["HungryCrab"][0]] * 100 if url.endswith("page=1") and "HungryCrab" in url else []
        data = r.fetch_sources(self.config, requester)
        self.assertEqual(len(data["HungryCrab"]), 100)
        self.assertTrue(any("page=2" in url for url in calls))
        with patch.object(r, "MAX_PAGES", 2), self.assertRaises(r.ProfileError):
            r.fetch_sources(self.config, lambda _: [{}] * 100)

    def test_partial_network_failure_never_returns_partial_data(self):
        def requester(url):
            if "Devostasis" in url:
                raise r.ProfileError("unavailable")
            return []
        with self.assertRaises(r.ProfileError):
            r.fetch_sources(self.config, requester)

    def test_static_render_preserves_live_block(self):
        live = "\n<p>existing live release</p>\n"
        rendered = build_static.render(self.config, live)
        start, end = r.block_bounds(rendered.encode())
        self.assertEqual(rendered.encode()[start:end], live.encode())
        for project in self.config["projects"]:
            if project["featured"]:
                self.assertIn(project["url"], rendered)
                self.assertIn('assets/cards/' + project["slug"] + '-light.svg', rendered)
        self.assertIn(self.config["heading"].replace("'", "&#x27;"), rendered)
        grid = copy.deepcopy(self.config)
        grid["layout"] = "grid"
        self.assertEqual(build_static.render(grid, live).count("<td "), 4)
        single = copy.deepcopy(self.config)
        single["layout"] = "single"
        self.assertNotIn("<td ", build_static.render(single, live))


@unittest.skipUnless(shutil.which("git"), "git required for publication integration tests")
class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.work = self.base / "work"
        self.remote = self.base / "origin.git"
        subprocess.run(["git", "init", "--bare", str(self.remote)], capture_output=True, check=True)
        self.work.mkdir()
        def command(*args):
            return subprocess.run(["git", *args], cwd=self.work, capture_output=True, check=True).stdout
        self.command = command
        command("init", "-b", "main")
        command("config", "user.name", "Fixture")
        command("config", "user.email", "fixture@example.invalid")
        command("config", "core.autocrlf", "false")
        self.before = b"intro\n" + r.START + b"\nold\n" + r.END + b"\ntail\n"
        (self.work / "README.md").write_bytes(self.before)
        command("add", "README.md")
        command("commit", "-m", "fixture")
        command("remote", "add", "origin", str(self.remote))
        command("push", "origin", "main")
        self.root_patch = patch.object(publish_refresh, "ROOT", self.work)
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.temp.cleanup()

    def remote_head(self):
        return subprocess.check_output(["git", "--git-dir", str(self.remote), "rev-parse", "main"])

    def test_unchanged_refresh_never_commits(self):
        before = self.remote_head()
        with contextlib.redirect_stdout(io.StringIO()):
            publish_refresh.publish("main")
        self.assertEqual(before, self.remote_head())

    def test_valid_block_is_published_once(self):
        (self.work / "README.md").write_bytes(r.replace_block(self.before, "<p>new release</p>"))
        with contextlib.redirect_stdout(io.StringIO()):
            publish_refresh.publish("main")
        committed = self.remote_head()
        with contextlib.redirect_stdout(io.StringIO()):
            publish_refresh.publish("main")
        self.assertEqual(committed, self.remote_head())

    def test_static_mutation_is_never_published(self):
        (self.work / "README.md").write_bytes(self.before.replace(b"intro", b"changed"))
        with self.assertRaises(r.ProfileError):
            publish_refresh.publish("main")

    def test_unexpected_file_is_never_published(self):
        (self.work / "README.md").write_bytes(r.replace_block(self.before, "new"))
        (self.work / "unexpected.txt").write_text("not allowed")
        with self.assertRaises(r.ProfileError):
            publish_refresh.publish("main")

    def test_concurrent_human_commit_survives_failed_push(self):
        other = self.base / "other"
        subprocess.run(["git", "clone", "-b", "main", str(self.remote), str(other)], capture_output=True, check=True)
        for args in (["config", "user.name", "Human"], ["config", "user.email", "human@example.invalid"]):
            subprocess.run(["git", *args], cwd=other, capture_output=True, check=True)
        (other / "human.txt").write_text("keep this commit")
        for args in (["add", "."], ["commit", "-m", "human edit"], ["push", "origin", "main"]):
            subprocess.run(["git", *args], cwd=other, capture_output=True, check=True)
        human_head = self.remote_head()
        (self.work / "README.md").write_bytes(r.replace_block(self.before, "new"))
        with self.assertRaises(r.ProfileError):
            publish_refresh.publish("main")
        self.assertEqual(human_head, self.remote_head())


if __name__ == "__main__":
    unittest.main()

