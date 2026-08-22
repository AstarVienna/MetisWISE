"""Tests for the Raw class."""
from metiswise.main.dataitem import DataItem
from metiswise.main.raw import Raw
from metiswise.main.pro import Pro

from .data import PATH_TEST_DATA, FN_RAW_2, FN_PRO_2, change_test_dir


def test_dataitem(change_test_dir):
    my_raw = Raw(PATH_TEST_DATA / FN_RAW_2)

    my_di = Pro(PATH_TEST_DATA / FN_PRO_2)
    assert my_di.filename == FN_PRO_2
    assert isinstance(my_di, DataItem), "TODO: this should become the twilight raw."
    frame = my_di.as_frame()
    assert frame.file == FN_PRO_2
