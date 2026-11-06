"""Read recipe provenance from FITS headers without accessing the database."""

import itertools


def get_things_from_header(header, ii, func):
    """Get all things for recipe recno from headers."""
    raws = itertools.takewhile(
        lambda x: x[0] is not None,
        (
            func(header, ii, i)
            for i in range(1,1000)
        ),
    )
    return raws


def get_raw_from_header(header, recno, rawno):
    """Get raw rawno for recipe recno from the header"""
    name = header.get(f"ESO PRO REC{recno} RAW{rawno} NAME", None)
    catg = header.get(f"ESO PRO REC{recno} RAW{rawno} CATG", None)
    datamd5 = header.get(f"ESO PRO REC{recno} RAW{rawno} DATAMD5", None)
    return name, catg, datamd5


def get_calib_from_header(header, recno, calibno):
    """Get calib calibno for recipe recno from the header"""
    name = header.get(f"ESO PRO REC{recno} CAL{calibno} NAME", None)
    catg = header.get(f"ESO PRO REC{recno} CAL{calibno} CATG", None)
    datamd5 = header.get(f"ESO PRO REC{recno} CAL{calibno} DATAMD5", None)
    if name is None:
        # Don't know why some files have CAL and others CALIB.
        name = header.get(f"ESO PRO REC{recno} CALIB{calibno} NAME", None)
        catg = header.get(f"ESO PRO REC{recno} CALIB{calibno} CATG", None)
        datamd5 = header.get(f"ESO PRO REC{recno} CALIB{calibno} DATAMD5", None)
    return name, catg, datamd5


def get_param_from_header(header, recno, paramno):
    """Get parameter paramno for recipe recno from the header"""
    name = header.get(f"ESO PRO REC{recno} PARAM{paramno} NAME", None)
    value = header.get(f"ESO PRO REC{recno} PARAM{paramno} VALUE", None)
    return name, value


def get_recipe_from_header(header, recno):
    """Get recipe recno from header."""
    raws = list(get_things_from_header(header, recno, get_raw_from_header))
    calibs = list(get_things_from_header(header, recno, get_calib_from_header))
    params = list(get_things_from_header(header, recno, get_param_from_header))
    return raws, calibs, params


def get_provenance_from_header(header):
    """Get all provenance from header."""
    recipes = itertools.takewhile(
        lambda x: x[0] != [],
        (
            get_recipe_from_header(header, i)
            for i in range(1,1000)
        ),
    )
    return list(recipes)
