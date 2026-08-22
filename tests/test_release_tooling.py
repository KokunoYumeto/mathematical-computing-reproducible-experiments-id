from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}_module", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


bundles = load_script("make_release_bundles")
compare = load_script("compare_build_manifests")
epub_qa = load_script("epub_qa")
html_qa = load_script("html_static_qa")
manifests = load_script("make_manifests")
update_backend = load_script("update_backend")


def write_csv_manifest(path: Path, rows: list[tuple[str, int, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["path", "bytes", "sha256"])
        writer.writerows(rows)


def make_epub(path: Path, *, external_image: bool = False) -> None:
    container = b'''<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>'''
    opf = b'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">urn:test:o002</dc:identifier>
    <dc:title>Uji O002</dc:title><dc:language>id</dc:language><dc:creator>Kontributor O002</dc:creator>
    <meta property="dcterms:modified">2026-08-22T00:00:00Z</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="chapter" href="chapter.xhtml" media-type="application/xhtml+xml" properties="mathml"/>
    <item id="css" href="style.css" media-type="text/css"/>
    <item id="image" href="image.svg" media-type="image/svg+xml"/>
  </manifest>
  <spine><itemref idref="chapter"/></spine>
</package>'''
    image_url = "https://example.invalid/image.svg" if external_image else "image.svg"
    chapter = f'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:m="http://www.w3.org/1998/Math/MathML" xml:lang="id">
<head><title>Bab</title><link rel="stylesheet" href="style.css"/></head>
<body><h1 id="bab">Bab</h1><m:math id="eq"><m:mi>x</m:mi></m:math><img src="{image_url}" alt="Grafik uji"/></body>
</html>'''.encode()
    nav = b'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="id"><head><title>Navigasi</title></head>
<body><nav><a href="chapter.xhtml#eq">Bab</a></nav></body></html>'''
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", b"application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("EPUB/content.opf", opf)
        archive.writestr("EPUB/nav.xhtml", nav)
        archive.writestr("EPUB/chapter.xhtml", chapter)
        archive.writestr("EPUB/style.css", b"body{background-image:url(image.svg)}")
        archive.writestr("EPUB/image.svg", b"<svg xmlns='http://www.w3.org/2000/svg'/>")


class BundleTests(unittest.TestCase):
    def test_archive_is_deterministic_and_has_verified_exact_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "a.txt").write_text("alpha\n", encoding="utf-8", newline="\n")
            (base / "sub").mkdir()
            (base / "sub" / "b.txt").write_bytes(b"beta\n")
            entries = bundles.archive_entries(
                [base / "sub" / "b.txt", base / "a.txt"], base
            )
            first = bundles.write_archive(
                base / "first.zip", entries, "test", "2026.08.22.1", record_base=base
            )
            second = bundles.write_archive(
                base / "second.zip", entries, "test", "2026.08.22.1", record_base=base
            )
            self.assertEqual((base / "first.zip").read_bytes(), (base / "second.zip").read_bytes())
            self.assertEqual(first["sha256"], second["sha256"])
            self.assertEqual(first["entry_count"], 3)
            self.assertTrue(all(first["verified_readback"].values()))
            self.assertEqual(first["entries"][0]["path"], "BUNDLE_MANIFEST.json")

    def test_reserved_manifest_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            reserved = base / "BUNDLE_MANIFEST.json"
            reserved.write_text("{}", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                bundles.archive_entries([reserved], base)

    def test_archive_artifacts_are_bound_externally_without_self_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            for relative in update_backend.RELEASE_ARTIFACT_PATHS.values():
                path = base / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(relative.encode("utf-8"))
            evidence = {
                "present": {"bundle": True},
                "receipt_ids": {"bundle": "receipt-o002-bundle"},
            }
            with patch.object(update_backend, "ROOT", base):
                first = {
                    record["id"]: record
                    for record in update_backend.artifact_records(evidence)
                    if record["id"] in update_backend.EXTERNALLY_BOUND_ARCHIVE_ARTIFACT_IDS
                }
                archive = base / update_backend.RELEASE_ARTIFACT_PATHS["art-o002-source-archive"]
                archive.write_bytes(b"mutated archive bytes")
                second = {
                    record["id"]: record
                    for record in update_backend.artifact_records(evidence)
                    if record["id"] in update_backend.EXTERNALLY_BOUND_ARCHIVE_ARTIFACT_IDS
                }
            self.assertEqual(first, second)
            self.assertEqual(set(first), update_backend.EXTERNALLY_BOUND_ARCHIVE_ARTIFACT_IDS)
            for record in first.values():
                self.assertEqual(record["state"], "current")
                self.assertEqual(record["receipt_ids"], ["receipt-o002-bundle"])
                self.assertNotIn("bytes", record)
                self.assertNotIn("sha256", record)

    def test_archive_artifact_schema_forbids_embedded_self_identity(self) -> None:
        schema = json.loads((ROOT / "backend" / "catalog.schema.json").read_text(encoding="utf-8"))
        artifact_schema = schema["$defs"]["artifact"]
        validator = Draft202012Validator(artifact_schema)
        record = {
            "id": "art-o002-source-archive",
            "kind": "source_archive",
            "path": "release/source.zip",
            "producer": "pipeline-o002-build",
            "state": "current",
            "receipt_ids": ["receipt-o002-bundle"],
        }
        self.assertFalse(list(validator.iter_errors(record)))
        self.assertTrue(list(validator.iter_errors({**record, "bytes": 1})))
        self.assertTrue(list(validator.iter_errors({**record, "sha256": "a" * 64})))

    def test_bundle_receipt_must_match_complete_live_source_and_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)

            def write(relative: str, data: bytes) -> Path:
                path = base / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                return path

            def local_record(relative: str) -> dict[str, object]:
                path = base / relative
                return {
                    "path": relative,
                    "bytes": path.stat().st_size,
                    "sha256": update_backend.sha256(path),
                }

            source = write("live-source.txt", b"source-v1\n")
            output = write("output/live-output.txt", b"output-v1\n")
            for relative in update_backend.RELEASE_ARTIFACT_PATHS.values():
                write(relative, relative.encode("utf-8"))

            source_content = {
                "path": "live-source.txt",
                "bytes": source.stat().st_size,
                "sha256": update_backend.sha256(source),
            }
            output_content = {
                "path": "live-output.txt",
                "bytes": output.stat().st_size,
                "sha256": update_backend.sha256(output),
            }
            manifest_record = {
                "path": bundles.RESERVED_ARCHIVE_MEMBER,
                "bytes": 2,
                "sha256": "a" * 64,
            }

            archives = []
            for kind, artifact_id, content in (
                ("editable_source", "art-o002-source-archive", source_content),
                ("offline_reader", "art-o002-offline-bundle", output_content),
            ):
                relative = update_backend.RELEASE_ARTIFACT_PATHS[artifact_id]
                archives.append(
                    {
                        **local_record(relative),
                        "bundle_kind": kind,
                        "entry_count": 2,
                        "content_entry_count": 1,
                        "content_bytes": content["bytes"],
                        "entries": [manifest_record, content],
                        "verified_readback": {
                            "inventory": True,
                            "bytes": True,
                            "sha256": True,
                            "crc": True,
                            "embedded_manifest": True,
                        },
                    }
                )

            document = {
                "schema": "o002.bundle-receipt.v1",
                "successful": True,
                "version": update_backend.RELEASE_VERSION,
                "tag": update_backend.RELEASE_TAG,
                "reader_artifacts": [
                    local_record(relative)
                    for artifact_id, relative in update_backend.RELEASE_ARTIFACT_PATHS.items()
                    if artifact_id
                    in {"art-o002-reader-html", "art-o002-reader-pdf", "art-o002-reader-epub"}
                ],
                "archives": archives,
                "self_reference_policy": {
                    "receipt_excluded_from_archives": True,
                    "release_directory_excluded_from_offline_archive": True,
                    "embedded_manifest_excludes_its_own_digest": True,
                },
            }

            with (
                patch.object(update_backend, "ROOT", base),
                patch.object(update_backend.BUNDLE_TOOLS, "source_files", return_value=[source]),
                patch.object(update_backend.BUNDLE_TOOLS, "offline_files", return_value=[output]),
            ):
                update_backend.validate_bundle(document)
                source.write_bytes(b"source-v2\n")
                with self.assertRaisesRegex(RuntimeError, "stale"):
                    update_backend.validate_bundle(document)


class DeterminismTests(unittest.TestCase):
    def test_four_valid_distinct_witnesses_produce_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            rows = [("output/index.html", 5, "a" * 64)]
            paths = [base / name for name in ("s1.csv", "s2.csv", "o1.csv", "o2.csv")]
            for path in paths:
                write_csv_manifest(path, rows)
            receipt = base / "receipt.json"
            with patch.object(compare, "ROOT", base):
                self.assertEqual(
                    compare.main(
                        [
                            "--first-source", str(paths[0]), "--second-source", str(paths[1]),
                            "--first-output", str(paths[2]), "--second-output", str(paths[3]),
                            "--receipt", str(receipt),
                        ]
                    ),
                    0,
                )
            document = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertTrue(document["successful"])
            self.assertEqual(document["clean_build_count"], 2)

    def test_duplicate_or_unsafe_manifest_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            write_csv_manifest(path, [("../escape", 1, "a" * 64)])
            with self.assertRaises(RuntimeError):
                compare.validate_manifest(path)


class StaticHtmlTests(unittest.TestCase):
    def test_local_runtime_and_css_closure_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            output = base / "output"
            output.mkdir()
            (output / "font.woff").write_bytes(b"font")
            (output / "styles.css").write_text(
                "body{font-family:test}@font-face{src:url(font.woff)}", encoding="utf-8"
            )
            (output / "app.js").write_text("document.body.dataset.ready='1';", encoding="utf-8")
            (output / "index.html").write_text(
                '''<!doctype html><html lang="id"><head><link rel="stylesheet" href="styles.css"/>
<script src="app.js"></script></head><body><main><h1 id="awal">Uji</h1>
<math><mi>x</mi></math><a href="#awal">Awal</a></main></body></html>''',
                encoding="utf-8",
            )
            receipt = base / "html.json"
            with patch.object(html_qa, "ROOT", base):
                self.assertEqual(
                    html_qa.main(["--output", str(output), "--receipt", str(receipt)]), 0
                )
            document = json.loads(receipt.read_text(encoding="utf-8"))
            paths = {record["path"] for record in document["runtime_resource_inventory"]}
            self.assertEqual(paths, {"app.js", "font.woff", "styles.css"})

    def test_missing_runtime_resource_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            output = base / "output"
            output.mkdir()
            (output / "index.html").write_text(
                '<html lang="id"><main><h1>Uji</h1><math><mi>x</mi></math><script src="missing.js"></script></main></html>',
                encoding="utf-8",
            )
            with patch.object(html_qa, "ROOT", base), self.assertRaises(RuntimeError):
                html_qa.main(["--output", str(output), "--receipt", str(base / "r.json")])


class EpubTests(unittest.TestCase):
    def test_epub_metadata_structure_and_offline_closure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            epub = base / "book.epub"
            receipt = base / "epub.json"
            make_epub(epub)
            with patch.object(epub_qa, "ROOT", base):
                self.assertEqual(
                    epub_qa.main(["--epub", str(epub), "--receipt", str(receipt)]), 0
                )
            document = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(document["metadata"]["identifier"], "urn:test:o002")
            self.assertTrue(all(document["checks"].values()))

    def test_external_epub_runtime_resource_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            epub = base / "book.epub"
            make_epub(epub, external_image=True)
            with patch.object(epub_qa, "ROOT", base), self.assertRaises(RuntimeError):
                epub_qa.main(["--epub", str(epub), "--receipt", str(base / "r.json")])


class SourceManifestTests(unittest.TestCase):
    def test_release_build_restarts_persistent_jupyter_daemon(self) -> None:
        build_script = (ROOT / "scripts" / "build.ps1").read_text(encoding="utf-8")
        quarto_config = (ROOT / "_quarto.yml").read_text(encoding="utf-8")
        self.assertIn("quarto render --execute-daemon-restart", build_script)
        self.assertIn("daemon: true", quarto_config)
        self.assertIn(r"\RecustomVerbatimEnvironment{Highlighting}", quarto_config)
        self.assertIn("breaklines=true", quarto_config)
        self.assertIn("breakanywhere=true", quarto_config)
        self.assertIn("Remove-Item -LiteralPath $BuildQAPath -Force", build_script)

    def test_release_and_manifest_source_scopes_are_kept_identical(self) -> None:
        self.assertEqual(manifests.SOURCE_ROOT_FILES, bundles.SOURCE_ROOT_FILES)
        self.assertEqual(manifests.SOURCE_DIRECTORIES, bundles.SOURCE_DIRECTORIES)
        self.assertEqual(manifests.SOURCE_CONTROL_FILES, bundles.SOURCE_CONTROL_FILES)
        files = manifests.source_inventory()
        manifests.validate_expanded_source(files)
        self.assertEqual(
            {_relative(path) for path in files},
            {_relative(path) for path in bundles.source_files()},
        )

    def test_collapsible_callouts_receive_keyboard_semantics(self) -> None:
        helper = (ROOT / "accessibility.html").read_text(encoding="utf-8")
        self.assertIn(".callout-header[data-bs-toggle='collapse']", helper)
        self.assertIn('header.tabIndex = 0', helper)
        self.assertIn('header.setAttribute("role", "button")', helper)
        self.assertIn('event.key !== "Enter"', helper)
        self.assertIn('event.key !== " "', helper)
        self.assertIn("header.click()", helper)

    def test_desktop_reader_uses_the_post_sidebar_grid_span(self) -> None:
        css = (ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertIn("grid-column: body-start / body-end", css)
        self.assertIn("padding-inline: clamp(1rem, 2vw, 2rem)", css)

    def test_reader_wraps_code_at_every_viewport(self) -> None:
        css = (ROOT / "styles.css").read_text(encoding="utf-8")
        media = css.index("@media (max-width: 767.98px)")
        wrap_rule = css.index("main pre > code")
        self.assertLess(wrap_rule, media)
        self.assertIn("overflow-wrap: anywhere", css[wrap_rule:media])
        self.assertIn("white-space: pre-wrap", css[wrap_rule:media])

    def test_reader_scales_figures_to_the_available_width(self) -> None:
        css = (ROOT / "styles.css").read_text(encoding="utf-8")
        rule = css.index("main img.figure-img")
        media = css.index("@media (min-width: 1200px)")
        self.assertLess(rule, media)
        self.assertIn("height: auto", css[rule:media])
        self.assertIn("max-width: 100%", css[rule:media])


def _relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


if __name__ == "__main__":
    unittest.main()
