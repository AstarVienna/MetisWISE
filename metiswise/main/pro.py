# -*- coding: utf-8 -*-
import itertools
from pathlib import Path

from astropy.io import fits

from common.database.ClassCache import classcache

from metiswise.main.dataitem import DataItem, persistent
from metiswise.main.drld import drld

current_module = __import__(__name__)


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


# noinspection PyTypeChecker
def get_optional_dataitem_from_filename(filename):
    """Get dataitem but allow it to not exist."""
    dis = DataItem.filename == filename
    ldis = len(dis)
    if ldis == 0:
        # It could be that the name was too long and truncated. So lets see
        # whether there is a DataItem where the filename starts with the same
        # string.
        # This can obviously lead to multiple results.
        if len(filename) > 40 and not filename.endswith(".fits"):
            dis = DataItem.filename.like(f"{filename}*")
            ldis = len(dis)

    if ldis == 0:
        print(f"Warning, {ldis} objects found with filename {filename}")
        return None
    if ldis > 1:
        print(f"Warning, {ldis} objects found with filename {filename}")
    return dis[0]



class Pro(DataItem):
    pro_catg = persistent("PRO.CATG", str, "")

    # Placeholder properties so any new recipe will automatically be supported.
    raws = persistent("Primary inputs", DataItem, [])
    raw1 = persistent("Primary input 1", DataItem, None)
    raw2 = persistent("Primary input 2", DataItem, None)
    raw3 = persistent("Primary input 3", DataItem, None)
    raw4 = persistent("Primary input 4", DataItem, None)
    raw5 = persistent("Primary input 5", DataItem, None)
    raw6 = persistent("Primary input 6", DataItem, None)
    raw7 = persistent("Primary input 7", DataItem, None)
    raw8 = persistent("Primary input 8", DataItem, None)
    raw9 = persistent("Primary input 9", DataItem, None)

    # Placeholder properties so any new recipe will automatically be supported.
    calibs = persistent("Calibration inputs", DataItem, [])
    calib1 = persistent("Calibration input 1", DataItem, None)
    calib2 = persistent("Calibration input 2", DataItem, None)
    calib3 = persistent("Calibration input 3", DataItem, None)
    calib4 = persistent("Calibration input 4", DataItem, None)
    calib5 = persistent("Calibration input 5", DataItem, None)
    calib6 = persistent("Calibration input 6", DataItem, None)
    calib7 = persistent("Calibration input 7", DataItem, None)
    calib8 = persistent("Calibration input 8", DataItem, None)
    calib9 = persistent("Calibration input 9", DataItem, None)

    # Collect the derived classes that correspond to a set of DPR keywords.
    class_from_procatg = {}

    def __init__(self, filename=None, *args, **kwargs):
        """Initialize processed dataitem from FITS headers.

        HIERARCH ESO PRO REC1 RAW1 NAME = 'METIS.DARK_GEO_RAW.2027-01-25_00_14_29.fits'
        HIERARCH ESO PRO REC1 RAW1 CATG = 'DARK_GEO_RAW' / Category of raw frame
        HIERARCH ESO PRO REC1 RAW2 NAME = 'METIS.DARK_GEO_RAW.2027-01-25_00_14_30.fits'
        HIERARCH ESO PRO REC1 RAW2 CATG = 'DARK_GEO_RAW' / Category of raw frame
        HIERARCH ESO PRO REC1 CAL1 NAME= 'LINEARITY_GEO_2025-11-24T14-24-27-403742.fits'
        HIERARCH ESO PRO REC1 CAL1 CATG = 'LINEARITY_GEO' / Category of calibration fram
        HIERARCH ESO PRO REC1 CAL1 DATAMD5 = 'Not computed' / MD5 signature of calib fra
        HIERARCH ESO PRO REC1 PARAM1 NAME = 'metis_det_dark.stacking.method' / Name of t
        HIERARCH ESO PRO REC1 PARAM1 VALUE = 'average ' / Default: 'average'
       """
        if filename is not None:
            path_file = Path(filename)
            assert path_file.exists(), f"File {filename} does not exist."
            assert path_file.is_file(), f"File {filename} is not a file."

            with fits.open(filename) as hdus:
                header_primary = hdus[0].header

            # Figure out which class this DataItem is, and initialize that.
            pro_catg = header_primary["ESO PRO CATG"]
            assert pro_catg in self.class_from_procatg, f"Cannot find {pro_catg}."
            thisclass = self.class_from_procatg[pro_catg]
            print("Found", thisclass)
            self.__class__ = thisclass
            super().__init__(*args, **kwargs)

            # Set path and filename of this file.
            self.pathname = filename

            # Get the provenance.
            provenance = get_provenance_from_header(header_primary)
            if provenance:
                # Only the last recipe is important now.
                prov_raws, prov_calibs, _params = provenance[-1]
                names_raws = [fn for fn, *_ in prov_raws]
                names_calibs = [fn for fn, *_ in prov_calibs]

                raws = [
                    get_optional_dataitem_from_filename(fn)
                    for fn in names_raws
                ]
                self.raws = raws
                (
                    self.raw1, self.raw2, self.raw3,
                    self.raw4, self.raw5, self.raw6,
                    self.raw7, self.raw8, self.raw9,
                    *_
                ) = raws + [None] * 10

                calibs = [
                    get_optional_dataitem_from_filename(fn)
                    for fn in names_calibs
                ]
                self.calibs = calibs
                (
                    self.calib1, self.calib2, self.calib3,
                    self.calib4, self.calib5, self.calib6,
                    self.calib7, self.calib8, self.calib9,
                    *_
                ) = calibs + [None] * 10


            # Set the properties that we can set automatically from the headers.
            for prop_name in thisclass.get_persistent_properties():
                prop = getattr(thisclass, prop_name)
                # attrname_short_eso is e.g. "DPR.CATG"
                attrname_short_eso = prop.__doc__
                attrname_fits = f"ESO {attrname_short_eso}".replace(".", " ")
                if attrname_fits in header_primary:
                    value = header_primary[attrname_fits]
                    setattr(self, prop_name, value)
        else:
            super().__init__(*args, **kwargs)


def generate_pro_classes_from_drld():
    # TODO: Fix this horrible hack.
    classcache_before_adding_pros = list(classcache.items())

    for name, di in drld.dataitems.items():
        if name.endswith("_RAW"):
            # Everything non-raw is PRO, or at least should have a PRO.CATG
            continue

        # TODO: Split up in subclasses as well?
        # classes_ok = [
        #     classa.aclass
        #     for classk, classa in classcache_before_adding_raws
        # ]
        # assert len(classes_ok) == 1
        # theclass = classes_ok[0]
        # theclass = Pro
        elements_tech = ["pro"]
        classes_ok = [
            classa.aclass
            for classk, classa in classcache_before_adding_pros
            if all(a in classk.lower() for a in elements_tech)
        ]
        assert len(classes_ok) == 1
        theclass = classes_ok[0]

        # Some LSS data items do not list their do_catg...
        # assert di.pro_catg == di.do_catg, f"{di.pro_catg=} != {di.do_catg=}"

        # Generate a class for this processed data.
        class_names = {
            di.pro_catg.replace("det", det).replace("cgrph", cgrph)
            # TODO: Split out band and detector.
            # There is some code somewhere to do that.
            for det in ["LM", "N", "IFU", "2RG", "GEO"]
            # TODO: Ensure this list of cgrph is correct.
            # Not all coronagraphs are available for all bands, so this double
            # for loop can't really work.
            for cgrph in ["RAVC", "CVC", "APP", "CLC", "SPP"]
        }
        for class_name in class_names:
            if class_name in Pro.class_from_procatg:
                # Already done. TODO: check why.
                continue
            if class_name.startswith("2"):
                # TODO: These should always be LM righT?
                continue

            newclass = type(class_name, (theclass,), {})
            Pro.class_from_procatg[class_name] = newclass
            setattr(current_module, newclass.__name__, newclass)
            globals()[newclass.__name__] = newclass

    correct_key_from_wrong_key = {
        # ('SCIENCE', 'IFU', 'SKY'): ('CALIB', 'IFU', 'SKY'),
        # ('SCIENCE', 'IMG_LM', 'OBJECT'): ('SCIENCE', 'IMAGE,LM', 'OBJECT'),
    }
    for badkey, goodkey in correct_key_from_wrong_key.items():
        Pro.class_from_procatg[badkey] = Pro.class_from_procatg[goodkey]
        setattr(current_module, newclass.__name__, newclass)
        globals()[newclass.__name__] = newclass


def generate_pro_classes_from_pipeline():
    """Use the pipeline to infer what the processed classes are."""
    try:
        import pymetis
    except ImportError as e:
        print(f"Cannot import pymetis! {e}")
        return

    # Importing the recipes should register all the DataItem classes.
    # noinspection PyUnusedImports
    import pymetis.instruments.metis.recipes
    from pymetis.engine.dataitems import DataItem as pipeDataItem
    # noinspection PyUnresolvedReferences,PyProtectedMember
    for class_name, di in pipeDataItem._registry.items():
        # TODO: Make the classes hierarchical.
        class_name = class_name.replace("{", "").replace("}", "")
        # assert di.pro_catg() == name
        # Classes that end with _RAW, and the Raw class.
        if class_name.upper().endswith("RAW") or class_name.upper().startswith("QC") or "UNKNOWN" in class_name.upper():
            continue
        if class_name not in Pro.class_from_procatg:
            # print(f"Pipeline DataItem that is not in the DRLD: {class_name}")
            newclass = type(class_name, (Pro,), {})
            Pro.class_from_procatg[class_name] = newclass
            setattr(current_module, newclass.__name__, newclass)
            globals()[newclass.__name__] = newclass


generate_pro_classes_from_drld()
generate_pro_classes_from_pipeline()
