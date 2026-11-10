# Working on MetisWISE

## Scope and layout

- MetisWISE contains its own archive/data-model code; it is not a packaging
  wrapper around a submodule. `metiswise/main/` defines persistent data items,
  FITS-header mapping and provenance; `metiswise/tools/` contains ingestion,
  database setup and fixture conversion tools.
- Metadata lives in PostgreSQL. FITS bytes live in the dataserver. Test these
  separately where useful; committing an object does not upload its file.
- Keep test infrastructure in `conftest.py` and `tests/`. Observing blocks and
  their YAML belong in `tests/simulations/`, not in METIS_Simulations or an
  installed package. `tests/data/minimalPipeline.json` is the ingestion snapshot.
- Sibling checkouts such as commonwise, dataserverwise, METIS_Simulations,
  METIS_Pipeline and irdb are separate projects. Keep upstream fixes intentional
  and distinct from changes to MetisWISE; do not patch installed `.venv` code
  as a persistent solution.

## Environment and dependencies

- Use uv and the repository `.venv`; Python compatibility and dependency
  requirements are specified in `pyproject.toml`. After installing the needed
  groups, use `uv run --no-sync` or `.venv/bin/python` to avoid changing the
  environment during verification, especially with local editable dependencies.
- `test` contains pytest, coverage, dataserverwise, EDPS, PyEsoRex and ADARI;
  `dev` includes `test` plus build tools; `postgres` includes `test` and the
  PostgreSQL harness. `simulations` adds metis-simulations; `notebook` adds Jupyter.
- Keep the explicit source mappings in `[tool.uv.sources]`: Entropynaut for WISE
  and METIS packages, the pycpl index for pycpl, and ESO for EDPS/PyEsoRex/ADARI.
  A package can be declared in a dependency group and still have a source mapping.
  pymetis also brings in pipeline tools transitively.
- Preserve the required pycpl release compatibility. Update `uv.lock` with uv
  when dependency metadata changes; do not upgrade unrelated packages or bump
  the project version for routine edits. Follow the existing release workflow.
- Avoid hardcoded credentials and machine-specific library paths in project
  configuration. Use the existing environment rather than replacing it merely
  because another interpreter is available.

## Verification

Run from this repository's root. See `README.md` for prerequisites and options.

```sh
uv sync --group postgres
uv run --no-sync python -m pytest
uv run --no-sync python -m pytest --run-postgresql
uv run --no-sync python -m pytest --run-postgresql tests/test_dataserver.py
uv run --no-sync python -m pytest --run-postgresql tests/test_ingestion_dataset.py --ingestion-dataset
```

- The default suite must work without starting PostgreSQL, a dataserver, or real
  pixel simulations. Mark database tests `postgresql` and real simulations
  `simulations`; ingestion snapshots are separately opt-in with `--ingestion-dataset`.
- Prefer focused tests and the ingestion snapshot over a full simulation/EDPS
  cycle when they cover the change. Full runs take tens of minutes and consume
  substantial RAM and disk. Describe what was actually verified; collection,
  mocked recipes and dry runs do not prove a complete reduction succeeded.
- Preserve running user tests and their files. For concurrent verification use
  a fresh, explicit `--basetemp` under `/tmp`; pytest's default temporary-directory
  retention can otherwise prune data from an older run.
- Run `git diff --check` before handing off changes. Documentation-only work
  does not require launching the integration stack. If the environment blocks
  sockets or downloads, report the limitation rather than treating skipped or
  unreachable checks as successful integration tests.
- GitHub CI runs ordinary tests and PostgreSQL coverage on pull requests and
  pushes to main. Preserve that trigger scope to avoid duplicate PR runs; full
  simulations and EDPS are currently opt-in rather than part of routine CI.

## Database and dataserver invariants

- Persistent classes register when imported. Import them inside test functions
  or fixtures that depend on `metiswise_database`, after schema initialization.
  Keep test collection free of database side effects. MetisWISE uses ordinary
  session fixtures; do not copy commonwise's pre-collection bootstrap here.
- The harness owns a disposable PostgreSQL cluster with pgcrypto and generated
  credentials. Setup runs as AWOPER, then tests connect as AWTEST. Override
  personal/inherited settings before importing the backend. Do not use a real
  archive or an external database service for these tests.
- The initialized schema and class registrations are shared across the session.
  Roll back failed transactions and clean up committed test objects where
  practical. Reconnect when verifying committed rows independently of the object
  cache. A derived Raw must remain visible through its ancestor classes.
- Existing xfails, comments and workarounds document common's inheritance/cache
  issue (MR 1146). Check whether the installed dependency contains the fix before
  changing those expectations; do not weaken assertions to hide model errors.
- `metiswise_dataserver` starts the installed server as a separate process on a
  dynamic loopback port, with temporary storage and its own local SQLite index.
  Keep startup diagnostics, bounded waits and cleanup on failures. Do not replace
  the real service with a generic HTTP mock for file-transfer integration tests.
- The current common storage client uses `pathname` as its remote lookup key and
  downloads into cwd. Tests retrieve with a basename (`filepath=""`) while
  temporarily inside the destination directory, restoring cwd and filepath
  afterward. Keep remote filenames separate from local destination paths.
- Keep `ingest_file(..., store=False)` available for metadata-only ingestion.
  Test actual upload/retrieval separately with nonzero FITS bytes and hash checks.
- Pure header parsing belongs in `metiswise/main/provenance.py` without database
  imports. The ingestion-dataset converter must also work without a configured DB.

## Simulations and EDPS

```sh
uv sync --group simulations --group postgres
uv run --no-sync python -m pytest --run-postgresql --run-simulations tests/test_simulations.py
uv run --no-sync python -m pytest --run-postgresql --run-simulations --run-edps --simulation-block minimalPipeline tests/test_simulations.py
```

- `functionalPipeline` is the default LM-only set (24 raws); `minimalPipeline`
  is the full set (78 raws). Both use explicit calibrations on the same night.
  The blocks disable automatic `--doCalib` expansion and generate static
  calibrations once. Run overlapping sets separately.
- Execute observing-block scripts through the current Python interpreter and
  call the installed simulator library from those scripts. Do not depend on
  packaged observing resources or `metis_simulations.__main__`.
- Pass `--noPsf`, keep full-size detectors, and preserve explicitly set
  `MSIM_NCORES` and other environment overrides. Avoid reintroducing `--small`:
  recipes can require full detector geometry.
- The default archive profile disables all PSFs and coarsens IFU sky sampling in
  a temporary IRDB overlay. Preserve detector layout, spectral traces, fine
  wavelength sampling, noise and FITS-header effects. `--simulation-profile default`
  selects the original IRDB. Point sources are defined directly in repository
  YAML; do not add transient observing-YAML copies or source-rewriting code.
- Resolve IRDB from `--irdb-root`, `DEFAULT_IRDB_LOCATION`, a sibling checkout,
  or downloads. Never modify the user's IRDB to tune tests. Multiple full-size
  IFU workers can exhaust memory even with the archive shortcuts.
- EDPS runs in process through its library API, with an isolated in-memory
  repository and PyEsoRex recipe subprocesses, not an HTTP server. Retain temporary
  configuration, job snapshots, provenance ordering and per-job recipe logs.
- The EDPS budget is for the whole reduction, not each job. Keep its configurable
  default large enough for the full set. On timeout, save diagnostics and use
  `halt_executions(terminate_running=False)` to cancel queued work and allow active
  recipes to finish; this avoids the observed zombie-process race in EDPS's scan.
  This is a soft limit. Report the timeout rather than masking it with cleanup errors.
- Keep live job summaries visible through pytest capture. Incomplete associations,
  failed jobs, zero jobs and zero FITS products must fail rather than silently pass.

## Compact ingestion fixture

- Use `python -m metiswise.tools.ingestion_dataset create SOURCE FIXTURE --overwrite`
  to deliberately refresh the snapshot; `restore FIXTURE DIRECTORY` recreates it.
  Keep the canonical fixture as pretty-printed plain JSON for inspection and Git
  diffs. Git handles compression; `.json.gz` remains an optional converter output.
- Preserve filenames, HDU order, physical 80-character header cards (including
  CONTINUE), column definitions and provenance. Images restore as zeros with
  their original dimensions, using sparse holes where possible. Tables have zero
  rows and no payloads: adjust NAXIS2, PCOUNT and THEAP accordingly.
- Remove CHECKSUM/DATASUM from modified HDUs. ESO DATAMD5 and recipe hashes remain
  original snapshot identifiers, not valid checksums of replacement data.
- Preserve ingestion order so parent references resolve. Test header round trips,
  duplicate cards, scaled pixels, empty variable-length tables, sparse restoration,
  reproducibility and the bundled fixture's provenance links when changing this tool.
- Preserve input files and protect outputs from accidental overwrite. Keep fixture
  format versions and readers consistent when changing the representation. These
  files test ingestion; they are not scientifically meaningful recipe inputs.
