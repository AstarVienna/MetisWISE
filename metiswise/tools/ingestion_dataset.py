"""Snapshot FITS metadata for ingestion tests without retaining image pixels.

Create a reproducible JSON(.gz) fixture, then restore valid FITS files with zero
image data and empty tables. Column definitions and other metadata are retained,
apart from table row/heap sizes and checksums for changed HDUs. ESO DATAMD5 values
remain identifiers from the original run, not checksums of the replacement data.
"""

import argparse
from contextlib import contextmanager
import gzip
import json
import math
import os
from pathlib import Path, PurePosixPath
import tempfile

from astropy.io import fits
import numpy as np


FORMAT = "metiswise-ingestion-dataset"
VERSION = 3
CARD = 80
BLOCK = 2880


@contextmanager
def _writer(path, overwrite):
    # Publish only complete fixtures. Fixed gzip metadata makes repeated
    # conversions byte-for-byte identical, regardless of the output filename.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as raw:
            temporary = Path(raw.name)
            if path.suffix == ".gz":
                with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as output:
                    yield output
            else:
                yield raw
        if overwrite:
            temporary.replace(path)
        else:
            os.link(temporary, path)  # Fail atomically if the destination exists.
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def create_dataset(source, destination, *, overwrite=False):
    """Capture FITS headers in ingestion order, dropping pixels and table rows."""
    source, destination = Path(source).resolve(), Path(destination)
    if not source.is_dir():
        raise ValueError(f"Not a source directory: {source}")
    candidates = sorted(
        (p for p in source.rglob("*") if p.is_file() and not p.is_symlink()
         and p.suffix.lower() in (".fits", ".fit", ".fts")),
        key=lambda p: (p.stat().st_mtime_ns, p.relative_to(source).as_posix()),
    )
    records = []
    names = set()
    original_bytes = 0
    for path in candidates:
        with fits.open(path, do_not_scale_image_data=True, memmap=True) as hdus:
            if not any(key in hdus[0].header for key in ("ESO DPR CATG", "ESO PRO CATG")):
                continue
            if path.name in names:
                raise ValueError(f"Duplicate archive filename: {path.name}")
            names.add(path.name)
            record = {"path": path.relative_to(source).as_posix(), "hdus": []}
            for hdu in hdus:
                if type(hdu) not in (fits.PrimaryHDU, fits.ImageHDU, fits.BinTableHDU, fits.TableHDU):
                    raise ValueError(f"Unsupported HDU {type(hdu).__name__} in {path}; use uncompressed FITS")
                header = hdu.header.copy()
                size = hdu.fileinfo()["datSpan"]
                entry = {"header": None, "size": size}
                changed = False
                if isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
                    changed = any(header.get(key, 0) != 0 for key in ("NAXIS2", "PCOUNT", "THEAP"))
                    header["NAXIS2"] = 0
                    header["PCOUNT"] = 0
                    if "THEAP" in header:
                        header["THEAP"] = 0
                    entry["size"] = 0
                elif size:
                    # Check that physical zero is representable before writing
                    # a fixture; this also supports FITS unsigned scaling.
                    _zero_pattern(header)
                    changed = True
                if changed:
                    for key in ("CHECKSUM", "DATASUM"):
                        header.remove(key, ignore_missing=True, remove_all=True)
                # Slice the physical card stream rather than Card.image:
                # long values can span several 80-character CONTINUE cards.
                text = header.tostring(padding=False)
                entry["header"] = [text[i:i + CARD] for i in range(0, len(text), CARD)]
                record["hdus"].append(entry)
            records.append(record)
            original_bytes += path.stat().st_size
    if not records:
        raise ValueError(f"No archive-classified FITS files found in {source}")
    document = {"format": FORMAT, "version": VERSION, "original_bytes": original_bytes,
                "files": records}
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.resolve() in candidates:
        raise ValueError("The fixture must not replace an input FITS file")
    with _writer(destination, overwrite) as output:
        output.write((json.dumps(document, ensure_ascii=True, indent=2) + "\n").encode("ascii"))
    return {"files": len(records), "original_bytes": original_bytes,
            "fixture_bytes": destination.stat().st_size}


def _zero_pattern(header):
    dtype = np.dtype({8: "u1", 16: ">i2", 32: ">i4", 64: ">i8",
                      -32: ">f4", -64: ">f8"}[header["BITPIX"]])
    scale, offset = header.get("BSCALE", 1), header.get("BZERO", 0)
    if scale == 0:
        raise ValueError("Cannot represent physical zero with BSCALE=0")
    value = -offset / scale
    if value == 0:
        value = 0  # Avoid a negative floating-point zero, which cannot be sparse.
    if dtype.kind in "iu":
        limits = np.iinfo(dtype)
        if value != int(value) or not limits.min <= value <= limits.max:
            raise ValueError("Physical zero is not representable with this integer FITS scaling")
    return np.asarray(value, dtype=dtype).tobytes()


def _write_image(output, header, size):
    count = math.prod(header[f"NAXIS{i}"] for i in range(1, header["NAXIS"] + 1))
    pattern = _zero_pattern(header)
    image_size = count * len(pattern)
    if size != math.ceil(image_size / BLOCK) * BLOCK:
        raise ValueError("Image data size does not match its FITS header")
    if pattern == bytes(len(pattern)):
        output.seek(size, 1)  # A sparse hole reads as zeros without occupying disk space.
    else:
        chunk = pattern * max(1, (1024 * 1024) // len(pattern))
        remaining = image_size
        while remaining:
            piece = chunk[:min(remaining, len(chunk))]
            output.write(piece)
            remaining -= len(piece)
        output.seek(size - image_size, 1)


def restore_dataset(fixture, destination):
    """Restore files in recorded order, refusing traversal and existing files.

    Images keep their logical dimensions; ordinary unscaled zero arrays occupy
    sparse holes. Tables retain their column definitions with zero rows.
    Returned paths are ready for ingest_file(..., store=False).
    """
    fixture, destination = Path(fixture), Path(destination).resolve()
    opener = gzip.open if fixture.suffix == ".gz" else open
    with opener(fixture, "rt", encoding="ascii") as stream:
        document = json.load(stream)
    if document.get("format") != FORMAT or document.get("version") != VERSION:
        raise ValueError("Unsupported ingestion dataset format/version")
    paths = []
    for record in document["files"]:
        relative = PurePosixPath(record["path"])
        if relative.is_absolute() or ".." in relative.parts or not relative.name:
            raise ValueError(f"Unsafe fixture path: {record['path']!r}")
        path = destination.joinpath(*relative.parts)
        if not path.resolve().is_relative_to(destination) or path.exists():
            raise ValueError(f"Destination exists or escapes the output directory: {path}")
        if path in paths:
            raise ValueError(f"Duplicate fixture path: {path}")
        paths.append(path)
    for record, path in zip(document["files"], paths):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as output:
            for entry in record["hdus"]:
                cards = entry["header"]
                if not isinstance(cards, list) or not all(isinstance(card, str) and len(card) == CARD for card in cards):
                    raise ValueError(f"Expected a list of 80-character FITS cards in {path}")
                header = fits.Header.fromstring("".join(cards))
                output.write(header.tostring().encode("ascii"))
                size = entry["size"]
                if not isinstance(size, int) or size < 0 or size % BLOCK:
                    raise ValueError(f"Invalid FITS data span in {path}")
                if size:
                    _write_image(output, header, size)
            output.truncate()
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="Capture a simulation/EDPS directory as JSON or JSON.gz")
    create.add_argument("source", type=Path)
    create.add_argument("fixture", type=Path)
    create.add_argument("--overwrite", action="store_true", help="Atomically replace an existing fixture")
    restore = commands.add_parser("restore", help="Recreate sparse, zero-image FITS files for ingestion")
    restore.add_argument("fixture", type=Path)
    restore.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    if args.command == "create":
        result = create_dataset(args.source, args.fixture, overwrite=args.overwrite)
        print(f"Captured {result['files']} FITS files: {result['original_bytes']:,} original bytes "
              f"-> {result['fixture_bytes']:,} fixture bytes in {args.fixture}")
    else:
        paths = restore_dataset(args.fixture, args.destination)
        print(f"Restored {len(paths)} FITS files below {args.destination}")


if __name__ == "__main__":
    main()
