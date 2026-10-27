# Verification record

## Latest design acceptance — cards and ECG pulse

Owner-requested follow-up in [PR #4](https://github.com/drevendev/drevendev/pull/4).
This section supersedes the earlier single-column text-block design record below.

- Devostasis uses an original ECG pulse in both hero SVGs, its project card and
  release icon selection. The anatomical heart is no longer displayed.
- Four equal rectangular local SVG cards wrap into two columns on a wide README,
  and one column on narrow screens. Each has a complete text alternative; ordinary
  repository/demo CTA links remain visible outside the images.
- LinkedIn, itch.io, Google Play and Spotify use local static banner links.
  The lower games/music block includes the corresponding game and artist banners.
- Every release row has one 20 by 20 px icon; package is the fallback. Icon names
  are validated against the curated local set, including the ECG pulse.
- Project facts, four featured identities, seven secondary projects, release
  sources, social destinations and Actions cadence are unchanged.
- 41 offline tests passed on Windows/Python 3.14 and in PR CI on Python 3.11/3.14.
  Static config/README/asset checks passed. Actual public collection accepted
  37 stable records across six sources before regenerating the release block.
- [CI for the tested source revision](https://github.com/drevendev/drevendev/actions/runs/40589782841)
  passed; source revision: d8dc17aa8bd16c7b70f8e88e7a97f32ead114c1f.
  Publication and post-merge Action receipts are linked from PR #4.

Actual GitHub rendering of the PR branch was checked in six combinations:

| Width | Light | Dark |
| --- | --- | --- |
| 390 px | [Cards](screenshots/cards-light-390.jpg) | [Cards](screenshots/cards-dark-390.jpg) |
| 768 px | [Cards](screenshots/cards-light-768.jpg) | [Cards](screenshots/cards-dark-768.jpg) |
| 1280 px | [Cards](screenshots/cards-light-1280.jpg) | [Cards](screenshots/cards-dark-1280.jpg) |

[Hero, ECG and link banners](screenshots/cards-hero-dark.jpg) ·
[Uniform release icons](screenshots/cards-releases-dark.jpg) ·
[Layout measurements](screenshots/cards-metrics.json).

At 1280 px, cards measured 400 px each in a 2x2 arrangement. At 768 px and
390 px they wrapped into one column, measuring approximately 391 px and 309 px.
All card images loaded. Page scrollWidth equalled clientWidth in each tested
size, so there was no horizontal page overflow. All four release icon rectangles
measured 20x20 px with the same horizontal start position.

The cards and buttons are built offline from the one profile config using
scripts/build_assets.py, invoked by the explicit authoring/check command.
Scheduled refresh still writes only LIVE_RELEASES.


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

## Published acceptance — 27 October 2026

Profile: https://github.com/drevendev
Repository: https://github.com/drevendev/drevendev
Accepted product revision: fa4f0ae6336de915388448866f85965204479cf5.

- [Implementation PR #1](https://github.com/drevendev/drevendev/pull/1): merged.
- [Owner-requested emoji/tagline PR #2](https://github.com/drevendev/drevendev/pull/2): merged.
- [CI on the accepted default-branch revision](https://github.com/drevendev/drevendev/actions/runs/40587236678):
  both Python 3.11 and 3.14 jobs passed all 39 offline tests and static/fixture checks.
- Final tagline: "Chew through a repository. Keep what is useful."
- Public profile was opened in GitHub and independently fetched without authentication:
  HTTP 200, correct heading/tagline, all 11 project links, all five supplied social
  destinations and the four real displayed release versions were present inside
  the rendered README article.

### Real Actions evidence

| Run | Outcome |
| --- | --- |
| [Initial refresh 40586231536](https://github.com/drevendev/drevendev/actions/runs/40586231536) | SUCCESS; six sources checked; 37 valid stable release records accepted; block changed |
| [Repeat refresh 40586357174](https://github.com/drevendev/drevendev/actions/runs/40586357174) | SUCCESS; identical facts; block_changed=false; commit_created=false |
| [After emoji/tagline changes 40587246193](https://github.com/drevendev/drevendev/actions/runs/40587246193) | SUCCESS; static edits preserved; block_changed=false; commit_created=false |

Initial publication created bot commit
[2ca816e6b2b15d44dd2bc8d25f3834ff22b6b969](https://github.com/drevendev/drevendev/commit/2ca816e6b2b15d44dd2bc8d25f3834ff22b6b969)
with the exact requested message. Only README.md changed. Comparing its parent
and result with assert_only_block confirmed byte-for-byte preservation of both
manual regions. The repeat run left the remote HEAD at that same commit.

The empty CompostClub collection was reported as no stable releases, not a failed
source. The final displayed projects are HungryCrab, PatchPitch, BeautifulRepo and
TradeCraft, ordered by published_at. This does not promote PatchPitch to featured.

[Refresh workflow](https://github.com/drevendev/drevendev/actions/workflows/refresh-profile.yml)
is active on master, with 02:17/14:17 UTC schedule and workflow_dispatch.
[Read-only PR CI](https://github.com/drevendev/drevendev/actions/workflows/ci.yml) is enabled.
These receipts prove real manual execution of the scheduled workflow's jobs.
A clock-triggered run was not awaited or claimed; future cron delivery remains best effort.

### Visual and accessibility acceptance

All screenshots below are actual published GitHub profile renders at the accepted
product revision, after the emoji/tagline change. They are viewport captures rather
than a local mockup. Additional lower-section captures show the release feed,
secondary catalogue and games/music links.

| Width | Light theme | Dark theme |
| --- | --- | --- |
| 390 px | [Mobile light](screenshots/light-390.jpg) | [Mobile dark](screenshots/dark-390.jpg) |
| 768 px | [Tablet light](screenshots/light-768.jpg) | [Tablet dark](screenshots/dark-768.jpg) |
| 1280 px | [Desktop light](screenshots/light-1280.jpg) | [Desktop dark](screenshots/dark-1280.jpg) |

Supplementary views: [desktop lower sections](screenshots/light-workbench-1280.jpg)
and [mobile lower sections](screenshots/light-workbench-390.jpg).

The initial 2x2 table was rejected after the real 390 px render produced narrow,
fragmented columns. The accepted layout uses four equally prominent full-width
featured blocks. On the mobile article, clientWidth and scrollWidth were both
293 CSS px; on desktop they were both 831 CSS px. No horizontal README overflow
was present. All eleven project links and four featured headings were also
checked in the actual rendered article.

Both banner themes loaded successfully. All essential banner meaning is repeated
as README text, and the loaded image has a meaningful alt.
SVG text/background contrast is 11.74:1 in light and 13.62:1 in dark.
Small decorative labels are not the sole source of any information.

During testing, GitHub's picture source selection followed the system scheme even
when GitHub was set manually to light. Both static SVGs therefore also adapt their
colours using embedded prefers-color-scheme CSS inherited from the containing
page. The two assets and required picture/source structure remain in place.
Actual light/dark profile screenshots confirm the visible palettes.

The owner requested recognizable emoji illustrations rather than schematic
symbols. The final banners embed licensed Twemoji crab/heart/fireworks/scales
art locally; [complete credits and license](ASSET_CREDITS.md) are provided.
No external emoji service, JavaScript, font or runtime package was introduced.

Keyboard navigation was exercised on the actual profile: Tab from LinkedIn
reached itch.io, and Tab from the first project CTA reached the next GitHub
heading permalink. Links remain normal text anchors. This is a browser keyboard
check, not a claim of a spoken screen-reader audit.

### Separate account settings

- Bio saved and read back: "I make things. Tools, games & experiments."
- Exactly four pins saved, reordered with GitHub's keyboard controls, and verified
  after reload: HungryCrab, Devostasis, BeautifulRepo, trade_simulation.
- Original appearance setting (Sync with system; Light default / Dark default)
  was restored after theme testing. Temporary viewport overrides were cleared.
- No remaining manual operation is needed for the profile or pins.

### Scope and remaining limits

LinkedIn remains unverified because the automated HTTP check returned 999.
The optional PyPI CTA remains omitted because the destination presented a client
challenge. The supplied LinkedIn URL was retained without availability claims.

No website in another repository, private data source, existing agent or scheduler
was modified. No trophies, counters, streak widgets or analytics were added to
the README. GitHub's own existing profile chrome (including achievements and
contribution UI visible in some screenshots) is outside the authored README.

Merged-PR feeds, social autoposting, extra visualizations and release-dispatch
integrations remain outside V1. GitHub may disable inactive public-repository
schedules after 60 days; the maintenance guide explains manual re-enablement.
