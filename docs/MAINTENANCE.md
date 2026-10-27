# Maintaining this profile

Python 3.11+ and Git are sufficient. The runtime has no third-party Python packages.
Always work in a branch and review the diff before merging.

## Edit public content

The only editable project/social catalogue is [data/profile.json](../data/profile.json).
Change labels, descriptions or links there, then run the explicit authoring command:

~~~sh
python scripts/build_static.py
python scripts/build_static.py --check
python -m unittest discover -s tests -v
~~~

The authoring command preserves the existing live block. It is never called by the
scheduled updater. Do not maintain separate descriptions/links by editing README output.
Presentation changes belong in scripts/build_static.py, scripts/build_assets.py and the two header SVGs. The authoring command also rebuilds and checks static project cards and link banners.
The initial four featured identities and seven secondary identities are covered by
a contract test. An intentional future catalogue replacement must update that
test in the same reviewed PR; a new release never promotes a project.

The default cards layout uses four native HTML cards with selectable text and real links in each card footer. Aligned 400 px layout tables wrap into two columns when space permits and one column on narrow screens. There is no separate CTA list. A clear break keeps the release section below the cards. Legacy grid/single text layouts remain supported. Runtime refresh does not change layout.

The active hero assets are header-profile-light.svg and header-profile-dark.svg. These fresh paths show the current editorial copy without a stale GitHub image cache; both retain the original ECG line for Systems. Older hero files remain historical assets.

Each project has a validated icon name. The default is package; Devostasis uses the original pulse path. Release icons always reserve an equal 20 by 20 px slot. Icon paths cannot point outside the local curated asset set.

Social URLs retain their expected provider hosts. A new provider requires a reviewed
validator update. Do not substitute an unrelated page for an unavailable supplied URL.

## Offline verification

~~~sh
python -m unittest discover -s tests -v
python scripts/build_static.py --check
python scripts/refresh_profile.py --fixture tests/fixtures/releases.json --dry-run
~~~

The fixture is deliberately synthetic. It is test data, not a statement about
published versions. Tests never contact GitHub, Spotify or other external services.
Git publication tests use temporary local repositories and a local bare remote.

CLI contract:

- No network by default: choose --fixture FILE or explicitly opt into --live.
- --dry-run renders and reports without changing README.
- --check also avoids writes; exit 1 means the release block differs.
- Exit 2 means invalid inputs or unavailable sources. Nothing is published.
- --snapshot-out FILE optionally saves sanitized release fields for local diagnosis.
  Keep diagnostic snapshots untracked; they are not an additional source of truth.

## Real refresh and schedule

~~~sh
python scripts/refresh_profile.py --live --dry-run
gh workflow run refresh-profile.yml --repo drevendev/drevendev --ref master
gh run list --repo drevendev/drevendev --workflow refresh-profile.yml --limit 5
~~~

Use the default branch. A workflow file must be merged into that branch before
manual dispatch is available. The cron is 17 2,14 * * * (UTC), in
[refresh-profile.yml](../.github/workflows/refresh-profile.yml).
Edit that file in a PR to change the cadence.

GitHub schedules are best effort. Runs can be delayed/dropped, and GitHub can
disable public-repository schedules after 60 days without repository activity.
Check Actions periodically and re-enable a disabled workflow in the Actions UI.
This project creates no keepalive commits and no additional scheduler.

## What the updater accepts

Only draft=false, prerelease=false releases with nonempty tags, matching GitHub
release URLs and valid UTC publication timestamps. The script reads all pages up
to a safety limit; hitting the limit aborts rather than publishing a partial result.
It ignores release bodies/titles/authors/assets and never echoes API payloads.
HTML-looking tags are escaped as text.

It takes one most recently published stable release per configured source,
then shows up to four projects. Equal publication dates use configured display
order; same-project ties also have a deterministic tag/URL order.
There is no daily refreshed-at timestamp.

A 200 response with [] means no releases. HTTP failures, 403/429, timeout,
malformed JSON, missing source, invalid date/URL, redirect or malformed markers
mean failure. Any such failure preserves the previous README in full.
Transient network/server retries are bounded; rate limits are not hammered.

Each refresh reports sources_checked, releases_accepted, block_changed and
skipped_reasons to the console and Actions summary; failures also report a safe error.
All collected valid candidates are counted as accepted, not just the four displayed.

## Publication and permissions

PR CI is contents:read. Only the refresh commit job has contents:write.
GitHub's token is repository-scoped, not file-scoped: the publication guard also
requires an otherwise clean worktree and proves that only LIVE_RELEASES changed.
Checkout does not persist credentials. The job uses its short-lived GITHUB_TOKEN
only for Git push, never for reading other repositories. No PAT is required.

The verified revision is checked out in both jobs. A concurrent default-branch
commit makes a normal push fail. The other commit wins; rerun on the latest branch.
There is no force push, automatic rebase or overwrite of a human change.
Bot pushes need not trigger another CI run: the refresh workflow tests before writing.

If protection rejects a direct push, retain protection. Prepare the same verified
README-only change in a branch and open a normal PR, or ask the owner to configure
a suitable reviewed publication policy. Do not add a PAT or bypass permission.
Automatic PR creation is not enabled in V1.

For marker failures, restore exactly one START/END pair in the correct order via PR.
For a source failure, fix/remove a source only through an explicit reviewed config
change; do not silently downgrade failures to empty arrays.

## Optional account settings

Bio: I make things. Tools, games & experiments.

Pins: open your profile, Customize your pins, select only HungryCrab, Devostasis,
BeautifulRepo and trade_simulation, save, then drag them into that order.
These account settings are separate from the README and require their own verification.

## Acceptance records

See [VERIFICATION.md](VERIFICATION.md) for dated link observations and publication
evidence. Repeat external checks at publication; HTTP success alone does not establish
the semantics or completeness of an application.

