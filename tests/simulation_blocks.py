"""Execute installed block scripts and find the FITS files they write."""

import subprocess
import sys

import pytest


def run_simulation_blocks(package_root, blocks, output_root, directory, environment, configured_yaml=None,
                          *, extra_args=()):
    filenames = set()
    script_root = package_root / "simulationBlocks"
    scripts = {
        path.relative_to(script_root).with_suffix("").as_posix(): path
        for path in script_root.rglob("*.py")
    }
    # Validate all selections before running any potentially expensive block.
    selected = []
    for block in blocks:
        name = block.removesuffix(".py")
        if name not in scripts:
            raise pytest.UsageError(
                f"Simulation block {block!r} is not in the installed metis-simulations package"
            )
        selected.append(scripts[name])
    for script in selected:
        yaml_root = package_root / "YAML" / script.parent.relative_to(script_root)
        block_environment = environment.copy()
        block_environment["MSIM_YAML_DIR"] = configured_yaml if configured_yaml is not None else str(yaml_root)
        before = {path: path.stat().st_mtime_ns for path in output_root.rglob("*.fits")}
        subprocess.run(
            [sys.executable, str(script), "--small", "--nCores", environment["MSIM_NCORES"], *extra_args],
            cwd=directory, env=block_environment, check=True,
        )
        generated = {
            path for path in output_root.rglob("*.fits")
            if path not in before or path.stat().st_mtime_ns != before[path]
        }
        assert generated, f"{script.name} produced no new or updated FITS files"
        filenames.update(generated)
    # Creation order helps ingest primary exposures before products referring to them.
    return sorted(filenames, key=lambda path: (path.stat().st_mtime_ns, str(path)))
