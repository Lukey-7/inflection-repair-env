import inflection


def test_titleize_acronym():
    assert inflection.titleize("HTMLTidyGenerator") == "Html Tidy Generator"


def test_tableize_acronym():
    assert inflection.tableize("HTMLPage") == "html_pages"


def test_humanize():
    assert inflection.humanize("paid") == "Paid"
    assert inflection.humanize("author_id") == "Author"
