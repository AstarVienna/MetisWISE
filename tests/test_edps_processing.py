"""Exercise real EDPS scheduling without an HTTP server or scientific recipes."""

import os
import sys
from uuid import uuid4

import pytest

from edps_processing import process_with_edps


@pytest.fixture
def edps_example(tmp_path):
    pytest.importorskip("edps")
    from astropy.io import fits

    workflow_dir = tmp_path / f"example_{uuid4().hex}"
    workflow_dir.mkdir()
    (workflow_dir / "__init__.py").write_text("")
    workflow = workflow_dir.name + ".sample_wkf"
    (workflow_dir / "sample_wkf.py").write_text(
        "from edps import classification_rule, data_source, task\n"
        "raw_class = classification_rule('TEST_RAW', {'dpr.type': 'OBJECT'})\n"
        "raw = data_source('raw').with_classification_rule(raw_class).build()\n"
        "reduce = task('reduce').with_main_input(raw).with_recipe('test_recipe').build()\n"
    )
    raw = tmp_path / "raw.fits"
    header = fits.Header({"INSTRUME": "TEST", "MJD-OBS": 60000.0,
                          "HIERARCH ESO DPR TYPE": "OBJECT"})
    fits.PrimaryHDU(header=header).writeto(raw)
    command = tmp_path / "pyesorex"
    command.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys, time\n"
        "from pathlib import Path\n"
        "from astropy.io import fits\n"
        "Path('used_config.txt').write_text(os.environ['PYESOREX_CONFIG'])\n"
        "assert 'PYESOREX_PLUGIN_DIR' not in os.environ\n"
        "if os.environ.get('EDPS_TEST_FAIL'): raise SystemExit(1)\n"
        "time.sleep(float(os.environ.get('EDPS_TEST_DELAY', '0')))\n"
        "product = Path('product.fits').resolve()\n"
        "header = fits.Header({'INSTRUME': 'TEST', 'HIERARCH ESO PRO CATG': 'TEST_PRODUCT'})\n"
        "fits.PrimaryHDU(header=header).writeto(product)\n"
        "manifest = next(arg.split('=', 1)[1] for arg in sys.argv if arg.startswith('--products-sof='))\n"
        "Path(manifest).write_text(json.dumps([{'name': str(product), 'category': 'TEST_PRODUCT'}]))\n"
    )
    command.chmod(0o755)
    return workflow_dir, workflow, raw, command


def test_edps_runs_locally_and_returns_inputs_before_products(edps_example, tmp_path, monkeypatch):
    workflow_dir, workflow, raw, command = edps_example
    monkeypatch.setenv("PYESOREX_CONFIG", "original-config")
    monkeypatch.setenv("PYESOREX_PLUGIN_DIR", "original-plugin-directory")
    monkeypatch.setenv("EDPS_TEST_DELAY", "0.3")
    directory = tmp_path / "reduction"
    reports = []

    files = process_with_edps(
        [raw], directory, workflow_dir, workflow=workflow,
        pyesorex=command, recipe_dir=tmp_path / "recipes", timeout=10,
        progress=reports.append, progress_interval=0.05,
    )

    assert files[0] == raw
    assert files[1].name.startswith("PYTEST.TEST.")
    assert files[1].suffix == ".fits"
    assert (directory / "submission.json").is_file()
    assert (directory / "pyesorex.rc").read_text() == f"pyesorex.recipe-dir={tmp_path / 'recipes'}\n"
    assert next(directory.rglob("used_config.txt")).read_text() == str(directory / "pyesorex.rc")
    assert os.environ["PYESOREX_CONFIG"] == "original-config"
    assert os.environ["PYESOREX_PLUGIN_DIR"] == "original-plugin-directory"
    assert reports[0].startswith("EDPS: associating inputs")
    running = [line for line in reports if "running=1" in line]
    assert len(running) >= 2  # Heartbeats continue while a job's status is unchanged.
    assert all("running: reduce" in line for line in running)
    assert "total=1 queued=0 running=0 completed=1 failed=0 missing=0" in reports[-1]


def test_edps_recipe_failures_fail_the_test(edps_example, tmp_path, monkeypatch):
    workflow_dir, workflow, raw, command = edps_example
    monkeypatch.setenv("EDPS_TEST_FAIL", "1")
    reports = []
    with pytest.raises(AssertionError, match="EDPS jobs failed"):
        process_with_edps(
            [raw], tmp_path / "failed", workflow_dir, workflow=workflow,
            pyesorex=command, recipe_dir=tmp_path / "recipes", timeout=10,
            progress=reports.append,
        )
    assert "completed=0 failed=1" in reports[-1]


def test_edps_cannot_pass_without_any_jobs(edps_example, tmp_path):
    workflow_dir, workflow, _, command = edps_example
    with pytest.raises(AssertionError, match="generated no jobs"):
        process_with_edps(
            [], tmp_path / "empty", workflow_dir, workflow=workflow,
            pyesorex=command, timeout=10,
        )


def test_edps_reports_missing_calibration_associations(edps_example, tmp_path):
    workflow_dir, workflow, raw, command = edps_example
    with (workflow_dir / "sample_wkf.py").open("a") as source:
        source.write(
            "calib_class = classification_rule('TEST_CALIB')\n"
            "calib = data_source('calib').with_classification_rule(calib_class).build()\n"
            "reduce = (task('reduce').with_main_input(raw).with_associated_input(calib)\n"
            "          .with_recipe('test_recipe').build())\n"
        )
    with pytest.raises(AssertionError, match="incomplete associations"):
        process_with_edps(
            [raw], tmp_path / "incomplete", workflow_dir, workflow=workflow,
            pyesorex=command, timeout=10,
        )


def test_edps_timeout_preserves_diagnostics_and_avoids_zombie_process_scan(edps_example, tmp_path, monkeypatch):
    import json

    from edps.EDPS import EDPS
    import psutil

    workflow_dir, workflow, raw, command = edps_example
    monkeypatch.setenv("EDPS_TEST_DELAY", "0.3")
    original_halt = EDPS.halt_executions
    calls = []

    def halt(engine, terminate_running=True):
        calls.append(terminate_running)
        if terminate_running:
            # Reproduce the exception thrown by EDPS's child-process scan.
            raise psutil.ZombieProcess(12345)
        return original_halt(engine, terminate_running=False)

    monkeypatch.setattr(EDPS, "halt_executions", halt)
    directory = tmp_path / "timeout"
    with pytest.raises(AssertionError, match=r"EDPS exceeded 0.01s.*reduce.*--edps-timeout"):
        process_with_edps(
            [raw], directory, workflow_dir, workflow=workflow,
            pyesorex=command, recipe_dir=tmp_path / "recipes", timeout=0.01,
        )

    assert calls == [False]
    snapshots = list(directory.glob("job-*.json"))
    assert len(snapshots) == 1
    assert json.loads(snapshots[0].read_text())["configuration"]["task_name"] == "reduce"
    # Graceful timeout waits for the active recipe; teardown leaves no worker
    # running with our temporary environment or workflow configuration.
    assert list(directory.rglob("products.json"))
