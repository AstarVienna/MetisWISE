# -*- coding: utf-8 -*-
from pathlib import Path

from astropy.io import fits

from common.database.DataObject import DataObject, persistent

# Cache of dataitems.
DATAITEM_CACHE = {}


class DataItem(DataObject):
    _frame = None

    def __new__(cls, filename=None, *args, **kwargs):
        import metiswise.main.aweimports
        from metiswise.main.raw import Raw
        from metiswise.main.pro import Pro
        # Is it a file?
        if filename is None:
            return DataObject.__new__(cls)

        # Is the file cached?
        # TODO: Ensure __init__() is not called on the cached file.
        filename2 = Path(filename)
        if filename2 in DATAITEM_CACHE:
            return DATAITEM_CACHE[filename2]
        if filename2.name in DATAITEM_CACHE:
            return DATAITEM_CACHE[filename2.name]

        # Not cached; is it a FITS file
        try:
            hdus = fits.open(filename)
            header = hdus[0].header
            if 'ESO PRO CATG' in header:
                return Pro.__new__(cls, filename=filename, *args, **kwargs)
            if 'ESO DPR CATG' in header:
                return Raw.__new__(cls, filename=filename, *args, **kwargs)
            return DataObject.__new__(cls)
        except (OSError, FileNotFoundError):
            # Not a FITS file
            return DataObject.__new__(cls)

    def __init__(self, filename=None, **kwargs):
        # DataObject does not support *args.
        filename_str = str(filename)
        super().__init__(filename_str, **kwargs)
        # TODO: What if object is instantiated through object_id?
        if filename is not None:
            filename2 = Path(filename)
            if filename2 in DATAITEM_CACHE:
                assert DATAITEM_CACHE[filename2] == self
            elif filename2.name in DATAITEM_CACHE:
                assert DATAITEM_CACHE[filename2.name] == self
            else:
                DATAITEM_CACHE[filename2] = self
                DATAITEM_CACHE[filename2.name] = self

    def as_frame(self):
        """Return a cpl Frame of this dataitem."""
        if self._frame is None:
            import cpl
            self._frame = cpl.ui.Frame(self.filename, tag=self.__class__.__name__)
        return self._frame


__all__ = ['DataItem', 'persistent']
