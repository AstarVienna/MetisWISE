"""FITS provenance parsing needs neither persistent classes nor a database."""

from astropy.io import fits
import pytest

from metiswise.main.provenance import (
    get_calib_from_header,
    get_param_from_header,
    get_provenance_from_header,
    get_raw_from_header,
    get_recipe_from_header,
)


def test_raw_header():
    header = fits.Header({
        "HIERARCH ESO PRO REC2 RAW3 NAME": "dark.fits",
        "HIERARCH ESO PRO REC2 RAW3 CATG": "DARK_GEO_RAW",
        "HIERARCH ESO PRO REC2 RAW3 DATAMD5": "0123456789abcdef",
    })
    assert get_raw_from_header(header, 2, 3) == (
        "dark.fits", "DARK_GEO_RAW", "0123456789abcdef",
    )


@pytest.mark.parametrize("prefix", ["CAL", "CALIB"])
def test_calibration_header_accepts_both_spellings(prefix):
    header = fits.Header({
        f"HIERARCH ESO PRO REC1 {prefix}1 NAME": "linearity.fits",
        f"HIERARCH ESO PRO REC1 {prefix}1 CATG": "LINEARITY_GEO",
        f"HIERARCH ESO PRO REC1 {prefix}1 DATAMD5": "abcdef",
    })
    assert get_calib_from_header(header, 1, 1) == (
        "linearity.fits", "LINEARITY_GEO", "abcdef",
    )


def test_cal_takes_precedence_over_calib():
    header = fits.Header({
        "HIERARCH ESO PRO REC1 CAL1 NAME": "current.fits",
        "HIERARCH ESO PRO REC1 CALIB1 NAME": "other.fits",
    })
    assert get_calib_from_header(header, 1, 1) == ("current.fits", None, None)


@pytest.mark.parametrize("reader", [get_raw_from_header, get_calib_from_header])
def test_missing_input_header(reader):
    assert reader(fits.Header(), 1, 1) == (None, None, None)


@pytest.mark.parametrize("value", ["average", 3, False])
def test_parameter_header_preserves_value_type(value):
    header = fits.Header({
        "HIERARCH ESO PRO REC1 PARAM1 NAME": "stacking.method",
        "HIERARCH ESO PRO REC1 PARAM1 VALUE": value,
    })
    name, result = get_param_from_header(header, 1, 1)
    assert name == "stacking.method"
    assert result == value
    assert type(result) is type(value)


def test_missing_parameter_header():
    assert get_param_from_header(fits.Header(), 1, 1) == (None, None)


def test_empty_provenance():
    assert get_recipe_from_header(fits.Header(), 1) == ([], [], [])
    assert get_provenance_from_header(fits.Header()) == []


def test_recipe_groups_inputs_and_stops_at_numbering_gap():
    header = fits.Header({
        "HIERARCH ESO PRO REC1 RAW1 NAME": "first.fits",
        "HIERARCH ESO PRO REC1 RAW2 NAME": "second.fits",
        "HIERARCH ESO PRO REC1 RAW4 NAME": "after-gap.fits",
        "HIERARCH ESO PRO REC1 CAL1 NAME": "calibration.fits",
        "HIERARCH ESO PRO REC1 PARAM1 NAME": "stacking.method",
        "HIERARCH ESO PRO REC1 PARAM1 VALUE": "average",
    })
    assert get_recipe_from_header(header, 1) == (
        [("first.fits", None, None), ("second.fits", None, None)],
        [("calibration.fits", None, None)],
        [("stacking.method", "average")],
    )


def test_provenance_keeps_recipe_order_and_stops_at_gap():
    header = fits.Header({
        "HIERARCH ESO PRO REC1 RAW1 NAME": "original.fits",
        "HIERARCH ESO PRO REC2 RAW1 NAME": "intermediate.fits",
        "HIERARCH ESO PRO REC4 RAW1 NAME": "after-gap.fits",
    })
    assert get_provenance_from_header(header) == [
        ([("original.fits", None, None)], [], []),
        ([("intermediate.fits", None, None)], [], []),
    ]
