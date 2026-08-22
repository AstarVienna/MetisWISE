from pathlib import Path

import pytest

PATH_TEST_DATA = Path(__file__).parent / "data"

FN_RAW_1 = "METIS.N_FLAT_TWILIGHT_RAW.2024-01-02_00_50_42.fits"

FN_RAW_2 = "METIS.N_LSS_STD_RAW.2027-01-25_00_02_20.fits"
FN_PRO_2 = "MASTER_N_RESPONSE_2025-11-30T15-10-09-675080.fits"


@pytest.fixture(autouse=True)
def change_test_dir(monkeypatch):
    monkeypatch.chdir(PATH_TEST_DATA)
