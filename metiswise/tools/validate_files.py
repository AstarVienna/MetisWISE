# -*- coding: utf-8 -*-
"""Ingest a raw fits file."""

import os
import sys

from typing import Optional

from astropy.io import fits

from metiswise.main.dataitem import DataItem
from metiswise.main.raw import *
from metiswise.main.pro import *
from common.database.ClassCache import classcache
from common.database.DBSelect import Select

def validate_file(filename: str) -> Optional[DataItem]:
    print()
    #print(f"Validating {filename} .")
    print(filename, "")
    
    pp = Path(filename)

    hdus = fits.open(filename)
    if "ESO DPR CATG" in hdus[0].header:
        mydi = Raw(filename)
    elif "ESO PRO CATG" in hdus[0].header:
        mydi = Pro(filename)
    else:
        print(f"Cannot find DPR.CATG or PRO.CATG in {filename}")



def show_help():
    print(f"{sys.argv[0]} <raw_file.fits>")


def main():
    if len(sys.argv) == 1:
        show_help()
        return

    filenames = sorted(sys.argv[1:], key=os.path.getctime)

    myraw = None
    for i, filename in enumerate(filenames):
        myraw = validate_file(filename)

    return myraw


if __name__ == "__main__":
    dataitem = main()
