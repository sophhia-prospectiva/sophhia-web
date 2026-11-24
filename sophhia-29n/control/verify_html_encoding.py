#!/usr/bin/env python3
"""Validate UTF-8 HTML before publishing and, optionally, compare the live copy.

Examples:
  python3 verify_html_encoding.py public/index.html public/ciudadana/index.html
  python3 verify_html_encoding.py public/index.html public/ciudadana/index.html \
      --root public --base-url https://example.org/sophhia-29n/ --json

Only the Python standard library is required. Exit status: 0 = all checks pass,
1 = validation/HTTP failure, 2 = invalid CLI arguments. This does not assess
editorial content or replace a visual browser check.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import Request, urlopen


def is_utf8(value: str) -> bool:
    return value.strip().lower().replace("_", "-") in {"utf-8", "utf8"}


class DocumentCheck(HTMLParser):
    """Check the document wrapper; ignore SVG titles and literal script text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.starts: Counter[str] = Counter()
        self.ends: Counter[str] = Counter()
        self.doctypes: list[str] = []
        self.charsets: list[str] = []
        self.errors: list[str] = []
        self.in_html = False
        self.in_head = False
        self.in_title = False
        self.head_titles = 0
        self.closed_head_titles = 0
        self.title_parts: list[str] = []

    def handle_decl(self, decl: str) -> None:
        if decl.lower().startswith("doctype"):
            self.doctypes.append(decl)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag in {"html", "head", "body"}:
            self.starts[tag] += 1
        if tag == "html":
            self.in_html = True
        elif tag == "head":
            if not self.in_html or self.starts["body"]:
                self.errors.append("<head> must be inside <html>, before <body>")
            self.in_head = True
        elif tag == "body":
            if not self.in_html or self.in_head or not self.ends["head"]:
                self.errors.append("<body> must follow </head> inside <html>")
        elif tag == "title" and self.in_head:
            self.head_titles += 1
            self.in_title = True
        elif tag == "meta" and self.in_head:
            if "charset" in values:
                self.charsets.append(values["charset"] or "")
            if (values.get("http-equiv") or "").strip().lower() == "content-type":
                match = re.search(
                    r"charset\s*=\s*[\"']?([^\s;\"']+)",
                    values.get("content") or "",
                    re.IGNORECASE,
                )
                if match:
                    self.charsets.append(match.group(1))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"html", "head", "body"}:
            self.ends[tag] += 1
        if tag == "title" and self.in_title:
            self.closed_head_titles += 1
            self.in_title = False
        elif tag == "head":
            if self.in_title:
                self.errors.append("<title> is not closed before </head>")
            self.in_head = False
            self.in_title = False
        elif tag == "html":
            self.in_html = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    def finish(self) -> tuple[str, list[str]]:
        self.close()
        if len(self.doctypes) != 1 or not re.match(
            r"doctype\s+html(?:\s|$)", self.doctypes[0] if self.doctypes else "", re.I
        ):
            self.errors.append("Exactly one HTML doctype is required")
        for tag in ("html", "head", "body"):
            if self.starts[tag] != 1 or self.ends[tag] != 1:
                self.errors.append(
                    f"Exactly one <{tag}> and </{tag}> required "
                    f"(found {self.starts[tag]}/{self.ends[tag]})"
                )
        if not self.charsets:
            self.errors.append("A UTF-8 charset declaration is required in <head>")
        elif any(not is_utf8(value) for value in self.charsets):
            self.errors.append(f"Non-UTF-8 or empty charset declaration: {self.charsets!r}")
        title = " ".join("".join(self.title_parts).split())
        if self.head_titles != 1 or self.closed_head_titles != 1 or not title:
            self.errors.append("Exactly one nonempty, closed <title> inside <head> required")
        return title, self.errors


def validate_bytes(data: bytes) -> dict:
    result = {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "title": None,
        "errors": [],
    }
    errors = result["errors"]
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        errors.append(f"Invalid UTF-8 at byte {exc.start}: {exc.reason}")
        return result
    if "\ufffd" in text:
        errors.append(f"Replacement character U+FFFD occurs {text.count(chr(0xfffd))} times")
    controls = Counter(
        ord(char)
        for char in text
        if (ord(char) < 0x20 and char not in "\t\n\r") or 0x7F <= ord(char) <= 0x9F
    )
    if controls:
        summary = ", ".join(f"U+{code:04X} x{count}" for code, count in sorted(controls.items()))
        errors.append(f"Unexpected control characters (including NUL if present): {summary}")
    parser = DocumentCheck()
    try:
        parser.feed(text)
        result["title"], wrapper_errors = parser.finish()
        errors.extend(wrapper_errors)
    except Exception as exc:
        errors.append(f"HTML parsing failed: {type(exc).__name__}: {exc}")
    return result


def verify_live(url: str, expected: bytes, timeout: float) -> dict:
    result = {"url": url, "errors": []}
    errors = result["errors"]
    request = Request(
        url,
        headers={
            "Accept": "text/html",
            "Accept-Encoding": "identity",
            "User-Agent": "SOPHHIA-HTML-Verification/1.0",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result["status"] = response.status
            result["final_url"] = response.url
            result["content_type"] = response.headers.get("Content-Type", "")
            result["content_encoding"] = response.headers.get("Content-Encoding", "")
            charset = response.headers.get_content_charset()
            result["http_charset"] = charset
            if response.status != 200:
                errors.append(f"Expected HTTP 200; received {response.status}")
            if response.headers.get_content_type() != "text/html":
                errors.append(f"Expected Content-Type text/html; received {result['content_type']!r}")
            if charset and not is_utf8(charset):
                errors.append(f"HTTP charset conflicts with UTF-8: {charset!r}")
            encoding = result["content_encoding"].strip().lower()
            if encoding and encoding != "identity":
                errors.append(
                    f"Expected identity Content-Encoding for an exact byte comparison; received {encoding!r}"
                )
                return result
            data = response.read()
        payload = validate_bytes(data)
        result.update({key: value for key, value in payload.items() if key != "errors"})
        errors.extend(payload["errors"])
        result["expected_sha256"] = hashlib.sha256(expected).hexdigest()
        result["bytes_match_local"] = data == expected
        if not result["bytes_match_local"]:
            errors.append("Live bytes differ from the validated local file (SHA-256 mismatch)")
    except HTTPError as exc:
        result["status"] = exc.code
        errors.append(f"HTTP request failed: {exc.code} {exc.reason}")
    except (URLError, OSError, ValueError) as exc:
        errors.append(f"HTTP request failed: {exc}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+", type=Path, help="Local HTML files to validate")
    parser.add_argument("--base-url", help="Published URL corresponding to --root; no cache-busting query is added")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Local publication root (default: current directory)")
    parser.add_argument("--timeout", type=float, default=20, help="HTTP timeout in seconds (default: 20)")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.base_url:
        parsed = urlsplit(args.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.query or parsed.fragment:
            parser.error("--base-url must be an HTTP(S) URL without query or fragment")
    root = args.root.resolve()
    records = []
    for path in args.files:
        record = {"path": str(path.resolve()), "local": {"errors": []}}
        records.append(record)
        try:
            data = path.read_bytes()
        except OSError as exc:
            record["local"]["errors"].append(f"Cannot read file: {exc}")
            continue
        record["local"] = validate_bytes(data)
        if args.base_url and not record["local"]["errors"]:
            try:
                relative = path.resolve().relative_to(root).as_posix()
            except ValueError:
                record["local"]["errors"].append(f"File is outside --root {root}")
                continue
            url = urljoin(args.base_url.rstrip("/") + "/", quote(relative, safe="/"))
            record["live"] = verify_live(url, data, args.timeout)
    ok = all(not part.get("errors") for record in records for part in (record["local"], record.get("live", {})))
    if args.json:
        print(json.dumps({"ok": ok, "files": records}, ensure_ascii=False, indent=2))
    else:
        for record in records:
            for kind in ("local", "live"):
                part = record.get(kind)
                if part is None:
                    continue
                print(f"{'FAIL' if part['errors'] else 'PASS'} {kind}: {part.get('url', record['path'])}")
                if part.get("sha256"):
                    print(f"  {part['bytes']} bytes; SHA-256 {part['sha256']}")
                if part.get("title"):
                    print(f"  Title: {part['title']}")
                for error in part["errors"]:
                    print(f"  ERROR: {error}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
