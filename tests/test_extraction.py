from app import constants as c
from app.services import extraction, lexicon


def test_two_sided_intervals():
    assert extraction.interval("between 10 and 12 please") == (10.0, 12.0)
    assert extraction.interval("from 9:30 to 11") == (9.5, 11.0)
    assert extraction.interval("in the 10-12 slot") == (10.0, 12.0)
    assert extraction.interval("2 pm - 4 pm works") == (14.0, 16.0)


def test_one_sided_bounds_and_afternoon_reading():
    assert extraction.interval("after 3, I'm at work") == (15.0, 17.0)
    assert extraction.interval("not before 15:00!!") == (15.0, 17.0)
    assert extraction.interval("until 11 am only") == (8.0, 11.0)
    assert extraction.interval("by 4pm at the latest") == (8.0, 16.0)
    assert extraction.interval("from 10 onwards") == (10.0, 17.0)


def test_named_periods_and_points():
    assert extraction.interval("in the morning please") == c.NAMED_PERIODS["morning"]
    assert extraction.interval("late afternoon is better") == c.NAMED_PERIODS["late_afternoon"]
    assert extraction.interval("around noon") == c.NAMED_PERIODS["noon"]
    assert extraction.interval("around 2 would be nice") == (13.0, 15.0)


def test_no_interval_for_non_temporal_numbers():
    assert extraction.interval("Please text me when you're 15 minutes away.") == (None, None)
    assert extraction.interval("The gate code is 2580, drive in.") == (None, None)
    assert extraction.interval("it's number 27 not 72") == (None, None)


def test_urgency_uses_strongest_marker_and_attenuation():
    assert lexicon.urgency("please, any time is fine") == 0.0
    assert lexicon.urgency("I would prefer after 10, I'm at work") == 0.45      # not 0.45 + 0.45
    assert lexicon.urgency("must be between 10 and 12") == 0.7
    assert lexicon.urgency("maybe between 12 and 2? not a must") <= 0.30       # hedge caps the score


def test_bands_and_hard_windows():
    binding = extraction.extract("Only after 3 pm, no other option.")
    assert binding.band == "binding" and binding.hard and binding.start_h == 15.0
    soft = extraction.extract("preferably after 3 pm")
    assert soft.band == "strong" and not soft.hard
    nothing = extraction.extract("Please bring a trolley, the boxes are heavy.")
    assert nothing.urgency == 0.0 and not nothing.has_window


def test_longest_match_masks_shorter_terms():
    terms = [m.term.text for m in lexicon.find_terms("i would prefer the morning")]
    assert terms == ["i would prefer"]
