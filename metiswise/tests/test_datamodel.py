"""Tests for `metiswise` data model."""

from common.config.Environment import Env


def test_imports():
    """Test whether the datamodel can be imported."""
    db_engine = Env["database_engine"]
    # TODO: Enable when classcache is enabled for filebased backend.  See
    #  https://gitlab.astro-wise.org/omegacen/common/-/merge_requests/1090
    # Env["database_engine"] = "filebased"
    # noinspection PyUnresolvedReferences
    import metiswise.main.aweimports
    Env["database_engine"] = db_engine

