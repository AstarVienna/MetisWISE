"""Validate both local observing sets without simulating detector pixels."""

from collections import Counter, defaultdict
import os
from pathlib import Path
import runpy
import subprocess
import sys
from types import ModuleType
from unittest.mock import Mock

import pytest
import yaml


ROOT = Path(__file__).resolve().parent / "simulations"
DATASETS = [("functionalPipeline", 24, 1), ("minimalPipeline", 78, 3)]


@pytest.mark.parametrize("name,exposures,detectors", DATASETS)
def test_local_exposure_budgets(name, exposures, detectors):
    recipes = yaml.safe_load((ROOT / "YAML" / f"{name}.yaml").read_text())
    full = yaml.safe_load((ROOT / "YAML/minimalPipeline.yaml").read_text())
    assert sum(r["properties"]["nObs"] for r in recipes.values()) == exposures
    assert all(full[key] == recipe for key, recipe in recipes.items())
    linearity = defaultdict(Counter)
    darks = set()
    for recipe in recipes.values():
        props = recipe["properties"]
        if props["type"] == "DETLIN":
            state = "OFF" if props["filter_name"] == "closed" else "ON"
            linearity[props["tech"]][props["dit"], state] += props["nObs"]
        else:
            assert (props["dit"], props["ndit"]) == (1, 1)
        if props["type"] == "DARK":
            assert props["nObs"] == 2
            darks.add(props["tech"])
        if props["type"] in ("OBJECT", "STD"):
            assert props["nObs"] == 1
    assert len(darks) == len(linearity) == detectors
    for counts in linearity.values():
        assert len({dit for dit, _ in counts}) == 3
        assert all(counts[dit, state] == 2 for dit, _ in counts for state in ("ON", "OFF"))
    assert sum((r["properties"]["dit"] * r["properties"]["ndit"] * 1.2 + 1)
               * r["properties"]["nObs"] for r in recipes.values()) < 3600


@pytest.mark.parametrize("name,exposures,detectors", DATASETS)
def test_blocks_find_local_yaml_outside_checkout(monkeypatch, tmp_path, name, exposures, detectors):
    runner = ModuleType("metis_simulations.runSimulationBlock")
    runner.runSimulationBlock = Mock()
    package = ModuleType("metis_simulations")
    package.runSimulationBlock = runner
    monkeypatch.setitem(sys.modules, package.__name__, package)
    monkeypatch.setitem(sys.modules, runner.__name__, runner)
    helper = ModuleType("_pipeline")
    helper.__dict__.update(runpy.run_path(str(ROOT / "simulationBlocks/_pipeline.py")))
    monkeypatch.setitem(sys.modules, "_pipeline", helper)
    monkeypatch.setenv("MSIM_OUTDIR", str(tmp_path / "custom-output"))
    monkeypatch.setenv("MSIM_NCORES", "3")
    monkeypatch.delenv("MSIM_YAML_DIR", raising=False)
    block = ROOT / "simulationBlocks" / f"{name}.py"
    monkeypatch.setattr(sys, "argv", [str(block), "--noPsf", "--doCalib=2"])
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(block), run_name="__main__")

    yamls, params, args = runner.runSimulationBlock.call_args.args
    assert Path(yamls[0]) == ROOT / "YAML" / f"{name}.yaml"
    assert params["outputDir"] == str(tmp_path / "custom-output" / name)
    assert params["nCores"] == "3"
    assert params["startMJD"] == "2027-01-25 00:00:00"
    assert args[0] == "--doStatic"
    assert args[-1] == "--doCalib=0"
    assert "--small" not in args


@pytest.mark.parametrize("name,exposures,detectors", DATASETS)
def test_real_dry_run_without_simulator_resources(tmp_path, name, exposures, detectors):
    pytest.importorskip("metis_simulations")
    block = ROOT / "simulationBlocks" / f"{name}.py"
    # Use the installed Python library, replacing the pixel backend whose import
    # would otherwise load IRDB instruments even for a dry run.
    program = (
        "import runpy, sys\n"
        "from types import ModuleType\n"
        "backend = ModuleType('metis_simulations.scopesimWrapper')\n"
        "def simulate(*args, **kwargs):\n"
        "    raise AssertionError('dry run tried to simulate')\n"
        "backend.simulate = simulate\n"
        "sys.modules[backend.__name__] = backend\n"
        f"sys.path.insert(0, {str(block.parent)!r})\n"
        f"sys.argv = [{str(block)!r}, '--testRun', '--doStatic', '--doCalib=2']\n"
        f"runpy.run_path({str(block)!r}, run_name='__main__')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", program], cwd=tmp_path, capture_output=True, text=True,
        env={**os.environ, "DEFAULT_IRDB_LOCATION": str(tmp_path),
             "MSIM_OUTDIR": str(tmp_path / "output")},
    )
    assert result.returncode == 0, result.stderr
    assert f"{name}.yaml" in result.stdout
    assert not list(tmp_path.rglob("*.fits"))
