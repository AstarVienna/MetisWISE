"""Database round trips for raw exposures."""

import pytest


pytestmark = [pytest.mark.postgresql, pytest.mark.usefixtures("metiswise_database")]


def test_raw_commit_and_select_all():
    # Persistent classes must only be imported after database initialization.
    from common.database.Context import context
    from common.database.Database import database
    from metiswise.main.raw import Raw

    raw = Raw()
    raw.ra = 123.45
    raw.dec = -54.321
    raw.commit()
    object_id = raw.object_id

    # Reconnect to clear the object cache and read the committed row from disk.
    database.disconnect()
    database.connect()
    try:
        matches = [item for item in Raw.select_all() if item.object_id == object_id]
        assert len(matches) == 1
        retrieved = matches[0]
        assert isinstance(retrieved, Raw)
        assert retrieved is not raw
        assert retrieved.ra == pytest.approx(123.45)
        assert retrieved.dec == pytest.approx(-54.321)
    finally:
        context.delete(Raw(object_id=object_id), commit=True)


@pytest.fixture
def raw_fits(tmp_path):
    from astropy.io import fits

    def write(**headers):
        header = fits.Header({
            "HIERARCH ESO DPR CATG": "CALIB",
            "HIERARCH ESO DPR TECH": "IMAGE,N",
            "HIERARCH ESO DPR TYPE": "DARK",
        })
        for key, value in headers.items():
            header[f"HIERARCH ESO {key}"] = value
        filename = tmp_path / "raw.fits"
        fits.PrimaryHDU(header=header).writeto(filename)
        return filename

    return write


@pytest.mark.parametrize(
    "tech, class_name",
    [("IMAGE,LM", "DARK_2RG_RAW"), ("IMAGE,N", "DARK_GEO_RAW"), ("IFU", "DARK_IFU_RAW")],
)
def test_raw_fits_selects_class_and_reads_properties(raw_fits, tech, class_name):
    from metiswise.main.raw import Raw

    filename = raw_fits(**{"DPR TECH": tech, "DET DIT": 2.5, "DET NDIT": 8})
    raw = Raw(filename)

    assert type(raw).__name__ == class_name
    assert raw.filename == filename.name
    assert raw.filepath == str(filename.parent)
    assert raw.det_dit == pytest.approx(2.5)
    assert raw.det_ndit == 8


@pytest.mark.parametrize("value, expected", [(True, 1), (False, 0), ("true", 1), ("FALSE", 0)])
def test_raw_fits_converts_boolean_headers(raw_fits, value, expected):
    from metiswise.main.raw import Raw

    raw = Raw(raw_fits(**{"DET CUBE MODE": value}))
    assert raw.det_cube_mode == expected
    assert isinstance(raw.det_cube_mode, int)


def test_raw_fits_converts_string_property(raw_fits):
    from metiswise.main.raw import Raw

    raw = Raw(raw_fits(**{"INS OPTI1 POSNAME": 7}))
    assert raw.ins_opti1_posname == "7"


def test_raw_fits_falls_back_for_known_unsupported_category(raw_fits):
    from metiswise.main.raw import Raw

    raw = Raw(raw_fits(**{"DPR TECH": "LMS", "DPR TYPE": "DETLIN"}))
    assert type(raw) is Raw


def test_raw_fits_rejects_unknown_category(raw_fits):
    from metiswise.main.raw import Raw

    with pytest.raises(AssertionError, match="Cannot find"):
        Raw(raw_fits(**{"DPR TYPE": "NOT_A_REAL_CATEGORY"}))


def test_raw_rejects_missing_file(tmp_path):
    from metiswise.main.raw import Raw

    with pytest.raises(AssertionError, match="does not exist"):
        Raw(tmp_path / "missing.fits")


def test_raw_rejects_directory(tmp_path):
    from metiswise.main.raw import Raw

    with pytest.raises(AssertionError, match="is not a file"):
        Raw(tmp_path)
