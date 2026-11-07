"""Check script execution and output discovery without running ScopeSim."""

import json
import os

import pytest

from simulation_blocks import run_simulation_blocks


@pytest.fixture
def block_package(tmp_path):
    root = tmp_path / "package"
    # Different groups and output layouts must not need changes in the runner.
    for group, name, output in (("ESO", "first", "arbitrary/first"), ("Tests", "second", "other/second")):
        script = root / "simulationBlocks" / group / f"{name}.py"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(
            "import json, os, sys\n"
            "from pathlib import Path\n"
            f"output = Path(os.environ['MSIM_OUTDIR']) / {output!r}\n"
            "output.mkdir(parents=True, exist_ok=True)\n"
            f"(output / '{name}.fits').write_text(json.dumps({{\n"
            "    'script': __file__, 'args': sys.argv[1:],\n"
            "    'yaml': os.environ['MSIM_YAML_DIR'],\n"
            "    'cores': os.environ['MSIM_NCORES'],\n"
            "}))\n"
        )
    return root


def test_runs_multiple_scripts_and_ignores_untouched_files(block_package, tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    stale = output / "unrelated.fits"
    stale.write_text("not created by a selected block")
    rewritten = output / "arbitrary/first/first.fits"
    rewritten.parent.mkdir(parents=True)
    rewritten.write_text("previous output that the block will overwrite")
    os.utime(rewritten, ns=(1, 1))
    environment = {**os.environ, "MSIM_OUTDIR": str(output), "MSIM_NCORES": "3"}
    original_environment = environment.copy()

    filenames = run_simulation_blocks(
        block_package, ["ESO/first", "Tests/second.py"], output, tmp_path, environment,
    )

    assert {path.name for path in filenames} == {"first.fits", "second.fits"}
    for path in filenames:
        data = json.loads(path.read_text())
        group = "ESO" if path.stem == "first" else "Tests"
        assert data["script"] == str(block_package / "simulationBlocks" / group / f"{path.stem}.py")
        assert data["args"] == ["--small", "--nCores", "3"]
        assert data["cores"] == "3"
        assert data["yaml"] == str(block_package / "YAML" / group)
    assert environment == original_environment


def test_honors_custom_yaml_directory(block_package, tmp_path):
    output = tmp_path / "output"
    environment = {**os.environ, "MSIM_OUTDIR": str(output), "MSIM_NCORES": "2"}
    yaml_root = str(tmp_path / "custom-yaml")

    filenames = run_simulation_blocks(
        block_package, ["ESO/first"], output, tmp_path, environment, configured_yaml=yaml_root,
        extra_args=("--doCalib=2", "--doStatic"),
    )

    assert json.loads(filenames[0].read_text())["yaml"] == yaml_root
    assert json.loads(filenames[0].read_text())["args"] == [
        "--small", "--nCores", "2", "--doCalib=2", "--doStatic",
    ]


def test_validates_all_block_names_before_execution(block_package, tmp_path):
    output = tmp_path / "output"
    with pytest.raises(pytest.UsageError, match="not in the installed"):
        run_simulation_blocks(
            block_package, ["ESO/first", "ESO/missing"], output, tmp_path, os.environ.copy(),
        )
    assert not output.exists()
