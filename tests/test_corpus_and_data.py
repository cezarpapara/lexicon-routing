import random
import shutil

from app import constants as c
from app.config import PROJECT_ROOT
from app.services import corpus, data, extraction, quality


def test_bank_categories_and_placeholders():
    bank = corpus.load_bank()
    assert set(m.category for m in bank) == set(c.CATEGORY_MIX)
    for m in bank:
        if m.shape == "two_sided":
            assert "{a}" in m.text and "{b}" in m.text
        elif m.shape == "after":
            assert "{a}" in m.text and "{b}" not in m.text
        elif m.shape == "before":
            assert "{b}" in m.text and "{a}" not in m.text
        elif m.shape == "named":
            assert m.period in c.NAMED_PERIODS
        else:
            assert "{" not in m.text


def test_anchored_instantiation_contains_the_anchor():
    rng = random.Random(7)
    bank = corpus.load_bank()
    for anchor in (8.2, 9.5, 12.0, 14.7, 16.8):
        for category in ("binding", "strong", "mild"):
            for _ in range(20):
                m = corpus.message_for(category, rng, anchor, bank)
                assert m.start_h <= anchor <= m.end_h, (m, anchor)
                assert "{" not in m.text


def test_instantiated_hours_are_recovered_by_the_rules():
    rng = random.Random(3)
    bank = [m for m in corpus.load_bank() if m.shape in ("two_sided", "after", "before")]
    recovered = 0
    for m in bank:
        text = corpus.instantiate(m, rng)
        assert "{" not in text.text
        recovered += extraction.interval(text.text) == (text.start_h, text.end_h)
    assert recovered / len(bank) > 0.9


def test_build_from_source_day(tmp_path, monkeypatch):
    shutil.copytree(PROJECT_ROOT / "data" / "source" / "DAY_1", tmp_path / "source" / "DAY_1")
    shutil.copytree(PROJECT_ROOT / "data" / "corpus", tmp_path / "corpus")
    monkeypatch.setattr(data.get_settings(), "DATA_DIR", tmp_path)
    built = data.build_instances()
    assert built and all(len(data.load_instance(i).stops) >= c.MIN_TRIP_STOPS for i in built)
    instance = data.load_instance(built[0])
    assert sorted(instance.dispatcher_route) == [n.id for n in instance.stops]
    assert all(n.message for n in instance.stops)
    assert data.concorde_tour(built[0]) is not None


def test_spearman_of_identical_rankings_is_one():
    assert quality.spearman([0.1, 0.5, 0.9, 0.5], [0.0, 0.5, 1.0, 0.5]) == 1.0
