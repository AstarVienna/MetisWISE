from pathlib import Path

import pytest

PATH_TEST_DATA = Path(__file__).parent / "data"

FN_RAW_1 = "METIS.N_FLAT_TWILIGHT_RAW.2024-01-02_00_50_42.fits"


@pytest.fixture(autouse=True)
def change_test_dir(monkeypatch):
    monkeypatch.chdir(PATH_TEST_DATA)
