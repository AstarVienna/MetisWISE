"""Tests for the DataItem class."""
from pathlib import Path

import pytest

from metiswise.main.dataitem import DataItem

PATH_TEST_DATA = Path(__file__).parent / "data"

fn_raw = "METIS.N_FLAT_TWILIGHT_RAW.2024-01-02_00_50_42.fits"


@pytest.fixture(autouse=True)
def change_test_dir(monkeypatch):
    monkeypatch.chdir(PATH_TEST_DATA)


def test_dataitem():
    my_di = DataItem(PATH_TEST_DATA / fn_raw)
    assert my_di.filename == fn_raw
    assert isinstance(my_di, DataItem), "TODO: this should become the twilight raw."
    frame = my_di.as_frame()
    assert frame.file == fn_raw
