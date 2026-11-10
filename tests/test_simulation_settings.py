"""Archive simulation shortcuts preserve the detector and calibration setup."""

import yaml

from simulation_settings import prepare_archive_irdb


def test_archive_profile_changes_only_temporary_optical_settings(tmp_path):
    irdb = tmp_path / "original"
    for package in ("METIS", "ELT", "Armazones"):
        (irdb / package).mkdir(parents=True)
    optics = irdb / "METIS/METIS_LMS.yaml"
    documents = [
        {"name": "METIS_LMS", "properties": {"pixel_scale": 0.0082}, "effects": [
            {"name": "psf", "include": True},
            {"name": "lms_spectral_traces", "kwargs": {"filename": "traces.fits"}},
        ]},
        {"name": "METIS_simulation_parameters", "properties": {
            "spectral": {"spectral_bin_width": 1e-5, "spectral_resolution": 200000},
        }},
    ]
    optics.write_text(yaml.safe_dump_all(documents))
    detectors = irdb / "METIS/detectors.yaml"
    detectors.write_text(yaml.safe_dump({"effects": [
        {"name": "detector_array_list", "kwargs": {"x_size": 2048, "y_size": 2048}},
        {"name": "readout_noise", "include": True},
        {"name": "det_ifu_fits_keywords", "include": True},
    ]}))
    asset = irdb / "METIS/traces.fits"
    asset.write_bytes(b"large unchanged calibration asset")
    fast_irdb = prepare_archive_irdb(irdb, tmp_path / "archive")

    adjusted = list(yaml.safe_load_all((fast_irdb / "METIS/METIS_LMS.yaml").read_text()))
    assert adjusted[0]["effects"][0]["include"] is False
    assert adjusted[0]["properties"]["pixel_scale"] == 0.0164
    assert adjusted[0]["effects"][1] == documents[0]["effects"][1]
    assert adjusted[1] == documents[1]  # Keep narrow wavelength-calibration lines.
    assert (fast_irdb / "METIS/detectors.yaml").read_bytes() == detectors.read_bytes()
    assert (fast_irdb / "METIS/traces.fits").resolve() == asset
    assert (fast_irdb / "ELT").resolve() == irdb / "ELT"
    assert list(yaml.safe_load_all(optics.read_text())) == documents
