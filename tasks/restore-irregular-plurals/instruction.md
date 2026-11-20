# Restore irregular plurals (partial credit)

A refactor deleted the library's support for irregular nouns, so for example
`pluralize("person")` now returns `"persons"` and `singularize("children")`
returns `"children"`.

Restore support for exactly these irregular pairs (singular -> plural):

```
person -> people     man   -> men      human  -> humans   child  -> children
sex    -> sexes      move  -> moves    cow    -> kine     zombie -> zombies
```

Requirements:

- Both `pluralize` and `singularize` must handle them, and so must anything
  built on them (`tableize`).
- They must also apply when the irregular word ends a longer word:
  `salesperson -> salespeople`, `node_child -> node_children`,
  `spokesman -> spokesmen`, `woman -> women`.
- Keep the case of the first letter: `Person -> People`, `Child -> Children`.
- Pluralizing a plural irregular word leaves it unchanged
  (`people -> people`), and singularizing a singular one leaves it unchanged.
- Note that `human -> humans` is listed on purpose: it must not become
  `humen`.

**Partial credit:** your reward is the fraction of hidden irregular-noun checks
that pass, but it drops to 0 if any other behaviour of the library breaks.

## Rules

- Work in `/app`. The library is `/app/inflection/__init__.py`.
- **Only `/app/inflection/__init__.py` is graded.** Put your whole fix in that
  file; other files you create or edit are ignored.
- Keep every public function name and signature unchanged, and keep the
  library dependency-free (standard library only).
- A few visible tests are in `/app/tests` (`cd /app && python -m pytest -q`).
  They are deliberately incomplete. The hidden grader checks many more inputs,
  including randomly generated ones, and also checks that every other function
  in the library still behaves correctly.
