"""Cheap ScopeSim inputs for archive tests, isolated from the user's IRDB."""

from copy import deepcopy
from pathlib import Path

import yaml


def prepare_archive_irdb(irdb, directory):
    """Return a temporary IRDB overlay while sharing unchanged large assets.

    Keep detector sizes, spectral traces, wavelength sampling, noise and FITS
    headers. Only skip PSF convolution and coarsen IFU sky sampling by two.
    """
    irdb, directory = map(Path, (irdb, directory))
    instrument_root = directory / "irdb"
    instrument_root.mkdir(parents=True)
    for package in ("METIS", "ELT", "Armazones"):
        source = irdb / package
        destination = instrument_root / package
        if package != "METIS":
            destination.symlink_to(source.resolve(), target_is_directory=True)
            continue
        destination.mkdir()
        for path in source.iterdir():
            target = destination / path.name
            if path.is_file() and path.suffix in (".yaml", ".yml"):
                documents = list(yaml.safe_load_all(path.read_text()))
                adjusted = deepcopy(documents)
                for document in adjusted:
                    if not isinstance(document, dict):
                        continue
                    for effect in document.get("effects", []):
                        if effect.get("name") == "psf":
                            effect["include"] = False
                    if document.get("name") == "METIS_LMS":
                        properties = document["properties"]
                        properties["pixel_scale"] *= 2
                if adjusted != documents:
                    target.write_text(yaml.safe_dump_all(adjusted, sort_keys=False))
                    continue
            target.symlink_to(path.resolve(), target_is_directory=path.is_dir())

    return instrument_root
