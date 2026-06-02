"""Tests for the DataItem class."""
from metiswise.main.dataitem import DataItem

from .data import PATH_TEST_DATA, FN_RAW_1, change_test_dir


def test_dataitem():
    my_di = DataItem(PATH_TEST_DATA / FN_RAW_1)
    assert my_di.filename == FN_RAW_1
    assert isinstance(my_di, DataItem), "TODO: this should become the twilight raw."
    frame = my_di.as_frame()
    assert frame.file == FN_RAW_1
