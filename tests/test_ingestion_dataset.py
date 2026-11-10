"""Compact metadata fixtures preserve FITS structure without image payloads."""

import gzip
import json
import os
from pathlib import Path

from astropy.io import fits
import numpy as np
import pytest

from metiswise.tools.ingestion_dataset import create_dataset, restore_dataset
from metiswise.main.provenance import get_provenance_from_header


def test_round_trip_preserves_headers_columns_and_unsigned_scaling(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    header = fits.Header({"HIERARCH ESO DPR CATG": "CALIB", "DATAMD5": "original identifier"})
    header["HISTORY"] = "first history card"
    header["HISTORY"] = "second history card"
    header["HIERARCH ESO LONG KEY"] = "long value " * 30
    table = fits.BinTableHDU.from_columns([
        fits.Column(name="name", format="12A", array=["alpha", "beta"]),
        fits.Column(name="value", format="D", array=[1.25, np.nan]),
        fits.Column(name="variable", format="PJ()", array=[np.arange(3), np.arange(5)]),
    ])
    table.header["THEAP"] = 128
    ascii_table = fits.TableHDU.from_columns([
        fits.Column(name="number", format="I6", array=[12, 34]),
    ])
    path = source / "example.fits"
    fits.HDUList([
        fits.PrimaryHDU(header=header),
        fits.ImageHDU(np.ones((8, 12), dtype=np.float32), name="FLOAT"),
        fits.ImageHDU(np.ones((4, 5), dtype=np.uint16), name="UNSIGNED"),
        table, ascii_table,
    ]).writeto(path, checksum=True)
    fits.PrimaryHDU().writeto(source / "unclassified.fits")
    (source / "linked.fits").symlink_to(path)
    before = path.read_bytes()
    fixture = tmp_path / "dataset.json.gz"

    result = create_dataset(source, fixture)
    restored = restore_dataset(fixture, tmp_path / "restored")

    assert result["files"] == 1
    with gzip.open(fixture, "rt") as stream:
        text = stream.read()
    assert text.startswith('{\n  "format":')
    assert text.endswith("\n")
    for entry in json.loads(text)["files"][0]["hdus"]:
        cards = entry["header"]
        assert isinstance(cards, list)
        assert all(len(card) == 80 for card in cards)
        assert cards[-1] == "END".ljust(80)
        assert "data" not in entry
    assert any(card.startswith("CONTINUE") for card in json.loads(text)["files"][0]["hdus"][0]["header"])
    assert path.read_bytes() == before
    assert [p.name for p in restored] == [path.name]
    with fits.open(path) as original, fits.open(restored[0]) as regenerated:
        assert len(original) == len(regenerated)
        for a, b in zip(original, regenerated):
            ignored = {"CHECKSUM", "DATASUM"} if a.is_image and a.header.get("NAXIS", 0) else set()
            if isinstance(a, (fits.BinTableHDU, fits.TableHDU)):
                ignored = {"CHECKSUM", "DATASUM", "NAXIS2", "PCOUNT", "THEAP"}
            assert [c.image for c in a.header.cards if c.keyword not in ignored] == [
                c.image for c in b.header.cards if c.keyword not in ignored
            ]
            if a.is_image and a.header.get("NAXIS", 0):
                np.testing.assert_array_equal(b.data, np.zeros_like(a.data))
                assert a.shape == b.shape
            elif a.header.get("XTENSION") in ("BINTABLE", "TABLE"):
                assert len(b.data) == b.header["NAXIS2"] == b.header["PCOUNT"] == 0
                assert b.header.get("THEAP", 0) == 0
                assert b.fileinfo()["datSpan"] == 0
                assert b.columns.names == a.columns.names
                assert b.columns.formats == a.columns.formats
            if "CHECKSUM" in b.header:
                assert b.verify_checksum() == 1


def test_fixture_is_reproducible_and_restores_sparse_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    path = source / "large.fits"
    fits.PrimaryHDU(np.ones((1024, 1024), dtype=np.float32),
                    header=fits.Header({"HIERARCH ESO PRO CATG": "TEST"})).writeto(path)
    first, second = tmp_path / "first.json.gz", tmp_path / "second.json.gz"
    create_dataset(source, first)
    create_dataset(source, second)
    assert first.read_bytes() == second.read_bytes()
    assert first.stat().st_size < 4096
    restored, = restore_dataset(first, tmp_path / "restored")
    assert restored.stat().st_size == path.stat().st_size
    if hasattr(restored.stat(), "st_blocks"):
        assert restored.stat().st_blocks * 512 < 65536
    np.testing.assert_array_equal(fits.getdata(restored), np.zeros((1024, 1024)))
    with pytest.raises(ValueError, match="Destination exists"):
        restore_dataset(first, tmp_path / "restored")
    with pytest.raises(FileExistsError):
        create_dataset(source, first)
    create_dataset(source, first, overwrite=True)
    assert first.read_bytes() == second.read_bytes()


def test_fixture_retains_original_creation_order_and_rejects_path_traversal(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    for name, timestamp in (("parent.fits", 1), ("product.fits", 2)):
        path = source / name
        fits.PrimaryHDU(header=fits.Header({"HIERARCH ESO PRO CATG": "TEST"})).writeto(path)
        os.utime(path, ns=(timestamp, timestamp))
    fixture = tmp_path / "dataset.json"
    create_dataset(source, fixture)
    paths = restore_dataset(fixture, tmp_path / "restored")
    assert [p.name for p in paths] == ["parent.fits", "product.fits"]
    document = json.loads(fixture.read_text())
    document["files"][0]["path"] = "../escape.fits"
    fixture.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="Unsafe fixture path"):
        restore_dataset(fixture, tmp_path / "unsafe")


def test_bundled_fixture_has_resolvable_provenance_in_ingestion_order():
    fixture = Path(__file__).parent / "data/minimalPipeline.json"
    with fixture.open() as stream:
        records = json.load(stream)["files"]
    names = [Path(record["path"]).name for record in records]
    assert len(names) == len(set(names))
    for index, record in enumerate(records):
        header = fits.Header.fromstring("".join(record["hdus"][0]["header"]))
        recipes = list(get_provenance_from_header(header))
        if not recipes:
            continue
        raws, calibrations, _ = recipes[-1]
        for parent, *_ in raws + calibrations:
            # Some ESO provenance cards truncate long names; ingestion supports
            # uniquely matching those prefixes too.
            matches = [i for i, name in enumerate(names) if name == parent or
                       (len(parent) > 40 and not parent.endswith(".fits") and name.startswith(parent))]
            assert len(matches) == 1, (record["path"], parent)
            assert matches[0] < index, (record["path"], parent)


@pytest.mark.postgresql
@pytest.mark.ingestion_dataset
def test_snapshot_files_can_be_ingested(request, metiswise_database, tmp_path):
    from common.database.Context import context
    from common.database.Database import database
    from metiswise.main.pro import Pro
    from metiswise.main.raw import Raw
    from metiswise.tools.ingest_file import ingest_file

    paths = restore_dataset(request.config.getoption("--ingestion-dataset"), tmp_path / "fits")
    ingested = []
    try:
        for path in paths:
            try:
                item = ingest_file(str(path), store=False)
            except Exception as error:
                error.add_note(f"While ingesting snapshot file {path}")
                raise
            ingested.append(item)
            header = fits.getheader(path)
            assert item.filename == path.name
            assert isinstance(item, Pro if "ESO PRO CATG" in header else Raw)
            if isinstance(item, Pro):
                assert all(parent is not None for parent in item.raws + item.calibs), path.name
    finally:
        database.rollback()
        for item in reversed(ingested):
            context.delete(item, commit=True)
