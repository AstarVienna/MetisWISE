# -*- coding: utf-8 -*-
from pathlib import Path

from astropy.io import fits

from metiswise.main.dataitem import DataItem, persistent
from metiswise.main.drld import drld

current_module = __import__(__name__)


class Pro(DataItem):
    pro_catg = persistent("PRO.CATG", str, "")

    # Collect the derived classes that correspond to a set of DPR keywords.
    class_from_procatg = {}

    def __init__(self, filename=None, *args, **kwargs):
        if filename is not None:
            path_file = Path(filename)
            assert path_file.exists(), f"File {filename} does not exist."
            assert path_file.is_file(), f"File {filename} is not a file."
            
            with fits.open(filename) as hdus:
                header_primary = hdus[0].header

            pro_catg = header_primary["ESO PRO CATG"]
            assert pro_catg in self.class_from_procatg, f"Cannot find {pro_catg}."
            thisclass = self.class_from_procatg[pro_catg]
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


def generate_pro_classes_from_drld():
    # TODO: Fix this horrible hack.
    # classcache_before_adding_raws = list(classcache.items())

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
        theclass = Pro

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
            # print(current_module, newclass.__name__, newclass)

    correct_key_from_wrong_key = {
        # ('SCIENCE', 'IFU', 'SKY'): ('CALIB', 'IFU', 'SKY'),
        # ('SCIENCE', 'IMG_LM', 'OBJECT'): ('SCIENCE', 'IMAGE,LM', 'OBJECT'),
    }
    for badkey, goodkey in correct_key_from_wrong_key.items():
        Pro.class_from_procatg[badkey] = Pro.class_from_procatg[goodkey]


def generate_pro_classes_from_pipeline():
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
        # assert di.pro_catg() == name
        if class_name.endswith("_RAW"):
            continue
        if class_name not in Pro.class_from_procatg:
            # print(f"Pipeline DataItem that is not in the DRLD: {class_name}")
            newclass = type(class_name, (Pro,), {})
            Pro.class_from_procatg[class_name] = newclass
            setattr(current_module, newclass.__name__, newclass)


generate_pro_classes_from_drld()
generate_pro_classes_from_pipeline()
