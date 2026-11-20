import inflection


def test_simple_ordinals():
    assert inflection.ordinalize(1) == "1st"
    assert inflection.ordinalize(2) == "2nd"
    assert inflection.ordinalize(3) == "3rd"
    assert inflection.ordinalize(4) == "4th"


def test_teens():
    assert inflection.ordinalize(11) == "11th"
    assert inflection.ordinalize(12) == "12th"
    assert inflection.ordinalize(13) == "13th"
