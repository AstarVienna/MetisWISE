"""Progress is visible during successful tests with normal pytest capture."""

import os
from pathlib import Path
import subprocess
import sys


def test_edps_progress_bypasses_capture_and_restores_it(tmp_path):
    fixtures = Path(__file__).resolve().parents[1] / "conftest.py"
    # Reuse the actual reporter fixture in an isolated pytest invocation.
    # Importing the module does not register its database setup hooks here.
    (tmp_path / "conftest.py").write_text(
        "import importlib.util\n"
        f"spec = importlib.util.spec_from_file_location('metiswise_progress_fixtures', {str(fixtures)!r})\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(module)\n"
        "edps_progress = module.edps_progress\n"
    )
    (tmp_path / "test_live.py").write_text(
        "def test_live(edps_progress, capsys):\n"
        "    print('ordinary output before')\n"
        "    edps_progress('EDPS live progress sentinel')\n"
        "    print('ordinary output after')\n"
        "    captured = capsys.readouterr().out\n"
        "    assert 'ordinary output before' in captured\n"
        "    assert 'ordinary output after' in captured\n"
        "    assert 'EDPS live progress sentinel' not in captured\n"
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--basetemp", str(tmp_path / "pytest-tmp")],
        cwd=tmp_path, capture_output=True, text=True,
        env={**os.environ, "PYTEST_ADDOPTS": ""}, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "EDPS live progress sentinel" in result.stdout
    assert "ordinary output before" not in result.stdout
    assert "ordinary output after" not in result.stdout
