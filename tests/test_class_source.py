"""Schema exports, including execution against common's real metaclass."""

import ast
import datetime
import os
from pathlib import Path
import subprocess
import sys

import pytest

from metiswise.tools.class_source import _Source


def test_exports_without_database_service(tmp_path):
    # Run common's filebased backend in a separate interpreter so it cannot
    # affect the PostgreSQL backend used by the rest of this pytest session.
    script = """
import runpy
from pathlib import Path
import sys
import pytest

suite = runpy.run_path(sys.argv[1])
with pytest.MonkeyPatch.context() as patch:
    suite['test_schema_round_trip'](Path(sys.argv[2]), patch)
suite['test_dynamic_classes_and_mixins']()
suite['test_invalid_class_name_does_not_touch_output'](Path(sys.argv[2]))
"""
    env = {key: value for key, value in os.environ.items() if not key.startswith("AWE")}
    env.update(database_engine="filebased", database_name="noname", log_dir=str(tmp_path))
    result = subprocess.run(
        [sys.executable, "-c", script, str(Path(__file__).resolve()), str(tmp_path)],
        env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_defaults_reject_arbitrary_repr():
    class Unsupported:
        def __repr__(self):
            raise AssertionError("repr must not be called")

    with pytest.raises(ValueError, match="Unsupported persistent default"):
        _Source().value(Unsupported())


@pytest.mark.postgresql
@pytest.mark.usefixtures("metiswise_database")
def test_schema_round_trip(tmp_path, monkeypatch):
    from common.database.DBMeta import inline
    from metiswise.main.dataitem import DataItem, persistent
    from metiswise.main.hardware import Detector

    class ExportSchemaExample(DataItem):
        """A schema with 'quotes', Unicode λ and\nmultiple lines."""

        count = persistent("Number of exposures", int, 2)
        exposure = persistent("Exposure time", float, 0.25)
        labels = persistent("Labels", str, ["a'b", "λ\nnext"])
        date = persistent("Date", datetime.datetime, datetime.datetime(2026, 11, 10))
        detector = persistent("Detector", Detector, None)
        detectors = persistent("Detectors", Detector, [])
        default_detector = persistent("Lazy detector", Detector, (Detector, (), {"id": 1}))
        default_detectors = persistent("Lazy detectors", Detector, [(Detector, (), {"id": 2})])
        embedded = inline("Embedded detector", Detector, None)
        previous = persistent("Previous version")

    text = ExportSchemaExample.to_python()
    assert text == ExportSchemaExample.to_python()
    assert "filename =" not in text
    assert "def as_frame" not in text

    # Give the round trip a unique name so common's global registration for the
    # original class remains intact during the shared database test session.
    tree = ast.parse(text)
    definition = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    definition.name = "ExportSchemaRoundTrip"
    namespace = {"__name__": __name__}
    exec(compile(tree, "export.py", "exec"), namespace)
    restored = namespace[definition.name]
    assert restored.__bases__ == ExportSchemaExample.__bases__
    assert restored.__doc__ == ExportSchemaExample.__doc__
    assert restored.get_persistent_properties() == ExportSchemaExample.get_persistent_properties()
    for field in restored.get_persistent_properties():
        original = getattr(ExportSchemaExample, field)
        actual = getattr(restored, field)
        assert type(actual) is type(original)
        assert actual.default == original.default
        assert actual.__doc__ == original.__doc__
        assert actual.is_inline == original.is_inline
        if field == "previous":
            assert actual.prop_type is restored
        else:
            assert actual.prop_type == original.prop_type

    monkeypatch.chdir(tmp_path)
    path = ExportSchemaExample.write_python()
    assert path == Path("generated/ExportSchemaExample.py")
    assert path.read_text(encoding="utf-8") == text
    with pytest.raises(FileExistsError):
        ExportSchemaExample.write_python()
    path.write_text("handwritten", encoding="utf-8")
    with pytest.raises(FileExistsError):
        ExportSchemaExample.write_python()
    assert path.read_text() == "handwritten"
    assert ExportSchemaExample.write_python(overwrite=True) == path
    assert path.read_text(encoding="utf-8") == text
    explicit = tmp_path / "elsewhere/schema.py"
    assert ExportSchemaExample.write_python(explicit) == explicit
    assert explicit.read_text(encoding="utf-8") == text


@pytest.mark.postgresql
@pytest.mark.usefixtures("metiswise_database")
def test_dynamic_classes_and_mixins():
    from common.database.DBMeta import DBMixin
    from metiswise.main.dataitem import DataItem, persistent
    from metiswise.main.raw import LM_IMAGE_STD_RAW, Raw, RawLmImage
    from metiswise.main.pro import Pro

    dynamic_pro = next(iter(Pro.class_from_procatg.values()))
    for cls in (Raw, LM_IMAGE_STD_RAW, RawLmImage, dynamic_pro):
        text = cls.to_python()
        tree = ast.parse(text)
        definition = next(node for node in tree.body if isinstance(node, ast.ClassDef))
        assert definition.name == cls.__name__
        assert len(definition.bases) == len(cls.__bases__)
        compile(text, "schema.py", "exec")
    assert "    pass\n" in LM_IMAGE_STD_RAW.to_python()
    assert "    ra = persistent(" in Raw.to_python()

    class SchemaMixin(DBMixin):
        mixed = persistent("From mixin", int, 3)

    # Exporting a local base must fail explicitly: it cannot be imported by a
    # standalone file. Module-level mixins such as RawLmImage.Image work above.
    class ExportLocalMixin(DataItem, SchemaMixin):
        pass

    with pytest.raises(ValueError, match="Not a Python identifier"):
        ExportLocalMixin.to_python()


@pytest.mark.postgresql
@pytest.mark.usefixtures("metiswise_database")
def test_invalid_class_name_does_not_touch_output(tmp_path):
    from metiswise.main.dataitem import DataItem

    cls = type("NOT-A-PYTHON-NAME", (DataItem,), {})
    path = tmp_path / "invalid.py"
    with pytest.raises(ValueError, match="Not a Python identifier"):
        cls.write_python(path)
    assert not path.exists()
