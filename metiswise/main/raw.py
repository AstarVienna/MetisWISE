# -*- coding: utf-8 -*-
from pathlib import Path

from astropy.io import fits

from common.database.ClassCache import classcache

from metiswise.main.dataitem import DataItem, persistent
from metiswise.main.drld import drld

current_module = __import__(__name__)
# These are used in the simulations but are not in the DRLD
keys_to_ignore = {
    ('SCIENCE', 'IMAGE,LM', 'SKY'),
    ('SCIENCE', 'IMAGE,N', 'SKY'),
    ('SCIENCE', 'LSS,LM', 'SKY'),
    ('SCIENCE', 'IMG_LM', 'SKY'),
    ('SCIENCE', 'LSS,N', 'SKY'),

    ('CALIB', 'IMAGE,N', 'STD'),

    ('CALIB', 'IFU', 'FLAT,LAMP'),
    ('CALIB', 'IFU', 'FLAT,TWILIGHT'),
}


# Mode mixins
class Image:
    pass


class Lss:
    pass


class Ifu:
    pass


class Pup:
    pass


class Raw(DataItem):
    dpr_catg = persistent("DPR.CATG", str, "")
    dpr_tech = persistent("DPR.TECH", str, "")
    dpr_type = persistent("DPR.TYPE", str, "")
    det_dit = persistent("DET.DIT", float, 1.0)
    det_ndit = persistent("DET.NDIT", int, 1)
    drs_filter = persistent("DRS.FILTER", str, "")

    # Collect the derived classes that correspond to a set of DPR keywords.
    class_from_dpr = {}

    def __init__(self, filename=None, *args, **kwargs):
        if filename is not None:
            path_file = Path(filename)
            assert path_file.exists(), f"File {filename} does not exist."
            assert path_file.is_file(), f"File {filename} is not a file."
            
            with fits.open(filename) as hdus:
                header_primary = hdus[0].header

            dpr_key_this = (
                header_primary["ESO DPR CATG"],
                header_primary["ESO DPR TECH"],
                header_primary["ESO DPR TYPE"],
            )
            if dpr_key_this in keys_to_ignore:
                print(f"Cannot find {dpr_key_this} as anticipated; using Raw.")
                thisclass = Raw
            else:
                assert dpr_key_this in self.class_from_dpr, f"Cannot find {dpr_key_this}."
                thisclass = self.class_from_dpr[dpr_key_this]
                print("Found", thisclass)
            self.__class__ = thisclass
            super().__init__(*args, **kwargs)
            self.filename = filename
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
        
    
class RawLm(Raw):
    pass


class RawLmImage(RawLm, Image):
    pass


class RawLmLss(RawLm, Lss):
    pass


class RawLmPup(RawLm, Pup):
    pass


class RawN(Raw):
    pass


class RawNImage(RawN, Image):
    pass


class RawNLss(RawN, Lss):
    pass


class RawNPup(RawN, Lss):
    pass


class RawIfu(Raw, Ifu):
    pass


# TODO: Fix this horrible hack.
classcache_before_adding_raws = list(classcache.items())

for name, di in drld.dataitems.items():
    if not name.endswith("_RAW"):
        # Only raw data supported for now.
        continue

    # print()
    # print(di.do_catg)
    dpr_key = (di.dpr_catg, di.dpr_tech, di.dpr_type)
    # print(dpr_key)
    # elements_tech is e.g. ['lss', 'n']
    elements_tech = [a.lower().strip() for a in di.dpr_tech.split(",")]

    classes_ok = [
        classa.aclass
        for classk, classa in classcache_before_adding_raws
        if all(a in classk.lower() for a in elements_tech)
    ]
    assert len(classes_ok) == 1
    theclass = classes_ok[0]
    # print(theclass.__name__)

    # Generate a class for this raw data.
    newclass = type(di.do_catg, (theclass,), {})

    assert dpr_key not in Raw.class_from_dpr
    Raw.class_from_dpr[dpr_key] = newclass
    setattr(current_module, newclass.__name__, newclass)
    # print(current_module, newclass.__name__, newclass)


correct_key_from_wrong_key = {
    ('SCIENCE', 'IFU', 'SKY'): ('CALIB', 'IFU', 'SKY'),
    # ('SCIENCE', 'IMAGE,LM', 'SKY'): ('CALIB', 'IMAGE,LM', 'SKY'),
    ('SCIENCE', 'IMG_LM', 'OBJECT'): ('SCIENCE', 'IMAGE,LM', 'OBJECT'),
}
for badkey, goodkey in correct_key_from_wrong_key.items():
    Raw.class_from_dpr[badkey] = Raw.class_from_dpr[goodkey]


def print_raw_classes_from_drld():
    for dpr_key, newclass in Raw.class_from_dpr.items():
        print(f"    {newclass.__name__} = Raw.class_from_dpr[{dpr_key}]")


try:
    IFU_WAVE_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'WAVE')]
    IFU_RSRF_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'RSRF')]
    IFU_DISTORTION_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'DISTORTION')]
    IFU_STD_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'STD')]
    IFU_SCI_RAW = Raw.class_from_dpr[('SCIENCE', 'IFU', 'OBJECT')]
    IFU_SKY_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'SKY')]
    LM_IMAGE_SCI_RAW = Raw.class_from_dpr[('SCIENCE', 'IMAGE,LM', 'OBJECT')]
    LM_IMAGE_STD_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,LM', 'STD')]
    N_IMAGE_SCI_RAW = Raw.class_from_dpr[('SCIENCE', 'IMAGE,N', 'OBJECT')]
    N_IMAGE_STD_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,N', 'STD')]
    LM_CHOPPERHOME_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,LM', 'CHOPHOME')]
    DETLIN_2RG_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,LM', 'DETLIN')]
    DETLIN_GEO_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,N', 'DETLIN')]
    DETLIN_IFU_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'DETLIN')]
    DARK_2RG_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,LM', 'DARK')]
    DARK_GEO_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,N', 'DARK')]
    DARK_IFU_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'DARK')]
    LM_WCU_OFF_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,LM', 'DARK,WCUOFF')]
    N_WCU_OFF_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,N', 'DARK,WCUOFF')]
    IFU_WCU_OFF_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'DARK,WCUOFF')]
    LM_FLAT_LAMP_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,LM', 'FLAT,LAMP')]
    LM_FLAT_TWILIGHT_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,LM', 'FLAT,TWILIGHT')]
    N_FLAT_LAMP_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,N', 'FLAT,LAMP')]
    N_FLAT_TWILIGHT_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,N', 'FLAT,TWILIGHT')]
    LM_DISTORTION_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,LM', 'DISTORTION')]
    N_DISTORTION_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,N', 'DISTORTION')]
    LM_PUPIL_RAW = Raw.class_from_dpr[('TECHNICAL', 'PUP,M', 'PUPIL')]
    N_PUPIL_RAW = Raw.class_from_dpr[('TECHNICAL', 'PUP,N', 'PUPIL')]
    LM_SLITLOSSES_RAW = Raw.class_from_dpr[('CALIB', 'LSS,LM', 'SLITLOSS')]
    N_SLITLOSSES_RAW = Raw.class_from_dpr[('CALIB', 'LSS,N', 'SLITLOSS')]
    LM_LSS_RSRF_RAW = Raw.class_from_dpr[('CALIB', 'LSS,LM', 'FLAT,LAMP')]
    LM_LSS_RSRF_PINH_RAW = Raw.class_from_dpr[('CALIB', 'LSS,LM', 'FLAT,LAMP,PINH')]
    LM_LSS_WAVE_RAW = Raw.class_from_dpr[('CALIB', 'LSS,LM', 'WAVE')]
    LM_LSS_STD_RAW = Raw.class_from_dpr[('CALIB', 'LSS,LM', 'STD')]
    LM_LSS_SCI_RAW = Raw.class_from_dpr[('SCIENCE', 'LSS,LM', 'OBJECT')]
    N_LSS_RSRF_RAW = Raw.class_from_dpr[('CALIB', 'LSS,N', 'FLAT,LAMP')]
    N_LSS_WAVE_RAW = Raw.class_from_dpr[('CALIB', 'LSS,N', 'WAVE')]
    N_LSS_RSRF_PINH_RAW = Raw.class_from_dpr[('CALIB', 'LSS,N', 'FLAT,LAMP,PINH')]
    N_LSS_STD_RAW = Raw.class_from_dpr[('CALIB', 'LSS,N', 'STD')]
    N_LSS_SCI_RAW = Raw.class_from_dpr[('SCIENCE', 'LSS,N', 'OBJECT')]
    LM_OFF_AXIS_PSF_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,LM', 'PSF,OFFAXIS')]
    N_OFF_AXIS_PSF_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,N', 'PSF,OFFAXIS')]
    IFU_OFF_AXIS_PSF_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'PSF,OFFAXIS')]
except KeyError as e:
    print("Error importing Raw classes:")
    print(e)
    print("Perhaps the list is wrong, use:")
    print_raw_classes_from_drld()
