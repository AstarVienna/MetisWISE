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

    # TODO: File issue
    ('CALIB', 'LMS', 'DETLIN'),
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
    ra = persistent("RA", float, 0.0)
    dec = persistent("DEC", float, 0.0)
    origin = persistent("ORIGIN", str, "")
    instrume = persistent("INSTRUME", str, "")
    telescop = persistent("TELESCOP", str, "")
    airmass = persistent("AIRMASS", float, 0.0)
    # TODO: convert mjdobs to datetime
    mjdobs = persistent("MJD-OBS", float, 0.0)
    # Ignore: EXTEND, NAXIS, BITPIX

    # dpr_catg = persistent("DPR.CATG", str, "")
    # dpr_tech = persistent("DPR.TECH", str, "")
    # dpr_type = persistent("DPR.TYPE", str, "")
    # det_dit = persistent("DET.DIT", float, 1.0)
    # det_ndit = persistent("DET.NDIT", int, 1)
    # drs_filter = persistent("DRS.FILTER", str, "")

    bool_type = int
    bool_false = 0
    bool_true = 1
    det_cube_mode = persistent("DET.CUBE.MODE", bool_type, bool_false) #
    det_dit = persistent("DET.DIT", float, 1) #
    det_ncorrs_name = persistent("DET.NCORRS.NAME", str, "TODO") #
    det_ndit = persistent("DET.NDIT", int, 1) #
    det1_cube_mode = persistent("DET1.CUBE.MODE", bool_type, bool_false) #
    det1_dit = persistent("DET1.DIT", float, 0.25) #
    det1_mode = persistent("DET1.MODE", str, "fast") #
    det1_ndit = persistent("DET1.NDIT", int, 1) #
    det2_cube_mode = persistent("DET2.CUBE.MODE", bool_type, bool_false) #
    det2_dit = persistent("DET2.DIT", float, 1) #
    det2_mode = persistent("DET2.MODE", str, "high_capacity") #
    det2_ndit = persistent("DET2.NDIT", int, 1) #
    det3_cube_mode = persistent("DET3.CUBE.MODE", bool_type, bool_false) #
    det3_dit = persistent("DET3.DIT", float, 0.0004) #
    det3_ndit = persistent("DET3.NDIT", int, 1) #
    dpr_catg = persistent("DPR.CATG", str, "CALIB") #
    dpr_tech = persistent("DPR.TECH", str, "IMAGE,N") #
    dpr_type = persistent("DPR.TYPE", str, "DARK") #
    drs_filter = persistent("DRS.FILTER", str, "open") #
    drs_ifu = persistent("DRS.IFU", str, "open") #
    drs_mask = persistent("DRS.MASK", str, "VPM-L,RAP-LM,APP-LMS") #
    drs_ndfilter = persistent("DRS.NDFILTER", str, "open") #
    ins_cfo_drot_devsim = persistent("INS.CFO_DROT.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_cfo_drot_id = persistent("INS.CFO_DROT.ID", str, "cfo-drot") # Derotator ID
    ins_cfo_drot_mode = persistent("INS.CFO_DROT.MODE", str, "eng") # Derotator mode
    ins_cfo_drot_name = persistent("INS.CFO_DROT.NAME", str, "") # Derotator name
    ins_cfo_drot_pos = persistent("INS.CFO_DROT.POS", int, 0) # Derotator position
    ins_cfo_drot_stat = persistent("INS.CFO_DROT.STAT", str, "Standstill") # Derotator status
    ins_drot_posang = persistent("INS.DROT.POSANG", int, 0) #
    ins_drs_slit = persistent("INS.DRS.SLIT", str, "C-38_1") #
    ins_lms_mode = persistent("INS.LMS.MODE", str, "Nominal") #
    ins_mode = persistent("INS.MODE", str, "IMG_N") #
    ins_opti1_devsim = persistent("INS.OPTI1.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti1_id = persistent("INS.OPTI1.ID", str, "cfo-pp1") # CFP_PP1.ID
    ins_opti1_name = persistent("INS.OPTI1.NAME", str, "") # CFO_PP1.NAME
    ins_opti1_pos = persistent("INS.OPTI1.POS", str, "list: [1.0, 1.0]") #
    ins_opti1_posname = persistent("INS.OPTI1.POSNAME", str, "ignore") # CFO_PP1 named position
    ins_opti1_stat = persistent("INS.OPTI1.STAT", str, "Standstill") # CFO_PP1 status
    ins_opti10_devsim = persistent("INS.OPTI10.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti10_id = persistent("INS.OPTI10.ID", str, "img-lm-fw") # IMG_LM_FW.ID
    ins_opti10_name = persistent("INS.OPTI10.NAME", str, "") # IMG_LM_FW.NAME
    ins_opti10_pos = persistent("INS.OPTI10.POS", int, 0) # IMG_LM_FW position
    ins_opti10_posname = persistent("INS.OPTI10.POSNAME", str, "open") # IMG_LM_FW named position
    ins_opti10_stat = persistent("INS.OPTI10.STAT", str, "Standstill") # IMG_LM_FW status
    ins_opti11_devsim = persistent("INS.OPTI11.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti11_id = persistent("INS.OPTI11.ID", str, "img-lm-ndw") # IMG_LM_NDW.ID
    ins_opti11_name = persistent("INS.OPTI11.NAME", str, "") # IMG_LM_NDW.NAME
    ins_opti11_pos = persistent("INS.OPTI11.POS", int, 0) # IMG_LM_NDW position
    ins_opti11_posname = persistent("INS.OPTI11.POSNAME", str, "open") # IMG_LM_NDW named position
    ins_opti11_stat = persistent("INS.OPTI11.STAT", str, "Standstill") # IMG_LM_NDW status
    ins_opti12_devsim = persistent("INS.OPTI12.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti12_id = persistent("INS.OPTI12.ID", str, "img-n-pw") # IMG_N_PW.ID
    ins_opti12_name = persistent("INS.OPTI12.NAME", str, "") # IMG_N_PW.NAME
    ins_opti12_pos = persistent("INS.OPTI12.POS", int, 0) # IMG_N_PW position
    ins_opti12_posname = persistent("INS.OPTI12.POSNAME", str, "open") # IMG_N_PW named position
    ins_opti12_stat = persistent("INS.OPTI12.STAT", str, "Standstill") # IMG_N_PW status
    ins_opti13_devsim = persistent("INS.OPTI13.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti13_id = persistent("INS.OPTI13.ID", str, "img-n-fw") # IMG_N_FW.ID
    ins_opti13_name = persistent("INS.OPTI13.NAME", str, "") # IMG_N_FW.NAME
    ins_opti13_pos = persistent("INS.OPTI13.POS", int, 0) # IMG_N_FW position
    ins_opti13_posname = persistent("INS.OPTI13.POSNAME", str, "open") # IMG_N_FW named position
    ins_opti13_stat = persistent("INS.OPTI13.STAT", str, "Standstill") # IMG_N_FW status
    ins_opti14_devsim = persistent("INS.OPTI14.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti14_id = persistent("INS.OPTI14.ID", str, "img-n-ndw") # IMG_N_NDW.ID
    ins_opti14_name = persistent("INS.OPTI14.NAME", str, "") # IMG_N_NDW.NAME
    ins_opti14_pos = persistent("INS.OPTI14.POS", int, 0) # IMG_N_NDW position
    ins_opti14_posname = persistent("INS.OPTI14.POSNAME", str, "open") # IMG_N_NDW named position
    ins_opti14_stat = persistent("INS.OPTI14.STAT", str, "Standstill") # IMG_N_NDW status
    ins_opti15_name = persistent("INS.OPTI15.NAME", str, "PUPIL2") #
    ins_opti17_devsim = persistent("INS.OPTI17.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti17_id = persistent("INS.OPTI17.ID", str, "wcu-per") # OPTI17.ID
    ins_opti17_name = persistent("INS.OPTI17.NAME", str, "") # OPTI17.NAME
    ins_opti17_pos = persistent("INS.OPTI17.POS", int, 0) # OPTI17 position
    ins_opti17_posname = persistent("INS.OPTI17.POSNAME", str, "IN") # OPTI17 named position
    ins_opti17_stat = persistent("INS.OPTI17.STAT", str, "Standstill") # OPTI17 status
    ins_opti18_devsim = persistent("INS.OPTI18.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti18_id = persistent("INS.OPTI18.ID", str, "wcu-pp1") # WCU.OPTI18.ID
    ins_opti18_name = persistent("INS.OPTI18.NAME", str, "") # WCU.OPTI18.NAME
    ins_opti18_pos = persistent("INS.OPTI18.POS", int, 0) # WCU.OPTI18 position
    ins_opti18_posname = persistent("INS.OPTI18.POSNAME", str, "open") # WCU.OPTI18 named position
    ins_opti18_stat = persistent("INS.OPTI18.STAT", str, "Standstill") # WCU.OPTI18 status
    ins_opti19_devsim = persistent("INS.OPTI19.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti19_id = persistent("INS.OPTI19.ID", str, "wcu-bb-aperture-mask") # OPTI19.ID
    ins_opti19_name = persistent("INS.OPTI19.NAME", str, "") # OPTI19.NAME
    ins_opti19_pos = persistent("INS.OPTI19.POS", int, 0) # OPTI10 position
    ins_opti19_posname = persistent("INS.OPTI19.POSNAME", float, 1.0) # OPTI19 named position
    ins_opti19_stat = persistent("INS.OPTI19.STAT", str, "Standstill") # OPTI19 status
    ins_opti2_devsim = persistent("INS.OPTI2.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti2_id = persistent("INS.OPTI2.ID", str, "cfo-adc") # CFO_ADC.ID
    ins_opti2_name = persistent("INS.OPTI2.NAME", str, "") # CFO_ADC.NAME
    ins_opti2_pos = persistent("INS.OPTI2.POS", int, 0) # CFO_ADC position
    ins_opti2_posname = persistent("INS.OPTI2.POSNAME", str, "False") # CFO_ADC named position
    ins_opti2_stat = persistent("INS.OPTI2.STAT", str, "Standstill") # CFO_ADC status
    ins_opti20_devsim = persistent("INS.OPTI20.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti20_id = persistent("INS.OPTI20.ID", str, "wcu-fp2-1") # WCU.OPTI20.ID
    ins_opti20_name = persistent("INS.OPTI20.NAME", str, "") # WCU.OPTI20.NAME
    ins_opti20_pos = persistent("INS.OPTI20.POS", int, 0) # WCU.OPTI20 position
    ins_opti20_posname = persistent("INS.OPTI20.POSNAME", str, "open") # WCU.OPTI20 named position
    ins_opti20_stat = persistent("INS.OPTI20.STAT", str, "Standstill") # WCU.OPTI20 status
    ins_opti3_devsim = persistent("INS.OPTI3.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti3_id = persistent("INS.OPTI3.ID", str, "cfo-fp2") # CFO_FP2.ID
    ins_opti3_name = persistent("INS.OPTI3.NAME", str, "") # CFO_FP2.NAME
    ins_opti3_pos = persistent("INS.OPTI3.POS", int, 0) # CFP_FP2 position
    ins_opti3_posname = persistent("INS.OPTI3.POSNAME", str, "False") # CFO_FP2 named position
    ins_opti3_stat = persistent("INS.OPTI3.STAT", str, "Standstill") # CFO_FP2 named position
    ins_opti4_devsim = persistent("INS.OPTI4.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti4_id = persistent("INS.OPTI4.ID", str, "cfo-lms") # CFO_LMS.ID
    ins_opti4_name = persistent("INS.OPTI4.NAME", str, "") # CFO_LMS.NAME
    ins_opti4_pos = persistent("INS.OPTI4.POS", int, 180) # CFO_LMS position
    ins_opti4_posname = persistent("INS.OPTI4.POSNAME", str, "OUT") # CFO_LMS named position
    ins_opti4_stat = persistent("INS.OPTI4.STAT", str, "Standstill") # CFO_LMS status
    ins_opti5_devsim = persistent("INS.OPTI5.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti5_id = persistent("INS.OPTI5.ID", str, "lms-pwa") # LMS_PWA.ID
    ins_opti5_name = persistent("INS.OPTI5.NAME", str, "APP-LMS") #
    ins_opti5_pos = persistent("INS.OPTI5.POS", int, 0) # LMS_PWA position
    ins_opti5_posname = persistent("INS.OPTI5.POSNAME", str, "open") # LMS_PWA named position
    ins_opti5_stat = persistent("INS.OPTI5.STAT", str, "Standstill") # LMS_PWA status
    ins_opti6_devsim = persistent("INS.OPTI6.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti6_id = persistent("INS.OPTI6.ID", str, "lms-gra") # LMS_GRA.ID
    ins_opti6_name = persistent("INS.OPTI6.NAME", str, "") # LMS_GRA.NAME
    ins_opti6_pos = persistent("INS.OPTI6.POS", int, 0) # LMS_GRA position
    ins_opti6_posname = persistent("INS.OPTI6.POSNAME", str, "OUT") # LMS_GRA named position
    ins_opti6_stat = persistent("INS.OPTI6.STAT", str, "Standstill") # LMS_GRA status
    ins_opti7_devsim = persistent("INS.OPTI7.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti7_id = persistent("INS.OPTI7.ID", str, "lms-pra") # LMS-PRA.ID
    ins_opti7_name = persistent("INS.OPTI7.NAME", str, "") # LMS-PRA.NAME
    ins_opti7_pos = persistent("INS.OPTI7.POS", float, 6.739134998995064) # LMS-PRA position [deg]
    ins_opti7_stat = persistent("INS.OPTI7.STAT", str, "Standstill") # LMS-PRA status
    ins_opti8_devsim = persistent("INS.OPTI8.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti8_id = persistent("INS.OPTI8.ID", str, "lms-msa") # LMS-MSA.ID
    ins_opti8_name = persistent("INS.OPTI8.NAME", str, "") # LMS-MSA.NAME
    ins_opti8_order = persistent("INS.OPTI8.ORDER", int, 26) # Spectral order (non-keyword)
    ins_opti8_pos = persistent("INS.OPTI8.POS", float, 2.040945000000022) # LMS-MSA position [deg]
    ins_opti8_stat = persistent("INS.OPTI8.STAT", str, "Standstill") # LMS-MSA status
    ins_opti9_devsim = persistent("INS.OPTI9.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_opti9_id = persistent("INS.OPTI9.ID", str, "img-lm-pw") # IMG_LM_PW.ID
    ins_opti9_name = persistent("INS.OPTI9.NAME", str, "") # IMG_LM_PW.NAME
    ins_opti9_pos = persistent("INS.OPTI9.POS", int, 0) # IMG_LM_PW position
    ins_opti9_posname = persistent("INS.OPTI9.POSNAME", str, "open") # IMG_LM_PW named position
    ins_opti9_stat = persistent("INS.OPTI9.STAT", str, "Standstill") # IMG_LM_PW status
    ins_wcu_bb_ambienttemp = persistent("INS.WCU_BB.AMBIENTTEMP", float, 26.85) # [C] Blackbody ambient temperature
    ins_wcu_bb_devsim = persistent("INS.WCU_BB.DEVSIM", bool_type, bool_true) # Device simulation flag
    ins_wcu_bb_hwstatus = persistent("INS.WCU_BB.HWSTATUS", str, "Hot") # Blackbody source status
    ins_wcu_bb_id = persistent("INS.WCU_BB.ID", str, "wcu-bb") # WCU_BB.ID
    ins_wcu_bb_name = persistent("INS.WCU_BB.NAME", str, "") # WCU_BB.NAME
    ins_wcu_bb_sourcesetp = persistent("INS.WCU_BB.SOURCESETP", float, 726.85) # [C] Blackbody setpoint temperature
    ins_wcu_bb_sourcetemp = persistent("INS.WCU_BB.SOURCETEMP", float, 726.85) # [C] Blackbody source temperature
    ins_wlen_cen = persistent("INS.WLEN.CEN", float, 4.2) # Central wavelength [um]
    ins_wlen_end = persistent("INS.WLEN.END", float, 4.232771559440505) # End wavelength [um]
    ins_wlen_start = persistent("INS.WLEN.START", float, 4.166300558252853) # Start wavelength [um]
    obs_id = persistent("OBS.ID", int, 42) #
    obs_name = persistent("OBS.NAME", str, "TODO") #
    obs_start = persistent("OBS.START", str, "TODO") #
    obs_tplno = persistent("OBS.TPLNO", int, 1) #
    seq_chopnod_offschop = persistent("SEQ.CHOPNOD.OFFSCHOP", str, "list: [3, 0]") # [arcsec]
    seq_chopnod_offsnod = persistent("SEQ.CHOPNOD.OFFSNOD", str, "list: [0, 3]") # [arcsec
    seq_chopnod_st = persistent("SEQ.CHOPNOD.ST", bool_type, bool_false) #
    seq_wcu_lamp_desc = persistent("SEQ.WCU.LAMP.DESC", str, "WCU lamp") #
    seq_wcu_lamp_name = persistent("SEQ.WCU.LAMP.NAME", str, "bb") #
    seq_wcu_laser1 = persistent("SEQ.WCU.LASER1", str, "ON") #
    seq_wcu_laser1_name = persistent("SEQ.WCU.LASER1.NAME", str, "LASER1") #
    seq_wcu_laser2 = persistent("SEQ.WCU.LASER2", str, "ON") #
    seq_wcu_laser3 = persistent("SEQ.WCU.LASER3", str, "ON") #
    seq_wcu_bb_temp = persistent("SEQ.WCU_BB_TEMP", float, 1000) #
    tel_alt = persistent("TEL.ALT", float, 24.5) # Dummy value
    tel_az = persistent("TEL.AZ", float, -1.3) # Dummy value
    tel_geoelev = persistent("TEL.GEOELEV", float, 3046.0) #
    tel_geolat = persistent("TEL.GEOLAT", float, -24.58928) #
    tel_geolon = persistent("TEL.GEOLON", float, -70.19166) #
    tel_targ_dec = persistent("TEL.TARG.DEC", float, 0.0) # Dummy value
    tel_targ_epoch = persistent("TEL.TARG.EPOCH", float, 2000.0) #
    tel_targ_epochsystem = persistent("TEL.TARG.EPOCHSYSTEM", str, "J") #
    tel_targ_parallax = persistent("TEL.TARG.PARALLAX", float, 0.0) # Dummy value
    tel_targ_ra = persistent("TEL.TARG.RA", float, 0.0) # Dummy value
    tel_targ_radvel = persistent("TEL.TARG.RADVEL", float, 0.0) # Dummy value
    tpl_expno = persistent("TPL.EXPNO", int, 1) #
    tpl_id = persistent("TPL.ID", str, "METIS_no_template") #
    tpl_name = persistent("TPL.NAME", str, "METIS_no_template") #
    tpl_start = persistent("TPL.START", str, "2020-01-01T00:00:00.000000") #

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
            super().__init__(filename, *args, **kwargs)
            self.pathname = filename
            for prop_name in thisclass.get_persistent_properties():
                prop = getattr(thisclass, prop_name)
                # attrname_short_eso is e.g. "DPR.CATG"
                attrname_short_eso = prop.__doc__
                attrname_fits = f"ESO {attrname_short_eso}".replace(".", " ")
                if attrname_fits in header_primary:
                    value = header_primary[attrname_fits]
                    if isinstance(value, str) and prop.prop_type != str:
                        # TODO: Does FITS allow all these differences?
                        assert value.lower() in {"false", "true", "f", "t"}
                        value = value.lower() in ("true", "f")
                    if isinstance(value, bool):
                        value = int(value)
                    if prop.prop_type == str:
                        # TODO: Log warning?
                        value = str(value)
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
    import pymetis.instruments.metis.recipes
    from pymetis.engine.dataitems import DataItem as pipeDataItem
    # noinspection PyUnresolvedReferences,PyProtectedMember
    for class_name, di in pipeDataItem._registry.items():
        # TODO: Make the classes hierarchical.
        class_name = class_name.replace("{", "").replace("}", "")
        if not class_name.endswith("_RAW"):
            continue
        if class_name not in classcache.keys():
            # print(f"Pipeline DataItem that is not in the DRLD: {class_name}")
            newclass = type(class_name, (Raw,), {})
            # TODO: Somehow get the dpr_key. Should be possible from the
            #       workflow, but that is not part of pymetis.
            #Raw.class_from_dpr[dpr_key] = newclass
            setattr(current_module, newclass.__name__, newclass)
            globals()[newclass.__name__] = newclass


generate_raw_classes_from_drld()
generate_raw_classes_from_pipeline()
