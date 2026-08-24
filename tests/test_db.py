"""Tests for database models and DBManager."""
import pytest
from mcs_cvor.database.db_manager import DBManager


@pytest.fixture
def db():
    """In-memory SQLite database."""
    mgr = DBManager(db_path=":memory:")
    return mgr


def test_seed_creates_10_bases(db):
    bases = db.get_all_bases()
    assert len(bases) == 10


def test_base_has_cvor_system(db):
    bases = db.get_all_bases()
    for base in bases:
        assert len(base.cvor_systems) >= 1


def test_base_has_shelter_layout(db):
    with db.get_session() as session:
        from mcs_cvor.database.models import AirForceBase, ShelterLayout
        base = session.query(AirForceBase).first()
        layout = session.query(ShelterLayout).filter_by(base_id=base.id).first()
        assert layout is not None


def test_add_base(db):
    db.add_base("Test Base", "TST_BASE", "Test City", -26.0, 28.0, "10.0.0.1", 112.0, "TST")
    bases = db.get_all_bases()
    codes = [b.code for b in bases]
    assert "TST_BASE" in codes


def test_delete_base(db):
    db.add_base("Del Base", "DEL_BASE", "Del City", -27.0, 29.0, "10.0.0.2", 113.0, "DEL")
    bases = db.get_all_bases()
    target = next(b for b in bases if b.code == "DEL_BASE")
    db.delete_base(target.id)
    bases2 = db.get_all_bases()
    assert all(b.code != "DEL_BASE" for b in bases2)


def test_update_cvor_status(db):
    bases = db.get_all_bases()
    cvor = bases[0].cvor_systems[0]
    db.update_cvor_status(cvor.system_id, "ACTIVE", freq=113.8, power=50, vswr=1.2)
    with db.get_session() as session:
        from mcs_cvor.database.models import CVORSystem
        updated = session.query(CVORSystem).filter_by(system_id=cvor.system_id).first()
        assert updated.status == "ACTIVE"


def test_split_base(db):
    bases = db.get_all_bases()
    parent = bases[0]
    db.split_base(parent.id, "Split Test", "SPL_TST", "Testing split", -25.0, 28.5)
    all_bases = db.get_all_bases()
    codes = [b.code for b in all_bases]
    assert "SPL_TST" in codes


def test_settings_history(db):
    bases = db.get_all_bases()
    cvor = bases[0].cvor_systems[0]
    db.save_settings_history(cvor.id, "FREQ", "113.8", "114.0")
    history = db.get_settings_history(cvor.id)
    assert len(history) >= 1
    assert history[0].parameter == "FREQ"
