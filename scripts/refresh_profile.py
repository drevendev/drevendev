"""Refresh only LIVE_RELEASES. Python 3.11+, standard library, anonymous public GETs."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import re
import socket
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, quote, unquote
from urllib.request import Request, build_opener, HTTPRedirectHandler

ROOT = Path(__file__).resolve().parents[1]
START = b"<!-- LIVE_RELEASES:START -->"
END = b"<!-- LIVE_RELEASES:END -->"
MAX_PAGES = 20
MAX_RESPONSE = 8 * 1024 * 1024
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
ICONS = {"crab": "Crab", "pulse": "ECG pulse", "sparkles": "Sparkles", "scales": "Balance scales", "package": "Package"}


class ProfileError(ValueError):
    """Invalid input or unavailable source: do not publish anything."""


def clean_text(value, label, limit=500):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ProfileError(f"Invalid {label}")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ProfileError(f"Control character in {label}")
    return value


def https_url(value, host=None):
    clean_text(value, "URL", 2048)
    parts = urlsplit(value)
    if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password
            or parts.port not in (None, 443) or "\\" in value or any(c.isspace() for c in value)):
        raise ProfileError("Unsafe URL")
    if host and parts.netloc != host:
        raise ProfileError("Unexpected URL host")
    return parts


def load_config(path=ROOT / "data/profile.json"):
    try:
        config = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ProfileError("Cannot read profile configuration") from exc
    if not isinstance(config, dict) or config.get("schema_version") != 1 or config.get("owner") != "drevendev":
        raise ProfileError("Invalid configuration owner/schema")
    if config.get("layout") not in ("grid", "single", "cards"):
        raise ProfileError("Invalid layout")
    for key in ("heading", "subtitle", "character"):
        clean_text(config.get(key), key)
    projects = config.get("projects")
    if not isinstance(projects, list) or not projects:
        raise ProfileError("Empty project allowlist")
    slugs, orders = set(), set()
    for project in projects:
        if not isinstance(project, dict):
            raise ProfileError("Invalid project")
        slug = project.get("slug")
        if not isinstance(slug, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", slug):
            raise ProfileError("Invalid project slug")
        if slug.lower() in slugs:
            raise ProfileError("Duplicate project slug")
        slugs.add(slug.lower())
        order = project.get("stable_display_order")
        if type(order) is not int or order < 1 or order in orders:
            raise ProfileError("Invalid/duplicate project order")
        orders.add(order)
        for field in ("featured", "secondary", "collect_releases"):
            if type(project.get(field)) is not bool:
                raise ProfileError(f"Invalid {field}")
        if project["featured"] == project["secondary"]:
            raise ProfileError("Project must have exactly one display tier")
        expected = f"https://github.com/{config['owner']}/{slug}"
        if project.get("url") != expected:
            raise ProfileError("Unexpected project owner/URL")
        clean_text(project.get("label"), "project label")
        clean_text(project.get("description"), "project description")
        if project.get("icon", "package") not in ICONS:
            raise ProfileError("Invalid project icon")
        if project["featured"]:
            clean_text(project.get("one_liner"), "one-liner")
        ctas = project.get("ctas")
        if not isinstance(ctas, list) or not 1 <= len(ctas) <= 2:
            raise ProfileError("Invalid CTAs")
        for cta in ctas:
            clean_text(cta.get("label"), "CTA label")
            parts = https_url(cta.get("url"))
            if not (cta["url"] == expected or cta["url"].startswith(expected + "#")
                    or cta["url"] == project.get("verified_demo_url")):
                raise ProfileError("Unverified CTA")
        if "verified_demo_url" in project:
            https_url(project["verified_demo_url"])
    if sum(p["featured"] for p in projects) != 4:
        raise ProfileError("Exactly four featured projects required")
    if sum(p["secondary"] for p in projects) != 7:
        raise ProfileError("Exactly seven secondary projects required")
    if not any(p["collect_releases"] for p in projects):
        raise ProfileError("No release sources")
    links = config.get("links")
    hosts = {"shop": "drevengames.itch.io", "linkedin": "www.linkedin.com", "itch": "drevengames.itch.io",
             "play": "play.google.com", "spotify": "open.spotify.com", "robot_anime": "open.spotify.com"}
    if not isinstance(links, dict) or links.keys() != hosts.keys():
        raise ProfileError("Invalid social links")
    for key, host in hosts.items():
        https_url(links[key], host)
    return config


def sources(config):
    return sorted((p for p in config["projects"] if p["collect_releases"]),
                  key=lambda p: p["stable_display_order"])


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProfileError("Redirect refused")


def request_json(url, opener=None, sleeper=time.sleep):
    parts = https_url(url, "api.github.com")
    if not re.fullmatch(r"/repos/drevendev/[A-Za-z0-9_.-]+/releases", parts.path):
        raise ProfileError("Unexpected API endpoint")
    opener = opener or build_opener(NoRedirect())
    for attempt in range(3):
        try:
            req = Request(url, headers={"Accept": "application/vnd.github+json",
                          "X-GitHub-Api-Version": "2022-11-28",
                          "User-Agent": "drevendev-profile-releases/1"})
            # Deliberately no Authorization header: only publicly accessible sources.
            with opener.open(req, timeout=20) as response:
                if response.status != 200 or response.geturl() != url:
                    raise ProfileError("Unexpected HTTP response")
                payload = response.read(MAX_RESPONSE + 1)
                if len(payload) > MAX_RESPONSE:
                    raise ProfileError("Response too large")
                return json.loads(payload)
        except HTTPError as exc:
            exc.close()
            if exc.code in (500, 502, 503, 504) and attempt < 2:
                sleeper(2 ** attempt)
                continue
            raise ProfileError(f"GitHub HTTP {exc.code}") from None
        except (URLError, TimeoutError, socket.timeout):
            if attempt < 2:
                sleeper(2 ** attempt)
                continue
            raise ProfileError("GitHub timeout/network failure") from None
        except ProfileError:
            raise
        except (ValueError, UnicodeError) as exc:
            raise ProfileError("Malformed GitHub JSON") from exc
    raise ProfileError("Source unavailable")


def fetch_sources(config, requester=request_json):
    result = {}
    for project in sources(config):
        releases = []
        for page in range(1, MAX_PAGES + 1):
            url = f"https://api.github.com/repos/{config['owner']}/{project['slug']}/releases?per_page=100&page={page}"
            data = requester(url)
            if not isinstance(data, list):
                raise ProfileError("Unexpected Releases response structure")
            releases.extend(data)
            if len(data) < 100:
                break
        else:
            raise ProfileError("Pagination limit exceeded; refusing incomplete collection")
        result[project["slug"]] = releases
    return result


def published_date(value):
    clean_text(value, "published_at", 40)
    if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", value):
        raise ProfileError("Invalid published_at format")
    try:
        return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError as exc:
        raise ProfileError("Invalid published_at date") from exc


def select_releases(config, collections):
    if not isinstance(collections, dict) or set(collections) != {p["slug"] for p in sources(config)}:
        raise ProfileError("Missing or unexpected release source")
    selected, skipped, accepted = [], {}, 0
    for project in sources(config):
        data = collections[project["slug"]]
        if not isinstance(data, list):
            raise ProfileError("Unexpected release collection")
        candidates, seen = [], set()
        for release in data:
            if not isinstance(release, dict):
                raise ProfileError("Unexpected release record")
            if type(release.get("draft")) is not bool or type(release.get("prerelease")) is not bool:
                raise ProfileError("Missing release visibility flags")
            if release["draft"] or release["prerelease"]:
                skipped["draft/prerelease"] = skipped.get("draft/prerelease", 0) + 1
                continue
            tag = clean_text(release.get("tag_name"), "release tag", 200)
            url = release.get("html_url")
            parts = https_url(url, "github.com")
            expected_path = f"/{config['owner']}/{project['slug']}/releases/tag/"
            if (not parts.path.startswith(expected_path) or parts.query or parts.fragment
                    or unquote(parts.path[len(expected_path):]) != tag):
                raise ProfileError("Release URL does not match allowlisted repository/tag")
            date = published_date(release.get("published_at"))
            key = (tag, url, date)
            if key in seen:
                skipped["duplicate"] = skipped.get("duplicate", 0) + 1
                continue
            seen.add(key)
            candidates.append({"project": project, "tag": tag, "url": url, "date": date})
            accepted += 1
        if candidates:
            candidates.sort(key=lambda r: (-r["date"].timestamp(), r["tag"], r["url"]))
            selected.append(candidates[0])
        else:
            skipped["no stable releases"] = skipped.get("no stable releases", 0) + 1
    selected.sort(key=lambda r: (-r["date"].timestamp(), r["project"]["stable_display_order"]))
    return selected[:4], accepted, skipped


def render_releases(releases):
    if not releases:
        return "<p>No stable public releases to show yet.</p>"
    lines = ['<table>',
             '<thead><tr><th scope="col">Project</th><th scope="col">Release</th><th scope="col">Date (UTC)</th></tr></thead>',
             '<tbody>']
    for r in releases:
        date = r["date"]
        label = html.escape(r["project"]["label"])
        icon = r["project"].get("icon", "package")
        if icon not in ICONS:
            raise ProfileError("Invalid project icon")
        visual = f'<img src="assets/icons/{icon}.svg" width="20" height="20" alt="{ICONS[icon]}">'
        tag = html.escape(r["tag"])
        url = html.escape(r["url"], quote=True)
        readable = f"{date.day:02d} {MONTHS[date.month - 1]} {date.year}"
        lines.append(f'<tr><td>{visual} <strong>{label}</strong></td>'
                     f'<td><a href="{url}">{tag}</a></td><td>{readable}</td></tr>')
    return "\n".join(lines + ["</tbody>", "</table>"])


def block_bounds(content):
    if content.count(START) != 1 or content.count(END) != 1:
        raise ProfileError("README must contain exactly one pair of LIVE_RELEASES markers")
    start = content.index(START) + len(START)
    end = content.index(END)
    if end < start:
        raise ProfileError("LIVE_RELEASES markers out of order")
    return start, end


def replace_block(content, rendered):
    start, end = block_bounds(content)
    newline = b"\r\n" if content[start:start + 2] == b"\r\n" else b"\n"
    body = rendered.encode("utf-8").replace(b"\n", newline)
    return content[:start] + newline + body + newline + content[end:]


def assert_only_block(before, after):
    bs, be = block_bounds(before)
    ats, ate = block_bounds(after)
    if before[:bs] != after[:ats] or before[be:] != after[ate:]:
        raise ProfileError("Change outside LIVE_RELEASES refused")


def atomic_write(path, original, updated):
    path = Path(path)
    if path.read_bytes() != original:
        raise ProfileError("README changed during refresh; retry on latest revision")
    fd, name = tempfile.mkstemp(prefix=".profile-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(updated)
        if path.read_bytes() != original:
            raise ProfileError("README changed during refresh")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def report(summary):
    print(json.dumps(summary, sort_keys=True))
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        safe = html.escape(json.dumps(summary, sort_keys=True))
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(f"### Profile refresh\n<pre>{safe}</pre>\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "data/profile.json")
    parser.add_argument("--readme", type=Path, default=ROOT / "README.md")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--fixture", type=Path)
    mode.add_argument("--live", action="store_true", help="Explicitly allow anonymous GitHub GET requests")
    parser.add_argument("--dry-run", action="store_true", help="Render/check without writing")
    parser.add_argument("--check", action="store_true", help="No write; exit 1 if block is stale")
    parser.add_argument("--snapshot-out", type=Path, help="Write sanitized source facts for the commit job")
    summary = {"sources_checked": 0, "releases_accepted": 0, "block_changed": False, "skipped_reasons": {}}
    try:
        args = parser.parse_args(argv)
        config = load_config(args.config)
        before = args.readme.read_bytes()
        block_bounds(before)
        if args.fixture:
            collections = json.loads(args.fixture.read_text(encoding="utf-8"))
        elif args.live:
            collections = fetch_sources(config)
        else:
            raise ProfileError("Choose --fixture or explicitly enable --live")
        summary["sources_checked"] = len(collections) if isinstance(collections, dict) else 0
        chosen, accepted, skipped = select_releases(config, collections)
        updated = replace_block(before, render_releases(chosen))
        assert_only_block(before, updated)
        summary.update(releases_accepted=accepted, block_changed=updated != before, skipped_reasons=skipped)
        if args.snapshot_out:
            # Never persist titles, bodies, authors, assets or API credentials.
            minimal = {slug: [{k: r.get(k) for k in ("draft", "prerelease", "tag_name", "html_url", "published_at")}
                              for r in values] for slug, values in collections.items()}
            args.snapshot_out.write_text(json.dumps(minimal, sort_keys=True) + "\n", encoding="utf-8")
        if not args.dry_run and not args.check and updated != before:
            atomic_write(args.readme, before, updated)
        report(summary)
        return int(args.check and updated != before)
    except (ProfileError, OSError, ValueError, TypeError, KeyError) as exc:
        # Errors are classified, never dump response payloads, headers or credentials.
        summary["error"] = str(exc) if isinstance(exc, ProfileError) else type(exc).__name__
        report(summary)
        return 2


if __name__ == "__main__":
    sys.exit(main())

