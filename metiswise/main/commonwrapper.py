import contextlib
import io
import os

MOCKCOMMON = os.environ.get("mockcommon", "")

try:
    import common
except ImportError:
    MOCKCOMMON = "True"


def suppress_fqdn_warning(fun):
    """Wrapper to prevent annoying warning about hostname not matching fqdn"""

    def wrap(*args, **kwargs):
        """The actual wrapper."""
        ff = io.StringIO()
        with contextlib.redirect_stderr(ff):
            val = fun(*args, **kwargs)
            for lline in ff.getvalue().splitlines():
                if "does not match your Fully Qualified Domain Name" not in lline:
                    print(lline)
        return val

    return wrap


@suppress_fqdn_warning
def import_configfile():
    """Import ConfigFile.

    This suppresses the warning about not matching fqdn."""
    from common.config.Environment import ConfigFile

    ConfigFile.set_sections = suppress_fqdn_warning(ConfigFile.set_sections)
    return ConfigFile


if not MOCKCOMMON:
    ConfigFile = import_configfile()
    from common.config.Environment import Env
    from common.database import DBSelect
    from common.database.ClassCache import classcache
    from common.database.DBMain import DBObject
    from common.database.DBMeta import DBObjectMeta
    from common.database.DBProperties import link_list_property
    from common.database.DBProperties import desc_list_property
    from common.database.DBProperties import link_property
    from common.database.DBProperties import desc_property
    from common.database.DBProperties import persistent_property
    from common.database.DataObject import DataObject
    from common.database.DataObject import persistent
    1/0

    Env["mockcommon"] = ""

else:
    from metiswise.main.commonmock import (
        ConfigFile,
        Env,
        DBSelect,
        classcache,
        DBObject,
        DBObjectMeta,
        link_list_property,
        desc_list_property,
        link_property,
        desc_property,
        persistent_property,
        DataObject,
        persistent,
    )

__all__ = [
    "classcache",
    "link_list_property",
    "desc_list_property",
    "persistent_property",
    "Env",
    "ConfigFile",
    "persistent",
    "DBObjectMeta",
    "ConfigFile",
    "DBObject",
    "desc_property",
    "link_property",
    "DataObject",
    "DBSelect",
]
