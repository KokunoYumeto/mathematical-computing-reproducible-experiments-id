from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = (
    ROOT
    / "output"
    / "Komputasi-Matematis-dan-Eksperimen-yang-Dapat-Direproduksi.pdf"
)
DEFAULT_RECEIPT = ROOT / "00_control" / "PDF_VISUAL_QA.json"
DEFAULT_RENDER_MANIFEST = ROOT / "00_control" / "PDF_VISUAL_RENDER_MANIFEST.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"jalur keluar dari lane: {path}") from exc


def pdf_page_count(pdf: Path) -> int:
    completed = subprocess.run(
        ["pdfinfo", str(pdf)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = re.search(r"^Pages:\s+(\d+)\s*$", completed.stdout, re.MULTILINE)
    if match is None:
        raise RuntimeError("pdfinfo tidak melaporkan jumlah halaman")
    return int(match.group(1))


def write_render_manifest(path: Path, render_dir: Path) -> tuple[int, int]:
    pages = sorted(render_dir.glob("page-*.png"))
    contacts = sorted((render_dir / "contact-sheets").glob("sheet-*.png"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["kind", "path", "bytes", "sha256"])
        for kind, files in (("page", pages), ("contact_sheet", contacts)):
            for item in files:
                writer.writerow(
                    [kind, relative_path(item), item.stat().st_size, sha256(item)]
                )
    return len(pages), len(contacts)


def validate_render_manifest(path: Path) -> tuple[int, int]:
    page_count = 0
    contact_count = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["kind", "path", "bytes", "sha256"]:
            raise ValueError("header manifest render tidak sah")
        seen: set[str] = set()
        for row in reader:
            relative = row["path"]
            if relative.casefold() in seen:
                raise ValueError(f"jalur render duplikat: {relative}")
            seen.add(relative.casefold())
            item = (ROOT / relative).resolve()
            relative_path(item)
            if not item.is_file():
                raise FileNotFoundError(f"render hilang: {relative}")
            if item.stat().st_size != int(row["bytes"]) or sha256(item) != row["sha256"]:
                raise ValueError(f"render tidak cocok: {relative}")
            if row["kind"] == "page":
                page_count += 1
            elif row["kind"] == "contact_sheet":
                contact_count += 1
            else:
                raise ValueError(f"jenis render tidak dikenal: {row['kind']}")
    return page_count, contact_count


def create_receipt(args: argparse.Namespace) -> int:
    pdf = args.pdf.resolve()
    pages = pdf_page_count(pdf)
    rendered_pages, contact_sheets = write_render_manifest(
        args.render_manifest.resolve(), args.render_dir.resolve()
    )
    if rendered_pages != pages:
        raise ValueError(
            f"jumlah render {rendered_pages} tidak sama dengan halaman PDF {pages}"
        )
    if args.inspected_pages != pages:
        raise ValueError(
            f"jumlah halaman diperiksa {args.inspected_pages} tidak sama dengan {pages}"
        )
    receipt = {
        "schema": "o002.pdf-visual-qa.v1",
        "pdf": {
            "path": relative_path(pdf),
            "bytes": pdf.stat().st_size,
            "sha256": sha256(pdf),
            "page_count": pages,
        },
        "render": {
            "dpi": args.dpi,
            "page_images": rendered_pages,
            "contact_sheets": contact_sheets,
            "manifest_path": relative_path(args.render_manifest),
            "manifest_sha256": sha256(args.render_manifest),
        },
        "review": {
            "reviewer": args.reviewer,
            "method": args.method,
            "inspected_pages": args.inspected_pages,
            "result": args.result,
        },
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return verify_receipt(args.receipt.resolve(), pdf)


def verify_receipt(receipt_path: Path, pdf: Path) -> int:
    receipt: dict[str, Any] = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != "o002.pdf-visual-qa.v1":
        raise ValueError("skema receipt visual PDF salah")
    pdf_record = receipt.get("pdf")
    render_record = receipt.get("render")
    review_record = receipt.get("review")
    if not all(isinstance(record, dict) for record in (pdf_record, render_record, review_record)):
        raise ValueError("struktur receipt visual PDF tidak lengkap")
    pages = pdf_page_count(pdf)
    if (
        pdf_record.get("path") != relative_path(pdf)
        or pdf_record.get("bytes") != pdf.stat().st_size
        or pdf_record.get("sha256") != sha256(pdf)
        or pdf_record.get("page_count") != pages
    ):
        raise ValueError("receipt visual tidak mengikat PDF saat ini")
    manifest_path = (ROOT / str(render_record.get("manifest_path", ""))).resolve()
    relative_path(manifest_path)
    if not manifest_path.is_file() or sha256(manifest_path) != render_record.get(
        "manifest_sha256"
    ):
        raise ValueError("manifest render visual tidak cocok")
    rendered_pages, contact_sheets = validate_render_manifest(manifest_path)
    if (
        rendered_pages != pages
        or render_record.get("page_images") != pages
        or render_record.get("contact_sheets") != contact_sheets
        or review_record.get("inspected_pages") != pages
        or review_record.get("result") != "pass"
        or not isinstance(review_record.get("reviewer"), str)
        or not review_record["reviewer"].strip()
        or not isinstance(review_record.get("method"), str)
        or not review_record["method"].strip()
    ):
        raise ValueError("receipt visual PDF belum memenuhi gerbang lulus")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    create.add_argument("--render-dir", type=Path, required=True)
    create.add_argument("--render-manifest", type=Path, default=DEFAULT_RENDER_MANIFEST)
    create.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    create.add_argument("--dpi", type=int, default=120)
    create.add_argument("--inspected-pages", type=int, required=True)
    create.add_argument("--reviewer", required=True)
    create.add_argument("--method", required=True)
    create.add_argument("--result", choices=("pass", "fail"), required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    verify.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    if args.command == "create":
        return create_receipt(args)
    return verify_receipt(args.receipt.resolve(), args.pdf.resolve())


if __name__ == "__main__":
    sys.exit(main())
