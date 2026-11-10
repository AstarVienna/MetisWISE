"""Run an EDPS workflow in process, with recipes executed through PyEsoRex."""

import configparser
from pathlib import Path
import shutil
import sys
import time
from uuid import UUID

import pytest


def process_with_edps(inputs, directory, workflow_dir, *, workflow="metis.metis_wkf",
                      targets=None, timeout=3600, pyesorex=None, recipe_dir=None):
    """Return inputs and products in dependency order for archive ingestion.

    EDPS manages its scheduler and repository directly here; no HTTP server or
    user configuration directory is involved. Logs and submission details remain
    in ``directory`` for diagnosing association and recipe failures.
    """
    from edps.EDPS import EDPS
    from edps.client.ProcessingJobStatus import ProcessingJobStatus
    from edps.client.ProcessingRequest import ProcessingRequest
    from edps.client.ReportsConfiguration import ReportsConfiguration
    from edps.config.configuration import Configuration

    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    workflow_dir = Path(workflow_dir).resolve()
    if not (workflow_dir / f"{workflow.rsplit('.', 1)[-1]}.py").is_file():
        raise pytest.UsageError(f"Workflow {workflow} is missing from {workflow_dir}")
    executable = pyesorex or (Path(sys.executable).parent / "pyesorex")
    executable = shutil.which(str(executable)) or str(executable)
    if not Path(executable).is_file():
        raise pytest.UsageError("PyEsoRex is not installed in the test environment")

    config = configparser.ConfigParser(interpolation=None)
    config.read_dict({
        "executor": {
            "esorex_path": str(executable), "base_dir": str(directory / "jobs"),
            "processes": "1", "cores": "1", "default_omp_threads": "1",
            "dummy": "false", "continue_on_error": "false",
            "output_prefix": "PYTEST",
        },
        "repository": {"type": "memory"},
        "generator": {"breakpoints_url": ""},
        "cleanup": {"enabled": "false"},
    })
    configuration = Configuration(config)
    configuration.write(str(directory / "application.properties"))

    with pytest.MonkeyPatch.context() as settings:
        # EDPS workflow names follow the instrument package convention, e.g.
        # metis.metis_wkf, independently of the enclosing pymetis namespace.
        settings.syspath_prepend(str(workflow_dir.parent))
        if recipe_dir is not None:
            pyesorex_config = directory / "pyesorex.rc"
            pyesorex_config.write_text(f"pyesorex.recipe-dir={Path(recipe_dir).resolve()}\n")
            settings.setenv("PYESOREX_CONFIG", str(pyesorex_config))
            # This environment variable takes precedence over recipe-dir in
            # the config file (e.g. when supplied by a system installation).
            settings.delenv("PYESOREX_PLUGIN_DIR", raising=False)

        engine = EDPS(configuration, {workflow: str(workflow_dir)})
        try:
            response = engine.process_data(ProcessingRequest(
                workflow=workflow, inputs=[str(Path(path).resolve()) for path in inputs],
                targets=targets,
                # This test exercises reduction and archive ingestion, not QC plots.
                reports_configuration=ReportsConfiguration(task_names=[], report_types=[]),
            ))
            submission = directory / "submission.json"
            submission.write_text(response.model_dump_json(indent=2))
            if response.incomplete_jobs or response.incomplete_groups:
                names = sorted({job.task_name for job in response.incomplete_jobs})
                missing = sorted({
                    association.task_name
                    for job in response.incomplete_jobs
                    for association in job.association_details
                    if not association.complete and not association.optional
                })
                raise AssertionError(
                    f"EDPS has incomplete associations for {names}: missing {missing}; "
                    "supply the required calibration "
                    f"blocks or --edps-input paths. See {submission}"
                )
            assert response.jobs, f"EDPS generated no jobs for {workflow}; see {submission}"

            deadline = time.monotonic() + timeout
            job_ids = [UUID(job.job_id) for job in response.jobs]
            terminal = {ProcessingJobStatus.COMPLETED, ProcessingJobStatus.FAILED, ProcessingJobStatus.MISSING}
            while True:
                statuses = [engine.get_job_status(job_id).status for job_id in job_ids]
                if all(status in terminal for status in statuses):
                    break
                if time.monotonic() >= deadline:
                    jobs = _save_job_details(engine, job_ids, directory)
                    pending = [job.configuration.task_name for job in jobs
                               if job.status not in terminal]
                    # Stop queued work, letting an active recipe finish. EDPS's
                    # terminate_running=True scans all child processes and does
                    # not handle ZombieProcess/NoSuchProcess races. Its public
                    # graceful-stop path avoids that scan and drains the queue.
                    engine.halt_executions(terminate_running=False)
                    raise AssertionError(
                        f"EDPS exceeded {timeout}s; unfinished tasks at the deadline: {pending}. "
                        f"Increase --edps-timeout for a longer run. Job snapshots and recipe logs: {directory}"
                    )
                time.sleep(0.1)

            jobs = _save_job_details(engine, job_ids, directory)
            failed = [job for job in jobs if job.status != ProcessingJobStatus.COMPLETED]
            assert not failed, (
                f"EDPS jobs failed: {[job.configuration.task_name for job in failed]}; "
                f"recipe stdout/stderr and job details are under {directory}"
            )

            # Parents finish before their consumers. Include associated input
            # calibrations too, so product provenance can refer to archived files.
            ordered = {}
            products = set()
            for job in sorted(jobs, key=lambda job: job.completion_date or ""):
                for file in job.input_files + job.output_files:
                    path = Path(file.name).resolve()
                    if path.suffix.lower() in (".fits", ".fz"):
                        assert path.is_file(), f"EDPS recorded a missing file: {path}"
                        ordered[path] = None
                products.update(Path(file.name).resolve() for file in job.output_files
                                if Path(file.name).suffix.lower() in (".fits", ".fz"))
            assert products, f"EDPS completed without producing FITS products; see {directory}"
            return list(ordered)
        finally:
            engine.shutdown()


def _save_job_details(engine, job_ids, directory):
    """Preserve the state before cancellation as well as after completed runs."""
    jobs = [engine.get_job_details(job_id) for job_id in job_ids]
    for job in jobs:
        (directory / f"job-{job.configuration.job_id}.json").write_text(job.model_dump_json(indent=2))
    return jobs
