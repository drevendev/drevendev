# Public profile contract

Source identifier: DREVEN-GITHUB-PROFILE-001, v1.0, 26 October 2026.
This is the public, sanitized implementation contract. The original owner-supplied
document is retained privately; no local file path or private operational context is published.

- Public profile: the root README of this repository, drevendev/drevendev.
- Public language: English. Voice: direct and conversational; explain what a project
  does before adding a joke. Avoid repeated slogans and forced self-deprecation.
- Exact heading: "Hello there! I'm Dreven"
- Introduction and project copy are editable in data/profile.json. The owner's
  October 2026 editorial revision replaces the original fixed subtitle.
- Exactly four featured projects, in order: HungryCrab, Devostasis,
  BeautifulRepo, TradeCraft (repository: trade_simulation).
- Exactly seven secondary projects: Dayflare, Scriptorium, Quillgrain,
  PatchPitch, Compost Club, Playmancer, EndlessZenFramework.
- Show games/music/social links quietly. Do not publish employers, job titles,
  career claims, awards, literary portfolios, private sources, or unpublished plans.
- Original static SVGs, light/dark variants, no trackers or third-party card services.
- Readability and accessibility take precedence over the optional two-column grid.
- All editable project/link data lives in ../data/profile.json. No repository discovery.
- Runtime updates only the unique LIVE_RELEASES block; all other bytes are preserved.
- Read only stable public GitHub Releases from configured sources. At most four
  repositories, one release each, ordered by publication date and stable config order.
- Render releases in a table with Project, Release, and Date (UTC) columns.
- No private endpoints, personal tokens, LLMs, paid APIs, body/title reuse or activity fabrication.
- Anonymous HTTPS GET requests go only to the expected GitHub API release endpoints.
  Release links must match the exact configured owner/repository/tag. Redirects are refused.
- A failed source aborts publication. A successful empty collection is valid.
- GitHub Actions requests two runs daily, 02:17 and 14:17 UTC, plus manual dispatch.
  Permissions are read-only except the publication job's repository-scoped contents write.
  A second unchanged run creates no commit. Force pushes are prohibited.
- Protected branches retain their protection. Use a reviewed PR/operator procedure
  when direct writes are unavailable.
- Acceptance: offline tests, live Action update/no-op evidence, public profile check,
  and GitHub-render screenshots at approximately 390/768/1280 px in both themes.
- Profile bio and repository pins are separate operations with explicit completion status.

Merged-PR feeds, social posting, extra graphs and other automation are outside V1.

