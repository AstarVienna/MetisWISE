# -*- coding: utf-8 -*-

from common.database.DataObject import DataObject, persistent


class DataItem(DataObject):
    _frame = None

    @classmethod
    def to_python(cls):
        """Return Python source for this class's persistent schema.

        Base classes are imported; inherited fields, methods and ordinary
        class attributes are not copied. See ``write_python`` to save it.
        """
        from metiswise.tools.class_source import class_source

        return class_source(cls)

    @classmethod
    def write_python(cls, path=None, *, overwrite=False):
        """Save the schema to ``path`` and return its pathlib.Path.

        The default is ``generated/<ClassName>.py`` relative to cwd.
        Existing files are protected unless ``overwrite=True``.
        """
        from metiswise.tools.class_source import write_class

        return write_class(cls, path, overwrite=overwrite)

    def as_frame(self):
        """Return a cpl Frame of this dataitem."""
        if self._frame is None:
            import cpl
            self._frame = cpl.ui.Frame(self.filename, tag=self.__class__.__name__)
        return self._frame


__all__ = ['DataItem', 'persistent']
