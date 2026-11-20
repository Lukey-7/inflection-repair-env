"""Hidden test-case generation for the inflection-repair tasks.

Every case is ``(group, func, args)``. Expected outputs are NOT stored here:
the grader computes them by running the pristine reference implementation on
the same inputs (differential testing). That lets us generate fresh random
inputs on every grading run, so memorising a fixed list of answers is useless.

Groups:
  ordinal           ordinal / ordinalize
  case              underscore / camelize / humanize / titleize / tableize / dasherize
  parameterize      parameterize (single-character or empty separators)
  plural_regular    pluralize / singularize on regular and uncountable words
  plural_irregular  pluralize / singularize / tableize on irregular words
  misc              transliterate and odd corners

A task names its *target* groups; every other group acts as a *guard* that
must stay fully correct (so "fixing" one function by breaking another fails).
"""

# --- fixed inputs taken from upstream test_inflection.py (MIT) -------------

SINGULAR_TO_PLURAL = (
    ("search", "searches"), ("switch", "switches"), ("fix", "fixes"),
    ("box", "boxes"), ("process", "processes"), ("address", "addresses"),
    ("case", "cases"), ("stack", "stacks"), ("wish", "wishes"),
    ("fish", "fish"), ("jeans", "jeans"), ("funky jeans", "funky jeans"),
    ("category", "categories"), ("query", "queries"),
    ("ability", "abilities"), ("agency", "agencies"), ("movie", "movies"),
    ("archive", "archives"), ("index", "indices"), ("wife", "wives"),
    ("safe", "saves"), ("half", "halves"), ("move", "moves"),
    ("salesperson", "salespeople"), ("person", "people"),
    ("spokesman", "spokesmen"), ("man", "men"), ("woman", "women"),
    ("basis", "bases"), ("diagnosis", "diagnoses"),
    ("diagnosis_a", "diagnosis_as"), ("datum", "data"), ("medium", "media"),
    ("stadium", "stadia"), ("analysis", "analyses"),
    ("node_child", "node_children"), ("child", "children"),
    ("experience", "experiences"), ("day", "days"), ("comment", "comments"),
    ("foobar", "foobars"), ("newsletter", "newsletters"),
    ("old_news", "old_news"), ("news", "news"), ("series", "series"),
    ("species", "species"), ("quiz", "quizzes"),
    ("perspective", "perspectives"), ("ox", "oxen"),
    ("passerby", "passersby"), ("photo", "photos"), ("buffalo", "buffaloes"),
    ("tomato", "tomatoes"), ("potato", "potatoes"), ("dwarf", "dwarves"),
    ("elf", "elves"), ("information", "information"),
    ("equipment", "equipment"), ("bus", "buses"), ("status", "statuses"),
    ("status_code", "status_codes"), ("mouse", "mice"), ("louse", "lice"),
    ("house", "houses"), ("octopus", "octopi"), ("virus", "viri"),
    ("alias", "aliases"), ("portfolio", "portfolios"),
    ("vertex", "vertices"), ("matrix", "matrices"),
    ("matrix_fu", "matrix_fus"), ("axis", "axes"), ("testis", "testes"),
    ("crisis", "crises"), ("rice", "rice"), ("shoe", "shoes"),
    ("horse", "horses"), ("prize", "prizes"), ("edge", "edges"),
    ("cow", "kine"), ("database", "databases"), ("human", "humans"),
)

IRREGULAR_STEMS = ("person", "people", "man", "men", "child", "children",
                   "cow", "kine", "move", "moves", "human", "humans",
                   "sex", "sexes", "zombie", "zombies")

CAMEL_INPUTS = ("Product", "SpecialGuest", "ApplicationController",
                "Area51Controller", "HTMLTidy", "HTMLTidyGenerator",
                "FreeBSD", "HTML")
SNAKE_INPUTS = ("product", "special_guest", "application_controller",
                "area51_controller", "html_tidy", "Camel_Case", "Capital")
HUMANIZE_INPUTS = ("employee_salary", "employee_id", "underground")
TITLEIZE_INPUTS = ("active_record", "ActiveRecord", "action web service",
                   "Action Web Service", "Action web service",
                   "actionwebservice", "Actionwebservice", "david's code",
                   "David's code", "david's Code", "ana índia", "Ana Índia",
                   "man from the boondocks", "x-men: the last stand",
                   "TheManWithoutAPast", "raiders_of_the_lost_ark")
DASHERIZE_INPUTS = ("street", "street_address", "person_street_address")
TABLEIZE_INPUTS = ("RawScaledScorer", "egg_and_ham", "fancyCategory",
                   "Country")
TABLEIZE_IRREGULAR = ("person", "ChildToy", "_RecipeIngredient", "SalesPerson")
PARAM_INPUTS = ("Donald E. Knuth", "Random text with *(bad)* characters",
                "Allow_Under_Scores", "Trailing bad characters!@#",
                "!@#Leading bad characters", "Squeeze   separators",
                "Test with + sign", "Test with malformed utf8 \251",
                "With-some-dashes", "Retain_underscore", "Malmö", "Garçons",
                "Ops\331", "Ærøskøbing", "Aßlar", "Japanese: 日本語")
ORDINAL_INPUTS = ("-1", "-2", "-3", "-4", "-11", "-12", "-13", "-21", "-101",
                  "-111", "-1001", "0", "1", "2", "3", "4", "10", "11", "12",
                  "13", "14", "20", "21", "22", "23", "24", "100", "101",
                  "102", "103", "104", "110", "111", "112", "113", "1000",
                  "1001")

# --- random generators ------------------------------------------------------

_WORDS = ("device", "type", "user", "account", "order", "item", "tidy",
          "error", "status", "box", "query", "node", "special", "guest",
          "area51", "record", "action", "web", "service", "paid", "valid",
          "squid", "android", "invalid", "raw", "scaled", "scorer", "egg",
          "ham", "fancy", "category", "page", "layer", "token", "v2")
_ACRONYMS = ("HTML", "IO", "URL", "API", "ID", "HTTP", "XML", "SQL", "BSD")


def _token(rng):
    if rng.random() < 0.3:
        return rng.choice(_ACRONYMS)
    return rng.choice(_WORDS)


def _identifier(rng):
    toks = [_token(rng) for _ in range(rng.randint(1, 4))]
    if rng.random() < 0.25:
        toks.append(rng.choice(("id", "Id", "ID", "paid", "valid")))
    style = rng.randrange(6)
    if style == 0:  # UpperCamel, acronyms kept upper
        return "".join(t if t.isupper() else t.capitalize() for t in toks)
    if style == 1:  # lowerCamel
        s = "".join(t if t.isupper() else t.capitalize() for t in toks)
        return s[0].lower() + s[1:]
    if style == 2:
        return "_".join(t.lower() for t in toks)
    if style == 3:
        return "-".join(t.lower() for t in toks)
    if style == 4:
        return " ".join(t.lower() for t in toks)
    return "_".join(toks)  # mixed snake


def _ordinal_cases(rng, n):
    cases = []
    for raw in ORDINAL_INPUTS:
        cases.append(("ordinal", (raw,)))
        cases.append(("ordinalize", (raw,)))
        cases.append(("ordinalize", (int(raw),)))
    for _ in range(n):
        kind = rng.randrange(4)
        if kind == 0:
            num = rng.randint(-10 ** 6, 10 ** 6)
        elif kind == 1:  # the tricky teens: ...11, ...12, ...13
            num = rng.randint(0, 10 ** 5) * 100 + rng.choice((11, 12, 13))
        elif kind == 2:  # ...1, ...2, ...3 outside the teens
            num = rng.randint(0, 10 ** 5) * 10 + rng.choice((1, 2, 3))
        else:
            num = rng.randint(-10 ** 18, 10 ** 18)
        if rng.random() < 0.5:
            num = -num
        arg = str(num) if rng.random() < 0.3 else num
        cases.append((rng.choice(("ordinal", "ordinalize")), (arg,)))
    return cases


def _case_cases(rng, n):
    cases = []
    for s in CAMEL_INPUTS:
        cases += [("underscore", (s,)), ("titleize", (s,)),
                  ("tableize", (s,))]
    for s in SNAKE_INPUTS:
        cases += [("camelize", (s,)), ("camelize", (s, False)),
                  ("humanize", (s,))]
    for s in HUMANIZE_INPUTS:
        cases.append(("humanize", (s,)))
    for s in TITLEIZE_INPUTS:
        cases.append(("titleize", (s,)))
    for s in DASHERIZE_INPUTS:
        cases.append(("dasherize", (s,)))
    for s in TABLEIZE_INPUTS:
        cases.append(("tableize", (s,)))
    funcs = ("underscore", "humanize", "titleize", "tableize", "camelize",
             "dasherize")
    for _ in range(n):
        cases.append((rng.choice(funcs), (_identifier(rng),)))
    return cases


_PARAM_POOL = ("abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
               "0123456789" "      --__" "!@#$%^&*().,;:'\"/?+=|~"
               "éüñçøÆßÅÖ日本\t")
PARAM_SEPARATORS = ("-", "_", "", ".", "+", "|", "~")


def _parameterize_cases(rng, n):
    cases = []
    for s in PARAM_INPUTS:
        cases.append(("parameterize", (s,)))
        cases.append(("parameterize", (s, "_")))
        cases.append(("parameterize", (s, "")))
    for _ in range(n):
        s = "".join(rng.choice(_PARAM_POOL)
                    for _ in range(rng.randint(0, 30)))
        if rng.random() < 0.3:
            cases.append(("parameterize", (s,)))
        else:
            cases.append(("parameterize", (s, rng.choice(PARAM_SEPARATORS))))
    return cases


def _is_irregular(word):
    w = word.lower()
    return any(w.endswith(stem) for stem in IRREGULAR_STEMS)


def _plural_regular_cases(rng, n):
    cases = []
    for singular, plural in SINGULAR_TO_PLURAL:
        if _is_irregular(singular) or _is_irregular(plural):
            continue
        for s, p in ((singular, plural),
                     (singular.capitalize(), plural.capitalize())):
            cases += [("pluralize", (s,)), ("singularize", (p,)),
                      ("pluralize", (p,))]
    cases += [("pluralize", ("",)), ("pluralize", ("plurals",)),
              ("pluralize", ("Plurals",)), ("singularize", ("word",)),
              ("singularize", ("sponsors",))]
    return cases


_IRREGULAR_PREFIXES = ("", "", "", "node_", "sales", "spokes", "wo", "old_",
                       "Big", "re")


def _plural_irregular_cases(rng, n):
    cases = []
    for singular, plural in SINGULAR_TO_PLURAL:
        if _is_irregular(singular) or _is_irregular(plural):
            for s, p in ((singular, plural),
                         (singular.capitalize(), plural.capitalize())):
                cases += [("pluralize", (s,)), ("singularize", (p,)),
                          ("pluralize", (p,))]
    for s in TABLEIZE_IRREGULAR:
        cases.append(("tableize", (s,)))
    for _ in range(n):
        word = rng.choice(_IRREGULAR_PREFIXES) + rng.choice(IRREGULAR_STEMS)
        if rng.random() < 0.3:
            word = word.capitalize()
        cases.append((rng.choice(("pluralize", "singularize")), (word,)))
    return cases


def _misc_cases(rng, n):
    cases = [("transliterate", (s,)) for s in PARAM_INPUTS]
    cases += [("camelize", ("Capital", False)), ("camelize", ("Camel_Case",))]
    return cases


GROUPS = {
    "ordinal": _ordinal_cases,
    "case": _case_cases,
    "parameterize": _parameterize_cases,
    "plural_regular": _plural_regular_cases,
    "plural_irregular": _plural_irregular_cases,
    "misc": _misc_cases,
}


def build_cases(config, rng):
    """Return a list of (role, group, func, args); role is target|guard."""
    targets = set(config["target_groups"])
    out = []
    for name, gen in GROUPS.items():
        role = "target" if name in targets else "guard"
        n = config.get("n_random", 300) if role == "target" else \
            config.get("n_guard_random", 40)
        for func, args in gen(rng, n):
            out.append((role, name, func, list(args)))
    return out
