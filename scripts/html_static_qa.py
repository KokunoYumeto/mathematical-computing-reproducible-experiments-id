from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable, Sequence
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ATTRIBUTES = (
    ("script", "src"),
    ("img", "src"),
    ("source", "src"),
    ("audio", "src"),
    ("video", "src"),
    ("video", "poster"),
    ("track", "src"),
    ("iframe", "src"),
    ("embed", "src"),
    ("object", "data"),
)
RUNTIME_LINK_RELS = {
    "stylesheet",
    "icon",
    "preload",
    "modulepreload",
    "manifest",
    "apple-touch-icon",
}
CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
CSS_IMPORT_RE = re.compile(
    r"@import\s+(?!url\()(['\"])(.*?)\1", re.IGNORECASE
)
LOCAL_PROFILE_MARKERS = (
    b"C:\\Users\\",
    b"C:/Users/",
    b"file:///C:/",
    b"file://C:/",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative_target(page: Path, raw_url: str, output_root: Path) -> tuple[Path, str]:
    split = urlsplit(raw_url)
    if split.scheme or split.netloc:
        raise ValueError(f"URL bukan jalur lokal: {raw_url!r}")
    target_path = unquote(split.path)
    if target_path.startswith("/"):
        candidate = output_root / target_path.lstrip("/")
    elif target_path:
        candidate = page.parent / target_path
    else:
        candidate = page
    candidate = candidate.resolve()
    candidate.relative_to(output_root.resolve())
    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate, unquote(split.fragment)


def _urls_from_srcset(value: str) -> Iterable[str]:
    if value.lstrip().casefold().startswith("data:"):
        return ()
    return tuple(part.strip().split()[0] for part in value.split(",") if part.strip())


def _css_urls(text: str) -> Iterable[str]:
    values = [match.group(2).strip() for match in CSS_URL_RE.finditer(text)]
    values.extend(match.group(2).strip() for match in CSS_IMPORT_RE.finditer(text))
    return tuple(value for value in values if value)


def _runtime_url(
    *,
    origin: Path,
    raw_url: str,
    output_root: Path,
    relative_origin: str,
    errors: list[str],
    resources: set[Path],
    counters: dict[str, int],
) -> None:
    split = urlsplit(raw_url.strip())
    if split.scheme.casefold() == "data":
        counters["embedded_runtime_resources"] += 1
        return
    if split.scheme or split.netloc:
        errors.append(f"sumber daya runtime eksternal {raw_url!r}: {relative_origin}")
        return
    if not split.path and split.fragment:
        return
    try:
        target, _ = safe_relative_target(origin, raw_url, output_root)
    except ValueError:
        errors.append(f"sumber daya keluar dari keluaran {raw_url!r}: {relative_origin}")
        return
    counters["local_runtime_references"] += 1
    if not target.is_file():
        errors.append(f"sumber daya runtime lokal hilang {raw_url!r}: {relative_origin}")
        return
    resources.add(target.resolve())


def _inventory(paths: Iterable[Path], base: Path) -> list[dict[str, object]]:
    return [
        {
            "path": path.relative_to(base).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(paths, key=lambda item: item.relative_to(base).as_posix().casefold())
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate static HTML accessibility and offline link closure."
    )
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    output_root = args.output.resolve()
    output_root.relative_to(ROOT.resolve())
    html_files = sorted(
        (path.resolve() for path in output_root.rglob("*.html") if path.is_file()),
        key=lambda path: path.relative_to(output_root).as_posix().casefold(),
    )
    if not html_files:
        raise RuntimeError("tidak ada halaman HTML untuk diperiksa")

    parsed: dict[Path, BeautifulSoup] = {}
    ids_by_page: dict[Path, set[str]] = {}
    runtime_resources: set[Path] = set()
    errors: list[str] = []
    counters = {
        "pages": len(html_files),
        "links": 0,
        "local_links": 0,
        "external_links": 0,
        "images": 0,
        "mathml_elements": 0,
        "local_runtime_references": 0,
        "embedded_runtime_resources": 0,
        "css_files_checked": 0,
    }
    for page in html_files:
        relative = page.relative_to(output_root).as_posix()
        data = page.read_bytes()
        if any(marker in data for marker in LOCAL_PROFILE_MARKERS):
            errors.append(f"jalur profil lokal bocor: {relative}")
        soup = BeautifulSoup(data, "html.parser")
        parsed[page] = soup
        html = soup.find("html")
        if html is None or html.get("lang") not in {"id", "id-ID"}:
            errors.append(f"bahasa halaman bukan id: {relative}")
        ids = [str(tag.get("id")) for tag in soup.find_all(id=True)]
        if len(ids) != len(set(ids)):
            errors.append(f"ID HTML duplikat: {relative}")
        ids_by_page[page] = set(ids)
        counters["mathml_elements"] += len(soup.find_all("math"))

        main = soup.find("main") or soup
        for image in main.find_all("img"):
            counters["images"] += 1
            if not image.has_attr("alt"):
                errors.append(f"gambar tanpa atribut alt: {relative}")
            elif not str(image.get("alt", "")).strip() and not (
                image.get("role") == "presentation" or image.get("aria-hidden") == "true"
            ):
                errors.append(f"gambar dengan alt kosong tanpa status dekoratif: {relative}")

        heading_levels = [
            int(tag.name[1])
            for tag in main.find_all(re.compile(r"^h[1-6]$"))
            if tag.name is not None
        ]
        for previous, current in zip(heading_levels, heading_levels[1:]):
            if current > previous + 1:
                errors.append(
                    f"tingkat heading melompat h{previous} ke h{current}: {relative}"
                )
                break

        runtime_values: list[str] = []
        for tag_name, attribute in RUNTIME_ATTRIBUTES:
            for tag in soup.find_all(tag_name):
                value = tag.get(attribute)
                if isinstance(value, str) and value.strip():
                    runtime_values.append(value)
        for link in soup.find_all("link", href=True):
            rel = {str(value).casefold() for value in (link.get("rel") or [])}
            if rel & RUNTIME_LINK_RELS:
                runtime_values.append(str(link.get("href")))
        for tag in soup.find_all(srcset=True):
            runtime_values.extend(_urls_from_srcset(str(tag.get("srcset"))))
        for style in soup.find_all("style"):
            runtime_values.extend(_css_urls(style.get_text()))
        for tag in soup.find_all(style=True):
            runtime_values.extend(_css_urls(str(tag.get("style"))))
        for raw_url in runtime_values:
            _runtime_url(
                origin=page,
                raw_url=raw_url,
                output_root=output_root,
                relative_origin=relative,
                errors=errors,
                resources=runtime_resources,
                counters=counters,
            )
        for meta in soup.find_all("meta"):
            if str(meta.get("http-equiv", "")).casefold() != "refresh":
                continue
            content = str(meta.get("content", ""))
            match = re.search(r"(?:^|;)\s*url\s*=\s*(.+)$", content, re.IGNORECASE)
            if match:
                _runtime_url(
                    origin=page,
                    raw_url=match.group(1).strip(" '\""),
                    output_root=output_root,
                    relative_origin=relative,
                    errors=errors,
                    resources=runtime_resources,
                    counters=counters,
                )

    for css in sorted(output_root.rglob("*.css")):
        if not css.is_file():
            continue
        counters["css_files_checked"] += 1
        data = css.read_bytes()
        relative = css.relative_to(output_root).as_posix()
        if any(marker in data for marker in LOCAL_PROFILE_MARKERS):
            errors.append(f"jalur profil lokal bocor: {relative}")
        text = data.decode("utf-8", errors="replace")
        for raw_url in _css_urls(text):
            _runtime_url(
                origin=css,
                raw_url=raw_url,
                output_root=output_root,
                relative_origin=relative,
                errors=errors,
                resources=runtime_resources,
                counters=counters,
            )

    for page, soup in parsed.items():
        relative = page.relative_to(output_root).as_posix()
        for link in soup.find_all("a", href=True):
            href = str(link.get("href"))
            counters["links"] += 1
            split = urlsplit(href)
            if split.scheme.casefold() in {"http", "https", "mailto", "tel"} or split.netloc:
                counters["external_links"] += 1
                continue
            if split.scheme or href.casefold().startswith("javascript:"):
                errors.append(f"skema tautan tidak diizinkan {href!r}: {relative}")
                continue
            counters["local_links"] += 1
            try:
                target, fragment = safe_relative_target(page, href, output_root)
            except ValueError:
                errors.append(f"tautan keluar dari keluaran {href!r}: {relative}")
                continue
            if not target.is_file():
                errors.append(f"target tautan lokal hilang {href!r}: {relative}")
                continue
            if fragment and target.suffix.casefold() in {".html", ".htm"}:
                target_resolved = target.resolve()
                if target_resolved not in ids_by_page:
                    target_soup = BeautifulSoup(target.read_bytes(), "html.parser")
                    ids_by_page[target_resolved] = {
                        str(tag.get("id")) for tag in target_soup.find_all(id=True)
                    }
                if fragment not in ids_by_page[target_resolved]:
                    errors.append(f"fragmen tautan lokal hilang {href!r}: {relative}")

    if counters["mathml_elements"] == 0:
        errors.append("tidak ada MathML dalam pembaca HTML")
    if errors:
        unique_errors = sorted(set(errors), key=str.casefold)
        raise RuntimeError(
            f"HTML static QA gagal dengan {len(unique_errors)} galat:\n- "
            + "\n- ".join(unique_errors)
        )
    receipt = {
        "schema": "o002.html-static-qa.v1",
        "successful": True,
        "output_inventory": _inventory(html_files, output_root),
        "runtime_resource_inventory": _inventory(runtime_resources, output_root),
        "counts": counters,
        "checks": {
            "language_id": True,
            "unique_ids": True,
            "heading_order": True,
            "image_alternatives": True,
            "local_links_and_fragments": True,
            "local_runtime_resource_closure": True,
            "offline_runtime_resources": True,
            "css_runtime_resource_closure": True,
            "mathml_present": True,
            "local_profile_paths_absent": True,
        },
    }
    receipt_path = args.receipt.resolve()
    receipt_path.relative_to(ROOT.resolve())
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"HTML static QA passed: {counters['pages']} pages, "
        f"{counters['links']} links, {counters['mathml_elements']} MathML elements"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
