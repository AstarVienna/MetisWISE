# -*- coding: utf-8 -*-
"""Ingest a raw fits file."""

from astropy.io import fits
import sys
from metiswise.main.raw import *
from metiswise.main.pro import *
from common.database.ClassCache import classcache


def ingest_file(filename: str):
    print()
    print(f"Ingesting {filename} .")

    q_di = (DataItem.filename == filename)
    if len(q_di):
        print(f"Found {len(q_di)} existing {filename}.")
        myraw = q_di[0]
        return myraw

    hdus = fits.open(filename)
    if "ESO DPR CATG" in hdus[0].header:
        myraw = Raw(filename)
        return myraw
    elif "ESO PRO CATG" in hdus[0].header:
        mypro = Pro(filename)
        return mypro
    else:
        raise ValueError(f"Cannot find DPR.CATG or PRO.CATG in {filename}")


def show_help():
    print(f"{sys.argv[0]} <raw_file.fits>")


def main():
    if len(sys.argv) == 1:
        show_help()

    for filename in sys.argv[1:]:
        toskip = {"LM_IMAGE_SKY_RAW", "LM_LSS_SKY_RAW", "N_IMAGE_SKY_RAW", "N_LSS_SKY_RAW", "PERSISTENCE_MAP"}
        if any(x in filename for x in toskip):
            continue
        myraw = ingest_file(filename)
        if myraw:
            print("Currently not actually storing the data.")
            # myraw.store()
            myraw.commit()

    print()
    for aclass in classcache.values():
        actualclass = aclass.aclass
        print(actualclass.__name__, len(actualclass.select_all()))


if __name__ == "__main__":
    main()
