#!/usr/bin/env python
"""Deep-read a public URL and save Markdown + metadata artifacts."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .artifact_paths import make_run_id, url_slug
from .source_grading import ALLOWED_GRADES

DEFAULT_OUTPUT_ROOT = Path("./artifacts/WebReads")


@dataclass
class ReadMetadata:
    url: str
    run_id: str
    fetched_at: str
    success: bool
    status_code: int | None
    markdown_length: int
    source_grade: str
    note: str
    title: str
    output_markdown: str
    output_metadata: str
    tool: str = "crawl4ai"
    tool_purpose: str = "responsible public webpage deep read"


def validate_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URL must start with http:// or https://")
    if not parsed.netloc:
        raise ValueError("URL must include a host")
    return url.strip()


def extract_title(markdown: str, fallback_url: str) -> str:
    for line in markdown.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()[:160]
    parsed = urlparse(fallback_url)
    return parsed.netloc or fallback_url


def markdown_with_frontmatter(meta: ReadMetadata, body: str) -> str:
    fields: dict[str, Any] = {
        "url": meta.url,
        "run_id": meta.run_id,
        "fetched_at": meta.fetched_at,
        "success": meta.success,
        "status_code": meta.status_code,
        "source_grade": meta.source_grade,
        "tool": meta.tool,
        "note": meta.note,
    }
    lines = ["---"]
    for key, value in fields.items():
        text = str(value).replace("\n", " ").replace('"', "'")
        lines.append(f'{key}: "{text}"')
    lines.extend(["---", "", body])
    return "\n".join(lines).rstrip() + "\n"


async def crawl(url: str) -> tuple[bool, int | None, str]:
    try:
        from crawl4ai import AsyncWebCrawler
    except Exception as exc:  # pragma: no cover - runtime environment guard
        print("ERROR: crawl4ai is not importable. Install with: pip install -e .", file=sys.stderr)
        print(f"IMPORT_ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        success = bool(getattr(result, "success", False))
        status_code = getattr(result, "status_code", None)
        markdown = str(getattr(result, "markdown", "") or "")
        return success, status_code, markdown


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deep-read a public URL into immutable research artifacts.")
    parser.add_argument("url", help="Public http(s) URL to deep-read")
    parser.add_argument("--source-grade", default="unknown", choices=sorted(ALLOWED_GRADES))
    parser.add_argument("--note", default="", help="Short note about why this URL was read")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Artifact root")
    parser.add_argument("--min-markdown-length", type=int, default=200, help="Fail if Markdown is shorter")
    return parser.parse_args(argv)


async def amain(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        url = validate_url(args.url)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    fetched_moment = datetime.now(timezone.utc).replace(microsecond=0)
    fetched_at = fetched_moment.isoformat()
    run_id = make_run_id(fetched_moment)
    date_dir = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(args.output_root) / date_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    success, status_code, markdown = await crawl(url)
    title = extract_title(markdown, url)
    slug = url_slug(url, title)
    markdown_path = output_dir / f"{slug}-{run_id}.md"
    metadata_path = output_dir / f"{slug}-{run_id}.metadata.json"

    meta = ReadMetadata(
        url=url,
        run_id=run_id,
        fetched_at=fetched_at,
        success=success,
        status_code=status_code,
        markdown_length=len(markdown),
        source_grade=args.source_grade,
        note=args.note,
        title=title,
        output_markdown=str(markdown_path),
        output_metadata=str(metadata_path),
    )

    markdown_path.write_text(markdown_with_frontmatter(meta, markdown), encoding="utf-8")
    metadata_path.write_text(json.dumps(asdict(meta), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(asdict(meta), ensure_ascii=False, indent=2))

    if not success:
        print("ERROR: crawl4ai reported success=false", file=sys.stderr)
        return 1
    if status_code is not None and int(status_code) >= 400:
        print(f"ERROR: HTTP status_code={status_code}", file=sys.stderr)
        return 1
    if len(markdown) < args.min_markdown_length:
        print(f"ERROR: markdown too short: {len(markdown)} < {args.min_markdown_length}", file=sys.stderr)
        return 1
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(amain(sys.argv[1:])))


if __name__ == "__main__":
    main()
