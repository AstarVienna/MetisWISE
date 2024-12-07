# -*- coding: utf-8 -*-
from pathlib import Path

from astropy.io import fits

from common.database.ClassCache import classcache

from metiswise.main.dataitem import DataItem, persistent
from metiswise.main.drld import drld

current_module = __import__(__name__)

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
    #print(current_module, newclass.__name__, newclass)


correct_key_from_wrong_key = {
    ('SCIENCE', 'IFU', 'SKY'): ('CALIB', 'IFU', 'SKY')
}
for badkey, goodkey in correct_key_from_wrong_key.items():
    Raw.class_from_dpr[badkey] = Raw.class_from_dpr[goodkey]


if False:
    for dpr_key, newclass in Raw.class_from_dpr.items():
        print(f"{newclass.__name__} = Raw.class_from_dpr[{dpr_key}]")

IFU_WAVE_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'WAVE')]  
IFU_RSRF_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'RSRF')]       
IFU_DISTORTION_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'DISTORTION')]       
IFU_STD_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'STD')]                   
IFU_SCI_RAW = Raw.class_from_dpr[('SCIENCE', 'IFU', 'OBJECT')]            
IFU_SKY_RAW = Raw.class_from_dpr[('CALIB', 'IFU', 'SKY')]  
LM_IMAGE_SCI_RAW = Raw.class_from_dpr[('SCIENCE', 'IMAGE,LM', 'OBJECT')]
LM_IMAGE_STD_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,LM', 'STD')]
N_IMAGE_SCI_RAW = Raw.class_from_dpr[('SCIENCE', 'IMAGE,N', 'OBJECT')]
N_IMAGE_STD_RAW = Raw.class_from_dpr[('CALIB', 'IMAGE,N', 'OBJECT')]
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
IFU_SKY_RAW = Raw.class_from_dpr[('SCIENCE', 'IFU', 'SKY')]
