"""Store real FITS bytes independently of the archive's persistent metadata."""

from hashlib import sha256
from uuid import uuid4

import pytest


pytestmark = [pytest.mark.postgresql, pytest.mark.usefixtures("metiswise_database")]


def test_ingested_fits_can_be_retrieved_after_removing_local_copy(tmp_path, metiswise_dataserver):
    from astropy.io import fits
    import numpy as np

    from common.database.Context import context
    from common.database.Database import database
    from metiswise.tools.ingest_file import ingest_file

    filename = tmp_path / f"pytest-storage-{uuid4().hex}.fits"
    pixels = np.arange(24, dtype=np.int16).reshape(4, 6)
    header = fits.Header({
        "INSTRUME": "METIS",
        "HIERARCH ESO DPR CATG": "CALIB",
        "HIERARCH ESO DPR TECH": "IMAGE,N",
        "HIERARCH ESO DPR TYPE": "DARK",
        "HIERARCH ESO DET DIT": 1.0,
        "HIERARCH ESO DET NDIT": 1,
    })
    fits.PrimaryHDU(data=pixels, header=header).writeto(filename)
    digest = sha256(filename.read_bytes()).hexdigest()

    item = ingest_file(str(filename))
    cls, object_id = type(item), item.object_id
    try:
        assert item.is_stored()
        assert list((metiswise_dataserver.directory / "sdata").rglob(filename.name + "*"))
        filename.unlink()
        # Read metadata from PostgreSQL rather than retaining the original object.
        database.disconnect()
        database.connect()
        retrieved = cls(object_id=object_id)
        assert retrieved.filename == filename.name
        download = tmp_path / "download"
        download.mkdir()
        retrieved.filepath = str(download)
        retrieved.retrieve()

        restored = download / filename.name
        assert restored.is_file()
        assert sha256(restored.read_bytes()).hexdigest() == digest
        np.testing.assert_array_equal(fits.getdata(restored), pixels)
        assert not filename.exists()
    finally:
        context.delete(cls(object_id=object_id), commit=True)
