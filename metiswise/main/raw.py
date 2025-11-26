# -*- coding: utf-8 -*-
from pathlib import Path

from astropy.io import fits

from common.database.ClassCache import classcache

from metiswise.main.dataitem import DataItem, persistent
from metiswise.main.drld import drld

current_module = __import__(__name__)
# These are used in the simulations but are not in the DRLD
keys_to_ignore = {
    # Unclear what the status is of the SCIENCE SKY_RAWs, see
    # https://github.com/AstarVienna/METIS_Simulations/issues/151
    ('SCIENCE', 'IMAGE,LM', 'SKY'),
    ('SCIENCE', 'IMAGE,N', 'SKY'),
    ('SCIENCE', 'LSS,LM', 'SKY'),
    ('SCIENCE', 'LSS,N', 'SKY'),

    # Should be IMAGE,LM, see
    # https://github.com/AstarVienna/METIS_Simulations/pull/149
    ('CALIB', 'LM', 'FLAT,LAMP'),
    ('CALIB', 'N', 'FLAT,LAMP'),

    # Should be PRO, see
    # https://github.com/AstarVienna/METIS_Simulations/issues/150
    ('CALIB', 'IMAGE,LM', 'PERSISTENCE'),
    ('CALIB', 'IMAGE,N', 'PERSISTENCE'),
    ('CALIB', 'IFU', 'PERSISTENCE'),
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


def generate_raw_classes_from_drld():
    # TODO: Fix this horrible hack.
    classcache_before_adding_raws = list(classcache.items())

    for name, di in drld.dataitems.items():
        if not name.endswith("_RAW"):
            # Only raw data supported for now.
            continue

        # print()
        # print(di.do_catg)
        dpr_key = (di.dpr_catg, di.dpr_tech, di.dpr_type)
        if dpr_key in Raw.class_from_dpr:
            continue
        
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

        # TODO: Aaargh. Instead, move generate_raw_classes_from_drld,
        # and do
        # import raw
        # setattr(raw, newclass.__name__, newclass)
        globals()[newclass.__name__] = newclass

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


def generate_raw_classes_from_pipeline():
    """Use the pipeline to infer what the processed classes are."""
    try:
        import pymetis
    except ImportError as e:
        print(f"Cannot import pymetis! {e}")
        return

    # Importing the recipes should register all the DataItem classes.
    # noinspection PyUnusedImports
    import pymetis.recipes
    from pymetis.classes.dataitems import DataItem as pipeDataItem
    # noinspection PyUnresolvedReferences,PyProtectedMember
    for class_name, di in pipeDataItem._DataItem__registry.items():
        if not class_name.endswith("_RAW"):
            continue
        if class_name not in classcache.keys():
            print(f"Pipeline DataItem that is not in the DRLD: {class_name}")
            newclass = type(class_name, (Raw,), {})
            # TODO: Somehow get the dpr_key. Should be possible from the
            #       workflow, but that is not part of pymetis.
            #Raw.class_from_dpr[dpr_key] = newclass
            setattr(current_module, newclass.__name__, newclass)


generate_raw_classes_from_drld()
generate_raw_classes_from_pipeline()
