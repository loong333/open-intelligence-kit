#!/usr/bin/env python
"""Batch deep-read public URLs and create a source bundle index."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .artifact_paths import bundle_slug, make_run_id, url_slug
from .source_grading import ALLOWED_GRADES

DEFAULT_WEBREAD_ROOT = Path("./artifacts/WebReads")
DEFAULT_BUNDLE_ROOT = Path("./artifacts/SourceBundles")


@dataclass
class PageRecord:
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
    error: str = ""
    tool: str = "crawl4ai"


@dataclass
class BundleRecord:
    bundle_name: str
    run_id: str
    created_at: str
    total_urls: int
    successful: int
    failed: int
    min_markdown_length: int
    source_grade: str
    note: str
    output_bundle_json: str
    output_bundle_markdown: str
    pages: list[PageRecord]
    tool: str = "batch_read_urls.py"


def validate_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"URL must start with http:// or https://: {url}")
    if not parsed.netloc:
        raise ValueError(f"URL must include a host: {url}")
    return url.strip()


def read_urls_file(path: str) -> list[str]:
    urls: list[str] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        urls.append(text)
    return urls


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def extract_title(markdown: str, fallback_url: str) -> str:
    for line in markdown.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()[:160]
    return urlparse(fallback_url).netloc or fallback_url


def markdown_with_frontmatter(record: PageRecord, body: str) -> str:
    fields = {
        "url": record.url,
        "run_id": record.run_id,
        "fetched_at": record.fetched_at,
        "success": record.success,
        "status_code": record.status_code,
        "source_grade": record.source_grade,
        "tool": record.tool,
        "note": record.note,
    }
    lines = ["---"]
    for key, value in fields.items():
        text = str(value).replace("\n", " ").replace('"', "'")
        lines.append(f'{key}: "{text}"')
    lines.extend(["---", "", body])
    return "\n".join(lines).rstrip() + "\n"


async def crawl_one(crawler: object, url: str, args: argparse.Namespace, output_dir: Path) -> PageRecord:
    fetched_moment = datetime.now(timezone.utc).replace(microsecond=0)
    fetched_at = fetched_moment.isoformat()
    run_id = make_run_id(fetched_moment)
    try:
        result = await crawler.arun(url=url)  # type: ignore[attr-defined]
        success = bool(getattr(result, "success", False))
        status_code = getattr(result, "status_code", None)
        markdown = str(getattr(result, "markdown", "") or "")
        title = extract_title(markdown, url)
        slug = url_slug(url, title)
        markdown_path = output_dir / f"{slug}-{run_id}.md"
        metadata_path = output_dir / f"{slug}-{run_id}.metadata.json"
        record = PageRecord(
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
        if status_code is not None and int(status_code) >= 400:
            record.error = f"HTTP status_code={status_code}"
        elif len(markdown) < args.min_markdown_length:
            record.error = f"markdown too short: {len(markdown)} < {args.min_markdown_length}"
        elif not success:
            record.error = "crawl4ai reported success=false"
        markdown_path.write_text(markdown_with_frontmatter(record, markdown), encoding="utf-8")
        metadata_path.write_text(json.dumps(asdict(record), ensure_ascii=False, indent=2), encoding="utf-8")
        return record
    except Exception as exc:
        slug = url_slug(url)
        markdown_path = output_dir / f"{slug}-{run_id}.failed.md"
        metadata_path = output_dir / f"{slug}-{run_id}.metadata.json"
        record = PageRecord(
            url=url,
            run_id=run_id,
            fetched_at=fetched_at,
            success=False,
            status_code=None,
            markdown_length=0,
            source_grade=args.source_grade,
            note=args.note,
            title=urlparse(url).netloc or url,
            output_markdown=str(markdown_path),
            output_metadata=str(metadata_path),
            error=f"{type(exc).__name__}: {exc}",
        )
        markdown_path.write_text(markdown_with_frontmatter(record, ""), encoding="utf-8")
        metadata_path.write_text(json.dumps(asdict(record), ensure_ascii=False, indent=2), encoding="utf-8")
        return record


def bundle_markdown(bundle: BundleRecord) -> str:
    lines = [
        f"# Source Bundle: {bundle.bundle_name}",
        "",
        f"- Created: {bundle.created_at}",
        f"- Run ID: {bundle.run_id}",
        f"- Total URLs: {bundle.total_urls}",
        f"- Successful: {bundle.successful}",
        f"- Failed: {bundle.failed}",
        f"- Source grade: {bundle.source_grade}",
        f"- Note: {bundle.note}",
        "",
        "## Pages",
        "",
    ]
    for i, page in enumerate(bundle.pages, 1):
        status = "PASS" if page.success and not page.error else "FAIL"
        lines.extend([
            f"### {i}. {page.title}",
            "",
            f"- Status: {status}",
            f"- URL: {page.url}",
            f"- HTTP: {page.status_code}",
            f"- Markdown length: {page.markdown_length}",
            f"- Markdown artifact: {page.output_markdown}",
            f"- Metadata artifact: {page.output_metadata}",
        ])
        if page.error:
            lines.append(f"- Error: {page.error}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch deep-read public URLs into immutable source bundles.")
    parser.add_argument("--bundle-name", required=True, help="Human-readable bundle name")
    parser.add_argument("--url", action="append", default=[], help="Public URL; can be repeated")
    parser.add_argument("--urls-file", help="UTF-8 text file with one URL per line; # comments allowed")
    parser.add_argument("--source-grade", default="unknown", choices=sorted(ALLOWED_GRADES))
    parser.add_argument("--note", default="", help="Short note shared by all URLs")
    parser.add_argument("--min-markdown-length", type=int, default=200)
    parser.add_argument("--webread-root", default=str(DEFAULT_WEBREAD_ROOT))
    parser.add_argument("--bundle-root", default=str(DEFAULT_BUNDLE_ROOT))
    parser.add_argument("--allow-partial", action="store_true", help="Exit 0 even if some URLs fail")
    return parser.parse_args(argv)


async def amain(argv: list[str]) -> int:
    args = parse_args(argv)
    raw_urls = list(args.url)
    if args.urls_file:
        raw_urls.extend(read_urls_file(args.urls_file))
    if not raw_urls:
        print("ERROR: provide at least one --url or --urls-file", file=sys.stderr)
        return 2
    try:
        urls = unique_preserve_order([validate_url(url) for url in raw_urls])
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        from crawl4ai import AsyncWebCrawler
    except Exception as exc:  # pragma: no cover - runtime environment guard
        print("ERROR: crawl4ai is not importable. Install with: pip install -e .", file=sys.stderr)
        print(f"IMPORT_ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    date_dir = datetime.now().strftime("%Y-%m-%d")
    webread_dir = Path(args.webread_root) / date_dir
    bundle_dir = Path(args.bundle_root) / date_dir
    webread_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    pages: list[PageRecord] = []
    async with AsyncWebCrawler() as crawler:
        for url in urls:
            pages.append(await crawl_one(crawler, url, args, webread_dir))

    successful = sum(1 for page in pages if page.success and not page.error)
    failed = len(pages) - successful
    created_moment = datetime.now(timezone.utc).replace(microsecond=0)
    created_at = created_moment.isoformat()
    run_id = make_run_id(created_moment)
    slug = bundle_slug(args.bundle_name, urls)
    bundle_json_path = bundle_dir / f"{slug}-{run_id}.json"
    bundle_md_path = bundle_dir / f"{slug}-{run_id}.md"
    bundle = BundleRecord(
        bundle_name=args.bundle_name,
        run_id=run_id,
        created_at=created_at,
        total_urls=len(pages),
        successful=successful,
        failed=failed,
        min_markdown_length=args.min_markdown_length,
        source_grade=args.source_grade,
        note=args.note,
        output_bundle_json=str(bundle_json_path),
        output_bundle_markdown=str(bundle_md_path),
        pages=pages,
    )
    bundle_json_path.write_text(json.dumps(asdict(bundle), ensure_ascii=False, indent=2), encoding="utf-8")
    bundle_md_path.write_text(bundle_markdown(bundle), encoding="utf-8")
    print(json.dumps(asdict(bundle), ensure_ascii=False, indent=2))
    if failed and not args.allow_partial:
        return 1
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(amain(sys.argv[1:])))


if __name__ == "__main__":
    main()
