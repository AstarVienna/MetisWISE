"""Database round trips for raw exposures."""

import pytest


pytestmark = pytest.mark.postgresql


def test_raw_commit_and_select_all():
    # Persistent classes must only be imported after database initialization.
    from common.database.Context import context
    from common.database.Database import database
    from metiswise.main.raw import Raw

    raw = Raw()
    raw.ra = 123.45
    raw.dec = -54.321
    raw.commit()
    object_id = raw.object_id

    # Reconnect to clear the object cache and read the committed row from disk.
    database.disconnect()
    database.connect()
    try:
        matches = [item for item in Raw.select_all() if item.object_id == object_id]
        assert len(matches) == 1
        retrieved = matches[0]
        assert isinstance(retrieved, Raw)
        assert retrieved is not raw
        assert retrieved.ra == pytest.approx(123.45)
        assert retrieved.dec == pytest.approx(-54.321)
    finally:
        context.delete(Raw(object_id=object_id), commit=True)
