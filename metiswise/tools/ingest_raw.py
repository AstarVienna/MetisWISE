# -*- coding: utf-8 -*-
"""Ingest a raw fits file."""

import sys
from metiswise.main.raw import *
from common.database.ClassCache import classcache


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


def show_help():
    print(f"{sys.argv[0]} <raw_file.fits>")


def main():
    if len(sys.argv) == 1:
        show_help()

    for filename in sys.argv[1:]:
        myraw = ingest_file(filename)
        myraw.commit()

    print()
    for aclass in classcache.values():
        actualclass = aclass.aclass
        print(actualclass.__name__, len(actualclass.select_all()))


if __name__ == "__main__":
    main()
