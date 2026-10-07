import hashlib
import inspect
import logging

from configparser import ConfigParser, InterpolationError
from copy import copy
from dataclasses import dataclass

from metiswise.main.FakePropertyDict import FakePropertyDict

Env = {}


class ConfigFile(dict):
    def __init__(self, filename):
        super().__init__()
        parser = ConfigParser()
        parser.read(filename)
        # self.update(parser["global"])
        section = "global"
        for option in parser.options(section):
            try:
                self[option] = parser.get(section, option)
            except InterpolationError:
                self[option] = parser.get(section, option, raw=True)
        self["mockcommon"] = "True"

    def as_dict(self):
        return self


class DBProxy(object):
    pass


class ClassCache(dict):
    def __setitem__(self, thecls, value):
        assert isinstance(value, FakePropertyDict)
        return dict.__setitem__(self, thecls.__name__, value)

    def __getitem__(self, thecls):
        return dict.__getitem__(self, thecls.__name)


classcache = ClassCache()


@dataclass
class ABCDE(object):
    prop: object
    attr: object


class persistent_property(property):
    def __init__(self, attribute, prop_type, default, doc):
        self.attribute = attribute
        self.prop_type = prop_type
        self.default = default

        def getter(inst):
            return inst._desc.setdefault(attribute, default)

        def setter(inst, value):
            inst._desc[attribute] = value

        property.__init__(self, getter, setter, None, doc)
        self.__doc__ = doc
        self.cls = None

    def __copy__(self):
        return self.__class__(
            self.attribute, self.prop_type, self.default, self.__doc__
        )


class desc_property(persistent_property):
    pass


class desc_list_property(persistent_property):
    pass


class link_property(persistent_property):
    def __getattr__(self, attr):
        return ABCDE(self, getattr(self.prop_type, attr))


class link_list_property(persistent_property):
    pass


def property_factory(*args):
    assert len(args) == 4, f"Only 4 arguments supported, not {len(args)}"
    attribute, doc, prop_type, prop_default = args
    if prop_type is float:
        prop_type = (float, int)
    if isinstance(prop_type, DBObjectMeta):
        if isinstance(prop_default, list):
            propclass = link_list_property
        else:
            propclass = link_property
    else:
        if isinstance(prop_default, list):
            propclass = desc_list_property
        else:
            propclass = desc_property

    return propclass(attribute, prop_type, prop_default, doc)


def persistent(*args):
    f1 = inspect.currentframe()
    fouters = inspect.getouterframes(f1)
    fouterswcode = [f for f in fouters if f.code_context]
    foutersok = [f for f in fouterswcode if "persistent(" in f.code_context[0]]
    # print("HB", foutersok)
    scode = foutersok[0].code_context[0]
    attrname = scode.strip().split()[0]
    args2 = [attrname] + list(args)
    return property_factory(*args2)


class oidtype(object):
    def binary(self):
        return "NOTIMPLEMENTED"


class DBObjectMeta(type):
    def __new__(mcs, name, bases, attributes):
        thecls = type.__new__(mcs, name, bases, attributes)
        base = bases[0]
        if hasattr(base, "get_persistent_properties"):
            for attr in base.get_persistent_properties():
                if attr not in thecls.__dict__:
                    # Need to copy the attr, because otherwise the
                    # setting of .cls below modifies the original.
                    theprop = copy(getattr(base, attr))
                    setattr(thecls, attr, theprop)

        if hasattr(thecls, "get_persistent_properties"):
            for attr in thecls.get_persistent_properties():
                getattr(thecls, attr).cls = thecls

        classcache[thecls] = FakePropertyDict(thecls)
        return thecls

    def get_persistent_properties(cls, exclude_object_id=False):
        """Return a list of persistent attribute names.

        Like the common one in DBMeta.py, but preserving the order in which
        they are defined.
        TODO: Move to common DBMeta?
        """
        return [
            attr
            for attr, v in cls.__dict__.items()
            if isinstance(v, persistent_property)
            and not (exclude_object_id and attr == "object_id")
        ]


class DBObject(object, metaclass=DBObjectMeta):
    dbproxy = DBProxy()

    def __init__(self, *args, **kwargs):
        self.object_id = oidtype()
        if not hasattr(self, "_desc"):
            self._desc = {"object_id": self.object_id}

    def persists(self):
        return True

    def get_persistent(self):
        return self.__class__.get_persistent_properties()


class DataObject(DBObject):
    storage = None
    filename = persistent("The name of the associated file [None]", str, "")

    def __init__(self, pathname="", **kw):
        DBObject.__init__(self)


class DBSelect(object):
    def __len__(self):
        return 0

    def __and__(self, other):
        return self


__all__ = [
    "classcache",
    "desc_property",
    "link_list_property",
    "desc_list_property",
    "persistent_property",
    "Env",
    "ConfigFile",
    "persistent",
    "DBObjectMeta",
    "ConfigFile",
    "DBObject",
    "link_property",
    "DataObject",
    "DBSelect",
]
