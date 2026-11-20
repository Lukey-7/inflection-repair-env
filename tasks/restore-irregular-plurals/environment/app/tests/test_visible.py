import inflection


def test_person():
    assert inflection.pluralize("person") == "people"
    assert inflection.singularize("people") == "person"


def test_child_compound():
    assert inflection.pluralize("node_child") == "node_children"
