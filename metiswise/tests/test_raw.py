"""Tests for the Raw class."""
from metiswise.main.dataitem import DataItem
from metiswise.main.raw import Raw

from .data import PATH_TEST_DATA, FN_RAW_1, change_test_dir


def test_dataitem(change_test_dir):
    my_di = Raw(PATH_TEST_DATA / FN_RAW_1)
    assert my_di.filename == FN_RAW_1
    assert isinstance(my_di, DataItem), "TODO: this should become the twilight raw."
    frame = my_di.as_frame()
    assert frame.file == FN_RAW_1
