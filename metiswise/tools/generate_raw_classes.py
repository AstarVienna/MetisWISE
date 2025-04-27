# -*- coding: utf-8 -*-

from metiswise.main.raw import *


def print_raw_classes_from_drld():
    print("from metiswise.main.raw import Raw")
    for dpr_key, newclass in Raw.class_from_dpr.items():
        print(f"{newclass.__name__} = Raw.class_from_dpr[{dpr_key}]")


print_raw_classes_from_drld()
