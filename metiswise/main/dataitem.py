# -*- coding: utf-8 -*-

from common.database.DataObject import DataObject, persistent


class DataItem(DataObject):
    _frame = None

    def as_frame(self):
        """Return a cpl Frame of this dataitem."""
        if self._frame is None:
            import cpl
            self._frame = cpl.ui.Frame(self.filename, tag=self.__class__.__name__)
        return self._frame


__all__ = ['DataItem', 'persistent']
