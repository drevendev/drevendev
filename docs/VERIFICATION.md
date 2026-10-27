# Verification record

## Preflight — 27 October 2026

- Target repository: public drevendev/drevendev. Default branch: master.
- Account authorization confirmed. No branch protection/rulesets at bootstrap.
- Actions enabled. No other repository or scheduler changed.
- All eleven explicitly approved source repositories were individually confirmed public.
  No account-wide repository listing or private content search was performed.
- The short project descriptions were checked against each source README.
- HungryCrab's observed latest stable release was v0.6.6; historical versions in the
  original specification were not hardcoded into the renderer.
- CompostClub returned a successful empty Releases collection.

External HTTP/content checks:

| Destination | Result | Handling |
| --- | --- | --- |
| itch.io | 200; Dreven Games page | Included |
| Google Play | 200; Android Apps by Dreven Games | Included |
| Spotify / Dr. Weeb | 200; matching artist title | Included |
| Spotify / Robot Anime | 200; matching artist title | Included |
| LinkedIn | 999 anti-automation response | Supplied URL retained; verification unknown |
| HungryCrab PyPI | 200 client challenge, package page not verified | Optional package CTA omitted |
| TradeCraft milestone viewer | 200; M4 one-region closed economy viewer | Included with exact milestone-viewer label |
| BeautifulRepo Start here | Heading/anchor present in current repository README | Included |

Checks establish destination identity/accessibility at the observation time, not
end-user availability in every region or a guarantee that all application features work.
No blocked external URL was replaced with a guessed alternative.

## Local verification

Python 3.14 on Windows: 39 offline unit/integration tests passed.
The local Git tests verify no-op publication, README-only publication and a rejected
push that preserves a concurrent human commit. No network is used by the tests.

Static configuration consistency and fixture dry-run passed.
Live dry-run, GitHub CI, visual evidence and real Action run receipts are recorded
during publication acceptance below.

