# Open Intelligence Kit

A lightweight open-source intelligence workflow for AI-assisted research: source discovery, reliability grading, public webpage deep reading, immutable evidence artifacts, source bundles, and decision-ready reports.

This project is **not** a bypass crawler. It is designed for low-frequency, responsible reading of public webpages and for keeping evidence trails behind AI-generated research.

## Core ideas

- **Public-source research**: read public webpages, official docs, changelogs, and reports.
- **Source reliability grading**: label sources as S/A/B/C/D/unknown instead of treating every page equally.
- **Immutable artifacts**: every read gets a `run_id`; repeated reads create new files instead of overwriting evidence.
- **Source bundles**: group related reads into a machine-readable JSON and human-readable Markdown index.
- **Decision-ready reports**: use templates to turn raw pages into concise briefs with uncertainty notes.

## Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows Git Bash: source .venv/Scripts/activate
pip install -e .
```

This toolkit uses [crawl4ai](https://github.com/unclecode/crawl4ai) as the optional webpage-to-Markdown engine. Open Intelligence Kit provides the research workflow, source grading, immutable artifact naming, and source bundle structure.

`crawl4ai` may need browser dependencies depending on your platform. See the upstream `crawl4ai` documentation if the first crawl fails.

## Quick start

Deep-read one URL:

```bash
python -m open_intelligence_kit.deep_read_url \
  https://example.com \
  --source-grade S \
  --note "demo public page" \
  --output-root ./artifacts/WebReads \
  --min-markdown-length 1
```

Batch-read URLs:

```bash
python -m open_intelligence_kit.batch_read_urls \
  --bundle-name demo-source-bundle \
  --source-grade S \
  --url https://example.com \
  --webread-root ./artifacts/WebReads \
  --bundle-root ./artifacts/SourceBundles \
  --min-markdown-length 1
```

Generated files look like:

```text
artifacts/
├─ WebReads/YYYY-MM-DD/<slug>-<hash>-YYYYMMDDTHHMMSSZ.md
├─ WebReads/YYYY-MM-DD/<slug>-<hash>-YYYYMMDDTHHMMSSZ.metadata.json
├─ SourceBundles/YYYY-MM-DD/<bundle>-<hash>-YYYYMMDDTHHMMSSZ.json
└─ SourceBundles/YYYY-MM-DD/<bundle>-<hash>-YYYYMMDDTHHMMSSZ.md
```

## Source reliability grades

| Grade | Source type | Decision use |
|---|---|---|
| S | Official docs, official announcements, laws, standards, code releases | Primary evidence |
| A | Company sites, maintainer blogs, authoritative reports, first-party interviews | Strong reference |
| B | Mainstream media, credible blogs, community discussions | Useful reference |
| C | Social samples, comments, forums, screenshots with context | Signal only |
| D | Marketing reposts, unsourced screenshots, one-off rumors | Lead only |
| unknown | Not graded yet | Do not rely on it |

## Responsible use

Default allowed:

- public webpages
- official docs
- GitHub/package registry pages
- search-indexed pages
- low-frequency manual reads
- user-provided public links

Default forbidden:

- bypassing login, paywalls, captchas, access controls, or anti-bot systems
- bulk scraping private/personal data
- high-frequency crawling without permission
- proxy pools or fingerprint spoofing
- automated scraping of comment sections or private social spaces

See `policies/responsible-use.md`.

## What this project is good for

- AI-assisted market or technical research
- creating source bundles for later review
- keeping auditable evidence behind AI summaries
- comparing official docs, releases, and changelogs
- building small OSINT-style research workflows

## What this project is not

- not a web-scale crawler
- not a scraping bypass toolkit
- not a social-media data harvesting tool
- not a replacement for fact-checking

## License

MIT
