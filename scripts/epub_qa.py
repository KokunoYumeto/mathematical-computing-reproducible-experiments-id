from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Iterable, Sequence
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
CONTAINER = "META-INF/container.xml"
CONTAINER_NS = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
OPF_NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}
XHTML_NS = "http://www.w3.org/1999/xhtml"
MATHML_NS = "http://www.w3.org/1998/Math/MathML"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
RUNTIME_ELEMENTS = {
    "script": ("src",),
    "img": ("src", "srcset"),
    "source": ("src", "srcset"),
    "audio": ("src",),
    "video": ("src", "poster"),
    "track": ("src",),
    "iframe": ("src",),
    "embed": ("src",),
    "object": ("data",),
    "image": ("href", "{http://www.w3.org/1999/xlink}href"),
}
CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
CSS_IMPORT_RE = re.compile(
    r"@import\s+(?!url\()(['\"])(.*?)\1", re.IGNORECASE
)
LOCAL_PROFILE_MARKERS = (b"C:\\Users\\", b"C:/Users/", b"file:///C:/")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_member(base: PurePosixPath, href: str) -> str:
    split = urlsplit(href)
    if split.scheme or split.netloc:
        raise ValueError(f"sumber daya EPUB eksternal: {href}")
    parts: list[str] = []
    for part in (base / unquote(split.path)).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                raise ValueError(f"jalur EPUB keluar dari akar: {href}")
            parts.pop()
        else:
            parts.append(part)
    return PurePosixPath(*parts).as_posix()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _srcset_urls(value: str) -> Iterable[str]:
    if value.lstrip().casefold().startswith("data:"):
        return ()
    return tuple(part.strip().split()[0] for part in value.split(",") if part.strip())


def _css_urls(text: str) -> Iterable[str]:
    values = [match.group(2).strip() for match in CSS_URL_RE.finditer(text)]
    values.extend(match.group(2).strip() for match in CSS_IMPORT_RE.finditer(text))
    return tuple(value for value in values if value)


def _safe_members(members: list[str], errors: list[str]) -> None:
    folded = [name.casefold() for name in members]
    if len(folded) != len(set(folded)):
        errors.append("jalur EPUB bertabrakan setelah case folding")
    for name in members:
        pure = PurePosixPath(name)
        if (
            "\\" in name
            or pure.is_absolute()
            or any(part in {"", ".", ".."} for part in pure.parts)
            or pure.as_posix() != name.rstrip("/")
        ):
            errors.append(f"jalur anggota EPUB tidak aman: {name!r}")


def _resource_target(
    *,
    origin: str,
    raw_url: str,
    members: set[str],
    manifest_paths: dict[str, str],
    errors: list[str],
    counts: dict[str, int],
) -> None:
    split = urlsplit(raw_url.strip())
    if split.scheme.casefold() == "data":
        counts["embedded_runtime_resources"] += 1
        return
    if split.scheme or split.netloc:
        errors.append(f"sumber daya runtime EPUB eksternal {raw_url!r}: {origin}")
        return
    if not split.path and split.fragment:
        return
    try:
        target = normalized_member(PurePosixPath(origin).parent, raw_url)
    except ValueError as error:
        errors.append(str(error))
        return
    counts["local_runtime_references"] += 1
    if target not in members:
        errors.append(f"sumber daya runtime EPUB hilang {raw_url!r}: {origin}")
    elif target not in manifest_paths:
        errors.append(f"sumber daya runtime EPUB tidak dideklarasikan: {target}")


def _metadata_text(package: ET.Element, query: str) -> str:
    return package.findtext(query, default="", namespaces=OPF_NS).strip()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate EPUB structure, offline closure, metadata, and accessibility."
    )
    parser.add_argument("--epub", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    epub = args.epub.resolve()
    epub.relative_to(ROOT.resolve())
    if not epub.is_file():
        raise FileNotFoundError(epub)

    errors: list[str] = []
    counts = {
        "members": 0,
        "manifest_items": 0,
        "spine_documents": 0,
        "xhtml_documents": 0,
        "images": 0,
        "mathml_elements": 0,
        "local_links": 0,
        "external_hyperlinks": 0,
        "local_runtime_references": 0,
        "embedded_runtime_resources": 0,
        "css_documents": 0,
    }
    metadata = {
        "title": "",
        "language": "",
        "creator": "",
        "identifier": "",
        "modified": "",
        "opf_rootfile": "",
    }
    with zipfile.ZipFile(epub, "r") as archive:
        members_list = archive.namelist()
        members = set(members_list)
        counts["members"] = len(members_list)
        _safe_members(members_list, errors)
        if not members_list or members_list[0] != "mimetype":
            errors.append("mimetype bukan anggota pertama EPUB")
        else:
            info = archive.getinfo("mimetype")
            if info.compress_type != zipfile.ZIP_STORED:
                errors.append("mimetype EPUB harus tanpa kompresi")
            if archive.read("mimetype") != b"application/epub+zip":
                errors.append("isi mimetype EPUB salah")
        if archive.testzip() is not None:
            errors.append("CRC anggota EPUB gagal")
        if CONTAINER not in members:
            errors.append("container.xml hilang")
            rootfile = ""
        else:
            try:
                container = ET.fromstring(archive.read(CONTAINER))
            except ET.ParseError as error:
                errors.append(f"container.xml tidak valid: {error}")
                rootfile = ""
            else:
                rootfiles = container.findall("c:rootfiles/c:rootfile", CONTAINER_NS)
                if len(rootfiles) != 1:
                    errors.append("container.xml harus memiliki tepat satu rootfile")
                root = rootfiles[0] if rootfiles else None
                rootfile = "" if root is None else str(root.attrib.get("full-path", ""))
                media_type = "" if root is None else str(root.attrib.get("media-type", ""))
                if media_type != "application/oebps-package+xml":
                    errors.append("media-type rootfile OPF tidak sah")
                if not rootfile or rootfile not in members:
                    errors.append("rootfile OPF tidak sah")
        metadata["opf_rootfile"] = rootfile

        manifest_by_id: dict[str, dict[str, str]] = {}
        manifest_paths: dict[str, str] = {}
        spine_ids: list[str] = []
        properties_by_path: dict[str, set[str]] = {}
        if rootfile:
            try:
                package = ET.fromstring(archive.read(rootfile))
            except ET.ParseError as error:
                errors.append(f"OPF tidak valid: {error}")
                package = None
            if package is not None:
                metadata["language"] = _metadata_text(package, "opf:metadata/dc:language")
                metadata["title"] = _metadata_text(package, "opf:metadata/dc:title")
                metadata["creator"] = _metadata_text(package, "opf:metadata/dc:creator")
                if metadata["language"] not in {"id", "id-ID"}:
                    errors.append(f"bahasa EPUB bukan id: {metadata['language']!r}")
                if not metadata["title"]:
                    errors.append("judul EPUB kosong")
                if not metadata["creator"]:
                    errors.append("creator EPUB kosong")

                unique_id = str(package.attrib.get("unique-identifier", ""))
                identifiers = package.findall("opf:metadata/dc:identifier", OPF_NS)
                selected_identifier = next(
                    (
                        element
                        for element in identifiers
                        if str(element.attrib.get("id", "")) == unique_id
                    ),
                    None,
                )
                if not unique_id or selected_identifier is None:
                    errors.append("unique identifier EPUB tidak terikat")
                else:
                    metadata["identifier"] = (selected_identifier.text or "").strip()
                    if not metadata["identifier"]:
                        errors.append("identifier EPUB kosong")
                modified = next(
                    (
                        (element.text or "").strip()
                        for element in package.findall("opf:metadata/opf:meta", OPF_NS)
                        if element.attrib.get("property") == "dcterms:modified"
                    ),
                    "",
                )
                metadata["modified"] = modified
                if not modified:
                    errors.append("metadata dcterms:modified EPUB hilang")

                opf_base = PurePosixPath(rootfile).parent
                for item in package.findall("opf:manifest/opf:item", OPF_NS):
                    item_id = str(item.attrib.get("id", ""))
                    href = str(item.attrib.get("href", ""))
                    media_type = str(item.attrib.get("media-type", ""))
                    if not item_id or item_id in manifest_by_id:
                        errors.append(f"ID manifest EPUB kosong/duplikat: {item_id!r}")
                        continue
                    if not href or urlsplit(href).query or urlsplit(href).fragment:
                        errors.append(f"href manifest EPUB tidak kanonik: {href!r}")
                        continue
                    try:
                        path = normalized_member(opf_base, href)
                    except ValueError as error:
                        errors.append(str(error))
                        continue
                    if path in manifest_paths or path.casefold() in {
                        value.casefold() for value in manifest_paths
                    }:
                        errors.append(f"jalur manifest EPUB duplikat: {path}")
                    if path not in members:
                        errors.append(f"anggota manifest EPUB hilang: {path}")
                    if not media_type:
                        errors.append(f"media-type manifest EPUB kosong: {path}")
                    properties = set(str(item.attrib.get("properties", "")).split())
                    manifest_by_id[item_id] = {
                        "path": path,
                        "media_type": media_type,
                    }
                    manifest_paths[path] = media_type
                    properties_by_path[path] = properties
                counts["manifest_items"] = len(manifest_by_id)
                for itemref in package.findall("opf:spine/opf:itemref", OPF_NS):
                    idref = str(itemref.attrib.get("idref", ""))
                    spine_ids.append(idref)
                    if idref not in manifest_by_id:
                        errors.append(f"spine merujuk ID manifest yang hilang: {idref}")
                    elif manifest_by_id[idref]["media_type"] != "application/xhtml+xml":
                        errors.append(f"spine bukan XHTML: {idref}")
                counts["spine_documents"] = len(spine_ids)
                if not spine_ids:
                    errors.append("spine EPUB kosong")
                if len(spine_ids) != len(set(spine_ids)):
                    errors.append("spine EPUB mengandung ID duplikat")
                if not any("nav" in values for values in properties_by_path.values()):
                    errors.append("dokumen navigasi EPUB hilang")

        ids_by_document: dict[str, set[str]] = {}
        xhtml_paths = sorted(
            path
            for path, media_type in manifest_paths.items()
            if media_type == "application/xhtml+xml"
        )
        counts["xhtml_documents"] = len(xhtml_paths)
        for path in xhtml_paths:
            data = archive.read(path)
            if any(marker in data for marker in LOCAL_PROFILE_MARKERS):
                errors.append(f"jalur profil lokal bocor dalam EPUB: {path}")
            try:
                document = ET.fromstring(data)
            except ET.ParseError as error:
                errors.append(f"XHTML EPUB tidak valid {path}: {error}")
                continue
            language = document.attrib.get("lang") or document.attrib.get(XML_LANG)
            if language not in {"id", "id-ID"}:
                errors.append(f"bahasa XHTML EPUB bukan id: {path}")
            ids = [value for element in document.iter() if (value := element.attrib.get("id"))]
            if len(ids) != len(set(ids)):
                errors.append(f"ID XHTML EPUB duplikat: {path}")
            ids_by_document[path] = set(ids)
            math = list(document.iter(f"{{{MATHML_NS}}}math"))
            counts["mathml_elements"] += len(math)
            if math and "mathml" not in properties_by_path.get(path, set()):
                errors.append(f"properti manifest mathml hilang: {path}")
            for element in document.iter():
                name = _local_name(element.tag)
                if name == "img":
                    counts["images"] += 1
                    alt = element.attrib.get("alt")
                    if alt is None or not alt.strip():
                        errors.append(f"gambar EPUB tanpa alt: {path}")
                for attribute in RUNTIME_ELEMENTS.get(name, ()):
                    value = element.attrib.get(attribute)
                    if not value:
                        continue
                    urls = _srcset_urls(value) if attribute == "srcset" else (value,)
                    for raw_url in urls:
                        _resource_target(
                            origin=path,
                            raw_url=raw_url,
                            members=members,
                            manifest_paths=manifest_paths,
                            errors=errors,
                            counts=counts,
                        )
                if name == "link" and "stylesheet" in str(element.attrib.get("rel", "")).split():
                    href = element.attrib.get("href")
                    if href:
                        _resource_target(
                            origin=path,
                            raw_url=href,
                            members=members,
                            manifest_paths=manifest_paths,
                            errors=errors,
                            counts=counts,
                        )
                if name == "style" and element.text:
                    for raw_url in _css_urls(element.text):
                        _resource_target(
                            origin=path,
                            raw_url=raw_url,
                            members=members,
                            manifest_paths=manifest_paths,
                            errors=errors,
                            counts=counts,
                        )
                style = element.attrib.get("style")
                if style:
                    for raw_url in _css_urls(style):
                        _resource_target(
                            origin=path,
                            raw_url=raw_url,
                            members=members,
                            manifest_paths=manifest_paths,
                            errors=errors,
                            counts=counts,
                        )

        for path, media_type in sorted(manifest_paths.items()):
            if media_type != "text/css" or path not in members:
                continue
            counts["css_documents"] += 1
            data = archive.read(path)
            if any(marker in data for marker in LOCAL_PROFILE_MARKERS):
                errors.append(f"jalur profil lokal bocor dalam EPUB: {path}")
            text = data.decode("utf-8", errors="replace")
            for raw_url in _css_urls(text):
                _resource_target(
                    origin=path,
                    raw_url=raw_url,
                    members=members,
                    manifest_paths=manifest_paths,
                    errors=errors,
                    counts=counts,
                )

        for path in xhtml_paths:
            try:
                document = ET.fromstring(archive.read(path))
            except ET.ParseError:
                continue
            base = PurePosixPath(path).parent
            for anchor in document.iter(f"{{{XHTML_NS}}}a"):
                href = anchor.attrib.get("href")
                if not href:
                    continue
                split = urlsplit(href)
                if split.scheme.casefold() in {"http", "https", "mailto", "tel"} or split.netloc:
                    counts["external_hyperlinks"] += 1
                    continue
                if split.scheme:
                    errors.append(f"skema tautan EPUB tidak diizinkan {href!r}: {path}")
                    continue
                try:
                    target = path if not split.path else normalized_member(base, href)
                except ValueError as error:
                    errors.append(str(error))
                    continue
                counts["local_links"] += 1
                if target not in members:
                    errors.append(f"target tautan EPUB hilang {href!r}: {path}")
                    continue
                fragment = unquote(split.fragment)
                if fragment and target in ids_by_document and fragment not in ids_by_document[target]:
                    errors.append(f"fragmen EPUB hilang {href!r}: {path}")

    if counts["xhtml_documents"] == 0:
        errors.append("dokumen XHTML tidak ditemukan dalam EPUB")
    if counts["mathml_elements"] == 0:
        errors.append("MathML tidak ditemukan dalam EPUB")
    if errors:
        unique_errors = sorted(set(errors), key=str.casefold)
        raise RuntimeError(
            f"EPUB QA gagal dengan {len(unique_errors)} galat:\n- "
            + "\n- ".join(unique_errors)
        )
    receipt = {
        "schema": "o002.epub-qa.v1",
        "successful": True,
        "epub": {
            "path": epub.relative_to(ROOT.resolve()).as_posix(),
            "bytes": epub.stat().st_size,
            "sha256": sha256(epub),
        },
        "metadata": metadata,
        "counts": counts,
        "checks": {
            "safe_unique_member_paths": True,
            "ocf_mimetype": True,
            "container_and_opf": True,
            "manifest_and_spine_closure": True,
            "publication_metadata": True,
            "language_id": True,
            "unique_ids": True,
            "image_alternatives": True,
            "local_links_and_fragments": True,
            "local_runtime_resource_closure": True,
            "css_runtime_resource_closure": True,
            "mathml_present_and_declared": True,
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
        f"EPUB QA passed: {counts['xhtml_documents']} XHTML documents, "
        f"{counts['mathml_elements']} MathML elements"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
