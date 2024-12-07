# -*- coding: utf-8 -*-
"""Ingest a raw fits file."""

import sys
from pathlib import Path

from astropy.io import fits

from metiswise.main.raw import *

def ingest_file(filename: str):
    print()
    print(f"Ingesting {filename} .")
    q_di = (DataItem.filename == filename)
    if len(q_di):
        print(f"Found {len(q_di)} existing {filename}.")
        myraw = q_di[0]
    else:
        myraw = Raw(filename)
    
    return myraw

def help():
    print(f"{argv[0]} <raw_file.fits>")

#def main():
if __name__ == '__main__':
    if len(sys.argv) < 1:
        help()

    #filename = sys.argv[1]
    for filename in sys.argv[1:]:
        myraw = ingest_file(filename)
        myraw.commit()


    print()
    for aclass in classcache.values():
        theclass = aclass.aclass
        print(theclass.__name__, len(theclass.select_all()))
