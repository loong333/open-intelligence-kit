# Public Release Review

Review date: 2026-06-30

## Scope

This repository is a sanitized public version of a public-source intelligence workflow. It includes reusable code, templates, and responsible-use policies only.

## Included

- `src/open_intelligence_kit/deep_read_url.py`
- `src/open_intelligence_kit/batch_read_urls.py`
- `src/open_intelligence_kit/artifact_paths.py`
- `src/open_intelligence_kit/source_grading.py`
- `templates/`
- `policies/`
- `docs/`
- `examples/`

## Excluded

- private workspace paths
- personal journals
- private Agent/OS memory
- private trend reports and business judgments
- local database files
- raw internal artifacts
- any account credentials or tokens

## Sanitization checks

Searched for private names, local workspace paths, internal Agent/workspace terminology, provider-specific residues, personal diary/memory terms, and private trend-report entities. No publish-blocking matches were found in public source files after sanitization.

## Verification

Syntax check:

```bash
python -m py_compile src/open_intelligence_kit/*.py
```

Result: passed.

Single URL deep read:

```bash
PYTHONPATH=src python -m open_intelligence_kit.deep_read_url \
  https://example.com \
  --source-grade S \
  --note 'public demo' \
  --output-root ./artifacts/WebReads \
  --min-markdown-length 1
```

Result: passed; generated immutable WebRead markdown and metadata with `run_id`.

Batch source bundle:

```bash
PYTHONPATH=src python -m open_intelligence_kit.batch_read_urls \
  --bundle-name demo \
  --source-grade S \
  --note 'batch demo' \
  --url https://example.com \
  --webread-root ./artifacts/WebReads \
  --bundle-root ./artifacts/SourceBundles \
  --min-markdown-length 1
```

Result: passed; generated SourceBundle JSON and Markdown.

## Remaining before GitHub publish

- Replace placeholder `Homepage = "https://github.com/your-org/open-intelligence-kit"` in `pyproject.toml` after the GitHub repo name is decided.
- Optional: add screenshots or a short demo GIF after public repo is created.
- Optional: run install test in a fresh venv before first tagged release.
