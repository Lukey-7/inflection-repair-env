import inflection


def test_basic():
    assert inflection.parameterize("Donald E. Knuth") == "donald-e-knuth"


def test_underscore_separator():
    assert inflection.parameterize("Donald E. Knuth", "_") == "donald_e_knuth"


def test_no_separator():
    assert inflection.parameterize("Donald E. Knuth", "") == "donaldeknuth"
