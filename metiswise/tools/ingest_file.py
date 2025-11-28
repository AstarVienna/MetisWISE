# -*- coding: utf-8 -*-
"""Ingest a raw fits file."""

import os
import sys

from typing import Optional

from metiswise.main.dataitem import DataItem
from metiswise.main.raw import *
from metiswise.main.pro import *
from common.database.ClassCache import classcache
from common.database.DBSelect import Select

def ingest_file(filename: str) -> Optional[DataItem]:
    print()
    print(f"Ingesting {filename} .")

    pp = Path(filename)

    to_skip = [
        "IFU_RSRF_BACKGROUND",
        "LM_SKY_BASIC_REDUCED",
        "N_SKY_BASIC_REDUCED",

        # METIS.LM_LSS_SCI_RAW.2027-01-25_00_01_09/2025-11-19T11:30:24.484475/_LM_LSS_SCI_FLUX_TELL_1D.fits .
        "LM_LSS_SCI_FLUX_TELL_1D",

        # METIS.N_LSS_SCI_RAW.2027-01-25_00_01_09/2025-11-19T11:30:24.484475/_N_LSS_SCI_FLUX_TELL_1D.fits
        "N_LSS_SCI_FLUX_TELL_1D",
        
        # METIS.N_IMAGE_SCI_RAW.2027-01-25_00_01_09/2025-11-19T11:30:24.484475/_N_SCI_BKG.fits
        "N_SCI_BKG",

        # METIS.N_IMAGE_SCI_RAW.2027-01-25_00_01_09/2025-11-19T11:30:24.484475/_N_STD_BKG.fits
        "N_STD_BKG",

        # METIS.N_IMAGE_SCI_RAW.2027-01-25_00_01_09/2025-11-19T11:30:24.484475/_N_STD_COMBINED.fits
        "N_STD_COMBINED",
    ]
    for skip in to_skip:
        if skip in filename:
            print(f"Skipping {filename}")
            return None

    # noinspection PyTypeChecker
    q_di: Select = (DataItem.filename == pp.name)
    if len(q_di):
        print(f"Found {len(q_di)} existing {pp.name}.")
        myraw = q_di[0]
        return myraw

    hdus = fits.open(filename)
    if "ESO DPR CATG" in hdus[0].header:
        mydi = Raw(filename)
    elif "ESO PRO CATG" in hdus[0].header:
        mydi = Pro(filename)
    else:
        raise ValueError(f"Cannot find DPR.CATG or PRO.CATG in {filename}")

    # TODO: Add some parameter to optionally store / commit.
    mydi.store()
    mydi.commit()
    return mydi


def show_help():
    print(f"{sys.argv[0]} <raw_file.fits>")


def main():
    if len(sys.argv) == 1:
        show_help()
        return

    filenames = sorted(sys.argv[1:], key=os.path.getctime)

    myraw = None
    for i, filename in enumerate(filenames):
        print(f"{i}/{len(filenames)}: {filename}")
        myraw = ingest_file(filename)

    print()
    for aclass in classcache.values():
        actualclass = aclass.aclass
        print(actualclass.__name__, len(actualclass.select_all()))

    return myraw


if __name__ == "__main__":
    dataitem = main()
