# -*- coding: utf-8 -*-

from metiswise.main.dataitem import DataItem, persistent


class Hardware(DataItem):
    pass


class Detector(Hardware):
    """A detector"""
    id = persistent("ID", int, -1)
    naxis1 = persistent("NAXIS1", int, -1)
    naxis2 = persistent("NAXIS2", int, -1)


class DetectorArray(Hardware):
    detectors = persistent("DETECTORS", Detector, [])
